import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


NORMALIZE_RE = re.compile(r"[^0-9A-Za-z\u3400-\u9fff]+")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fuse ASR continuity with subtitle OCR corrections into review drafts."
    )
    parser.add_argument("transcript_dir", type=Path)
    return parser.parse_args()


def normalize(text: str) -> str:
    return NORMALIZE_RE.sub("", text or "").lower()


def sample_quality(sample: dict) -> float:
    candidates = [
        candidate
        for candidate in sample.get("ocr_candidates", [])
        if candidate.get("center_y_ratio", 0) >= 0.38
        and CHINESE_RE.search(candidate.get("text", ""))
    ]
    confidence = (
        sum(candidate.get("confidence", 0) for candidate in candidates)
        / len(candidates)
        if candidates
        else 0
    )
    text = sample.get("ocr_text", "")
    unusual = len(
        re.findall(r"[^0-9A-Za-z\u3400-\u9fff，。！？：；、“”《》%\-]", text)
    )
    return confidence * 10 + len(normalize(text)) * 0.05 - unusual * 0.3


def subtitle_consensus(ocr: dict) -> list[dict]:
    output = []
    for sample in sorted(ocr.get("samples", []), key=lambda item: item["time"]):
        text = sample.get("ocr_text", "").strip()
        normalized = normalize(text)
        if not normalized:
            continue
        item = {
            "time": float(sample["time"]),
            "text": text,
            "normalized": normalized,
            "quality": sample_quality(sample),
        }
        if output:
            previous = output[-1]
            gap = item["time"] - previous["time"]
            similarity = SequenceMatcher(
                None, previous["normalized"], normalized, autojunk=False
            ).ratio()
            if normalized == previous["normalized"]:
                continue
            if gap < 2.2 and similarity >= 0.70:
                if item["quality"] > previous["quality"]:
                    output[-1] = item
                continue
        output.append(item)
    return output


def fuse_normalized(asr: str, ocr: str) -> str:
    matcher = SequenceMatcher(None, asr, ocr, autojunk=False)
    output = []
    for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
        left = asr[left_start:left_end]
        right = ocr[right_start:right_end]
        if tag == "equal":
            output.append(left)
        elif tag == "delete":
            output.append(left)
        elif tag == "insert":
            output.append(right)
        else:
            output.append(right if right else left)
    return "".join(output)


def readable_paragraphs(lines: list[dict], max_lines: int = 5) -> list[str]:
    paragraphs = []
    bucket = []
    for item in lines:
        text = item["text"].strip(" ，。！？；：")
        if not text:
            continue
        bucket.append(text)
        question = bool(re.search(r"(吗|呢|么|什么|为什么|怎么|如何|哪[个里]|谁)$", text))
        if len(bucket) >= max_lines or question:
            paragraph = "，".join(bucket)
            paragraphs.append(paragraph + ("？" if question else "。"))
            bucket = []
    if bucket:
        paragraphs.append("，".join(bucket) + "。")
    return paragraphs


def main() -> int:
    args = parse_args()
    written = 0
    for asr_path in sorted(args.transcript_dir.glob("*.transcript.small.json")):
        aweme_id = asr_path.name.split(".")[0]
        ocr_path = args.transcript_dir / f"{aweme_id}.subtitle_ocr.json"
        if not ocr_path.exists():
            continue
        transcript = json.loads(asr_path.read_text(encoding="utf-8"))
        ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
        lines = subtitle_consensus(ocr)
        ocr_normalized = "".join(item["normalized"] for item in lines)
        asr_normalized = normalize(transcript.get("transcript", ""))
        fused = fuse_normalized(asr_normalized, ocr_normalized)
        title = (transcript.get("desc") or f"作品 {aweme_id}").split("#")[0].strip()
        episode = transcript.get("episode") or "待补"
        paragraphs = readable_paragraphs(lines)
        content = [
            f"# 第{episode}集：{title}",
            "",
            f"- 作品ID：`{aweme_id}`",
            f"- 链接：https://www.douyin.com/video/{aweme_id}",
            "- 状态：机器融合校订底稿，等待逐字人工复核；不得标记为最终人工校订版。",
            "- 融合方式：高精度 ASR 保证连续性，字幕 OCR 共识纠正同音词、数字、引文和专有名词。",
            "",
            "## 字幕共识可读稿",
            "",
            *paragraphs,
            "",
            "## ASR+OCR 字符合并层（无标点，用于查漏）",
            "",
            fused,
            "",
            "## 复核提醒",
            "",
            "- 优先检查人名、书名、古籍、诗句、数字、英文术语和自创概念。",
            "- 画面字幕本身若存在错字，应在最终稿中按原视频保留并写入核验备注。",
            "- 事实核验与逐字转录是两件事：转录准确不代表视频观点真实。",
            "",
        ]
        output_path = args.transcript_dir / f"{aweme_id}.transcript.fused.md"
        output_path.write_text("\n".join(content), encoding="utf-8")
        written += 1
    print(f"WROTE {written} fused review drafts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
