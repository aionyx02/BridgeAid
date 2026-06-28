---
type: adr
status: proposed
priority: p1
updated: 2026-06-25
context_policy: on_demand
owner: project
---
# ADR-0005: Opt-in reminder system and source-trace endpoints

## Status

accepted

（記錄方向；maintainer 確認後才 accepted，依 docs/CLAUDE.md §3。提醒涉及個資/同意邊界與對外 API 契約。）

## Context

Week 6 需求：提醒系統（補件、申請期限、續辦、即將符合條件）與來源追溯（每筆推薦顯示官方來源、版本、最後檢查日期）。限制（docs/security.md）：

- 預設匿名試算；**只有明確 opt-in 才建立提醒或保存紀錄**。
- 欄位最小化；不存完整敘述。
- 來源需可追溯，過期/未審服務以 `needs_review` 標示，不列高信心。

## Decision

1. **提醒（opt-in）**：`POST /reminders` 需帶 `consent: true`，否則拒絕（403）。儲存最小欄位：`session_id`、`reminder_type`、`scheduled_at`、`channel`、`status`、選填 `note`；不存個資敘述。
2. **類型/通道**：`reminder_type ∈ {document, deadline, renewal, eligibility}`；`channel ∈ {line, email}`。非法值 → 422。
3. **生命週期**：`status ∈ {pending, cancelled, sent}`；`GET /reminders/{session_id}` 列出、`DELETE /reminders/{id}?session_id=...` 取消（需屬於該 session，否則 404）。實際送達（排程/LINE/Email）為後續（Redis/Celery）。
4. **儲存**：先 in-memory（`ReminderStore` port）；DB 沿用 `reminder_tasks`（TASK.003 schema）為後續。
5. **來源追溯**：`GET /services` 與 `GET /services/{id}/source` 唯讀回傳來源、版本、`status`、`needs_review`、`last_checked_at`；推薦結果已內含 `source`（不重複實作判斷）。

## Consequences

### Positive

- 同意邊界明確、欄位最小化，符合個資原則。
- 來源透明、可追溯；needs_review 一致呈現。
- 儲存以 port 解耦，之後換 DB 不動 API。

### Negative

- in-memory 提醒於重啟後消失（before DB 落地）。
- 實際送達未實作（僅建立/列出/取消）。

### Neutral / Tradeoffs

- 不在本 ADR 實作排程/通知；留待提醒送達任務（Redis/Celery）。

## Alternatives Considered


| Option                     | Pros       | Cons                 | Reason not chosen |
| -------------------------- | ---------- | -------------------- | ----------------- |
| 預設建立提醒（免 consent） | 流程少一步 | 違反 opt-in/個資原則 | 必須 opt-in       |
| 直接寫 DB                  | 持久       | DB 尚未落地、耦合    | 先 in-memory port |
| 立即接排程送達             | 功能完整   | 範圍過大             | 拆為後續任務      |

## Security Review

- Trust boundary impact: 新增 reminders 寫入（需 consent）與 services 唯讀來源端點。
- Sensitive data impact: 僅存 session_id + 類型/時間/通道；無姓名/身分證/完整敘述。
- Permission impact: 無 consent 不建立；取消需 session 擁有權。
- Failure mode: 非法輸入 422；找不到 404；不可用不影響推薦/對話。

## Resource Impact

- Memory: in-memory 提醒清單（小）。
- CPU/I-O: 建立/列出/取消為 O(n) 記憶體操作；送達另議。

## Rollback Plan

- 移除 reminders router 與 store 即回退；唯讀來源端點無資料風險。
