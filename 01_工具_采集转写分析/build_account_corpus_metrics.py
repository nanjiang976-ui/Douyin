import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


PHRASE_PATTERNS = {
    "提问开场": r"^(什么|为什么|你知道|你有没有|有没有|究竟|到底|什么样)",
    "场景开场": r"^(当你|如果你|假设|想象一下|仔细回想)",
    "命令或建议开场": r"^(建议|记住|别再|千万|无论如何|尝试|请)",
    "暴论或断言开场": r"^(说一个暴论|真正|大多数|很多人|天赋|财富|人生)",
    "延迟反驳": r"别急着(反驳|划走)|先别急着(反驳|划走)",
    "时间承诺": r"接下来的(这)?几分钟|请给我几分钟",
    "结果承诺": r"我会帮你|能帮你|彻底(拆解|撕开|颠覆)|听懂了",
    "观众镜像": r"你有没有发现|你一定有过|仔细回想|回想一下|你仔细",
    "概念引入": r"(引出|引入).{0,18}(概念|理论|效应)|我把它叫作|我把它称之为",
    "大白话翻译": r"大白话|通俗点说|用大白话",
    "权威背书": r"心理学|经济学|社会学|神经科学|哲学家|古人|名臣|兵法|定律|效应",
    "强反转": r"但实际上|恰恰|真相|根本不是|大错特错|绝对不是|反而",
    "身份分层": r"普通人|高手|强者|弱者|智者|顶级|真正能|绝大多数人",
    "替观众质疑": r"你可能会|你肯定会|听到这里|这时候你|是不是觉得|你会问",
    "行动收束": r"从今天开始|从此刻开始|去行动|走出去|立刻|按下开始键|记住",
    "价值升华": r"生活的掌控权|人生|自由|底气|本心|生命|社会资本|复利",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build corpus-level writing metrics.")
    parser.add_argument("transcript_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_json", type=Path)
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", "", text or "")
    return text.replace("著", "着").replace("裡", "里")


def read_preferred_transcript(transcript_dir: Path, payload: dict) -> tuple[str, str]:
    """Prefer the reviewed body and fall back to the ASR layer when necessary."""
    aweme_id = str(payload.get("aweme_id") or "")
    final = transcript_dir / "01_最终完整文案" / f"{aweme_id}.transcript.reviewed.md"
    reviewed = final if final.exists() else transcript_dir / f"{aweme_id}.transcript.reviewed.md"
    if reviewed.exists():
        raw = reviewed.read_text(encoding="utf-8")
        marker = "## 校订版完整文案"
        risk_marker = "## 核验备注"
        if marker in raw:
            body = raw.split(marker, 1)[1]
            if risk_marker in body:
                body = body.split(risk_marker, 1)[0]
            body = body.strip()
            if body:
                return body, "人工终审稿"
    return payload.get("transcript", ""), "高精度ASR回退层"


def asr_dir(root: Path) -> Path:
    archived = root / "03_校对证据归档" / "01_ASR原始层"
    return archived if archived.exists() else root


def opening_type(text: str) -> str:
    for name in ("提问开场", "场景开场", "命令或建议开场", "暴论或断言开场"):
        if re.search(PHRASE_PATTERNS[name], text):
            return name
    return "直接断言或故事开场"


def ending_type(text: str) -> str:
    ending = text[-220:]
    if re.search(PHRASE_PATTERNS["行动收束"], ending):
        return "行动号召"
    if re.search(PHRASE_PATTERNS["价值升华"], ending):
        return "价值升华"
    if "吗" in ending or "？" in ending:
        return "问题收束"
    return "结论收束"


def main() -> int:
    args = parse_args()
    rows = []
    phrase_counts = Counter()
    opening_counts = Counter()
    ending_counts = Counter()

    for path in sorted(asr_dir(args.transcript_dir).glob("*.transcript.small.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        preferred_text, text_source = read_preferred_transcript(args.transcript_dir, payload)
        text = normalize_text(preferred_text)
        statistics = payload.get("statistics") or {}
        hits = []
        for name, pattern in PHRASE_PATTERNS.items():
            count = len(re.findall(pattern, text))
            if count:
                phrase_counts[name] += count
                hits.append(f"{name}:{count}")

        opening = opening_type(text)
        ending = ending_type(text)
        opening_counts[opening] += 1
        ending_counts[ending] += 1
        create_time = payload.get("create_time")
        created_at = (
            datetime.fromtimestamp(create_time).isoformat(timespec="seconds")
            if create_time
            else ""
        )
        rows.append(
            {
                "episode": payload.get("episode"),
                "aweme_id": payload.get("aweme_id"),
                "created_at": created_at,
                "desc": payload.get("desc", ""),
                "duration_seconds": round((payload.get("duration_ms") or 0) / 1000, 2),
                "transcript_chars": len(text),
                "text_source": text_source,
                "digg_count": statistics.get("digg_count", 0),
                "collect_count": statistics.get("collect_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "share_count": statistics.get("share_count", 0),
                "opening_type": opening,
                "ending_type": ending,
                "opening_excerpt": text[:160],
                "ending_excerpt": text[-180:],
                "pattern_hits": " | ".join(hits),
            }
        )

    rows.sort(key=lambda row: int(row["episode"] or 0))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "video_count": len(rows),
        "duration_seconds_total": round(sum(row["duration_seconds"] for row in rows), 2),
        "transcript_chars_total": sum(row["transcript_chars"] for row in rows),
        "duration_seconds_average": round(
            sum(row["duration_seconds"] for row in rows) / max(len(rows), 1), 2
        ),
        "transcript_chars_average": round(
            sum(row["transcript_chars"] for row in rows) / max(len(rows), 1), 2
        ),
        "opening_types": opening_counts,
        "ending_types": ending_counts,
        "phrase_counts": phrase_counts,
        "top_by_digg": sorted(
            (
                {
                    "episode": row["episode"],
                    "aweme_id": row["aweme_id"],
                    "desc": row["desc"],
                    "digg_count": row["digg_count"],
                    "collect_count": row["collect_count"],
                    "share_count": row["share_count"],
                }
                for row in rows
            ),
            key=lambda item: item["digg_count"],
            reverse=True,
        )[:15],
    }
    args.output_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
