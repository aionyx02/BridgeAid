---
type: working_memory
status: active
priority: p0
updated: 2026-06-25
context_policy: always_retrievable
owner: project
---

# Current Project Memory

## Current Strategy

- 收斂題目為「主動式公共服務導航」：事件/情境驅動，而非搜尋式服務。
- MVP 主場景：急難救助 + 住宅/生活補助 + 邊緣戶提醒；先 1–2 縣市 + 中央，人工整理 5–10 筆服務規則。
- AI 只做入口/轉譯（意圖、欄位、追問、白話）；rule engine 做資格判斷、衝突檢查、文件條件。
- 保持 docs retrieval-first：啟動狀態維持精簡，詳細計畫放 on-demand task 檔。

## Current Focus

- Active priority: TASK.003 後端骨架已實作（FastAPI + schema.sql + importer + LINE 驗章 + keychain）；待 ADR-0003 接受、架好 DB 並實跑匯入。
- Current phase: API 可在 degraded mode 啟動（/healthz、/recommend、/line/webhook）；尚無真實 DB 與對話流程。
- Current owner / handoff state: shawn（maintainer）；團隊其他成員尚未登錄。

## Important Constraints

- AI 不得直接承諾資格；回覆用「可能符合，需承辦單位確認」格式。
- 個資最小化：預設匿名試算，僅 opt-in 才建立提醒/保存紀錄；Demo 用假資料。
- 每條服務規則須附 source_url、last_checked_at、version；過期標記 needs_review。
- 不重複歷史敘事於 current memory、active tasks、completed history。

## Next Step

- 由 maintainer 確認 ADR-0003；架設 PostgreSQL（位置待定）後 `psql -f db/schema.sql` 並 `uv run python -m app.importer` 實跑匯入。
- 使用者把 LINE 憑證存入 keychain：`uv run keyring set bridgeaid LINE_CHANNEL_SECRET`（+ ACCESS_TOKEN）。
- 補齊 5–10 筆服務的真實官方來源 URL 並由人工審核（目前為示範 example.gov.tw）。

## Last Validation Snapshot

- Last docs refresh: 2026-06-25
- Last test command: uv run pytest -q（32 passed）/ uv run ruff check . / npm run docs:ready
- Known failing checks: none
