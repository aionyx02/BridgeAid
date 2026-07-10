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
| 部署 | Cloudflare Containers（黑客松，見下）／Docker Compose 本地 → Render / Fly.io / GCP（決選備案） |

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

啟動後：`GET /healthz`、`POST /recommend`、`POST /chat`、`/reminders`、`GET /services`、`POST /line/webhook`，Web demo 在 `http://127.0.0.1:8000/demo/`。無 DB / 無憑證時仍可啟動（degraded mode）。

### 憑證設定（OS keychain）

LINE / DB 憑證存入 OS keychain（Windows Credential Manager），不進版控。互動輸入、值不經命令列參數：

```bash
uv run keyring set bridgeaid LINE_CHANNEL_ID            # console 基本憑證
uv run keyring set bridgeaid LINE_CHANNEL_SECRET        # 驗 webhook 簽章
uv run keyring set bridgeaid LINE_CHANNEL_ACCESS_TOKEN  # 另行核發，reply/push 用
uv run keyring set bridgeaid DATABASE_URL               # 之後架好資料庫再設
```

CI/容器可改用同名環境變數（或 `BRIDGEAID_` 前綴）作為 fallback。

LINE 實連（tunnel URL 每次重開會變，重跑一次即可）：

```bash
ngrok http 8000                                            # 或 cloudflared tunnel
uv run python -m app.line.set_webhook https://<tunnel-host>  # 設 webhook + LINE 官方測試
```

### Cloudflare Containers 部署（黑客松）

把現有 uvicorn app 打包成容器，由一個薄 Worker 前置（`worker/index.ts` → `getContainer` 轉發原始請求，保留 LINE 簽章所需的 raw body）。設定在 `wrangler.jsonc`、映像在 `Dockerfile`。應用碼零改動，維持 degraded／記憶體模式（不接 DB、不接 Ollama）。

前置：Docker Desktop、Node、Cloudflare 付費方案（Containers 需 Workers Paid）。

```bash
npm install
npx wrangler login                              # 互動登入
# LINE 憑證存為 Worker secret（會注入容器環境，config 走 env fallback 讀取）
npx wrangler secret put LINE_CHANNEL_SECRET
npx wrangler secret put LINE_CHANNEL_ACCESS_TOKEN
npx wrangler secret put LINE_CHANNEL_ID
npm run cf:deploy                               # = wrangler deploy（容器佈建需數分鐘）
npx wrangler containers list                    # 確認 provisioned
```

部署後取得 `https://bridgeaid.<account>.workers.dev`，把 `.../line/webhook` 設為 LINE webhook（`uv run python -m app.line.set_webhook https://bridgeaid.<account>.workers.dev`）。

本地先驗證映像：

```bash
docker build --platform linux/amd64 -t bridgeaid:local .
docker run --rm -p 8099:8080 bridgeaid:local    # 開 http://localhost:8099/demo/
```

### 自架 + Cloudflare Tunnel（免費路徑）

不想付費也可自架：app 用 Docker 常駐、前面掛免費 Cloudflare Tunnel（`cloudflared`）取得穩定 HTTPS 網址。一鍵部署腳本 `scripts/deploy.sh` 同時支援本機建置與遠端 SSH 部署：

```bash
cp scripts/deploy.env.example scripts/deploy.env   # 填 SSH_HOST / PORT / PUBLIC_URL（gitignored）
scripts/deploy.sh                                  # ship build context → 遠端 build → 重建容器（帶 --env-file）
```

LINE 憑證放在部署主機的 `--env-file`（預設 `<repo>/.line.env`，`KEY=value` 每行一組，`chmod 600`），容器透過環境變數 fallback 讀取；`scripts/deploy.sh` 會自動帶入，缺檔則降級（不啟用 LINE）。Tunnel 設定為 `cloudflared` systemd 服務（具名 tunnel + DNS route → `http://localhost:<PORT>`）。

> 限制：單一容器 `sleepAfter` 後記憶體 session／已排程提醒會清空（無 DB 為本設計），提醒僅在容器喚醒時送達。要可靠持久化時走 Hyperdrive + 外部 Postgres 實作既有 `SessionStore`／`ReminderStore` seam（**非** D1；D1 是 SQLite，與現行 psycopg/Postgres 方言不相容，且其 REST API 僅適合管理用途）。

### LLM intent parser（本地 Ollama，ADR-0004）

預設使用 deterministic 關鍵字 parser，不需任何設定。要啟用本地 Ollama 抽取（個資不出機器；不可用時自動 fallback）：

```bash
# 先安裝 Ollama 並拉模型：ollama pull qwen2.5:1.5b（實測優於 qwen3:4b 非思考模式）
$env:BRIDGEAID_INTENT_PARSER = "ollama"         # 或 keyring set bridgeaid INTENT_PARSER
$env:BRIDGEAID_OLLAMA_MODEL  = "qwen2.5:1.5b"   # 選填；預設 qwen2.5:1.5b
uv run uvicorn app.main:app --reload
```

### 本機資料庫（Docker）

```bash
docker compose up -d                    # 首次啟動自動套用 db/schema.sql
uv run keyring set bridgeaid DATABASE_URL
#   值：postgresql://bridgeaid:bridgeaid-local-dev@127.0.0.1:5432/bridgeaid
uv run python -m app.importer           # 匯入 data/services/*.json
```

Postgres 只綁 `127.0.0.1`；密碼可用 `BRIDGEAID_DB_PASSWORD` 覆寫。API 無 DB 也能跑（degraded mode）。

## 工程原則（規劃優先順序）

1. 先降低資安與個資風險
2. 再改善記憶體與 CPU 成本
3. 維持解耦與可替換邊界
4. 最後才比較交付速度與便利

詳見 `docs/engineering-principles.md`。

## 狀態

MVP 核心可跑：規則引擎、對話（/chat + LINE webhook）、推薦彙整、opt-in 提醒（含到期送達）、來源追溯、Web demo（`/demo/`）；session 先 in-memory，DB 可用 Docker 落地。當前任務見 `docs/tasks/active.md`。
