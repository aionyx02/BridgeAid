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

- [ ] LINE 實連驗證 reply/push（client 已實作；需 channel access token + 公開 webhook URL/tunnel）。
- [ ] Ollama 本機實測與模型選型（TASK.010 已實作 parser；需裝 Ollama 實測中文抽取品質）。
- [ ] session / 提醒改 DB 持久化（Docker Postgres 已落地、schema 已就緒；目前 in-memory）。
- [ ] Email 提醒通道實作（目前 email channel 為模擬送達）。
- [ ] 後台管理頁：維護服務、規則 JSON 與來源審核狀態。
- [ ] 邊緣戶 opt-in 提醒（以年齡/事件/期限觸發）。
- [ ] 多語/白話轉寫（英、越南語、台語語氣）。
- [ ] 語音入口（STT → LLM → 規則 → TTS），第二階段。
- [ ] RAG 來源/FAQ 檢索（pgvector/Qdrant），第二階段。
- [ ] 場域驗證：5–10 位不同數位熟悉度使用者 usability test。

## Parking Lot

Ideas not yet ready for implementation. Move to `active.md` only when scope, acceptance criteria, and risk are clear.
