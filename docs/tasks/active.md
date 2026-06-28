---
type: task_index
status: active
priority: p0
updated: 2026-06-26
context_policy: always_retrievable
owner: project
---

# Active Tasks

## Active Queue

### TASK.001 - 題目收斂與 MVP 服務清單

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/project.md`
  - `docs/memory/current.md`
- Acceptance criteria:
  - [x] 確認 MVP 主場景（急難救助 + 住宅/生活補助 + 邊緣戶提醒）。
  - [x] 選定 5–10 筆服務候選並標註官方來源 URL。
  - [x] 確認 Demo 地理範圍（1–2 縣市 + 中央）。
- Validation:
  - [x] `npm run docs:refresh`
- Notes:
  - 詳細服務整理見 `docs/data.md` 的 MVP Service Candidate Scope。

### TASK.006 - 提醒系統（opt-in）與來源追溯（Week 6）

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/security.md`
  - `docs/data.md`
  - `docs/adr/0005-opt-in-reminder-system-and-source-trace-endpoints.md`
- Acceptance criteria:
  - [x] 提醒需 opt-in（無 consent 拒絕 403）；可建立/列出/取消，最小化欄位。
  - [x] `reminder_type`/`channel`/`scheduled_at` 驗證（422）；取消需 session 擁有權（404）。
  - [x] 來源追溯端點：`GET /services` 與 `GET /services/{id}/source`（含 version/needs_review/last_checked_at）。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（65 passed）
- Notes:
  - 提醒先 in-memory（`ReminderStore` port）；DB（`reminder_tasks`）與實際送達（排程）為後續。

### TASK.007 - Demo 情境回歸測試（Week 7）

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-06-26
- Related docs:
  - `docs/testing.md`
  - `docs/data.md`
- Acceptance criteria:
  - [x] 建立 10–20 組 demo 情境 fixture，涵蓋急難、租屋、低收入、長照、失業與衝突提示。
  - [x] 回歸測試確認 deterministic parser 抽取關鍵欄位，rule engine 推薦預期服務。
  - [x] 每組可能推薦結果皆保留來源追溯，不輸出不存在的服務 ID。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（91 passed）
  - [x] `npm run docs:refresh`
- Notes:
  - 12 組情境 fixture 位於 `tests/fixtures/demo_scenarios.json`；不接外部 LLM、不新增網路或排程依賴。

### TASK.008 - MVP 服務資料準確性稽核

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-06-26
- Related docs:
  - `docs/data.md`
  - `docs/testing.md`
- Acceptance criteria:
  - [x] 重新核對 6 筆服務的官方來源與核心資格摘要。
  - [x] 修正明顯過寬或過舊的 demo 規則。
  - [x] 對仍需人工政策審核的服務保留 `needs_review`。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（91 passed）
  - [x] `npm run docs:refresh`
- Notes:
  - 修正租金補貼來源、社宅成年年齡、急難救助事件條件、長照 care_need 條件。

### TASK.009 - Web Demo Shell（無新增依賴）

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-06-26
- Related docs:
  - `docs/ui.md`
  - `docs/accessibility.md`
  - `docs/html-guidelines.md`
- Acceptance criteria:
  - [x] FastAPI 可於 `/demo/` serve Web demo，不需新增 Node 或前端依賴。
  - [x] Demo 可呼叫 `/chat`、`/services/{id}/source`、`/reminders`，展示推薦、文件 checklist、來源追溯與 opt-in 提醒。
  - [x] UI 使用語意化 HTML、鍵盤可操作表單與可見 focus。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（93 passed）
  - [x] `npm run docs:refresh`
- Notes:
  - 靜態檔位於 `demo/`；本機服務 URL：`http://127.0.0.1:8000/demo/`。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`. 已完成任務見 `docs/tasks/completed.md`。

## Next Phase Candidates

- 提醒實際送達（Redis/Celery + LINE/Email）。
- 接入本地 Ollama intent parser（ADR-0004）。
- Demo 打磨與 10–20 組測試情境（Week 7）。
