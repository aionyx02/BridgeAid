---
type: task_index
status: active
priority: p0
updated: 2026-06-25
context_policy: always_retrievable
owner: project
---

# Active Tasks

## Active Queue

### TASK.001 - 題目收斂與 MVP 服務清單

- Status: doing
- Priority: P0
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/project.md`
  - `docs/memory/current.md`
- Acceptance criteria:
  - [ ] 確認 MVP 主場景（急難救助 + 住宅/生活補助 + 邊緣戶提醒）。
  - [ ] 選定 5–10 筆服務候選並標註官方來源 URL。
  - [ ] 確認 Demo 地理範圍（1–2 縣市 + 中央）。
- Validation:
  - [ ] `npm run docs:refresh`
- Notes:
  - 詳細服務整理放 `docs/data.md` 與後續 task 檔。

### TASK.003 - 後端 API 與資料庫骨架

- Status: review
- Priority: P1
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/architecture.md`
  - `docs/dependencies.md`
  - `docs/adr/0003-backend-skeleton-persistence-secrets-and-api-surface.md`
- Acceptance criteria:
  - [x] FastAPI 專案骨架與 PostgreSQL schema（`db/schema.sql` 九張表）。
  - [~] 服務匯入工具（`app.importer`）：轉換已測；待真實 DB 實跑驗證。
  - [x] LINE webhook 簽章驗證 + 憑證走 OS keychain（env fallback）。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（32 passed）
- Notes:
  - 依工程優先序：先安全/個資邊界，再效能，再解耦。
  - 卡點：ADR-0003 待 maintainer 接受；伺服器/DB 位置未定，骨架在無 DB/無 secret 時仍可啟動（degraded）。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`.

## Next Phase Candidates

- LINE/Web 對話流程與 session 欄位追問（Week 4）。
- 文件 checklist 與衝突檢查（Week 5）。
- 提醒系統與來源追溯 UI（Week 6）。
