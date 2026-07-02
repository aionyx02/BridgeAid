---
type: adr
status: accepted
priority: p1
updated: 2026-07-02
context_policy: on_demand
owner: project
---
# ADR-0004: LLM intent parser via local Ollama

## Status

accepted

（maintainer 已於 2026-07-02 確認接受，依 docs/CLAUDE.md §3。）

## Context

TASK.004 的 intent parser 目前是 deterministic 關鍵字版（`IntentParser` port，預設 `DeterministicIntentParser`）。要提升對自然語言的覆蓋（同義、語序、口語、錯字），需要 LLM 做意圖辨識與欄位抽取。限制：個資敏感、需可離線/低成本、不希望把使用者敘述送到外部雲端 LLM。

使用者方向：先接**本地 Ollama**。

## Decision

1. 新增 `OllamaIntentParser`，實作既有 `IntentParser` port（`extract(text) -> dict`），不改 ConversationManager。
2. 對本地 Ollama HTTP endpoint（預設 `http://localhost:11434`）呼叫，要求模型輸出**嚴格 JSON**，只允許既定欄位與 token（與 `docs/data.md` 一致）；輸出再經白名單/型別清洗才併入 profile。
3. 邊界：AI 僅做抽取，**不做資格判斷**（仍由規則引擎）；抽取結果視為不可信輸入，需驗證。
4. Degraded / 安全：Ollama 不可用或逾時 → fallback 回 `DeterministicIntentParser`，不阻斷對話。endpoint、model 走設定（keychain/env：`OLLAMA_HOST`、`OLLAMA_MODEL`）。
5. 設定旗標決定使用哪個 parser（預設 deterministic；明確開啟才用 Ollama）。

## Consequences

### Positive

- 自然語言覆蓋提升；資料留在本地（個資不出機器）。
- 沿用 port 介面，ConversationManager 與測試不變；可隨時 fallback。

### Negative

- 需本機跑 Ollama（額外執行環境與模型下載）。
- LLM 抽取需嚴格 schema 清洗，避免幻覺欄位。

### Neutral / Tradeoffs

- 本地推論延遲/資源 vs 雲端品質；先本地，雲端日後再議。

## Alternatives Considered


| Option           | Pros               | Cons                   | Reason not chosen  |
| ---------------- | ------------------ | ---------------------- | ------------------ |
| 雲端 LLM API     | 品質高、免本機資源 | 個資外送、成本、需金鑰 | 個資敏感，先本地   |
| 純 deterministic | 簡單、可測         | 口語/同義覆蓋不足      | 作為 fallback 保留 |
| 本地 Ollama      | 個資不外送、可離線 | 需本機資源             | 採用方向           |

## Security Review

- Trust boundary impact: 新增對本地 Ollama 的 HTTP 呼叫（egress 限本機）。
- Sensitive data impact: 使用者敘述送本地模型、不出機器；輸出經白名單清洗。
- Permission impact: endpoint/model 走設定，不寫死；無新增雲端金鑰。
- Failure mode: 不可用即 fallback deterministic，不阻斷。

## Resource Impact

- Memory/CPU: 本地模型推論成本（依模型大小）；對話為單次抽取。
- I/O: 單次 HTTP 呼叫本機。

## Rollback Plan

- 以設定旗標關閉 Ollama 即回 deterministic；移除 adapter 不影響其餘流程。
