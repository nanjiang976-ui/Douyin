# Errors

Command failures and integration errors.

---

## [ERR-20260601-001] eastmoney_kline_fetch

**Logged**: 2026-06-01T23:05:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
EastMoney public historical K-line requests could not complete the A-share screen.

### Error
```text
SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC
Remote end closed connection without response
```

### Context
- Attempted to fetch public adjusted daily K-lines for an 18-stock AI application and CPU-related candidate pool.
- Direct requests still became unreliable after a small number of responses.
- No credentials or private APIs were involved.

### Suggested Fix
Use Tencent Securities public adjusted daily K-line endpoint as a fallback.

### Metadata
- Reproducible: unknown
- Related Files: screen_low_position_stocks.py

### Resolution
- **Resolved**: 2026-06-01T23:05:00+08:00
- **Notes**: Switched the reusable screen script to Tencent Securities and verified 18 records with zero errors.

---
