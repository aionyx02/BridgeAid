---
type: security_policy
status: active
priority: p1
updated: 2026-06-25
context_policy: retrieve_only
owner: project
---

# Security And Permission Boundary

## Security Principles

- 最小權限預設；資安/個資風險優先於交付速度與便利。
- 破壞性動作需明確確認。
- secrets（LINE channel token、LLM API key、DB 連線）不得進入 docs、prompt、fixtures、logs、workflow。
- log 不得含敏感個資與私有路徑。

## AI 使用邊界（可信任設計）

| 任務 | 是否交給 AI | 原則 |
|---|---|---|
| 意圖辨識 | 是 | 判斷急難/租屋/長照/失業/文件/進度 |
| 欄位抽取 | 是 | 轉成 city/age/event_type 等，需使用者確認 |
| 補問問題 | 是 | 依缺失欄位產生低門檻問題 |
| 資格判斷 | 否 | 由規則引擎決策，AI 不直接決定 |
| 文件清單 | 半自動 | 文件由規則提供，AI 只做白話說明 |
| 多語/白話轉寫 | 是 | 簡單中文、英、越南語、台語語氣 |
| 資料更新 | 否 | 人工審核或可信來源同步 |

## 回覆安全格式

- 避免：「你一定符合這項補助。」→ 用：「根據你提供的資訊，你『可能符合』以下服務，仍需承辦單位依正式資料確認。」
- 避免：「你不用準備其他文件。」→ 用：「以下是目前規則列出的常見文件，實際以承辦單位最新公告為準。」
- 高風險情境導向承辦單位，並加入免責提醒。

## 個資與同意（PII）

- 預設匿名試算，不要求身分證字號、完整地址或真實姓名。
- 僅 opt-in（建立提醒或保存紀錄）時才要求明確同意。`POST /reminders` 強制 `consent=true`，否則 403（ADR-0005）；提醒僅存 session_id/類型/時間/通道，不存姓名或完整敘述；取消需 session 擁有權。
- 敏感欄位最小化：年齡區間、居住縣市、事件類型，不存完整敘述。
- 提供刪除資料、取消提醒、重新同意機制。
- Demo 階段使用假資料與示範服務，不處理真實個案個資。

## 憑證與後端安全（TASK.003 / ADR-0003）

- LINE 與 DB 憑證來源：**OS keychain 為主**（`keyring`，服務名 `bridgeaid`，鍵 `LINE_CHANNEL_ID`、`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`、`DATABASE_URL`），環境變數為 fallback（CI/容器）。
- LINE 憑證對應：channel id + channel secret 為 console 基本憑證（secret 用於驗 webhook 簽章）；channel access token 另行核發，僅 reply/push API 需要。
- 設定方式（互動輸入，值不經 shell 參數、不入版控/日誌）：`uv run keyring set bridgeaid <key>`（例：`LINE_CHANNEL_SECRET`）。
- LINE webhook 先以 stdlib HMAC-SHA256 驗證 `X-Line-Signature` 才處理；未設定 secret 回 503，簽章錯誤回 401。
- Degraded mode：無 secret / 無 DB 時後端仍可啟動（`/recommend` 可用），不崩潰、不洩漏設定細節。
- 憑證只在記憶體使用，不寫入 repo、log、error message。

## Data Classification

| Data | Sensitivity | Handling |
|---|---|---|
| 服務/規則公開資料 | Low | 可記錄；附來源與版本 |
| 使用者情境/抽取欄位 | Medium/High | 最小化、匿名、限期保存 |
| Credentials / tokens | Critical | 永不入 docs/prompt/fixtures |
| 推薦/提醒紀錄 | Medium | opt-in 才保存，可刪除 |

## Automated Checks

- `npm run security:scan` 對 docs、bootstrap、workflow 做高信心 secret 掃描。
- `npm run docs:refresh` 含 link、schema、secret、ADR、task-marker guard。
- CI 在 `npm run docs:refresh` 後跑 `git diff --exit-code`，避免 generated policy 漂移。

## Approval-Gated Changes

- 憑證儲存/取得、網路 egress、專案邊界外的檔案寫入/刪除、權限擴張、telemetry、接受不可信輸入的 shell 執行。

## Review Checklist

1. 新增或擴大了哪個信任邊界？
2. 哪些使用者/系統輸入跨越該邊界？
3. 最小權限版本為何？
4. 如何安全失敗（fail safe）？
5. 需要哪些不洩漏 secret 的稽核紀錄？
