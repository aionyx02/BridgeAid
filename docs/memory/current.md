---
type: working_memory
status: active
priority: p0
updated: 2026-06-25
context_policy: always_retrievable
owner: project
---

# Current Project Memory

## Current Strategy

- 收斂題目為「主動式公共服務導航」：事件/情境驅動，而非搜尋式服務。
- MVP 主場景：急難救助 + 住宅/生活補助 + 邊緣戶提醒；先 1–2 縣市 + 中央，人工整理 5–10 筆服務規則。
- AI 只做入口/轉譯（意圖、欄位、追問、白話）；rule engine 做資格判斷、衝突檢查、文件條件。
- 保持 docs retrieval-first：啟動狀態維持精簡，詳細計畫放 on-demand task 檔。

## Current Focus

- Active priority: 完成 context engineering 初始化並通過 docs:ready；準備進入 Week 1（題目收斂、Persona、服務清單）。
- Current phase: 專案啟動 / 文件治理就緒，尚無應用程式碼。
- Current owner / handoff state: shawn（maintainer）；團隊其他成員尚未登錄。

## Important Constraints

- AI 不得直接承諾資格；回覆用「可能符合，需承辦單位確認」格式。
- 個資最小化：預設匿名試算，僅 opt-in 才建立提醒/保存紀錄；Demo 用假資料。
- 每條服務規則須附 source_url、last_checked_at、version；過期標記 needs_review。
- 不重複歷史敘事於 current memory、active tasks、completed history。

## Next Step

- 整理 5–10 筆 MVP 服務候選與官方來源，並設計 JSON rule schema（見 TASK.002）。

## Last Validation Snapshot

- Last docs refresh: 2026-06-25
- Last test command: npm run docs:ready
- Known failing checks: none
