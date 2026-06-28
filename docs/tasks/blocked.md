---
type: task_blockers
status: active
priority: p1
updated: 2026-06-26
context_policy: retrieve_when_planning
owner: project
---

# Blocked / Approval-Gated Work

## Blocked

- 正式服務規則的細部資格條件仍需人工政策審核；目前 demo 已核對官方來源，部分服務以 `needs_review` 避免高信心呈現。
- 團隊其他成員（含至少 1 位非中華民國國籍成員）尚未確定與登錄。

## Requires Explicit Approval

- 架構/資料契約變更的實作須先有 accepted ADR。首個架構 ADR-0002 已 accepted；後續重大變更需新增 ADR。
- 破壞性動作行為變更。
- 憑證、權限、檔案系統、網路或個資邊界變更。
- 大型依賴新增或移除（如導入 pgvector/Qdrant、電話/電信串接）。
- 處理真實個案個資（Demo 階段僅用假資料）。
