---
type: data_contracts
status: active
priority: p1
updated: 2026-07-02
context_policy: retrieve_when_planning
owner: project
---

# Data Contracts

## Purpose

定義 BridgeAid 的持久化資料形狀、規則格式與版本/來源規則。臨時除錯輸出不放這裡。

## MVP Scope

臺北市 + 中央，6 筆候選規則見 `data/services/*.json`；官方 URL 在 `source.url`。

## 中介格式策略

服務規則以 JSON/YAML 作為「中介格式」（利於版控與人工審核），經 JSON Schema 驗證後匯入 PostgreSQL。不可只用 JSON 檔當正式資料庫。

來源 → 標準化 JSON/YAML → JSON Schema 驗證 → 匯入 PostgreSQL → API / Rule Engine / Reminder。

## Core Entities（資料表）

| 資料表 | 用途 | 關鍵欄位 |
|---|---|---|
| `services` | 公共服務主檔 | id, name, category, jurisdiction, description, status |
| `service_versions` | 服務版本 | service_id, version, effective_from, effective_to, review_status |
| `eligibility_rules` | 資格規則 | service_id, version, rule_jsonb, source_id |
| `required_documents` | 文件條件 | service_id, document_name, condition_jsonb |
| `conflict_rules` | 補助衝突 | service_id, conflict_service_id, conflict_type, reason |
| `source_documents` | 資料來源 | title, url, publisher, last_checked_at, checksum |
| `user_sessions` | 匿名對話狀態 | session_id, channel, extracted_profile_jsonb, expires_at |
| `recommendation_results` | 推薦紀錄 | session_id, result_jsonb, created_at |
| `reminder_tasks` | 提醒任務 | session_id, reminder_type, scheduled_at, channel, status |

## API Contracts（FastAPI，TASK.003 已實作骨架）

| Endpoint / Function | Input | Output | Error |
|---|---|---|---|
| `GET /healthz` | — | `{status, rules_loaded, line_configured, db_configured}` | — |
| `POST /recommend` | `{profile: {...}}` | `{results: [{service_id, service_name, status, hit_conditions, missing_fields, documents, needs_review, source}], conflicts: [{service_ids, type, reason}], document_checklist: [{document, services}]}` | 422 (驗證) |
| `POST /chat` | `{session_id, message}` | `{kind: "question"\|"result", text, options[], results[], conflicts[], document_checklist[]}` | 422 (驗證) |
| `POST /reminders` | `{session_id, reminder_type, scheduled_at, channel, consent, note?}` | `{id, session_id, reminder_type, scheduled_at, channel, status, note}` | 403（無 consent）/ 422（驗證） |
| `GET /reminders/{session_id}` | — | `{reminders: [...]}` | — |
| `DELETE /reminders/{id}?session_id=` | — | 取消後的 reminder | 404（非該 session 擁有） |
| `GET /services` | — | `{services: [{service_id, name, category, status, needs_review}]}` | — |
| `GET /services/{id}/source` | — | `{service_id, service_name, version, status, needs_review, source}` | 404 |
| `POST /line/webhook` | raw body + `X-Line-Signature` | `{status: "ok"}` | 401（簽章錯）/ 503（未設定 secret） |
| `rule_engine.evaluate_all()` | rules, profile | `Evaluation[]`（possible/insufficient_data/unlikely） | — |

`/recommend` 不需資料庫即可運作（規則於啟動載入）。`status` 取值見「評估輸出」。

## 規則格式與規則引擎（TASK.002）

- 正式契約：`data/schemas/service-rule.schema.json`（JSON Schema draft 2020-12）。
- 規則檔：`data/services/*.json`（每筆需通過 schema 驗證才入庫）。
- 規則引擎：`backend/app/rule_engine/`（`loader` 驗證、`evaluator` 判斷、`operators` 比較）。
- 條件 operator 允許清單（固定，不用 eval）：`equals`、`not_equals`、`in`、`not_in`、`gt`、`gte`、`lt`、`lte`、`exists`。
- `eligibility_rules` 為遞迴的 `all` / `any` 群組 + leaf condition `{field, operator, value}`。
- `required_documents[].condition` 為 `"always"` 或一個 condition 物件（不採字串 DSL，避免 eval 風險）。
- profile 欄位值採固定 token（如 `event_type`：`unemployment` / `illness` / `fire` / `major_accident` / `death_in_family`）。

### 規則 JSON 範例

```json
{
  "id": "emergency_aid_taipei",
  "name": "臺北市急難救助",
  "category": "emergency_aid",
  "jurisdiction": "local",
  "area": { "type": "city", "value": "Taipei" },
  "status": "active",
  "version": "2026.06",
  "eligibility_rules": {
    "all": [
      { "field": "residence_city", "operator": "equals", "value": "Taipei" },
      { "any": [
        { "field": "event_type", "operator": "in", "value": ["unemployment", "illness", "fire", "major_accident"] },
        { "field": "income_status", "operator": "in", "value": ["low_income", "mid_low_income", "near_threshold"] }
      ]}
    ]
  },
  "required_documents": [
    { "name": "身分證明文件", "condition": "always" },
    { "name": "事故證明", "condition": { "field": "event_type", "operator": "in", "value": ["fire", "major_accident"] } }
  ],
  "source": { "title": "官方服務頁或公告", "url": "https://example.gov.tw", "last_checked_at": "2026-06-25" }
}
```

### 評估輸出

- 三態：`possible` / `insufficient_data` / `unlikely`，附 `hit_conditions` 與真正阻擋的 `missing_fields`。
- `needs_review` 服務（來源過期/未審）以旗標標示，不列為高信心。
- `detect_conflicts` 找出 `choose_one` / `exclusive` 衝突（如租金補貼 vs 社會住宅）。

## Persistence Rules

- 每條規則必附 `source_url`、`last_checked_at`、`version`、`review_status`。
- 來源失效或超過檢查期限 → 標記 `needs_review`，不再作為高信心推薦。
- 匿名 session 設 `expires_at`；僅 opt-in 才保存提醒/紀錄（見 `docs/security.md`）。
- 推薦結果必須綁定資料庫服務 ID，不可由 LLM 自由生成服務。

## Migration Rules

- Schema 變更需測試或驗證步驟。
- 破壞性資料格式變更需 ADR。
- 需相容時記錄向後相容方式。
- 資料遷移指令與輸出放 session log。

## Cache Rules

- 規則與服務資料可快取，但版本變更或來源更新時需失效。
