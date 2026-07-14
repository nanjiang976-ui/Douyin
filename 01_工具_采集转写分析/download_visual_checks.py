import json
import time
import urllib.request
from pathlib import Path


SEC_USER_ID = "MS4wLjABAAAAeWofQ7S4xhzDuQYzUbSxCQXsDB82CpYe2OOZeiq2lvc"
API_URL = (
    "https://douyin.wtf/api/douyin/web/fetch_user_post_videos"
    f"?sec_user_id={SEC_USER_ID}&max_cursor=0&count=50"
)
IMAGE_IDS = {
    "7643855630177200369",
    "7641061080391530597",
    "7640778374580144101",
}

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "visual_checks"


def fetch_json(url: str) -> dict:
    for attempt in range(1, 5):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                chunks = []
                while chunk := response.read(1024 * 1024):
                    chunks.append(chunk)
            return json.loads(b"".join(chunks))
        except Exception:
            if attempt == 4:
                raise
            time.sleep(attempt * 2)


def download(url: str, output_path: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.douyin.com/"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        output_path.write_bytes(response.read())


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    response = fetch_json(API_URL)
    items = response["data"]["aweme_list"]
    for item in items:
        aweme_id = item["aweme_id"]
        if aweme_id not in IMAGE_IDS:
            continue
        images = item.get("images") or item.get("image_list") or []
        for index, image in enumerate(images[:3], start=1):
            urls = image.get("url_list") or (image.get("download_url") or {}).get("url_list") or []
            if not urls:
                continue
            output_path = OUTPUT_DIR / f"{aweme_id}-{index}.jpg"
            download(urls[0], output_path)
            print(output_path)


if __name__ == "__main__":
    main()
