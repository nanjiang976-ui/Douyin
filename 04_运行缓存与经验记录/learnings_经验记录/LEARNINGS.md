# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260609-001] best_practice

**Logged**: 2026-06-09T20:20:00+08:00
**Priority**: low
**Status**: pending
**Area**: docs

### Summary
创建含中文内容的 Codex skill 后，用 UTF-8 模式运行校验脚本更稳。

### Details
Windows 环境下 `quick_validate.py` 默认按系统编码读取文件，遇到中文 `SKILL.md` 可能触发 GBK 解码错误。用 `python -X utf8 quick_validate.py <skill-path>` 可以避免误判。

### Suggested Action
以后创建中文 skill 时，校验命令优先使用 `python -X utf8`；同时注意 `agents/openai.yaml` 的 `short_description` 需要满足 25-64 字符限制。

### Metadata
- Source: error
- Related Files: C:\Users\NJ\.codex\skills\douyin-content-analysis\SKILL.md
- Tags: skill, validation, windows, utf8

---

## [LRN-20260601-001] best_practice

**Logged**: 2026-06-01T23:05:00+08:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Use Tencent Securities public adjusted daily K-line endpoint as the stable fallback for A-share relative-position screens.

### Details
The EastMoney historical K-line endpoint was unreliable in this environment because TLS failures and intermittent connection closures prevented a complete candidate screen. Tencent Securities returned the required adjusted daily candles for all 18 candidates and supported the same 250-session relative-position calculation.

### Suggested Action
For future A-share screens, try the existing AlphaEar stock workflow first. If the EastMoney path fails, switch to the Tencent Securities `fqkline` endpoint and preserve the data-source label in generated notes.

### Metadata
- Source: error
- Related Files: screen_low_position_stocks.py
- Tags: finance, a-share, market-data, fallback

---
