---
type: adr
status: proposed
priority: p1
updated: 2026-07-04
context_policy: on_demand
owner: project
---

# ADR-0007: Application process data contract and LINE interactive layer

## Status

Proposed

## Context

Demo 回饋（2026-07-04）：推薦結果只回「可能符合的服務名單」，缺少「接下來怎麼辦」——完整行政流程、官方申請連結、時限，以及邊緣個案的人工諮詢出口。同時 LINE 端需要資料登錄/修正能力與圖像化呈現。限制：

- 規則檔是公開資料契約（`data/schemas/service-rule.schema.json`），變更需 ADR（docs/CLAUDE.md §7）。
- AI 邊界不變（ADR-0002）：流程/時限一律來自規則檔靜態欄位，不由 LLM 生成。
- 提醒仍為 opt-in（ADR-0005）；LINE 按鈕不得未經同意就建立提醒。
- LINE 限制：reply 最多 5 則訊息、carousel 12 bubbles、action label 20 字。

## Decision

1. **資料契約**：service rule 新增選填 `application_process: process_step[]`；`process_step = {name*, description*, url, url_title, deadline（人話說明）, deadline_at（YYYY-MM-DD，供排程）}`。步驟為官方公告之行政流程，與 `source` 同步人工審核。
2. **API**：`GET /services/{id}/process` 回傳步驟 + version/needs_review/source；`/chat`、LINE 推薦結果的每筆 possible 服務附帶 `application_process`。
3. **LINE 圖像化**：`backend/app/line/flex.py` 純函式產生 Flex carousel（每服務一張卡：狀態行、流程步驟、⏰ 時限、官方申請入口/資料來源 uri 按鈕、「提醒我申請」postback）。上限 10 bubbles、label 截 20 字、reply cap 5 則。
4. **提醒 opt-in postback 流**：`action=remind` → 回同意確認（quickReply）；`action=remind_ok` → 以 `deadline_at − 7 天 09:00`（無期限則 +7 天、不早於明日 09:00）建立 `deadline` 提醒（consent=True，note=服務名）；`action=remind_no` → 不建立。
5. **對話式資料管理**：`我的資料`（摘要 + 修改選項）、`修改<欄位>`（重問該欄位）、`清除資料`（清空 session）；新增 reply kind `info`。指令在意圖抽取前攔截，不進 LLM。
6. **1957 出口**：結果為空、或 `income_status=near_threshold`（邊緣戶）時，文末附 1957 福利諮詢專線轉介。

## Consequences

### Positive

- 使用者拿到可行動的下一步（官方連結、時限、提醒），而非只有名單。
- 流程資料與資格規則同一審核管線，來源可追溯；LLM 不參與。
- 資料查看/修改/清除滿足個資自主權（配合 docs/security.md 最小化原則）。

### Negative

- 流程/時限為靜態資料，政策改版需人工更新（沿用 `last_checked_at` 審核節奏）。
- Flex JSON 與 LINE 限制耦合（bubbles/label 上限），版面調整需重測。

### Neutral / Tradeoffs

- `deadline_at − 7 天`為固定提醒策略，先不做使用者自訂時間（Web 表單已可自訂）。

## Alternatives Considered

| Option | Pros | Cons | Reason not chosen |
|---|---|---|---|
| LLM 即時生成申請流程 | 零資料維護 | 幻覺風險、不可追溯 | 違反 ADR-0002 AI 邊界 |
| LIFF 網頁表單管資料 | UI 自由 | 需另做前端 + LIFF 設定 | demo 期程內對話指令已足夠 |
| 流程存獨立檔案/表 | 關注點分離 | 與規則審核脫鉤、易漂移 | 同檔同審最不易失真 |

## Security Review

- Trust boundary impact: postback data 視為不可信輸入，僅接受白名單 action + 已知 service id；無新增 egress。
- Sensitive data impact: 提醒仍只存類型/時間/服務名；`我的資料` 只回放結構化欄位，不含自由敘述。
- Permission impact: 無新增權限；提醒建立仍強制 consent。
- Failure mode: 未知 action/service 靜默忽略；Flex 建構失敗不影響文字回覆主流程。

## Resource Impact

- Memory impact: 規則檔各 +4 步驟，可忽略。
- CPU impact: Flex JSON 組裝 O(服務數)，可忽略。
- I/O impact: 無新增常態 I/O；postback 多一次 LINE reply 呼叫。

## Rollback Plan

- 移除 `application_process` 欄位（選填，讀取端 `get(..., [])` 容忍缺席）、`/process` 端點與 flex/postback 模組即可回退；提醒/對話核心不受影響。
