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

- Active priority: 規則引擎雛形已完成（TASK.002：schema + evaluator + 5 rules + 14 tests）；下一步 TASK.003 後端 API 與 PostgreSQL 骨架。
- Current phase: rule engine 雛形可運作；尚無 FastAPI/DB 與對話流程。
- Current owner / handoff state: shawn（maintainer）；團隊其他成員尚未登錄。

## Important Constraints

- AI 不得直接承諾資格；回覆用「可能符合，需承辦單位確認」格式。
- 個資最小化：預設匿名試算，僅 opt-in 才建立提醒/保存紀錄；Demo 用假資料。
- 每條服務規則須附 source_url、last_checked_at、version；過期標記 needs_review。
- 不重複歷史敘事於 current memory、active tasks、completed history。

## Next Step

- TASK.003：設計 PostgreSQL schema 並寫 JSON→DB 匯入工具，重用 `app.rule_engine.load_rules`。
- 補齊 5–10 筆服務的真實官方來源 URL 並由人工審核（目前為示範 example.gov.tw）。

## Last Validation Snapshot

- Last docs refresh: 2026-06-25
- Last test command: uv run pytest -q（14 passed）/ npm run docs:ready
- Known failing checks: none
