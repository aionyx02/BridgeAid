# BridgeAid — 主動式公共服務導航系統

> Proactive Public Service Navigator · 2026 總統盃黑客松國際松參賽作品
> 主題：Digital Inclusion in the AI Era（數位共好：打造 AI 新未來）

讓民眾用 **LINE / Web**（語音為延伸）描述生活困境，系統由 **AI 解析意圖**、追問缺漏，再交由**可驗證的規則引擎**判斷可能符合的公共服務，並產生**文件清單、流程提醒與來源追溯**。

核心轉變：從「人找服務」改為「**服務找人**」。AI 只降低入口門檻；資格判斷由規則引擎、版本化資料與官方來源負責。

## 為什麼

許多人不是沒有資格、不是不需要公共服務，而是被資訊分散、語言難度、網站入口、文件規定與期限追蹤排除在外（隱形的數位落差）。BridgeAid 透過既有生活入口降低門檻，把公共服務變成可被理解、可被追蹤、可被提醒的行動流程。

## MVP 範圍

- **主場景**：急難救助 + 住宅/生活補助 + 邊緣戶提醒
- **地理範圍**：先 1–2 縣市 + 中央服務
- **資料**：人工整理 5–10 筆高價值服務規則（附官方來源、版本、最後檢查日期）
- **入口**：LINE Bot + Web demo
- **不做**：全臺所有服務、AI 直接承諾資格、獨立 App、正式電話專線、無人工審核的全自動爬蟲

## 技術架構

```text
[LINE / Web / Voice]
   -> Conversation Manager（session 狀態、欄位追問）
   -> LLM Intent Parser（情境理解、欄位抽取、補問）
   -> Rule Engine（資格判斷、衝突檢查、文件條件）
   -> PostgreSQL + JSONB Rules + Source Documents
   -> Recommendation / Checklist / Reminder / Source Trace
```

| 層級 | 技術 |
|---|---|
| 前端 / Demo | Next.js |
| 後端 API + 規則引擎 | FastAPI（Python 3.14） |
| 資料庫 | PostgreSQL + JSONB |
| 入口 / 提醒 | LINE Messaging API |
| AI 層 | LLM API（意圖、欄位、白話/多語轉寫） |
| 排程 | Redis + Celery / RQ |
| 部署 | Docker Compose（黑客松）→ Render / Fly.io / GCP（決選） |

採「**文件檢索輔助 + 規則引擎決策**」，而非純 LLM RAG（避免漏條件、誤判與幻覺）。詳見 `docs/architecture.md` 與 `docs/adr/0002-bridgeaid-initial-architecture-and-ai-boundary.md`。

## 專案文件（Context Engineering）

本專案採 retrieval-first 文件治理系統。AI 與貢獻者啟動順序：

1. `CLAUDE.md` — session 啟動入口
2. `docs/index.md` — 文件路由表
3. `docs/memory/current.md` — 目前策略、約束、下一步
4. `docs/tasks/active.md` — 目前任務佇列
5. 依任務意圖讀最小必要文件（如 `docs/architecture.md`、`docs/data.md`、`docs/security.md`）

| 文件 | 內容 |
|---|---|
| `docs/project.md` | 產品、目標、非目標、技術棧、平台、工程優先級 |
| `docs/data.md` | 資料表、規則 JSON 格式、來源/版本規則 |
| `docs/security.md` | AI 使用邊界、個資與同意、回覆安全格式 |
| `docs/architecture.md` | 系統架構與後端切分 |
| `docs/testing.md` | 驗證命令與規則引擎測試重點 |
| `docs/adr/` | 架構/安全/資料契約等重大決策（AI 只提 proposed，由人類接受） |
| `docs/CLAUDE.md` | AI 治理與 ADR 規則 |

## 開發指令

文件 / context 治理（Node 20+）：

```bash
npm install
npm run docs:refresh   # 重建索引 + guard 檢查
npm run docs:ready     # 嚴格驗收（lint + secret scan + test + refresh + placeholder）
npm run team:status    # 確認本機 identity
```

應用層（Python 3.14，uv 管理）：

```bash
uv sync                 # 安裝依賴並以 editable 方式安裝 app 套件
uv run ruff check .
uv run pytest
uv run uvicorn app.main:app --reload   # 本地後端常駐
```

啟動後：`GET /healthz`、`POST /recommend`、`POST /line/webhook`。無 DB / 無憑證時仍可啟動（`/recommend` 可用）。

### 憑證設定（OS keychain）

LINE / DB 憑證存入 OS keychain（Windows Credential Manager），不進版控。互動輸入、值不經命令列參數：

```bash
uv run keyring set bridgeaid LINE_CHANNEL_ID            # console 基本憑證
uv run keyring set bridgeaid LINE_CHANNEL_SECRET        # 驗 webhook 簽章
uv run keyring set bridgeaid LINE_CHANNEL_ACCESS_TOKEN  # 另行核發，reply/push 用
uv run keyring set bridgeaid DATABASE_URL               # 之後架好資料庫再設
```

CI/容器可改用同名環境變數（或 `BRIDGEAID_` 前綴）作為 fallback。

### 資料庫（伺服器位置之後決定）

```bash
psql "$DATABASE_URL" -f db/schema.sql   # 建立 schema
uv run python -m app.importer           # 匯入 data/services/*.json
```

## 工程原則（規劃優先順序）

1. 先降低資安與個資風險
2. 再改善記憶體與 CPU 成本
3. 維持解耦與可替換邊界
4. 最後才比較交付速度與便利

詳見 `docs/engineering-principles.md`。

## 狀態

專案啟動中：context engineering 文件治理已就緒並通過 `docs:ready`；應用程式碼尚未開始。當前任務見 `docs/tasks/active.md`。
