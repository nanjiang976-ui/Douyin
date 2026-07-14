import argparse
import csv
import json
import re
from pathlib import Path


TAG_RULES = {
    "反常识/悖论": r"恰恰|反而|并不是|根本不是|从来不是|越.{0,12}越",
    "身份分层": r"普通人|弱者|强者|智者|高手|顶级|第一层|第二层|第三层|境界",
    "概念命名": r"我把它叫|我把它称|这就叫|概念叫|理论叫|效应",
    "权威借力": r"道德经|周易|庄子|王阳明|鲁迅|纳瓦尔|索罗斯|达里奥|心理学|经济学|社会学|神经科学|史记|资治通鉴|鬼谷子|孙子兵法",
    "现实场景": r"职场|老板|同事|客户|婚姻|父母|孩子|房贷|开店|工作|账户|工资",
    "替观众反驳": r"你可能会|你肯定会|你会问|是不是觉得|别急着反驳|先别急着",
    "三级或清单": r"第一|第二|第三|三种|三层|三个|四种|六句|十条",
    "类比可视化": r"就像|好比|仿佛|像一台|像一张|像一个|就好像",
    "短句重锤": r"大错特错|绝对不是|这就是|记住|真相是|为什么|怎么办",
    "行动方案": r"从今天开始|从此刻开始|第一道题|第二道题|只需要|具体怎么做|方法是|按下开始键",
    "诗性升华": r"本心|自由|生命|人生|清醒|通透|逍遥|圆满|山海|光|尘",
}


RISK_RULES = {
    "投资/财务": r"炒股|交易|持仓|盈利|财富|利息|贷款|本金|复利|资金链|投资",
    "医学/神经科学": r"大脑|神经|皮质醇|前额叶|多巴胺|内啡肽|医生|手术|心理学",
    "历史/名言归属": r"古人|名臣|哲学家|说过|写过|名句|道德经|周易|史记|资治通鉴|鲁迅|王阳明",
    "宗教/传统概念": r"道家|禅宗|佛|业力|斩三尸|无相|修行|开悟|命数|风水",
    "绝对化承诺": r"唯一|绝对|一定|只要.{0,12}就|百分之|99%|十倍|暴涨",
    "羞辱/高压表达": r"弱者|慢性自杀|绞肉机|生吞活剥|废物|奴隶|收割|杀伐|妓女",
}


