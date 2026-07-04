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

### TASK.013 - 4 筆 needs_review 服務政策審核

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-02
- Related docs:
  - `docs/data.md`
- Acceptance criteria:
  - [x] 4 筆服務逐筆對照官方來源（行政院/北市府/1966/勞動部）核實資格要件。
  - [x] 修正：租金補貼加 18 歲門檻與失效來源 URL；長照 2.0 → 3.0；失業給付補「非自願離職」法定要件（新 profile 欄位 + 追問 + 關鍵字 + LLM 白名單）。
  - [x] 全數升為 active（version 2026.07、last_checked_at 2026-07-02）。
- Validation:
  - [x] `uv run pytest`（121 passed）
  - [x] live API：自願離職 unlikely、未知追問、17 歲租屋 unlikely。
- Notes:
  - 未建模的查核項（無自有住宅、所得分位點、就保年資）寫入文件清單說明，由承辦查調。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`. 已完成任務見 `docs/tasks/completed.md`（TASK.001–009 已移出本檔）。

## Next Phase Candidates

- Demo 演練：12 組情境走一遍 LINE + Web，順講稿節奏。
- session/提醒改 DB 持久化（schema 已就緒）。
- 服務規則季度性複查（來源 last_checked_at 超過 90 天標 needs_review）。
