---
type: adr
status: accepted
priority: p1
updated: 2026-06-25
context_policy: on_demand
owner: project
---
# ADR-0002: BridgeAid initial architecture and AI boundary

## Status

accepted

（依治理規則 docs/CLAUDE.md §3，AI 僅能建立 proposed；本 ADR 已由 maintainer 於 2026-06-25 明確確認接受，可據此擴大實作。）

## Context

BridgeAid 要在黑客松時間內，讓使用者用自然語言描述生活情境並取得可信、可解釋的公共服務推薦。核心限制：

- 公共服務涉及交錯條件、衝突與期限；錯誤承諾資格有法律與信任風險。
- 涉及年齡、收入、健康、家庭狀況等個資。
- 需在 Demo 時完整跑通一個真實情境，並可追溯來源。

## Decision

採以下初始架構與 AI 邊界：

1. 技術棧：Next.js（前端/Demo）+ FastAPI（後端 API，Python 3.14）+ PostgreSQL/JSONB（版本化規則）+ LINE Messaging API（入口/提醒）+ LLM API（意圖/欄位/白話）+ Redis+Celery/RQ（提醒排程）。
2. 職責分離：**AI = 入口/轉譯層**（意圖辨識、欄位抽取、追問、白話/多語）；**Rule Engine = 資格判斷決策者**（資格、衝突、文件條件）。
3. 不採純 LLM RAG 做資格判斷；RAG 僅第二階段輔助查來源/FAQ（pgvector/Qdrant，非 MVP）。
4. 資料以 JSON/YAML 中介格式 + JSON Schema 驗證 + 人工審核後匯入 PostgreSQL；每條規則附 source_url、last_checked_at、version。
5. 推薦結果必須綁定 DB 服務 ID；回覆採「可能符合，需承辦單位確認」格式。
6. 解耦：domain（rule_engine）不依賴 transport/storage/LLM 具體實作，經 port/adapter 介接。

## Consequences

### Positive

- 可解釋、可追溯、降低幻覺與誤判風險。
- domain 邏輯可測試、可替換 LLM/儲存/入口而不重寫核心。
- 符合競賽可行性與影響性敘事（主動式、邊緣戶發現、規則可解釋）。

### Negative

- 規則需人工整理與審核，初期資料成本較高。
- 兩套工具鏈（Node 文件治理 + Python 應用）需並存維護。

### Neutral / Tradeoffs

- MVP 限定 1–2 縣市 + 中央、5–10 筆服務，換取深度與完成度。
- 語音、RAG、後台完整功能延後到第二階段。

## Alternatives Considered


| Option                  | Pros             | Cons                              | Reason not chosen           |
| ----------------------- | ---------------- | --------------------------------- | --------------------------- |
| 純 LLM RAG 直接判斷資格 | 開發快、少寫規則 | 易漏條件/幻覺、不可解釋、法律風險 | 不符可信任設計              |
| 純搜尋式服務入口        | 實作簡單         | 需使用者先知道關鍵字、創新不足    | 不符「服務找人」敘事        |
| 只用 JSON 檔當資料庫    | 易版控           | 查詢/session/提醒/版本管理弱      | 改為 JSON 中介 + PostgreSQL |

## Security Review

- Trust boundary impact: 新增 LINE webhook、LLM API、DB 三個外部邊界，皆經 adapter 與輸入驗證。
- Sensitive data impact: 預設匿名試算、欄位最小化、opt-in 才保存；Demo 用假資料（見 docs/security.md）。
- Permission impact: secrets 以環境變數注入，不入版控。
- Failure mode: 資料不足回 insufficient_data，不臆測；來源過期標 needs_review。

## Resource Impact

- Memory impact: 規則/服務資料可快取，版本變更時失效。
- CPU impact: rule evaluation 為有界計算；避免不必要重複解析。
- I/O impact: 提醒/來源檢查以排程批次處理。

## Rollback Plan

- 規則版本化，錯誤版本可回退至前一 service_version。
- 部署以前一 Docker image / release tag 回滾。