TITLE_TOPIC_RULES = [
    ("传统智慧_现代认知", r"道德经|庄子|鬼谷子|周易|金刚经|心相|三尸|冰心诀|内求|和光同尘|大象无形|胜败荣辱|止学"),
    ("财富_商业_执行", r"财富|赚钱|穷人|富人|商业|创业|开店|投资|钱|业力循环"),
    ("家庭_关系_情感", r"父母|孩子|家庭|婚姻|亲情|情感|喜欢的人|爱河|托举"),
    ("行动_系统_能力", r"执行力|坚持|输出|体系|重复|天赋|操作系统|行动|努力|正反馈"),
    ("情绪_自我成长", r"内耗|焦虑|心烦|空虚|迷茫|生气|清醒|觉醒|人生|认知|当下"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a per-video teardown evidence index.")
    parser.add_argument("transcript_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    return parser.parse_args()


def clean(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def read_reviewed_body(transcript_dir: Path, payload: dict) -> tuple[str, str]:
    """Return only the reviewed spoken copy; never mix risk notes into analysis text."""
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


def reviewed_relative_path(root: Path, aweme_id: str) -> str:
    final = root / "01_最终完整文案" / f"{aweme_id}.transcript.reviewed.md"
    if final.exists():
        return final.relative_to(root).as_posix()
    return f"{aweme_id}.transcript.reviewed.md"


def sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？!?])", text) if item.strip()]


def opening_window(items: list[str], char_limit: int) -> str:
    """Use only reviewed copy; timing labels are editorial approximations, not ASR text."""
    result = ""
    for item in items:
        result += clean(item)
        if len(result) >= char_limit:
            break
    return result[:char_limit]


def title_formula(title: str) -> str:
    if re.search(r"为什么.*(越|反而|根本)", title):
        return "为什么X却Y的反常识问句"
    if re.search(r"(真正|最高|最好).*(人|境界|状态)", title):
        return "身份/境界重新定义"
    if re.search(r"(三个|三种|四个|六句|十条|心法|阶段)", title):
        return "清单/阶段承诺"
    if re.search(r"(道德经|庄子|鬼谷子|陈抟|老祖宗|古人)", title):
        return "传统概念现代化"
    return "痛点或判断式标题"


def audience_pain(text: str, topic: str) -> str:
    rules = [
        (r"焦虑|内耗|心烦|烦躁|生气|情绪", "情绪被外界牵引、内耗而无法稳定行动"),
        (r"空虚|迷茫|方向|坚持|反馈", "缺少方向或正反馈，怀疑自己是否走错"),
        (r"关系|喜欢|伴侣|父母|朋友", "关系中的期待、控制、误解或不安全感"),
        (r"钱|财富|赚钱|商业|创业|穷", "资源不足、结果焦虑与现实上升压力"),
        (r"成长|认知|行动|努力|输出", "想改变却被方法、节奏或自我怀疑卡住"),
    ]
    for pattern, result in rules:
        if re.search(pattern, text):
            return result
    return f"{topic}中的模糊困惑，需要被重新命名"


def evidence_methods(text: str) -> str:
    methods = []
    if re.search(r"道德经|庄子|周易|论语|大学|孙子兵法|鬼谷子|金刚经", text):
        methods.append("传统文本")
    if re.search(r"心理学|神经科学|研究|实验|效应|大脑", text):
        methods.append("现代概念/研究")
    if re.search(r"王阳明|苏轼|曾国藩|刘邦|商鞅|范仲淹|陆游|蔺相如|孔子", text):
        methods.append("历史人物")
    if re.search(r"老板|同事|伴侣|父母|朋友|工作|消息|手机", text):
        methods.append("生活场景")
    if re.search(r"就像|像一|好比|仿佛", text):
        methods.append("类比意象")
    return " + ".join(methods) or "观点推演"


def short_hammers(items: list[str]) -> str:
    picks = []
    for index, item in enumerate(items, start=1):
        compact = clean(item)
        if 8 <= len(compact) <= 48 and re.search(r"不是|而是|真正|这就是|你越|只有|所以", compact):
            picks.append(f"第{index}句：{compact[:46]}")
        if len(picks) >= 3:
            break
    return " | ".join(picks)


def objections(items: list[str]) -> str:
    hits = [
        clean(item)[:80]
        for item in items
        if re.search(r"你可能会|你会问|难道|是不是|误读|不是.*而是", item)
    ]
    return " | ".join(hits[:3])


def action_or_cta(items: list[str]) -> str:
    candidates = [
        clean(item)[:100]
        for item in items[-8:]
        if re.search(r"问自己|从今天|下次|建议|记住|去做|保存|背下来|停下来|试着", item)
    ]
    return " | ".join(candidates[:2])


def transfer_capability(phase: str, topic: str) -> str:
    if phase == "mature_31_65":
        return "传统概念现代化 + 情绪修复 + 分层/排比收束；默认迁移到认知成长主题"
    if phase == "transition_14_30":
        return "人物故事/历史镜像 + 现实方法论；适合故事型认知稿"
    return "现实压力/行动冲突 + 强钩子；仅在赚钱、执行力主题选择性调用"


def no_copy_rule() -> str:
    return "不得复用原句、标志性比喻、人物案例顺序或未经核验事实；仅迁移结构、节奏与论证功能。"


def phase_for_episode(episode: int) -> str:
    if episode <= 13:
        return "early_1_13"
    if episode <= 30:
        return "transition_14_30"
    return "mature_31_65"


def topic_cluster(title: str, text: str) -> str:
    for name, pattern in TITLE_TOPIC_RULES:
        if re.search(pattern, title):
            return name
    for name, pattern in TITLE_TOPIC_RULES:
        if re.search(pattern, text[:1000]):
            return name
    return "认知_个人成长"


def main() -> int:
    args = parse_args()
    rows = []
    for path in asr_dir(args.transcript_dir).glob("*.transcript.small.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        reviewed_text, text_source = read_reviewed_body(args.transcript_dir, payload)
        text = clean(reviewed_text)
        reviewed_sentences = sentences(reviewed_text)
        title = (payload.get("desc") or "").split("#")[0].strip()
        chapters = payload.get("chapter_list") or []
        chapter_chain = " → ".join(
            filter(
                None,
                (
                    f"{chapter.get('desc', '').strip()}：{chapter.get('detail', '').strip()}".strip("：")
                    for chapter in chapters
                ),
            )
        )
        mechanism_tags = [
            name for name, pattern in TAG_RULES.items() if re.search(pattern, text)
        ]
        risk_tags = [
            name for name, pattern in RISK_RULES.items() if re.search(pattern, text)
        ]
        statistics = payload.get("statistics") or {}
        episode = int(payload.get("episode") or 0)
        digg_count = int(statistics.get("digg_count", 0) or 0)
        collect_count = int(statistics.get("collect_count", 0) or 0)
        share_count = int(statistics.get("share_count", 0) or 0)
        first_3 = opening_window(reviewed_sentences, 32)
        first_30 = opening_window(reviewed_sentences, 260)
        opening = clean(reviewed_sentences[0])[:160] if reviewed_sentences else text[:160]
        core_claim = clean("".join(reviewed_sentences[:3]))[:260] if reviewed_sentences else text[:260]
        ending = clean("".join(reviewed_sentences[-3:]))[-260:] if reviewed_sentences else text[-240:]
        rows.append(
            {
                "episode": episode,
                "aweme_id": payload.get("aweme_id"),
                "title": title,
                "account_phase": phase_for_episode(episode),
                "topic_cluster": topic_cluster(title, text),
                "text_source": text_source,
                "reviewed_transcript_path": reviewed_relative_path(args.transcript_dir, str(payload.get('aweme_id'))),
                "duration_seconds": round(
                    (payload.get("duration_ms") or payload.get("duration", 0) * 1000)
                    / 1000,
                    2,
                ),
                "digg_count": digg_count,
                "collect_count": collect_count,
                "comment_count": statistics.get("comment_count", 0),
                "share_count": share_count,
                "collect_to_digg": round(collect_count / digg_count, 4)
                if digg_count
                else "",
                "share_to_digg": round(share_count / digg_count, 4)
                if digg_count
                else "",
                "title_formula": title_formula(title),
                "audience_pain": audience_pain(text, topic_cluster(title, text)),
                "opening_hook": opening,
                "first_3s_evidence": first_3 or opening,
                "first_30s_evidence": first_30 or text[:260],
                "core_claim": core_claim,
                "chapter_argument_chain": chapter_chain,
                "evidence_methods": evidence_methods(reviewed_text),
                "short_hammer_positions": short_hammers(reviewed_sentences),
                "rhythm_evidence": f"句数:{len(reviewed_sentences)}；短句重锤:{len([s for s in reviewed_sentences if len(clean(s)) <= 28])}；反转词:{len(re.findall(r'不是|而是|反而|恰恰|真正', text))}",
                "anticipated_objections": objections(reviewed_sentences),
                "ending_evidence": ending,
                "cta_or_action": action_or_cta(reviewed_sentences),
                "transfer_capability": transfer_capability(phase_for_episode(episode), topic_cluster(title, text)),
                "mechanism_tags": " | ".join(mechanism_tags),
                "risk_tags": " | ".join(risk_tags),
                "no_copy_boundary": no_copy_rule(),
                "evidence_anchor": f"终审稿:{payload.get('aweme_id')}.transcript.reviewed.md；开头、前3秒近似口播与前30秒近似口播均由终审稿起始段落定位",
                "chapter_abstract": payload.get("chapter_abstract", ""),
                "reviewed_md_exists": (
                    args.transcript_dir / reviewed_relative_path(args.transcript_dir, str(payload.get('aweme_id')))
                ).exists(),
                "subtitle_ocr_exists": (
                    (args.transcript_dir / "03_校对证据归档" / "02_字幕OCR" / f"{payload.get('aweme_id')}.subtitle_ocr.json")
                    if (args.transcript_dir / "03_校对证据归档" / "02_字幕OCR").exists()
                    else args.transcript_dir / f"{payload.get('aweme_id')}.subtitle_ocr.json"
                ).exists(),
            }
        )

    rows.sort(key=lambda row: int(row["episode"] or 0))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"WROTE {len(rows)} rows -> {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
