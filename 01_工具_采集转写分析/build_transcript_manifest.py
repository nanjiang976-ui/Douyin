import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a transcript quality manifest.")
    parser.add_argument("transcript_dir", type=Path)
    parser.add_argument("output_md", type=Path)
    return parser.parse_args()


def layer_dir(root: Path, archived_name: str) -> Path:
    archived = root / "03_校对证据归档" / archived_name
    return archived if archived.exists() else root


def reviewed_path(root: Path, aweme_id: str) -> Path:
    final = root / "01_最终完整文案" / f"{aweme_id}.transcript.reviewed.md"
    return final if final.exists() else root / f"{aweme_id}.transcript.reviewed.md"


def main() -> int:
    args = parse_args()
    items = []
    asr_dir = layer_dir(args.transcript_dir, "01_ASR原始层")
    ocr_dir = layer_dir(args.transcript_dir, "02_字幕OCR")
    evidence_dir = layer_dir(args.transcript_dir, "03_证据稿")
    for path in asr_dir.glob("*.transcript.small.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        aweme_id = payload.get("aweme_id")
        reviewed = reviewed_path(args.transcript_dir, aweme_id)
        evidence = evidence_dir / f"{aweme_id}.transcript.evidence.md"
        ocr = ocr_dir / f"{aweme_id}.subtitle_ocr.json"
        if reviewed.exists():
            quality = "人工校订版"
            preferred = reviewed
        elif evidence.exists():
            quality = "ASR+字幕OCR双轨底稿"
            preferred = evidence
        else:
            quality = "高精度ASR原始层"
            preferred = path
        items.append(
            {
                "episode": int(payload.get("episode") or 0),
                "aweme_id": aweme_id,
                "title": (payload.get("desc") or "").split("#")[0].strip(),
                "quality": quality,
                "preferred": preferred,
                "ocr": ocr.exists(),
                "reviewed": reviewed.exists(),
            }
        )
    items.sort(key=lambda item: item["episode"])
    reviewed_count = sum(item["reviewed"] for item in items)
    ocr_count = sum(item["ocr"] for item in items)
    lines = [
        "# ‘如果说’全账号转写索引",
        "",
        f"- 视频总数：{len(items)}",
        f"- 已完成字幕 OCR 对照：{ocr_count}",
        f"- 已形成逐字人工校订版：{reviewed_count}",
        "- 读取优先级：人工校订版 > ASR+字幕OCR双轨底稿 > 高精度ASR原始层",
        "",
        "| 集数 | 标题 | 作品ID | 当前最高质量 | 首选文件 |",
        "|---:|---|---|---|---|",
    ]
    for item in items:
        relative = item["preferred"].relative_to(args.transcript_dir).as_posix()
        title = item["title"].replace("|", "／")
        lines.append(
            f"| {item['episode']} | {title} | `{item['aweme_id']}` | {item['quality']} | [{relative}]({relative}) |"
        )
    lines.extend(
        [
            "",
            "## 质量说明",
            "",
            "- 高精度 ASR 原始层用于保证语音内容连续完整，但可能有同音字和专有名词错误。",
            "- 双轨底稿同时提供画面字幕时间轴与语音全文，能够互相补齐；它是证据层，不代表人物原话或科学主张已完成事实核验。",
            "- 人工校订版补充标点、段落、关键字纠错和风险备注，是后续文案拆解的优先文本。",
            "",
        ]
    )
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"WROTE manifest videos={len(items)} ocr={ocr_count} reviewed={reviewed_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
