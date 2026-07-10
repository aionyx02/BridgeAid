---
type: project_overview
status: active
priority: p1
updated: 2026-06-25
context_policy: always_retrievable
owner: project
---

# Project Overview

## Product

BridgeAid（主動式公共服務導航系統 / Proactive Public Service Navigator）。
使用者用自然語言描述生活情境（如「我失業、房租繳不出來、爸爸住院」），系統由 AI 解析意圖、抽取欄位、追問缺漏，再交由可驗證的規則引擎判斷可能符合的公共服務，並產生文件清單、流程提醒與來源追溯。核心轉變：從「人找服務」改為「服務找人」。

2026 總統盃黑客松國際松參賽作品，主題「Digital Inclusion in the AI Era」。

## Goals

- 降低公共服務入口門檻：多入口（LINE / Web，語音為延伸）讓不熟政府網站者也能用。
- 判斷可解釋：每個推薦附命中規則、缺少資料與官方來源（source_url / last_checked_at / version）。
- 主動提醒：在期限、補件、續辦、即將符合條件時通知（opt-in）。
- Demo 可行：先做 5–10 個服務、1–2 縣市 + 中央，完整跑通一個真實情境。

## Non-Goals

- 不做全臺所有政府服務；MVP 限定 1–2 縣市 + 中央、5–10 筆人工整理規則。
- 不讓 AI 直接做資格承諾（「你一定符合」）；資格判斷由規則引擎負責。
- 不先做獨立 App（LINE/Web 觸及成本較低）。
- 不先做正式電話專線（語音僅模擬或第二階段）。
- 不做全自動爬蟲且無人工審核的資料管線。

## Stack

- 前端 / Demo：Next.js（landing、chat demo、後台）。
- 後端 API：FastAPI（Python 3.14），含自製 JSON rule engine。
- 資料庫：PostgreSQL + JSONB（規則版本化）。
- 入口：LINE Messaging API；Web chat。
- AI 層：LLM API（意圖辨識、欄位抽取、白話/多語轉寫）。
- 任務排程：Redis + Celery/RQ（提醒、來源檢查）。
- 檢索層：pgvector / Qdrant（第二階段，非 MVP）。
- 部署：Cloudflare Containers（黑客松，Worker 前置 + uvicorn 容器）／Docker Compose 本地 → Render/Fly.io/GCP（決選備案）。

## Platform Targets

- 終端使用者：LINE Bot + Web demo（語音為延伸亮點）。
- 開發：本機 AI 輔助工作流 + GitHub CI（Node 20+ 跑文件治理 guard）。

## Engineering Priorities

1. 先降低資安與個資風險。
2. 再改善記憶體與 CPU 成本。
3. 維持解耦與可替換邊界（domain 邏輯獨立於 transport/storage/UI）。
4. 最後才比較交付速度與實作便利。

## Current Strategy

- 透過 `CLAUDE.md` → `docs/index.md` → `docs/memory/current.md` → `docs/tasks/active.md` 做 retrieval-first 啟動。
- AI 只負責入口與轉譯；資格判斷、衝突檢查、文件條件由 rule engine + 版本化資料 + 官方來源支撐。
- 重大技術/資料/安全決策走 ADR，AI 只提 `proposed`，由人類接受。
