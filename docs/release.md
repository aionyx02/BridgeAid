---
type: release_policy
status: active
priority: p2
updated: 2026-06-25
context_policy: retrieve_when_planning
owner: project
---

# Release And Deployment

## Purpose

記錄發布、部署與回滾預期。環境特定 secrets 不放本檔。

## 部署策略

- **現階段（決定）：先本地**。PostgreSQL 跑在本機，`DATABASE_URL` 指向本地（如 `postgresql://localhost/bridgeaid`）；後端以 `uv run uvicorn app.main:app` 本地常駐。之後再搬到其他位置。
- 黑客松/決選階段：Docker Compose 一鍵起 Next.js + FastAPI + PostgreSQL + Redis；雲端（Render / Fly.io / GCP）日後再評估。
- secrets 走 OS keychain（fallback 環境變數），不進版控（見 `docs/security.md`）。

## Release Checklist

- [ ] 文件最新（docs:refresh 通過）。
- [ ] 測試/驗證命令通過（ruff、pytest、npm guard）。
- [ ] 設定變更已記錄。
- [ ] 需要時記錄遷移與回滾說明。
- [ ] 使用者可見變更已摘要。

## Demo 交付物

- Demo video（傳統搜尋 vs BridgeAid 對話前後差異）。
- GitHub 連結與部署網址。
- 可展示對話紀錄、規則命中與來源追溯。

## Validation Commands

```bash
npm run docs:refresh
ruff check .
pytest
```

## Rollback Notes

- 規則資料以版本化匯入；錯誤版本可回退到前一 service_version。
- 部署回滾以前一個 Docker image / release tag 為準。
