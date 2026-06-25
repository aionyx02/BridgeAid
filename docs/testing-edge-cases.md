---
type: testing_reference
status: active
priority: p2
updated: 2026-06-25
context_policy: retrieve_when_debugging
owner: project
---

# Testing Edge Cases

| ID | Area | Edge case | Expected behavior | Regression check |
|---|---|---|---|---|
| `EDGE.001` | Intent parser | 模糊/多重情境（同時失業+住院+租金） | 分類為多類別並逐一追問，不漏類別 | 意圖分類測試集 |
| `EDGE.002` | Rule engine | 資料不足無法判斷資格 | 回 `insufficient_data` 並列出缺失欄位，不臆測 | rule evaluator 單元測試 |
| `EDGE.003` | Rule engine | 多服務衝突（同一事故不可重複申請） | 觸發 conflict 規則並提示擇一 | conflict 規則測試 |
| `EDGE.004` | Data / source | 來源過期（超過 last_checked_at 期限） | 標記 needs_review，不列為高信心推薦 | source 過期掃描 |
| `EDGE.005` | AI boundary | LLM 產生不存在的服務或條件 | 結果綁定 DB 服務 ID，未命中則不輸出 | 推薦結果與 DB 對照測試 |
| `EDGE.006` | Privacy | 使用者於匿名階段被要求敏感欄位 | 僅在 opt-in 後要求；最小化欄位 | 個資流程測試 |
