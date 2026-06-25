---
type: dependency_policy
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_when_planning
owner: project
---

# Dependencies

## Dependency Rules

- 優先使用語言內建、標準庫與既有依賴。
- 新增 runtime 依賴需明確理由。
- 大型框架、基礎設施、資料庫、認證或建構系統依賴需 ADR。
- 資安敏感依賴採用前需審查。
- 對應功能移除時一併移除未用依賴。

## Current Dependencies（規劃中，將隨實作落地）

| Dependency | Purpose | Scope | Replaceable? | Notes |
|---|---|---|---|---|
| Next.js | 前端 / Demo / 後台 | runtime | yes | landing、chat、後台管理 |
| FastAPI | 後端 API + rule engine 服務 | runtime | yes | Python 3.14 |
| PostgreSQL | 服務/規則/session/提醒儲存 | infra | hard | JSONB 存規則 |
| LINE Messaging API | 主要入口與提醒通道 | runtime | yes | 臺灣場景自然 |
| LLM API | 意圖辨識、欄位抽取、白話/多語轉寫 | runtime | yes | adapter 化，可換供應商 |
| Redis + Celery/RQ | 提醒、來源檢查排程 | infra | yes | MVP 簡化版 |
| 文件治理 guard（Node） | docs/context 治理 | dev | no | 隨模板提供，不進應用 runtime |

## Rejected / Deferred Dependencies

| Dependency | Reason | Date |
|---|---|---|
| pgvector / Qdrant | RAG 為第二階段，非 MVP 必要 | 2026-06-25 |
| 正式電話/電信串接（STT/TTS） | 技術與成本過高，MVP 不做 | 2026-06-25 |

## Dependency Change Checklist

- [ ] 既有依賴無法解決需求。
- [ ] 授權與維護狀態可接受。
- [ ] 資安影響已理解。
- [ ] 執行/體積成本可接受。
- [ ] 測試或驗證命令涵蓋新依賴路徑。
- [ ] 大型/基礎設施依賴已建立 ADR。
