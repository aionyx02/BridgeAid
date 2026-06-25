---
type: ui_spec
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_when_planning
owner: project
---

# UI Architecture

## UI Goals

- 流程簡單可預期；以對話 + 按鈕降低打字負擔。
- 先用語意化 HTML 再加自訂 JavaScript。
- 元件可重用、可測試、最小狀態。
- 透明化：明確標示「可能符合 / 缺少資料 / 需承辦單位確認」與資料來源。

## Demo 畫面（對應企畫書 §6.3）

| 畫面 | 責任 | 備註 |
|---|---|---|
| 對話入口 | LINE/Web chat，輸入生活情境 | 主入口 |
| 欄位追問 | 以按鈕選項追問必要欄位 | 一次不超過 3 題 |
| 推薦清單 | 列出候選服務與狀態標籤 | 可能符合/缺資料/需確認 |
| 文件 checklist | 依情境產生，可勾選/匯出/分享 | 分享給家人或社工 |
| 來源透明化 | 顯示官方來源、更新日期、規則版本 | 可追溯 |
| 建立提醒 | opt-in，補件/期限/續辦提醒 | 可建立/列出/取消 |

## 對話回合模型（TASK.004）

`POST /chat`（`{session_id, message}`）每次回傳一個 `Reply`：

- `kind: "question"`：`text` 為追問問題，`options[]` 為按鈕標籤（降低打字負擔，一輪最多 3 題）。
- `kind: "result"`：`text` 為白話摘要（「可能符合…需承辦單位確認」），`results[]` 為可能服務（含 `status`、`documents`、`source`、`needs_review`）。

前端依 `kind` 切換「追問氣泡 + quick-reply 按鈕」或「推薦清單卡片」。LINE 端由 webhook 走同一流程，`options` 轉為 LINE quick reply。

## Component Boundary Rules

- 一個元件一個清楚責任。
- 資料抓取、驗證、渲染不混在一起（除非框架要求）。
- 共用元件放共用元件目錄；頁面專屬元件靠近頁面。

## State Rules

| State Type | Preferred Location |
|---|---|
| Local UI state | Component |
| Form / 對話追問狀態 | Form/conversation component |
| Server/cache state | Data layer |
| Global app state | 僅多個遠端元件都需要時 |

## UI Decision Triggers

變更 layout 系統、元件庫、styling 策略、路由、狀態管理、表單驗證或無障礙基線時建立 ADR。
無障礙與 design system 細節見 `docs/accessibility.md`、`docs/design-system.md`（MVP 階段最小化）。
