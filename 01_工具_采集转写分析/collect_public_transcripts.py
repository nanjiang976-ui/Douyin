import json
import sys
import time
import urllib.request
from pathlib import Path

from faster_whisper import WhisperModel


SEC_USER_ID = "MS4wLjABAAAAeWofQ7S4xhzDuQYzUbSxCQXsDB82CpYe2OOZeiq2lvc"
API_URL = (
    "https://douyin.wtf/api/douyin/web/fetch_user_post_videos"
    f"?sec_user_id={SEC_USER_ID}&max_cursor=0&count=50"
)

# Clearly non-market lifestyle posts are intentionally excluded. Empty-title
# videos remain in the queue because their topic cannot be inferred safely.
CANDIDATE_IDS = {
    "7643808906398284217",
    "7643715083390644730",
    "7643627663895114682",
    "7643394084045081701",
    "7643240193834860453",
    "7642941098390943611",
    "7642680163386515642",
    "7642608011191004325",
    "7642423811690460069",
    "7642296151417758202",
    "7642246743447202661",
    "7642117873808787963",
    "7641950824029293541",
    "7641872691260173541",
    "7641741138441321402",
    "7641638765430303973",
    "7641562911303114417",
    "7641484206904535793",
    "7641161469463124837",
    "7641105811037276005",
    "7641001081346765285",
    "7640626559939042213",
    "7640265460990474363",
    "7640110232099015525",
    "7639765145099749093",
    "7639685370444003429",
    "7639654263337699441",
    "7639602900573968293",
}

ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "public_videos"
OUTPUT_PATH = ROOT / "public_transcripts.json"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def first_video_url(item: dict) -> str:
    video = item.get("video") or {}
    for key in ("play_addr_h264", "play_addr", "download_addr"):
        urls = (video.get(key) or {}).get("url_list") or []
        if urls:
            return urls[0]
    raise RuntimeError(f"No downloadable video URL for {item['aweme_id']}")


def download(url: str, output_path: Path) -> None:
    partial_path = output_path.with_suffix(".mp4.part")
    for attempt in range(1, 5):
        downloaded = partial_path.stat().st_size if partial_path.exists() else 0
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.douyin.com/",
        }
        if downloaded:
            headers["Range"] = f"bytes={downloaded}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                mode = "ab" if downloaded and response.status == 206 else "wb"
                with partial_path.open(mode) as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
            partial_path.replace(output_path)
            return
        except Exception as exc:
            print(f"Download retry {attempt}/4 for {output_path.name}: {exc}", flush=True)
            if attempt == 4:
                raise
            time.sleep(attempt * 2)


def transcribe(model: WhisperModel, input_path: Path) -> str:
    segments, _ = model.transcribe(
        str(input_path),
        language="zh",
        vad_filter=True,
        beam_size=5,
    )
    return "".join(segment.text.strip() for segment in segments)


def main() -> int:
    VIDEO_DIR.mkdir(exist_ok=True)
    response = fetch_json(API_URL)
    items = response["data"]["aweme_list"]
    selected = [
        item
        for item in items
        if item.get("aweme_id") in CANDIDATE_IDS and item.get("aweme_type") == 0
    ]
    print(f"Selected {len(selected)} videos for local transcription.", flush=True)

    model = WhisperModel("base", device="cpu", compute_type="int8")
    results = []
    if OUTPUT_PATH.exists():
        results = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    completed_ids = {result["aweme_id"] for result in results}
    for index, item in enumerate(selected, start=1):
        aweme_id = item["aweme_id"]
        if aweme_id in completed_ids:
            print(f"[{index}/{len(selected)}] {aweme_id}: already transcribed", flush=True)
            continue
        video_path = VIDEO_DIR / f"{aweme_id}.mp4"
        print(f"[{index}/{len(selected)}] {aweme_id}: download", flush=True)
        if not video_path.exists():
            download(first_video_url(item), video_path)
        print(f"[{index}/{len(selected)}] {aweme_id}: transcribe", flush=True)
        results.append(
            {
                "aweme_id": aweme_id,
                "create_time": item["create_time"],
                "desc": item.get("desc", ""),
                "duration_ms": item.get("duration"),
                "url": f"https://www.douyin.com/video/{aweme_id}",
                "transcript": transcribe(model, video_path),
            }
        )
        OUTPUT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"Wrote {len(results)} transcripts to {OUTPUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
