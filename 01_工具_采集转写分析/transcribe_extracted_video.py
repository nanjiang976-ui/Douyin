import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel

from collect_public_transcripts import download, first_video_url, transcribe


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python transcribe_extracted_video.py <extract-json> <output-json>")
        return 1

    extract_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    response = json.loads(extract_path.read_text(encoding="utf-8"))
    bodies = [
        entry["body"]
        for entry in response["responseBodies"]
        if "aweme/detail" in entry["url"] and entry.get("body")
    ]
    if not bodies:
        raise RuntimeError("No aweme detail body found in extract")

    payload = json.loads(bodies[-1])
    item = payload["aweme_detail"]
    video_path = output_path.with_suffix(".mp4")
    if not video_path.exists():
        download(first_video_url(item), video_path)

    model = WhisperModel("base", device="cpu", compute_type="int8")
    result = {
        "aweme_id": item["aweme_id"],
        "author": item["author"]["nickname"],
        "unique_id": item["author"].get("unique_id", ""),
        "create_time": item["create_time"],
        "desc": item.get("desc", ""),
        "caption": item.get("caption", ""),
        "chapter_abstract": item.get("chapter_abstract", ""),
        "chapter_list": item.get("chapter_list", []),
        "duration_ms": item.get("duration"),
        "url": f"https://www.douyin.com/video/{item['aweme_id']}",
        "transcript": transcribe(model, video_path),
    }
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
