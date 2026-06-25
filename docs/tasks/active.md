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

### TASK.004 - 對話流程與欄位追問（Web /chat + LINE）

- Status: review
- Priority: P0
- Owner: shawn
- Started: 2026-06-25
- Related docs:
  - `docs/architecture.md`
  - `docs/ui.md`
  - `docs/data.md`
- Acceptance criteria:
  - [x] Session 狀態管理：保存已抽取欄位、追問次數（一次不超過 3 題）。
  - [x] 依規則引擎缺失欄位動態追問，足夠後輸出推薦摘要（服務/文件/來源）。
  - [x] `POST /chat` 對話端點可多輪運作；LINE webhook 事件接到同一流程。
- Validation:
  - [x] `uv run ruff check .`
  - [x] `uv run pytest`（45 passed）
- Notes:
  - deterministic intent parser（關鍵字→欄位 token）；LLM adapter 為 port，之後接入（屆時另開 ADR：新增 LLM 依賴 + 金鑰 + 網路 egress）。
  - Session 為 in-memory store；DB 持久化（`user_sessions`）為後續。
  - 待真實 LINE 連線驗證 reply/push（需 channel access token + 公開 webhook URL）。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`.

## Next Phase Candidates

- LINE/Web 對話流程與 session 欄位追問（Week 4）。
- 文件 checklist 與衝突檢查（Week 5）。
- 提醒系統與來源追溯 UI（Week 6）。
