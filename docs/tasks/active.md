---
type: task_index
status: active
priority: p0
updated: 2026-07-02
context_policy: always_retrievable
owner: project
---

# Active Tasks

## Active Queue

### TASK.010 - OllamaIntentParser（ADR-0004）

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-02
- Related docs:
  - `docs/adr/0004-llm-intent-parser-via-local-ollama.md`
  - `docs/data.md`
- Acceptance criteria:
  - [x] `OllamaIntentParser` 實作 `IntentParser` port；`INTENT_PARSER=ollama` 才啟用，預設 deterministic。
  - [x] 輸出經白名單/型別/枚舉清洗；布林只設 True；deterministic 命中優先。
  - [x] Ollama 不可用/逾時/非 JSON → fallback deterministic，不阻斷對話。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（114 passed）
- Notes:
  - 本機 Ollama 實測待 maintainer 安裝（`ollama pull qwen3:4b`）；測試用 MockTransport。

### TASK.011 - 提醒到期送達（輕量 in-process 排程）

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-02
- Related docs:
  - `docs/adr/0006-reminder-delivery-via-lightweight-in-process-scheduler.md`
  - `docs/security.md`
- Acceptance criteria:
  - [x] FastAPI lifespan 內 asyncio 排程每 30s 掃描到期 pending 提醒。
  - [x] LINE 配置時 push（`push_text`），否則模擬送達記 log；皆轉 `sent`。
  - [x] 送達失敗留 pending 重試；排程例外不影響 API。
- Validation:
  - [x] `uv run pytest`（含 10 個 delivery 測試）
  - [x] 實機驗證：過期提醒 30s 內轉 `sent`。
- Notes:
  - ADR-0006 為 proposed，待 maintainer 接受；Redis/Celery 延後至部署規模需要時。

### TASK.012 - Docker Postgres 落地 + Demo UI 打磨

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-02
- Related docs:
  - `docs/ui.md`
  - `docs/accessibility.md`
- Acceptance criteria:
  - [x] `docker-compose.yml`（postgres:17-alpine，綁 127.0.0.1，initdb 自動套 schema）。
  - [x] `app.importer` 實跑匯入 6 服務；API 保留 degraded mode。
  - [x] Demo UI：提醒狀態中文徽章 + 輪詢展示送達、送出中狀態、衝突訊息服務名稱化。
- Validation:
  - [x] `docker compose up -d` + importer（6 services / 15 documents / 2 conflicts）
  - [x] `uv run pytest`（114 passed）
- Notes:
  - 對話衝突提示改顯示服務中文名稱（原 raw id）。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`. 已完成任務見 `docs/tasks/completed.md`（TASK.001–009 已移出本檔）。

## Next Phase Candidates

- LINE 實連驗證：tunnel（ngrok/cloudflared）+ webhook URL 設定 + 真機 reply/push（憑證機制已就緒）。
- Ollama 本機實測與模型選型（qwen3 小尺寸起）。
- 4 筆 `needs_review` 服務的人工政策審核（maintainer）。
- session/提醒改 DB 持久化（schema 已就緒）。
