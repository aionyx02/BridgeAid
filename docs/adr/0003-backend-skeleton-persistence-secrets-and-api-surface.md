---
type: adr
status: accepted
priority: p1
updated: 2026-06-25
context_policy: on_demand
owner: project
---
# ADR-0003: Backend skeleton: persistence, secrets, and API surface

## Status

accepted

（已由 maintainer 於 2026-06-25 確認接受。可據此擴大：對真實資料庫執行 migration、將 schema 與 API 視為公開契約。）

## Context

TASK.003 要建立後端骨架：FastAPI + PostgreSQL，以及把 `data/services/*.json` 規則匯入 DB 的工具。新增限制：

- 使用者已申請 LINE bot 憑證；憑證**不可進版控/日誌**，且後端「本地常駐」執行時要能安全取得。
- 伺服器架設位置未定（之後決定），故骨架不可綁死特定雲端或要求即時連線到資料庫才能啟動。
- ADR-0002 已接受技術棧（FastAPI / PostgreSQL / LINE / 規則引擎決策）；本 ADR 只定 schema、憑證與 API 的**具體做法**。

## Decision

1. **Secrets / 憑證**：以 OS keychain 為主來源，透過 `keyring`（Windows→Credential Manager）讀取；服務名 `bridgeaid`，鍵：`LINE_CHANNEL_ID`、`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`、`DATABASE_URL`。LINE 對應：channel id + channel secret 為 console 基本憑證（secret 驗 webhook 簽章）；channel access token 另行核發，僅 reply/push 需要。提供環境變數 fallback（CI/容器用）。任何 secret 不寫入 repo、log 或錯誤訊息。設定方式：`uv run keyring set bridgeaid LINE_CHANNEL_SECRET`（互動輸入，不經 shell 參數）。
2. **LINE webhook 安全**：以 stdlib `hmac`/`hashlib` 自行驗證 `X-Line-Signature`（HMAC-SHA256 + channel secret），不引入 LINE SDK。未設定 secret 時 webhook 回 503，不處理。
3. **持久化**：PostgreSQL DDL 放 `db/schema.sql`（對應 docs/data.md 九張表）。DB 存取用 `psycopg`(v3)，以 Repository Protocol 解耦；domain/規則引擎不依賴 DB。匯入工具 = 純轉換 `rule_to_rows()`（可測）+ 薄寫入層。不採 ORM（避免過早抽象與大型依賴）。
4. **API 介面**（FastAPI）：`GET /healthz`；`POST /recommend`（用規則引擎 `evaluate_all`，**不需 DB 即可運作**）；`POST /line/webhook`（驗章後最小回應）。對外契約見 docs/data.md。
5. **啟動**：本地常駐用 `uv run uvicorn app.main:app`；DB 與雲端部署位置之後再定，骨架在無 DB/無 secret 時仍可啟動（degraded）。

## Consequences

### Positive

- 憑證集中於 OS keychain，降低外洩風險；無 secret 也能跑 demo recommend。
- DB 解耦（Protocol）、無 ORM，依賴小、可測、可替換。
- API 立即可用於規則引擎 demo，不被未定的伺服器位置阻塞。

### Negative

- keyring 在無桌面/CI 環境需改用 env fallback，需文件說明。
- 自行驗 LINE 簽章需正確實作（已用 stdlib + 測試覆蓋）。

### Neutral / Tradeoffs

- 不用 ORM/Alembic：schema 以 SQL 檔管理，migration 流程之後視需要再引入（屆時另開 ADR）。
- psycopg 連線僅在設定 `DATABASE_URL` 時啟用；單元測試以 fake repo 覆蓋匯入邏輯。

## Alternatives Considered


| Option                   | Pros       | Cons               | Reason not chosen               |
| ------------------------ | ---------- | ------------------ | ------------------------------- |
| 用 .env 檔存 LINE secret | 簡單       | 易誤入版控/日誌    | 改用 OS keychain + env fallback |
| SQLAlchemy ORM + Alembic | 功能完整   | 大型依賴、過早抽象 | 骨架階段用 psycopg + schema.sql |
| 引入 line-bot-sdk        | 省驗章程式 | 多一個依賴、黑箱   | stdlib hmac 驗章足夠且透明      |

## Security Review

- Trust boundary impact: 新增 LINE webhook（外部 POST）、DB 連線、keychain 讀取三個邊界。
- Sensitive data impact: 憑證只在記憶體使用，來源為 OS keychain；webhook 先驗簽章再處理；recommend 預設匿名、最小化欄位（見 docs/security.md）。
- Permission impact: secrets 不入版控；DATABASE_URL 亦走 keychain/env。
- Failure mode: 無 secret → webhook 503、recommend 仍可用；無 DB → 啟動為 degraded，不崩潰。

## Resource Impact

- Memory impact: 規則在啟動載入一次並快取；連線池之後再評估。
- CPU impact: 驗章為單次 HMAC；規則評估有界。
- I/O impact: 匯入為批次；webhook 為事件驅動。

## Rollback Plan

- 骨架皆為本地檔案與可選連線；移除 router 或停用 webhook 即可回退。
- schema.sql 變更以版本控制；尚未對正式資料執行 migration 前無資料風險。
