import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import easyocr
import numpy as np
import torch


CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
NORMALIZE_RE = re.compile(r"[^0-9A-Za-z\u3400-\u9fff]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR burned-in subtitles at ASR segment midpoints and ASR gaps."
    )
    parser.add_argument("video_dir", type=Path)
    parser.add_argument("transcript_dir", type=Path)
    parser.add_argument("--only-id")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--episode-start", type=int, default=1)
    parser.add_argument("--episode-end", type=int, default=10_000)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--job-name", default="all")
    return parser.parse_args()


def normalize(text: str) -> str:
    return NORMALIZE_RE.sub("", text).lower()


def similarity(left: str, right: str) -> float:
    left_normalized = normalize(left)
    right_normalized = normalize(right)
    if not left_normalized or not right_normalized:
        return 0.0
    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def sample_points(segments: list[dict], duration: float) -> list[dict]:
    points = []
    for index, segment in enumerate(segments):
        start = float(segment["start"])
        end = float(segment["end"])
        points.append(
            {
                "time": round((start + end) / 2, 2),
                "source": "segment",
                "segment_index": index,
                "asr_text": segment["text"],
            }
        )

    boundaries = [(0.0, float(segments[0]["start"]))] if segments else []
    boundaries.extend(
        (float(left["end"]), float(right["start"]))
        for left, right in zip(segments, segments[1:])
    )
    if segments:
        boundaries.append((float(segments[-1]["end"]), duration))
    else:
        boundaries.append((0.0, duration))

    for start, end in boundaries:
        if end - start < 1.2:
            continue
        time = start + 0.6
        while time < end:
            points.append(
                {
                    "time": round(time, 2),
                    "source": "gap",
                    "segment_index": None,
                    "asr_text": "",
                }
            )
            time += 1.0

    # Batched ASR uses longer segments. Uniform subtitle samples preserve
    # short on-screen lines and quotes even when ASR has no matching segment.
    time = 0.6
    while time < duration:
        points.append(
            {
                "time": round(time, 2),
                "source": "uniform",
                "segment_index": None,
                "asr_text": "",
            }
        )
        time += 1.5

    points.sort(key=lambda point: point["time"])
    deduped = []
    for point in points:
        if deduped and abs(point["time"] - deduped[-1]["time"]) < 0.25:
            if point["source"] == "segment":
                deduped[-1] = point
            continue
        deduped.append(point)
    return deduped


