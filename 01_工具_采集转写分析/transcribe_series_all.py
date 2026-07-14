import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from faster_whisper import BatchedInferencePipeline, WhisperModel

from collect_public_transcripts import download, first_video_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and resumably transcribe every video in a Douyin series JSON."
    )
    parser.add_argument("series_json", type=Path)
    parser.add_argument("video_dir", type=Path)
    parser.add_argument("transcript_dir", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--download-workers", type=int, default=3)
    parser.add_argument("--episode-start", type=int, default=1)
    parser.add_argument("--episode-end", type=int, default=10_000)
    parser.add_argument("--cpu-threads", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--job-name", default="all")
    return parser.parse_args()


def transcript_path(transcript_dir: Path, aweme_id: str) -> Path:
    return transcript_dir / f"{aweme_id}.transcript.small.json"


def has_complete_transcript(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool((payload.get("transcript") or "").strip())


def download_one(item: dict, video_dir: Path) -> tuple[str, str]:
    aweme_id = item["aweme_id"]
    video_path = video_dir / f"{aweme_id}.mp4"
    if video_path.exists() and video_path.stat().st_size > 0:
        return aweme_id, "existing"
    download(first_video_url(item), video_path)
    return aweme_id, "downloaded"


def write_transcript(
    item: dict,
    episode: int,
    model_name: str,
    segments: list[dict],
    output_path: Path,
) -> None:
    transcript = "".join(segment["text"] for segment in segments)
    payload = {
        "episode": episode,
        "aweme_id": item["aweme_id"],
        "author": (item.get("author") or {}).get("nickname", ""),
        "unique_id": (item.get("author") or {}).get("unique_id", ""),
        "create_time": item.get("create_time"),
        "desc": item.get("desc", ""),
        "caption": item.get("caption", ""),
        "chapter_abstract": item.get("chapter_abstract", ""),
        "chapter_list": item.get("chapter_list", []),
        "duration_ms": item.get("duration"),
        "statistics": item.get("statistics", {}),
        "url": f"https://www.douyin.com/video/{item['aweme_id']}",
        "model": f"faster-whisper-{model_name}",
        "segments": segments,
        "transcript": transcript,
        "transcription_note": "faster-whisper small / CPU int8；原始稿，需结合画面字幕生成校订稿",
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_progress(
    transcript_dir: Path,
    items: list[dict],
    failures: dict[str, str],
    job_name: str,
) -> None:
    completed = []
    for item in items:
        aweme_id = item["aweme_id"]
        path = transcript_path(transcript_dir, aweme_id)
        if has_complete_transcript(path):
            completed.append(aweme_id)
    progress = {
        "total": len(items),
        "completed": len(completed),
        "completed_ids": completed,
        "failures": failures,
    }
    (transcript_dir / f"series_transcription_small_progress_{job_name}.json").write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    args.video_dir.mkdir(parents=True, exist_ok=True)
    args.transcript_dir.mkdir(parents=True, exist_ok=True)

    series = json.loads(args.series_json.resolve().read_text(encoding="utf-8"))
    items = sorted(
        series["aweme_list"],
        key=lambda item: (item.get("series_play_info") or {}).get(
            "series_aweme_index", 0
        ),
    )
    items = [
        item
        for item in items
        if args.episode_start
        <= (item.get("series_play_info") or {}).get("series_aweme_index", 0)
        <= args.episode_end
    ]
    pending_items = [
        item
        for item in items
        if not has_complete_transcript(
            transcript_path(args.transcript_dir, item["aweme_id"])
        )
    ]
    print(
        f"Series total={len(items)} completed={len(items) - len(pending_items)} pending={len(pending_items)}",
        flush=True,
    )

    failures: dict[str, str] = {}
    if pending_items:
        print(
            f"Downloading {len(pending_items)} missing source videos with {args.download_workers} workers...",
            flush=True,
        )
        with ThreadPoolExecutor(max_workers=args.download_workers) as executor:
            futures = {
                executor.submit(download_one, item, args.video_dir): item
                for item in pending_items
            }
            completed_downloads = 0
            for future in as_completed(futures):
                item = futures[future]
                aweme_id = item["aweme_id"]
                try:
                    _, status = future.result()
                    completed_downloads += 1
                    print(
                        f"DOWNLOAD {completed_downloads}/{len(pending_items)} {aweme_id} {status}",
                        flush=True,
                    )
                except Exception as exc:  # continue so successful downloads remain reusable
                    failures[aweme_id] = f"download: {type(exc).__name__}: {exc}"
                    print(f"DOWNLOAD_FAILED {aweme_id}: {exc}", flush=True)

    transcribable = [
        item
        for item in pending_items
        if item["aweme_id"] not in failures
        and (args.video_dir / f"{item['aweme_id']}.mp4").exists()
    ]
    if transcribable:
        print(
            f"Loading faster-whisper model={args.model} cpu_threads={args.cpu_threads}",
            flush=True,
        )
        model = WhisperModel(
            args.model,
            device="cpu",
            compute_type="int8",
            cpu_threads=args.cpu_threads,
            num_workers=1,
        )
        batched_model = BatchedInferencePipeline(model=model)
        for index, item in enumerate(transcribable, start=1):
            aweme_id = item["aweme_id"]
            episode = (item.get("series_play_info") or {}).get(
                "series_aweme_index", 0
            )
            video_path = args.video_dir / f"{aweme_id}.mp4"
            output_path = transcript_path(args.transcript_dir, aweme_id)
            print(
                f"TRANSCRIBE {index}/{len(transcribable)} episode={episode} id={aweme_id}",
                flush=True,
            )
            try:
                raw_segments, _ = batched_model.transcribe(
                    str(video_path),
                    language="zh",
                    vad_filter=True,
                    batch_size=8,
                )
                segments = []
                for segment in raw_segments:
                    text = segment.text.strip()
                    if text:
                        segments.append(
                            {
                                "start": round(segment.start, 2),
                                "end": round(segment.end, 2),
                                "text": text,
                            }
                        )
                text = "".join(segment["text"] for segment in segments)
                if not text.strip():
                    raise RuntimeError("empty transcript")
                write_transcript(item, episode, args.model, segments, output_path)
                print(
                    f"TRANSCRIBED episode={episode} id={aweme_id} chars={len(text)}",
                    flush=True,
                )
            except Exception as exc:  # keep processing remaining episodes
                failures[aweme_id] = f"transcribe: {type(exc).__name__}: {exc}"
                print(f"TRANSCRIBE_FAILED {aweme_id}: {exc}", flush=True)
            write_progress(args.transcript_dir, items, failures, args.job_name)

    write_progress(args.transcript_dir, items, failures, args.job_name)
    completed = sum(
        has_complete_transcript(transcript_path(args.transcript_dir, item["aweme_id"]))
        for item in items
    )
    print(
        f"DONE completed={completed}/{len(items)} failures={len(failures)}",
        flush=True,
    )
    return 0 if completed == len(items) else 2


if __name__ == "__main__":
    sys.exit(main())
