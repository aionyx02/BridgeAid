---
type: task_index
status: backlog
priority: p2
updated: 2026-06-25
context_policy: on_demand
owner: project
---

# Backlog

## Future Work

- [ ] 對真實 PostgreSQL 實跑 `db/schema.sql` + `app.importer`（TASK.003 後續，待 DB/伺服器位置決定）。
- [ ] LINE 實連驗證 reply/push（client 已實作；需 channel access token + 公開 webhook URL）。
- [ ] 接入 LLM intent parser（替換 deterministic parser；新增依賴+金鑰，需另開 ADR）。
- [ ] 文件 checklist 產生器與衝突檢查規則（Week 5）。
- [ ] 提醒系統（LINE/Email）與來源追溯 UI（Week 6）。
- [ ] 後台管理頁：維護服務、規則 JSON 與來源審核狀態。
- [ ] 邊緣戶 opt-in 提醒（以年齡/事件/期限觸發）。
- [ ] 多語/白話轉寫（英、越南語、台語語氣）。
- [ ] 語音入口（STT → LLM → 規則 → TTS），第二階段。
- [ ] RAG 來源/FAQ 檢索（pgvector/Qdrant），第二階段。
- [ ] 場域驗證：5–10 位不同數位熟悉度使用者 usability test。

## Parking Lot

Ideas not yet ready for implementation. Move to `active.md` only when scope, acceptance criteria, and risk are clear.
