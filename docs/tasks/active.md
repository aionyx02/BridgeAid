---
type: task_index
status: active
priority: p0
updated: 2026-07-04
context_policy: always_retrievable
owner: project
---

# Active Tasks

## Active Queue

### TASK.014 - application_process 資料契約 + /process 端點

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-04
- Related docs:
  - `docs/adr/0007-application-process-data-contract-and-line-interactive-layer.md`
  - `docs/data.md`
- Acceptance criteria:
  - [x] schema 新增選填 `application_process[]`（name/description/url/url_title/deadline/deadline_at）。
  - [x] 6 筆服務各補 4 步官方流程（含線上申請入口與時限）。
  - [x] `GET /services/{id}/process`；`/chat` 與 LINE 結果每筆 possible 附 steps。
- Validation:
  - [x] `uv run pytest`（142 passed）/ `uv run ruff check .`

### TASK.015 - LINE Flex 流程卡 + 提醒 opt-in postback

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-04
- Related docs:
  - `docs/adr/0007-application-process-data-contract-and-line-interactive-layer.md`
- Acceptance criteria:
  - [x] `line/flex.py`：carousel 卡（狀態行、流程步驟、⏰ 時限、官方入口/來源按鈕、提醒我申請）。
  - [x] postback 流：remind → 同意確認；remind_ok → `deadline_at−7天09:00` 建 deadline 提醒（consent=True）；remind_no → 不建立。
  - [x] Web demo 卡片同步渲染流程步驟 + 「提醒我申請」預填表單（consent 仍需人勾）。
- Validation:
  - [x] flex/postback 單元測試 + webhook 整合測試（簽章 + 假 reply client）。

### TASK.016 - 對話式資料管理 + 1957 諮詢出口

- Status: done
- Priority: P0
- Owner: shawn
- Started: 2026-07-04
- Related docs:
  - `docs/security.md`
- Acceptance criteria:
  - [x] 指令：`我的資料`（摘要+修改選項）、`修改<欄位>`（重問）、`清除資料`（清空 session）；新增 reply kind `info`。
  - [x] 指令在意圖抽取前攔截，pending 問題不會吞掉指令。
  - [x] 結果為空或邊緣戶（near_threshold）→ 附 1957 福利諮詢專線轉介。
- Validation:
  - [x] `uv run pytest`（142 passed，含 8 個 profile-command 測試）。

## Strategy

Keep `active.md` compact. Every active task must include an `Owner` from `docs/team/members.md`. Use `project` only for placeholder or unassigned setup work; `doing` tasks should be assigned to a real member. Put task-level details in dedicated `docs/tasks/*.md`, detailed implementation notes in per-member session logs, and future ideas in `docs/tasks/backlog.md`. 已完成任務見 `docs/tasks/completed.md`（TASK.001–013 已移出本檔）。

## Next Phase Candidates

- Demo 演練：12 組情境走一遍 LINE + Web，順講稿節奏。
- session/提醒改 DB 持久化（schema 已就緒）。
- 服務規則季度性複查（來源 last_checked_at 超過 90 天標 needs_review）。
- ADR-0007 待 maintainer 接受。
