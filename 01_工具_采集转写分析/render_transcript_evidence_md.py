import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render ASR and subtitle-OCR evidence into readable Markdown files."
    )
    parser.add_argument("transcript_dir", type=Path)
    return parser.parse_args()


def format_time(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    return f"{total // 60:02d}:{total % 60:02d}"


def main() -> int:
    args = parse_args()
    written = 0
    for ocr_path in sorted(args.transcript_dir.glob("*.subtitle_ocr.json")):
        aweme_id = ocr_path.name.split(".")[0]
        transcript_path = args.transcript_dir / f"{aweme_id}.transcript.small.json"
        if not transcript_path.exists():
            continue
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
        ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
        episode = transcript.get("episode") or "待补"
        title = (transcript.get("desc") or f"作品 {aweme_id}").split("#")[0].strip()
        duration_seconds = (
            (transcript.get("duration_ms") or 0) / 1000
            or transcript.get("duration")
            or ocr.get("duration")
            or 0
        )
        lines = [
            f"# 第{episode}集：{title}",
            "",
            f"- 作品ID：`{aweme_id}`",
            f"- 链接：https://www.douyin.com/video/{aweme_id}",
            f"- 时长：约 {format_time(duration_seconds)}",
            "- 文档性质：语音转写与画面字幕的双轨核验底稿；人工校订版存在时，以 `transcript.reviewed.md` 为准。",
            "",
            "## 画面字幕时间轴",
            "",
        ]
        for item in ocr.get("subtitle_sequence", []):
            text = str(item.get("text", "")).strip()
            if text:
                lines.append(f"- `{format_time(float(item.get('time', 0)))}` {text}")
        lines.extend(
            [
                "",
                "## 高精度语音转写全文（原始层）",
                "",
                transcript.get("transcript", "").strip(),
                "",
                "## 使用说明",
                "",
                "- 字幕 OCR 用于纠正专有名词、引文、数字和同音字；语音转写用于补全字幕采样间隙。",
                "- 本文保留证据层，不代表所有人物原话、古文出处、科学或财务主张已经事实核验。",
                "- 进入正式文案资产库前，应优先读取同作品的人工校订版和核验备注。",
                "",
            ]
        )
        output_path = args.transcript_dir / f"{aweme_id}.transcript.evidence.md"
        output_path.write_text("\n".join(lines), encoding="utf-8")
        written += 1
    print(f"WROTE {written} evidence markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
