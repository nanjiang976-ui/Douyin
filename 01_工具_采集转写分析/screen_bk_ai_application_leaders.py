from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener


KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
OUTPUT_PATH = Path("bk_ai_application_leader_screen.json")
DIRECT_OPENER = build_opener(ProxyHandler({}))
START_DATE = "2025-11-01"
END_DATE = "2026-06-01"

CANDIDATES = [
    {"code": "688111", "name": "金山办公", "layer": "办公与生产力"},
    {"code": "002230", "name": "科大讯飞", "layer": "大模型与垂直应用"},
    {"code": "300624", "name": "万兴科技", "layer": "创意软件"},
    {"code": "688095", "name": "福昕软件", "layer": "文档软件"},
    {"code": "600588", "name": "用友网络", "layer": "企业软件"},
    {"code": "603039", "name": "泛微网络", "layer": "协同办公"},
    {"code": "300170", "name": "汉得信息", "layer": "企业数字化与智能体"},
    {"code": "300634", "name": "彩讯股份", "layer": "企业协同与邮件"},
    {"code": "002315", "name": "焦点科技", "layer": "跨境 B2B"},
    {"code": "300418", "name": "昆仑万维", "layer": "内容与智能体"},
    {"code": "300364", "name": "中文在线", "layer": "数字内容"},
    {"code": "601360", "name": "三六零", "layer": "搜索与安全"},
    {"code": "300229", "name": "拓尔思", "layer": "语义智能与行业应用"},
    {"code": "300033", "name": "同花顺", "layer": "金融信息与智能投顾工具"},
    {"code": "300058", "name": "蓝色光标", "layer": "营销与内容生成"},
    {"code": "000681", "name": "视觉中国", "layer": "视觉内容与版权"},
    {"code": "603533", "name": "掌阅科技", "layer": "数字阅读与内容"},
    {"code": "300785", "name": "值得买", "layer": "消费内容与电商导购"},
]


def market_code(code: str) -> str:
    return f"sh{code}" if code.startswith(("6", "9")) else f"sz{code}"


def pct(value: float) -> float:
    return round(value * 100, 2)


