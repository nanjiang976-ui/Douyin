from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener


KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
OUTPUT_PATH = Path("ai_cpu_low_position_screen.json")
DIRECT_OPENER = build_opener(ProxyHandler({}))

CANDIDATES = [
    # AI applications: productivity, enterprise software, creative content, vertical apps.
    {"code": "688111", "name": "金山办公", "theme": "AI应用端", "layer": "办公与生产力"},
    {"code": "002230", "name": "科大讯飞", "theme": "AI应用端", "layer": "大模型与垂直应用"},
    {"code": "300624", "name": "万兴科技", "theme": "AI应用端", "layer": "创意软件"},
    {"code": "688095", "name": "福昕软件", "theme": "AI应用端", "layer": "文档软件"},
    {"code": "600588", "name": "用友网络", "theme": "AI应用端", "layer": "企业软件"},
    {"code": "603039", "name": "泛微网络", "theme": "AI应用端", "layer": "协同办公"},
    {"code": "300170", "name": "汉得信息", "theme": "AI应用端", "layer": "企业数字化"},
    {"code": "300634", "name": "彩讯股份", "theme": "AI应用端", "layer": "企业协同与邮件"},
    {"code": "002315", "name": "焦点科技", "theme": "AI应用端", "layer": "跨境B2B"},
    {"code": "300418", "name": "昆仑万维", "theme": "AI应用端", "layer": "内容与智能体"},
    {"code": "300364", "name": "中文在线", "theme": "AI应用端", "layer": "数字内容"},
    {"code": "601360", "name": "三六零", "theme": "AI应用端", "layer": "搜索与安全"},
    # CPU chain: distinguish CPU products from system and server-chain extensions.
    {"code": "688041", "name": "海光信息", "theme": "CPU相关", "layer": "CPU与DCU本体"},
    {"code": "688047", "name": "龙芯中科", "theme": "CPU相关", "layer": "CPU与基础软件生态"},
    {"code": "603019", "name": "中科曙光", "theme": "CPU相关", "layer": "高端计算系统"},
    {"code": "000066", "name": "中国长城", "theme": "CPU相关", "layer": "自主计算系统生态"},
    {"code": "688008", "name": "澜起科技", "theme": "CPU相关", "layer": "服务器互连配套"},
    {"code": "000977", "name": "浪潮信息", "theme": "CPU相关", "layer": "服务器与智算系统"},
]


def market_code(code: str) -> str:
    return f"sh{code}" if code.startswith(("6", "9")) else f"sz{code}"


def fetch_daily(code: str, start_date: str, end_date: str) -> list[dict[str, float | str]]:
    ticker = market_code(code)
    params = {"param": f"{ticker},day,{start_date},{end_date},500,qfq"}
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
    columns = [
            "date",
            "open",
            "close",
            "high",
            "low",
            "volume",
    ]
    numeric_columns = {"open", "close", "high", "low", "volume"}
    records = []
    for row in rows:
        record = dict(zip(columns, row[:6]))
        try:
            for column in numeric_columns:
                record[column] = float(record[column])
        except (TypeError, ValueError):
            continue
        records.append(record)
    return records


def pct(value: float) -> float:
    return round(value * 100, 2)


def return_over(frame: list[dict[str, float | str]], periods: int) -> float | None:
    if len(frame) <= periods:
        return None
    return pct(float(frame[-1]["close"]) / float(frame[-1 - periods]["close"]) - 1)


def metrics(candidate: dict[str, str], frame: list[dict[str, float | str]]) -> dict[str, object]:
    window = frame[-250:]
    close = float(window[-1]["close"])
    low_52w = min(float(row["low"]) for row in window)
    high_52w = max(float(row["high"]) for row in window)
    position = (close - low_52w) / (high_52w - low_52w) if high_52w != low_52w else 0.0
    drawdown = close / high_52w - 1
    low_20d = min(float(row["low"]) for row in window[-20:])
    ma_60d = sum(float(row["close"]) for row in window[-60:]) / len(window[-60:])

    if position <= 0.35:
        position_label = "低位观察"
    elif position <= 0.50:
        position_label = "中低位观察"
    else:
        position_label = "非低位"

    return {
        **candidate,
        "as_of": str(window[-1]["date"]),
        "close": round(close, 2),
        "low_52w": round(low_52w, 2),
        "high_52w": round(high_52w, 2),
        "position_52w_pct": pct(position),
        "drawdown_from_52w_high_pct": pct(drawdown),
        "return_20d_pct": return_over(window, 20),
        "return_60d_pct": return_over(window, 60),
        "distance_from_20d_low_pct": pct(close / low_20d - 1),
        "distance_from_60d_ma_pct": pct(close / ma_60d - 1),
        "position_label": position_label,
    }


def main() -> None:
    today = date.today()
    start = (today - timedelta(days=500)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    records = []
    errors = []
    for candidate in CANDIDATES:
        try:
            time.sleep(0.8)
            frame = fetch_daily(candidate["code"], start, end)
            if not frame:
                raise RuntimeError("empty kline response")
            records.append(metrics(candidate, frame))
        except Exception as exc:  # Keep the rest of the screen usable if one ticker fails.
            errors.append({**candidate, "error": str(exc)})

    records.sort(key=lambda item: (item["theme"], item["position_52w_pct"]))
    payload = {
        "generated_on": str(today),
        "method": {
            "source": "Tencent Securities public daily adjusted K-line endpoint",
            "window": "latest 250 trading sessions",
            "low_position": "52-week position <= 35%",
            "mid_low_position": "35% < 52-week position <= 50%",
            "note": "Relative position is a screening signal, not a buy signal.",
        },
        "records": records,
        "errors": errors,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
