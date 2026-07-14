"""Rebuild full-corpus report/table artifacts from the reviewed per-video teardown index."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 65-video content table and report from reviewed teardown evidence."
    )
    parser.add_argument("teardown_csv", type=Path)
    parser.add_argument("metrics_json", type=Path)
    parser.add_argument("output_table_csv", type=Path)
    parser.add_argument("output_report_md", type=Path)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def brief(text: str, limit: int = 90) -> str:
    text = (text or "").replace("\n", "").strip()
    return text if len(text) <= limit else f"{text[:limit]}…"


def write_table(rows: list[dict[str, str]], output: Path) -> None:
    fields = [
        "集数", "作品ID", "链接", "发布时间", "时长秒", "点赞", "评论", "收藏", "分享",
        "账号阶段", "标题", "主题簇", "选题母题", "用户痛点", "标题公式", "开头钩子",
        "前3秒近似口播", "前30秒近似口播", "核心主张", "章节论证链", "论证方式",
        "节奏证据", "预判质疑", "结尾", "行动/CTA", "可迁移能力", "事实风险",
        "禁止照搬", "终审稿路径", "证据定位",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "集数": row.get("episode"),
                    "作品ID": row.get("aweme_id"),
                    "链接": f"https://www.douyin.com/video/{row.get('aweme_id')}",
                    "发布时间": row.get("created_at"),
                    "时长秒": row.get("duration_seconds"),
                    "点赞": row.get("digg_count"),
                    "评论": row.get("comment_count"),
                    "收藏": row.get("collect_count"),
                    "分享": row.get("share_count"),
                    "账号阶段": row.get("account_phase"),
                    "标题": row.get("title"),
                    "主题簇": row.get("topic_cluster"),
                    "选题母题": row.get("mechanism_tags"),
                    "用户痛点": row.get("audience_pain"),
                    "标题公式": row.get("title_formula"),
                    "开头钩子": row.get("opening_hook"),
                    "前3秒近似口播": row.get("first_3s_evidence"),
                    "前30秒近似口播": row.get("first_30s_evidence"),
                    "核心主张": row.get("core_claim"),
                    "章节论证链": row.get("chapter_argument_chain"),
                    "论证方式": row.get("evidence_methods"),
                    "节奏证据": row.get("rhythm_evidence"),
                    "预判质疑": row.get("anticipated_objections"),
                    "结尾": row.get("ending_evidence"),
                    "行动/CTA": row.get("cta_or_action"),
                    "可迁移能力": row.get("transfer_capability"),
                    "事实风险": row.get("risk_tags"),
                    "禁止照搬": row.get("no_copy_boundary"),
                    "终审稿路径": row.get("reviewed_transcript_path"),
                    "证据定位": row.get("evidence_anchor"),
                }
            )


def write_report(rows: list[dict[str, str]], metrics: dict, output: Path) -> None:
    phase_counts = Counter(row.get("account_phase", "") for row in rows)
    topic_counts = Counter(row.get("topic_cluster", "") for row in rows)
    lines = [
        "# ‘如果说’65条视频内容总结报告（终审稿全量版）",
        "",
        "## 数据范围",
        "",
        f"- 覆盖作品：{len(rows)}条；每条均回链到人工终审稿。",
        "- 正文来源：终审稿的“校订版完整文案”区段；ASR、OCR、融合稿仅作证据层。",
        "- 逐视频字段请见 `01_视频内容总表.csv` 与 `06_全65条逐视频拆解证据索引.csv`。",
        "",
        "## 全量结构概览",
        "",
        f"- 总口播字符数：{metrics.get('transcript_chars_total', '')}；平均每条：{metrics.get('transcript_chars_average', '')}。",
        f"- 总时长：{metrics.get('duration_seconds_total', '')}秒；平均每条：{metrics.get('duration_seconds_average', '')}秒。",
        f"- 阶段覆盖：早期1—13（{phase_counts.get('early_1_13', 0)}条）、过渡期14—30（{phase_counts.get('transition_14_30', 0)}条）、成熟期31—65（{phase_counts.get('mature_31_65', 0)}条）。",
        "- 标题/正文母题以传统概念现代化、情绪与自我成长、财富/执行、关系和行动系统为主；分类只用于检索，不替代单条终审判断。",
        "",
        "## 65条逐视频覆盖清单",
        "",
        "| 集数 | 标题 | 阶段 | 主题 | 核心主张摘要 | 论证方式 | 风险 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {episode} | {title} | {phase} | {topic} | {claim} | {method} | {risk} |".format(
                episode=row.get("episode", ""),
                title=(row.get("title", "").replace("|", "／")),
                phase=row.get("account_phase", ""),
                topic=row.get("topic_cluster", ""),
                claim=brief(row.get("core_claim", "")).replace("|", "／"),
                method=(row.get("evidence_methods", "").replace("|", "／")),
                risk=(row.get("risk_tags", "").replace("|", "／")),
            )
        )
    lines.extend(
        [
            "",
            "## 全量结论",
            "",
            "65条共同形成的稳定机制是：命名痛苦 → 推翻旧解释 → 古语/概念或人物支点 → 日常场景翻译 → 处理极端误读 → 低门槛动作 → 情绪收束。",
            "",
            "未来迁移只调用题材机制、结构、论证、节奏和情绪功能。古籍、人物、研究、数字和绝对承诺必须独立核验；不得复制原句、标志性比喻、故事顺序或个人叙事。",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = load_rows(args.teardown_csv)
    rows.sort(key=lambda row: int(row.get("episode") or 0))
    if not rows:
        raise ValueError("No teardown rows found")
    metrics = json.loads(args.metrics_json.read_text(encoding="utf-8"))
    write_table(rows, args.output_table_csv)
    write_report(rows, metrics, args.output_report_md)
    print(f"WROTE full_table_rows={len(rows)} report_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
