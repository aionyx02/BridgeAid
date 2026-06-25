---
type: testing_policy
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_when_debugging
owner: project
---

# Testing Strategy

## Required Checks

文件 / context 治理（Node）：

```bash
npm run lint
npm run security:scan
npm test
npm run team:guard
npm run docs:refresh
npm run docs:ready
```

應用層（Python 3.14，待程式碼落地後）：

```bash
ruff check .
ruff format --check .
pytest
```

## Test Layers

| Layer | Purpose | Command |
|---|---|---|
| Docs static | guard/test 腳本語法檢查 | `npm run lint` |
| Docs unit | guard 行為、路徑正規化、generated 穩定性 | `npm test` |
| Team checks | task owner 與成員註冊有效性 | `npm run team:guard` |
| Docs integration | refresh、link、schema、index 重建 | `npm run docs:refresh` |
| Adoption readiness | 嚴格 placeholder + lint + scan + test + refresh | `npm run docs:ready` |
| App lint/format | Python 風格 | `ruff check .` / `ruff format --check .` |
| App unit | rule engine、services、repositories | `pytest` |
| CI drift | refresh 後 generated 不應變動 | `npm run docs:refresh` + `git diff --exit-code` |

## Rule Engine 驗證重點（對應成效指標）

- 意圖分類：10 組測試句，至少正確分類 8 組（急難/租屋/照顧/失業）。
- 資格判斷：20 組案例與人工標註比對一致率。
- 每個推薦結果附命中條件與缺失欄位；不同事件類型輸出不同文件清單。
- 衝突檢查：至少支援同一事故不可重複申請的規則。
- 來源追溯：結果可點開官方來源、版本、最後檢查日期。

## Regression Policy

修 bug 時：

1. 重現或記錄無法重現的原因。
2. 可能無聲回歸者加 targeted 測試或 guard。
3. root cause 記錄在 session log。
4. 只有 durable 行為/政策/active plan 改變時才更新 current docs。

## Security Validation

- 動到 docs、workflow、fixtures、automation 前跑 `npm run security:scan`。
- 動到 secrets、憑證、shell 執行、網路行為時，測試證據需搭配資安理由（見 `docs/security.md`）。
