---
type: adr
status: accepted
priority: p1
updated: 2026-07-02
context_policy: on_demand
owner: project
---
# ADR-0006: Reminder delivery via lightweight in-process scheduler

## Status

accepted

（maintainer 已於 2026-07-02 的計畫核准中同意此方向；此 ADR 記錄細節，接受與否依 docs/CLAUDE.md §3。）

## Context

ADR-0005 完成提醒的建立/列出/取消，實際送達留待後續，原構想為 Redis + Celery。限制：

- Celery 4+ 官方不支援 Windows（開發機為 Windows），Redis 也需 Docker/WSL，對黑客松 demo 過重。
- 提醒目前 in-memory（`ReminderStore` port），量小（demo 等級）。
- `docs/security.md`：提醒欄位最小化，送達內容不得回放個資敘述。
- Demo 需要「提醒真的會到」的可展示性（LINE push 或畫面可見的模擬送達）。

## Decision

1. 以 **asyncio 背景迴圈**（FastAPI lifespan 內啟動）每 30 秒掃描 `ReminderStore` 中 `pending` 且 `scheduled_at` 到期的提醒，不新增 Redis/Celery/APScheduler 依賴。
2. 送達走 `ReminderSender` port：`channel=line` 且 LINE access token 已配置時，呼叫 LINE Push API（`to = session_id`，LINE 會話的 session_id 即 LINE userId）；其他情況記 log 標示「模擬送達」。兩者皆將狀態轉 `sent`。
3. 送達文案由 `reminder_type` 對應固定白話模板 + 選填 note；不含個資敘述，並附「以承辦單位說明為準」。
4. 送達失敗（如 LINE API 錯誤）不改狀態，留在 `pending` 下一輪重試；排程迴圈任何例外都不得讓 API 崩潰。
5. `ReminderStore` port 增加 `list_pending()`；儲存與 API 契約不變，之後換 DB 或分散式排程（Redis/Celery）只需替換 store/scheduler，不動 API。

## Consequences

### Positive

- 零新增依賴、Windows 可跑；demo 可展示「到期即送達」。
- port 邊界不變，日後升級 Redis/Celery 是替換實作而非改契約。

### Negative

- 單一 process 內排程：多 worker 部署會重複掃描（in-memory store 下不會發生；DB 落地後需鎖或搬遷至真正的排程系統）。
- 重啟遺失提醒（沿 ADR-0005 in-memory 既有限制）。

### Neutral / Tradeoffs

- 30 秒輪詢對 demo 足夠；精確到秒的送達不是目標。

## Alternatives Considered


| Option                   | Pros         | Cons                      | Reason not chosen    |
| ------------------------ | ------------ | ------------------------- | -------------------- |
| Redis + Celery（原構想） | 正式、可分散 | Windows 不支援、demo 過重 | 延後至部署規模需要時 |
| APScheduler              | 現成排程功能 | 新增依賴，功能超出需求    | asyncio 迴圈已足夠   |
| 不做送達（僅模擬畫面）   | 零成本       | demo 說服力不足           | 送達是提醒的核心價值 |

## Security Review

- Trust boundary impact: 新增對 LINE Push API 的 egress（既有 LINE 信任邊界內，token 走 keychain）。
- Sensitive data impact: 送達文案僅含類型模板與選填 note，不含姓名/敘述。
- Permission impact: 無新增權限；未配置 LINE 時自動降級為 log。
- Failure mode: 送達失敗留 pending 重試；排程例外被吞掉並記 log，不影響 API。

## Resource Impact

- Memory impact: 無新增常駐結構（掃描既有 store）。
- CPU impact: 每 30 秒 O(pending 數) 掃描，demo 規模可忽略。
- I/O impact: 到期時每筆一次 LINE Push HTTP 呼叫。

## Rollback Plan

- 移除 lifespan 中的排程啟動即回退為「僅建立/列出/取消」；store 與 API 不受影響。
