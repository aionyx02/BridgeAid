# Extracted Workflow From Reference Project

## 核心構件

這個模板把 context engineering 拆成幾個明確角色，避免所有規則都塞進單一 prompt。

| 構件 | 檔案 | 作用 |
|---|---|---|
| Bootstrap | `CLAUDE.md` | 定義 session 啟動順序與最小規則 |
| Governance | `docs/CLAUDE.md` | 定義文件路由、ADR 權限、同步規則 |
| Router | `docs/index.md` | 讓 AI 按任務意圖讀最小必要文件 |
| Engineering policy | `docs/engineering-principles.md` | 定義 Google-style coding、資安優先、效能與解耦原則 |
| Team registry | `docs/team/members.md` | 記錄 fake member ID，讓 task owner 和 session log 可追蹤 |
| Stable facts | `docs/project.md` | 放產品背景、目標、平台與工程優先級 |
| Current state | `docs/memory/current.md` | 放目前策略、約束、下一步 |
| Task state | `docs/tasks/active.md` | 放 active queue 與任務狀態 |
| Detailed task plan | `docs/tasks/*.md` | 放較大任務的 plan、acceptance criteria、validation |
| Decision records | `docs/adr/*.md` | 放架構、安全、資料契約、依賴等重大決策 |
| Historical log | `docs/memory/sessions/*.md` | 放 debug narrative、命令輸出、完成紀錄 |
| Guard scripts | `scripts/docs-*.mjs` | 驗證 frontmatter、連結、size、secret、ADR 與任務格式 |
| Generated summaries | `docs/state/*.json` / generated indexes | 提供輕量可檢索的摘要資訊 |

## 啟動流程

```text
CLAUDE.md
  -> team identity check
  -> docs/team/members.md
  -> docs/index.md
  -> docs/memory/current.md
  -> docs/tasks/active.md
  -> docs/engineering-principles.md (planning / implementation / refactor / architecture)
  -> task-specific docs
```

## 規劃優先順序

每次比較方案時，順序固定如下：

1. 先選資安風險較低的方案
2. 再選記憶體與 CPU 成本更合理的方案
3. 再看是否維持解耦與可替換邊界
4. 最後才比較交付速度與實作便利性

## 文件路由原則

- `current.md` 和 `active.md` 只放現在狀態，不放歷史敘事。
- session log 才放 debug narrative、指令輸出、root cause。
- durable rule 寫進 reference docs，不要重複貼進 bootstrap 文件。
- 需要重大決策時，用 `npm run docs:new-adr -- "Decision title"` 產生 `proposed` ADR，再等明確接受。

## 自動檢查原則

模板內建的 guard scripts 會檢查：

- frontmatter schema
- 文件大小上限
- 連結存在性
- secret / token / private key 洩漏
- ADR 命名與狀態規則
- task marker 與 narrative routing
- generated doc 是否可穩定重建

CI 應該執行：

```bash
npm run lint
npm run security:scan
npm test
npm run team:guard
npm run docs:refresh
git diff --exit-code
```

真實專案導入完成後，執行：

```bash
npm run docs:ready
```
