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

### TASK.002 - 資料格式與規則引擎原型

- Status: todo
- Priority: P0
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/data.md`
  - `docs/architecture.md`
  - `docs/testing.md`
- Acceptance criteria:
  - [ ] 定義服務規則 JSON schema 與 eligibility/conflict/document 結構。
  - [ ] rule evaluator 能輸出 possible / insufficient_data / unlikely 並附命中條件。
  - [ ] 至少 5 筆服務規則通過 schema 驗證。
- Validation:
  - [ ] `pytest`（rule engine 測試案例）
  - [ ] `npm run docs:refresh`
- Notes:
  - 重大資料契約變更需先建立或更新 ADR。

### TASK.003 - 後端 API 與資料庫骨架

- Status: todo
- Priority: P1
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/architecture.md`
  - `docs/dependencies.md`
- Acceptance criteria:
  - [ ] FastAPI 專案骨架與 PostgreSQL schema（services/rules/documents/sources）。
  - [ ] 服務匯入工具能把 JSON 規則匯入 DB。
- Validation:
  - [ ] `ruff check .`
  - [ ] `pytest`
- Notes:
  - 依工程優先序：先安全/個資邊界，再效能，再解耦。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`.

## Next Phase Candidates

- LINE/Web 對話流程與 session 欄位追問（Week 4）。
- 文件 checklist 與衝突檢查（Week 5）。
- 提醒系統與來源追溯 UI（Week 6）。
