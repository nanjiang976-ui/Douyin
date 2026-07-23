import json
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "audio"
OUTPUT_PATH = ROOT / "fragment_verification.small.json"
WINDOWS = {
    "7650793954459283813": (126, 154),
    "7614808385040518434": (72, 100),
    "7636694641883473905": (39, 58),
    "7616596634591530249": (86, 103),
    "7611150020510846246": (24, 40),
    "7657518242554023195": (62, 82),
    "7654930914341883179": (54, 78),
    "7627567027091213602": (75, 143),
}


def main() -> None:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    rows = []
    for index, (aweme_id, (start, end)) in enumerate(WINDOWS.items(), start=1):
        source = AUDIO_DIR / f"{aweme_id}.m4a"
        clip = AUDIO_DIR / f"{aweme_id}.verify-{start}-{end}s.wav"
        if not clip.exists():
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    str(start),
                    "-i",
                    str(source),
                    "-t",
                    str(end - start),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(clip),
                ],
                check=True,
            )
        print(f"VERIFY {index}/8 {aweme_id}", flush=True)
        segments, _ = model.transcribe(
            str(clip), language="zh", vad_filter=True, beam_size=5
        )
        segment_rows = [
            {
                "start": round(start + segment.start, 3),
                "end": round(start + segment.end, 3),
                "text": segment.text.strip(),
            }
            for segment in segments
            if segment.text.strip()
        ]
        rows.append(
            {
                "aweme_id": aweme_id,
                "window": [start, end],
                "transcript": "".join(row["text"] for row in segment_rows),
                "segments": segment_rows,
            }
        )
    OUTPUT_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