def read_frame_crop(capture: cv2.VideoCapture, timestamp: float) -> np.ndarray:
    capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    ok, frame = capture.read()
    if not ok or frame is None:
        raise RuntimeError(f"Cannot read frame at {timestamp:.2f}s")
    height = frame.shape[0]
    crop = frame[int(height * 0.62) : height, :]
    if crop.shape[1] > 960:
        scale = 960 / crop.shape[1]
        crop = cv2.resize(
            crop,
            (960, max(1, int(crop.shape[0] * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return crop


def choose_subtitle(result: list, crop_height: int) -> tuple[str, list[dict]]:
    candidates = []
    for bbox, text, confidence in result:
        center_y = sum(point[1] for point in bbox) / len(bbox)
        candidate = {
            "text": text.strip(),
            "confidence": round(float(confidence), 4),
            "center_y_ratio": round(center_y / crop_height, 4),
        }
        if candidate["text"]:
            candidates.append(candidate)

    selected = [
        candidate
        for candidate in candidates
        if candidate["center_y_ratio"] >= 0.38
        and CHINESE_RE.search(candidate["text"])
    ]
    if not selected:
        selected = [
            candidate
            for candidate in candidates
            if CHINESE_RE.search(candidate["text"])
        ]
    selected.sort(key=lambda candidate: candidate["center_y_ratio"])
    return "".join(candidate["text"] for candidate in selected), candidates


def process_one(
    reader: easyocr.Reader,
    video_path: Path,
    transcript_path: Path,
    output_path: Path,
    batch_size: int,
) -> dict:
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    segments = transcript["segments"]
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    duration = capture.get(cv2.CAP_PROP_FRAME_COUNT) / max(
        capture.get(cv2.CAP_PROP_FPS), 1
    )
    points = sample_points(segments, duration)

    results = []
    for offset in range(0, len(points), batch_size):
        batch_points = points[offset : offset + batch_size]
        crops = [read_frame_crop(capture, point["time"]) for point in batch_points]
        batch_results = reader.readtext_batched(
            crops,
            batch_size=min(batch_size, len(crops)),
            workers=0,
            decoder="greedy",
            detail=1,
            paragraph=False,
        )
        for point, crop, ocr_result in zip(batch_points, crops, batch_results):
            ocr_text, all_candidates = choose_subtitle(ocr_result, crop.shape[0])
            results.append(
                {
                    **point,
                    "ocr_text": ocr_text,
                    "similarity": round(similarity(point["asr_text"], ocr_text), 4)
                    if point["source"] == "segment"
                    else None,
                    "ocr_candidates": all_candidates,
                }
            )
        print(
            f"OCR {transcript['aweme_id']} {min(offset + batch_size, len(points))}/{len(points)}",
            flush=True,
        )
    capture.release()

    subtitle_sequence = []
    previous = ""
    for result in results:
        normalized = normalize(result["ocr_text"])
        if not normalized or normalized == previous:
            continue
        previous = normalized
        subtitle_sequence.append(
            {"time": result["time"], "text": result["ocr_text"]}
        )

    review_candidates = [
        result
        for result in results
        if result["ocr_text"]
        and (
            result["source"] in {"gap", "uniform"}
            or result["similarity"] is not None
            and result["similarity"] < 0.82
        )
    ]
    payload = {
        "aweme_id": transcript["aweme_id"],
        "video": str(video_path),
        "transcript": str(transcript_path),
        "duration": round(duration, 2),
        "sample_count": len(results),
        "subtitle_sequence": subtitle_sequence,
        "review_candidates": review_candidates,
        "samples": results,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def main() -> int:
    args = parse_args()
    transcript_paths = sorted(args.transcript_dir.glob("*.transcript.small.json"))
    if args.only_id:
        transcript_paths = [
            path for path in transcript_paths if path.name.startswith(args.only_id)
        ]
    if not args.only_id:
        selected_paths = []
        for path in transcript_paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            episode = int(payload.get("episode") or 0)
            if args.episode_start <= episode <= args.episode_end:
                selected_paths.append(path)
        transcript_paths = selected_paths
    torch.set_num_threads(args.cpu_threads)
    print(f"Loading EasyOCR; transcript_count={len(transcript_paths)}", flush=True)
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    failures = {}
    completed = 0
    for index, transcript_path in enumerate(transcript_paths, start=1):
        aweme_id = transcript_path.name.split(".")[0]
        video_path = args.video_dir / f"{aweme_id}.mp4"
        output_path = args.transcript_dir / f"{aweme_id}.subtitle_ocr.json"
        if output_path.exists():
            completed += 1
            print(f"SKIP {index}/{len(transcript_paths)} {aweme_id}", flush=True)
            continue
        try:
            process_one(
                reader,
                video_path,
                transcript_path,
                output_path,
                args.batch_size,
            )
            completed += 1
            print(f"DONE {index}/{len(transcript_paths)} {aweme_id}", flush=True)
        except Exception as exc:
            failures[aweme_id] = f"{type(exc).__name__}: {exc}"
            print(f"FAILED {aweme_id}: {exc}", flush=True)
        (args.transcript_dir / f"series_subtitle_ocr_progress_{args.job_name}.json").write_text(
            json.dumps(
                {
                    "total": len(transcript_paths),
                    "completed": completed,
                    "failures": failures,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
