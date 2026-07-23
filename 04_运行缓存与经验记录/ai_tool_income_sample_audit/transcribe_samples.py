import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "samples.raw.json"
AUDIO_DIR = ROOT / "audio"
TRANSCRIPT_DIR = ROOT / "transcripts"
MAX_ANALYSIS_SECONDS = 180


def audio_url(detail: dict) -> str:
    tracks = (detail.get("video") or {}).get("bit_rate_audio") or []
    for track in tracks:
        urls = ((track.get("audio_meta") or {}).get("url_list") or {})
        for key in ("main_url", "backup_url", "fallback_url"):
            if urls.get(key):
                return urls[key]
    raise RuntimeError("No audio-only URL")


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.douyin.com/",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        with target.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)


def make_analysis_wav(source: Path, target: Path, seconds: int) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-t",
            str(seconds),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(target),
        ],
        check=True,
    )


def main() -> int:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    samples = json.loads(RAW_PATH.read_text(encoding="utf-8"))["samples"]
    model = WhisperModel("base", device="cpu", compute_type="int8")

    for index, sample in enumerate(samples, start=1):
        aweme_id = sample["awemeId"]
        output_path = TRANSCRIPT_DIR / f"{aweme_id}.json"
        if output_path.exists():
            print(f"SKIP {index}/8 {aweme_id}", flush=True)
            continue
        detail = sample.get("detail") or {}
        source_duration = round(((detail.get("video") or {}).get("duration") or 0) / 1000, 3)
        analyzed_duration = min(MAX_ANALYSIS_SECONDS, max(1, int(source_duration + 0.999)))
        audio_path = AUDIO_DIR / f"{aweme_id}.m4a"
        wav_path = AUDIO_DIR / f"{aweme_id}.first-{analyzed_duration}s.wav"

        print(f"DOWNLOAD {index}/8 {aweme_id}", flush=True)
        if not audio_path.exists():
            download(audio_url(detail), audio_path)
        if not wav_path.exists():
            make_analysis_wav(audio_path, wav_path, analyzed_duration)

        print(f"TRANSCRIBE {index}/8 {aweme_id}", flush=True)
        segments, info = model.transcribe(
            str(wav_path),
            language="zh",
            vad_filter=True,
            beam_size=5,
        )
        segment_rows = [
            {"start": round(segment.start, 3), "end": round(segment.end, 3), "text": segment.text.strip()}
            for segment in segments
            if segment.text.strip()
        ]
        payload = {
            "aweme_id": aweme_id,
            "author": (detail.get("author") or {}).get("nickname", ""),
            "create_time": detail.get("create_time"),
            "source_duration_seconds": source_duration,
            "analyzed_duration_seconds": analyzed_duration,
            "coverage": "full" if analyzed_duration >= source_duration else "opening_partial",
            "method": "official detail audio URL + faster-whisper base CPU int8",
            "language": info.language,
            "language_probability": info.language_probability,
            "transcript": "".join(row["text"] for row in segment_rows),
            "segments": segment_rows,
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