def fetch_daily(code: str) -> list[dict[str, float | str]]:
    ticker = market_code(code)
    params = {"param": f"{ticker},day,{START_DATE},{END_DATE},500,qfq"}
    url = f"{KLINE_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error = None
    for attempt in range(4):
        try:
            if attempt:
                time.sleep(2**attempt)
            with DIRECT_OPENER.open(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
                data = (payload.get("data") or {}).get(ticker) or {}
            break
        except Exception as exc:
            last_error = exc
    else:
        raise RuntimeError(f"request failed after retries: {last_error}")

    rows = data.get("qfqday") or data.get("day") or []
    records = []
    for row in rows:
        try:
            records.append(
                {
                    "date": str(row[0]),
                    "open": float(row[1]),
                    "close": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "volume": float(row[5]),
                }
            )
        except (IndexError, TypeError, ValueError):
            continue
    return records


def first_date(rows: list[dict[str, float | str]], predicate) -> str | None:
    for row in rows:
        if predicate(row):
            return str(row["date"])
    return None


def trading_days_between(rows: list[dict[str, float | str]], start_date: str, end_date: str | None) -> int | None:
    if not end_date:
        return None
    dates = [str(row["date"]) for row in rows]
    try:
        return dates.index(end_date) - dates.index(start_date)
    except ValueError:
        return None


def first_stabilization_date(rows: list[dict[str, float | str]], low_index: int) -> str | None:
    """Proxy for stabilization: reclaim 20-day MA and hold it in >= 3 of next 5 sessions."""
    for index in range(max(low_index + 1, 19), len(rows) - 4):
        ma20 = sum(float(row["close"]) for row in rows[index - 19 : index + 1]) / 20
        if float(rows[index]["close"]) < ma20:
            continue
        holds = 0
        for future_index in range(index, index + 5):
            future_ma20 = sum(float(row["close"]) for row in rows[future_index - 19 : future_index + 1]) / 20
            if float(rows[future_index]["close"]) >= future_ma20:
                holds += 1
        if holds >= 3:
            return str(rows[index]["date"])
    return None


def classify(record: dict[str, object]) -> str:
    peak_ratio = float(record["first_rebound_peak_vs_jan_high_pct"])
    days_90 = record["days_from_low_to_reclaim_90pct_jan_high"]
    latest_ratio = float(record["latest_vs_jan_high_pct"])
    if peak_ratio >= 100 and days_90 is not None and int(days_90) <= 15:
        return "最符合：较快收复并突破 1 月高点"
    if peak_ratio >= 90 and days_90 is not None and int(days_90) <= 20:
        return "较符合：较快反弹至接近 1 月高点"
    if peak_ratio >= 85:
        return "部分符合：第一轮反弹较强，但尚未接近 1 月高点"
    if latest_ratio >= 85:
        return "观察：当前仍接近 1 月高点"
    return "不优先：尚未接近 1 月高点"


def metrics(candidate: dict[str, str], rows: list[dict[str, float | str]]) -> dict[str, object]:
    january = [row for row in rows if "2026-01-01" <= str(row["date"]) <= "2026-01-31"]
    if not january:
        raise RuntimeError("missing January trading data")

    jan_high_row = max(january, key=lambda row: float(row["close"]))
    jan_high_index = next(index for index, row in enumerate(rows) if row["date"] == jan_high_row["date"])
    # BK's rule refers to the first repair after the January decline. Restrict the
    # correction low to the next 12 sessions so later secondary pullbacks do not
    # distort the original comparison.
    correction_window = rows[jan_high_index : jan_high_index + 13]
    low_row = min(correction_window, key=lambda row: float(row["close"]))
    low_index = next(index for index, row in enumerate(rows) if row["date"] == low_row["date"])
    after_low = rows[low_index:]
    first_rebound_window = rows[low_index : low_index + 21]
    jan_high = float(jan_high_row["close"])
    low_close = float(low_row["close"])
    first_rebound_peak = max(float(row["close"]) for row in first_rebound_window)
    latest = float(rows[-1]["close"])

    reclaim_90_date = first_date(after_low, lambda row: float(row["close"]) >= jan_high * 0.90)
    reclaim_100_date = first_date(after_low, lambda row: float(row["close"]) >= jan_high)
    stabilization_date = first_stabilization_date(rows, low_index)

    record = {
        **candidate,
        "as_of": str(rows[-1]["date"]),
        "jan_high_date": str(jan_high_row["date"]),
        "jan_high_close": round(jan_high, 2),
        "correction_low_date": str(low_row["date"]),
        "correction_low_close": round(low_close, 2),
        "drawdown_from_jan_high_to_low_pct": pct(low_close / jan_high - 1),
        "stabilization_proxy_date": stabilization_date,
        "days_from_low_to_stabilization_proxy": trading_days_between(rows, str(low_row["date"]), stabilization_date),
        "reclaim_90pct_jan_high_date": reclaim_90_date,
        "days_from_low_to_reclaim_90pct_jan_high": trading_days_between(rows, str(low_row["date"]), reclaim_90_date),
        "reclaim_jan_high_date": reclaim_100_date,
        "days_from_low_to_reclaim_jan_high": trading_days_between(rows, str(low_row["date"]), reclaim_100_date),
        "first_rebound_peak_vs_jan_high_pct": pct(first_rebound_peak / jan_high),
        "latest_close": round(latest, 2),
        "latest_vs_jan_high_pct": pct(latest / jan_high),
    }
    record["bk_shape_label"] = classify(record)
    return record


def rank_key(record: dict[str, object]) -> tuple[float, float, float]:
    days = record["days_from_low_to_reclaim_90pct_jan_high"]
    speed = 999.0 if days is None else float(days)
    return (
        -float(record["first_rebound_peak_vs_jan_high_pct"]),
        speed,
        -float(record["latest_vs_jan_high_pct"]),
    )


def main() -> None:
    records = []
    errors = []
    for candidate in CANDIDATES:
        try:
            time.sleep(0.5)
            rows = fetch_daily(candidate["code"])
            if not rows:
                raise RuntimeError("empty kline response")
            records.append(metrics(candidate, rows))
        except Exception as exc:
            errors.append({**candidate, "error": str(exc)})
    records.sort(key=rank_key)
    for index, record in enumerate(records, 1):
        record["rank"] = index

    payload = {
        "generated_on": str(date.today()),
        "as_of": END_DATE,
        "method": {
            "source": "Tencent Securities public adjusted daily K-line endpoint",
            "candidate_pool": "18 representative A-share AI application candidates; not exhaustive",
            "stabilization_proxy": "After the correction low, first close above the 20-day moving average with at least 3 of the next 5 closes also at or above their rolling 20-day moving average.",
            "rebound_speed": "Trading days from the correction low to the first close at or above 90% of the January close high.",
            "correction_low": "Lowest close in the first 12 trading sessions from the January close high. This keeps later secondary pullbacks out of the first-repair comparison.",
            "strength": "Maximum close in the first 20 trading sessions from the correction low divided by the January close high.",
            "note": "BK-shape fit is a technical screen, not an investment recommendation.",
        },
        "records": records,
        "errors": errors,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
