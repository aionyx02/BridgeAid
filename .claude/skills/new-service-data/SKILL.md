---
name: new-service-data
description: 從官方來源生成一筆 BridgeAid 服務規則資料（service rule JSON + 必要的參照資料集），通過 schema 與防護測試後放入 data/。適用於新增公共服務、更新年度門檻、或把政府網頁轉成可判斷的規則。
argument-hint: <服務名稱或官方網址，例：桃園市租金補貼 或 https://...gov.tw/...>
---

# 生成 BridgeAid 服務規則資料

你要把「$ARGUMENTS」變成一筆 schema 合格、來源可追溯的服務規則，讓規則引擎能判斷資格。
**核心原則（ADR-0002）：AI 只負責把官方資料整理成結構化規則；資格判斷永遠由規則引擎執行，所以規則內容必須逐條對得上官方文字。**

## 第 1 步：讀懂資料契約

依序讀（不要跳過）：

1. `docs/data.md` — 資料契約總覽、canonical profile 欄位
2. `data/schemas/service-rule.schema.json` — 規則格式
3. `data/services/rent_subsidy_central.json` — 最完整的範本（含 ref 條件與 application_process）

## 第 2 步：查證官方來源

- 用 WebSearch / WebFetch 找 **.gov.tw 官方頁面**（法規、公告、申辦頁）。非官方彙整（部落格、新聞）只能當線索，不可當 source。
- 逐條記下：資格要件、所需文件、申請流程、期限、承辦單位、官方申請入口 URL。
- 打不開或內容對不上的 URL 一律不用。`source.last_checked_at` 填今天。

## 第 3 步：產生規則 JSON（`data/services/<snake_case_id>.json`）

**只能用這些 canonical profile 欄位**（值必須是下列 token，不可自創）：

| 欄位 | 值 |
|---|---|
| `residence_city` | `Taipei` / `Kaohsiung`（新縣市見下方「新增欄位值」） |
| `event_type` | `unemployment` / `illness` / `fire` / `major_accident` / `death_in_family` |
| `income_status` | `low_income` / `mid_low_income` / `near_threshold` / `general` |
| `has_lease` `employment_insured` `involuntary_separation` `caregiver` `care_need` | boolean |
| `age` | 整數（歲） |
| `monthly_income` | 整數（元/月） |

規則要點：

- `status` 一律填 `"needs_review"` — **AI 生成的規則必須經人工政策審核後才能改 active**。
- `eligibility_rules` 用 `all` / `any` 巢狀 + leaf `{field, operator, value}`；operator 只能用 schema 列的白名單。
- **年度衍生門檻嚴禁硬編碼**（如「最低生活費 × 3」）：改用
  `{ "field": ..., "operator": "lte", "ref": { "dataset": "<id>", "multiplier": N, "by": "residence_city" } }`
  並把官方數字放進 `data/reference/<id>.json`（照 `reference-dataset.schema.json`：各 token 值 + 保守 `default` + `sources` + `period` 效期）。硬編碼會被 `tests/test_references.py` 擋下。
- 法規明文的穩定數字（如「18 歲以上」）可以直接寫 value。
- `application_process`：3–5 步（準備文件 → 申請 → 審查 → 核定），申請步驟附官方入口 `url` + `url_title`；有截止日就填 `deadline`（人話）+ `deadline_at`（YYYY-MM-DD，會用來排提醒）。
- `required_documents`：無法建模的查核項（財產、戶籍調查等）寫成文件說明，註明「由受理機關查調」。
- `conflicts`：檢查與既有 6 筆服務是否互斥/擇一（例：租屋類 vs 社會住宅）。
- 規則檔一律 LF 換行、UTF-8。

## 第 4 步：驗證（全部要綠）

```bash
cd backend
uv run pytest ../tests -q          # schema、參照資料防護、demo 回歸全套
```

常見失敗：schema 驗證錯（對照錯誤訊息修欄位）、`test_no_hardcoded_reference_derived_thresholds`（你硬編碼了衍生門檻）、`test_reference_datasets_not_expired`（參照資料效期過期，要重新查官方公告）。

（選用）Docker Postgres 在跑的話：`uv run python -m app.importer` 重新匯入；重建乾淨資料用 `docker compose down -v` 再 up。

## 第 5 步：需要新欄位或新縣市時（先停下來）

需要新 profile 欄位（或 `residence_city` 新 token）時**不要只改規則檔**，要同步：
`backend/app/conversation/questions.py`（追問）、`intent.py`（關鍵字）、`manager.py` 的 `FIELD_LABELS`（我的資料）、`docs/data.md`。欄位屬公開契約變更 → 依 `docs/CLAUDE.md` §7 開 ADR（proposed），交 maintainer 決定。

## 第 6 步：收尾

1. 用 3 句話向使用者摘要：服務名稱、關鍵資格要件、來源與待人工確認的點。
2. 提醒：規則現在是 `needs_review`，前端會顯示「資料待人工確認」；請 maintainer 對照官方來源審核後改 `active` 並升 `version`。
3. 依 `docs/CLAUDE.md` §5 更新文件（session log 記來源查證過程），commit 前跑 `npm run docs:refresh`。
