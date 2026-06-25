---
type: data_contracts
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_when_planning
owner: project
---

# Data Contracts

## Purpose

定義 BridgeAid 的持久化資料形狀、規則格式與版本/來源規則。臨時除錯輸出不放這裡。

## 中介格式策略

服務規則以 JSON/YAML 作為「中介格式」（適合版控、人工審核、黑客松快速修改），經 JSON Schema 驗證後匯入 PostgreSQL（適合查詢、session、提醒、版本管理）。不可只用 JSON 檔當正式資料庫。

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

## API Contracts（初版，將隨 TASK.003 細化）

| Endpoint / Function | Input | Output | Error shape |
|---|---|---|---|
| `POST /chat` | session_id, message | intent, missing_fields, follow_up | `{code, message}` |
| `POST /recommend` | extracted_profile | services[] (status, hit_rules, missing, documents, sources) | `{code, message}` |
| `rule_engine.evaluate()` | profile, rule_jsonb | possible / insufficient_data / unlikely + hit conditions | raises ValidationError |

## 規則 JSON 範例

```json
{
  "id": "demo_emergency_aid_taipei",
  "name": "急難救助示範服務",
  "category": "emergency_aid",
  "jurisdiction": "local",
  "area": { "type": "city", "value": "Taipei" },
  "eligibility_rules": {
    "all": [
      { "field": "residence_city", "operator": "equals", "value": "Taipei" },
      { "any": [
        { "field": "event_type", "operator": "in", "value": ["失業","傷病","火災","重大事故"] },
        { "field": "income_status", "operator": "in", "value": ["低收入戶","中低收入戶","邊緣戶"] }
      ]}
    ]
  },
  "required_documents": [
    { "name": "身分證明文件", "condition": "always" },
    { "name": "事故證明", "condition": "event_type in ['火災','重大事故']" },
    { "name": "診斷證明", "condition": "event_type == '傷病'" }
  ],
  "source": { "title": "官方服務頁或公告", "url": "https://example.gov.tw", "last_checked_at": "2026-06-25" }
}
```

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
