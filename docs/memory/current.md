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

- LINE 實連已完成真機驗證（2026-07-02：真實帳號發訊息收到 bot 回覆）；tunnel 重開後用 `uv run python -m app.line.set_webhook https://<tunnel-host>` 重設。
- Ollama 已實測定案：`qwen2.5:1.5b`（優於 qwen3:4b 非思考模式，無幻覺、0.8–3s）；`think:false` + 證據閘門已入 code。
- 政策審核完成（2026-07-02）：6 筆服務全 active；失業給付新增 `involuntary_separation` 法定要件。後續建議季度複查來源。

## Last Validation Snapshot

- Last docs refresh: 2026-07-02
- Last test command: uv run pytest（114 passed）/ uv run ruff check .
- Known failing checks: none
