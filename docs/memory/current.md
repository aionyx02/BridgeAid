---
type: working_memory
status: active
priority: p0
updated: 2026-06-26
context_policy: always_retrievable
owner: project
---

# Current Project Memory

## Current Strategy

- 收斂題目為「主動式公共服務導航」：事件/情境驅動，而非搜尋式服務。
- MVP 主場景：急難救助 + 住宅/生活補助 + 邊緣戶提醒；Demo 範圍固定為臺北市 + 中央全國性服務，已整理 6 筆官方來源規則。
- AI 只做入口/轉譯（意圖、欄位、追問、白話）；rule engine 做資格判斷、衝突檢查、文件條件。
- 保持 docs retrieval-first：啟動狀態維持精簡，詳細計畫放 on-demand task 檔。

## Current Focus

- Active priority: TASK.001/004/005/006/007/008/009 完成。MVP 服務清單、對話、推薦彙整、opt-in 提醒、來源追溯端點、12 組 demo 情境、資料稽核與 `/demo/` Web shell 皆可跑。ADR-0002/0003 accepted；ADR-0004（Ollama）、0005（提醒）proposed。
- Current phase: API degraded mode 可跑（healthz/recommend/chat/reminders/services/line webhook）；session 與提醒皆 in-memory；DB 決定先本地；LLM 待接 Ollama。
- Current owner / handoff state: shawn（maintainer）；團隊其他成員尚未登錄。

## Important Constraints

- AI 不得直接承諾資格；回覆用「可能符合，需承辦單位確認」格式。
- 個資最小化：預設匿名試算，僅 opt-in 才建立提醒/保存紀錄；Demo 用假資料。
- 每條服務規則須附 source_url、last_checked_at、version；過期標記 needs_review。
- 不重複歷史敘事於 current memory、active tasks、completed history。

## Next Step

- 待 maintainer 確認 ADR-0004（Ollama）、ADR-0005（提醒）。候選下一任務：接本地 Ollama parser、提醒實際送達（Redis/Celery）、或前端 Demo UI 打磨。
- 使用者把 LINE 憑證存入 keychain（`uv run keyring set bridgeaid LINE_CHANNEL_ID / LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN`），再做 LINE 實連驗證。
- DB 決定先本地：本機架 PostgreSQL → `psql "$DATABASE_URL" -f db/schema.sql` + `uv run python -m app.importer`（之後再搬）。
- `rent_subsidy_central`、`social_housing_taipei`、`long_term_care_central`、`unemployment_assistance_central` 仍標 `needs_review`：來源已核對，但 demo 規則需人工政策審核後再升為高信心。

## Last Validation Snapshot

- Last docs refresh: 2026-06-26
- Last test command: uv run pytest（93 passed）/ uv run ruff check .
- Known failing checks: none
