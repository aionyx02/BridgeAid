---
type: working_memory
status: active
priority: p0
updated: 2026-07-02
context_policy: always_retrievable
owner: project
---

# Current Project Memory

## Current Strategy

- 收斂題目為「主動式公共服務導航」：事件/情境驅動，而非搜尋式服務。
- MVP 主場景：急難救助 + 住宅/生活補助 + 邊緣戶提醒；Demo 範圍固定為臺北市 + 中央全國性服務，已整理 6 筆官方來源規則。
- AI 只做入口/轉譯（意圖、欄位、追問、白話）；rule engine 做資格判斷、衝突檢查、文件條件。
- 下一階段主軸（maintainer 2026-07-02 確認）：Demo 體驗優先；LLM 走本地 Ollama；提醒送達用輕量 in-process 排程（非 Redis/Celery）；DB 用 Docker Postgres。

## Current Focus

- Active priority: TASK.010–012 完成。Ollama parser（預設關閉，`INTENT_PARSER=ollama` 啟用）、提醒到期送達（lifespan 排程）、Docker Postgres（compose + initdb）、Demo UI 打磨皆可跑並實測。
- Current phase: API 全功能可跑（degraded mode 仍支援）；ADR-0002–0006 全數 accepted。
- Current owner / handoff state: shawn（maintainer）；團隊其他成員尚未登錄。

## Important Constraints

- AI 不得直接承諾資格；回覆用「可能符合，需承辦單位確認」格式。
- 個資最小化：預設匿名試算，僅 opt-in 才建立提醒/保存紀錄；Demo 用假資料。
- 每條服務規則須附 source_url、last_checked_at、version；過期標記 needs_review。
- LLM 抽取結果視為不可信輸入：白名單清洗後才併入 profile；資格判斷永遠在 rule engine。
- 不重複歷史敘事於 current memory、active tasks、completed history。

## Next Step

- LINE 實連：keychain 已有 channel secret（healthz line_configured=true）；補 access token 確認 + tunnel（ngrok/cloudflared）+ LINE Developers webhook URL，真機驗證 reply/push。
- Ollama 本機實測：安裝 Ollama、`ollama pull qwen3:4b`、`BRIDGEAID_INTENT_PARSER=ollama` 起服務，實測中文抽取品質後定案模型。
- `rent_subsidy_central`、`social_housing_taipei`、`long_term_care_central`、`unemployment_assistance_central` 仍標 `needs_review`：需人工政策審核後再升高信心（demo 評審信心點）。

## Last Validation Snapshot

- Last docs refresh: 2026-07-02
- Last test command: uv run pytest（114 passed）/ uv run ruff check .
- Known failing checks: none
