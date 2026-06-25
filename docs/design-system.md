---
type: design_system
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_when_planning
owner: project
---

# Design System

MVP 階段最小規範；正式視覺 token 待 Demo 打磨時補齊（見 `docs/ui.md`）。

## Visual Direction

- 信任、清楚、低門檻；以可讀性與無障礙優先，避免裝飾性複雜度。
- 一致的間距、字級與元件行為。
- 狀態語意色：可能符合 / 缺少資料 / 需承辦單位確認 用清楚對比與文字標籤（不只靠顏色）。

## Layout Tokens（暫定，待確認）

| Token | Value |
|---|---|
| Page max width | 待定（建議 720px 對話為主） |
| Section spacing | 待定 |
| Card radius | 待定 |
| Input height | 待定 |

## Typography（暫定）

| Use | Style |
|---|---|
| Page title | 待定 |
| Section title | 待定 |
| Body text | 待定，確保中文可讀字級 |
| Helper text | 待定 |

## Components

| Component | Rule |
|---|---|
| Button | 追問以按鈕選項為主，降低打字負擔 |
| Card | 一張卡片一個服務推薦，含狀態標籤與來源連結 |
| Modal | 僅用於來源細節與同意（opt-in）說明 |
| Form field | 最小化欄位；敏感欄位僅 opt-in 後出現 |
| Navigation | 對話為主，導覽簡單可預期 |

## Change Policy

Create an ADR before changing the global styling system, design token structure, or component library.
