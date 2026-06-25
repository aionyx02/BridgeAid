---
type: architecture_spec
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_only
owner: project
---

# Architecture

## System Overview

BridgeAid 採多入口、解耦的事件驅動架構。AI 只負責入口與轉譯；資格判斷由規則引擎決策，並以版本化資料與官方來源支撐。核心立場：「文件檢索輔助 + 規則引擎決策」，而非純 LLM RAG。

```text
[LINE / Web / Voice]
        -> Conversation Manager (session 狀態、欄位追問)
        -> LLM Intent Parser (情境理解、欄位抽取、補問)
        -> Rule Engine (資格判斷、衝突檢查、文件條件)
        -> PostgreSQL + JSONB Rules + Source Documents
        -> Recommendation / Checklist / Reminder / Source Trace
```

## Layers

| Layer | Responsibility | Depends On |
|---|---|---|
| Interface | LINE webhook、Web chat、(語音延伸) | Application |
| Application | Conversation Manager、recommendation/checklist/reminder 服務編排 | Domain, Infrastructure ports |
| Domain | Rule Engine（資格/衝突/文件判斷）、推薦邏輯 | 無框架/儲存依賴 |
| Infrastructure | PostgreSQL repositories、LLM client、LINE client、job queue | — |

## Modules（後端切分）

| 模組 | 責任 | 備註 |
|---|---|---|
| `api/` | REST endpoints / LINE webhook | transport 層，薄 |
| `services/` | recommendation, checklist, reminder 編排 | application |
| `rule_engine/` | JSON rule evaluator | domain 核心，不依賴框架 |
| `llm/` | intent parser, 欄位抽取, 白話/多語轉寫 | 可替換的 adapter |
| `models/` | Pydantic schemas | 資料契約 |
| `repositories/` | PostgreSQL access | 持久化 port 實作 |
| `jobs/` | reminders, stale source checks | Redis + Celery/RQ |
| `data/services/*.json`, `data/schemas/*.json` | 版本化服務定義與 JSON schema | 人工審核後入庫 |

## Dependency Direction

- domain（rule_engine）不得依賴 transport、storage、LLM 具體實作。
- LLM、LINE、PostgreSQL 經 port/adapter 介接，可替換而不改 domain 邏輯。
- 副作用集中在邊界；核心判斷邏輯純函式、可測試。
- 推薦結果綁定 DB 服務 ID；LLM 不得自由生成服務或條件。

## 為何不用純 LLM RAG

公共服務涉及交錯條件、衝突與期限；若僅讓 LLM 摘要文件，易漏條件、誤判或幻覺。故採規則引擎決策，RAG 僅作為第二階段查來源/FAQ 輔助（pgvector/Qdrant，非 MVP）。

## Architecture Constraints

- 資安/個資邊界優先於交付便利。
- 記憶體與 CPU 改善以可量測、有界的方式進行。
- 歷史敘事放 session log；啟動與規劃文件保持精簡。
- generated 檔需可決定性重建，讓 CI 以 diff 偵測漂移。
- 重大架構/資料契約/安全邊界變更需 ADR（見 `docs/CLAUDE.md` §3、§7）。

## Open Architecture Questions

- 語音入口（STT/TTS）何時納入？目前列第二階段。
- 提醒系統 MVP 以簡化版（LINE/Email）為主，排程細節待 TASK.003 後確認。
