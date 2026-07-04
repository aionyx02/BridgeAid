---
type: adr
status: proposed
priority: p1
updated: 2026-07-04
context_policy: on_demand
owner: project
---

# ADR-0008: Income amount extraction and question strategy

## Status

Proposed

## Context

實測回饋（2026-07-04）：使用者說「我年薪四十萬」，系統判資訊不足並轉介 1957。根因有二：

1. 收入**金額**無法解析——parser 只認低收/中低收等**核定身分**關鍵字；而租金補貼的所得要件（每人每月平均所得＜當地最低生活費 3 倍）本質是金額判斷，年薪 40 萬（月 33,333）明顯低於門檻，是可判斷的。
2. 提問策略以「全域最常被卡的欄位」排序，3 題預算花在縣市/事故上；全國性的租金補貼根本不需要這兩欄，它缺的租約/年齡永遠排不到。

限制：核定身分（低收入戶等）不可由金額推斷；規則檔為公開資料契約，變更需 ADR；門檻數字須有官方來源。

## Decision

1. **`monthly_income` profile 欄位**：deterministic parser 解析「年薪/月薪/月收入 + 金額」（阿拉伯數字、中文數字、3萬5 縮寫；年薪 ÷12）。必須有年/月前綴，裸金額（「40萬」）不猜；範圍檢查 1,000–10,000,000。**不開放 LLM 抽取**（與 income_status 同理由：數值誤抽風險高，deterministic pattern 已涵蓋）。
2. **租金補貼所得條件改為 `any`**：`income_status ∈ {低收,中低收,邊緣,一般}` **或** `monthly_income ≤ 當地最低生活費 × 3`。門檻**不硬編碼**：規則以 `ref: {dataset: "minimum_living_cost", multiplier: 3, by: "residence_city"}` 引用 `data/reference/minimum_living_cost.json`（各縣市值 + 全國最低保守 default，含官方來源與效期，schema 驗證）。評估時依縣市取值；縣市未知時比對所有候選門檻——全數同結果即判定，否則 blocking `residence_city`（自動追問縣市）。
   - **通用防護（不再發生硬編碼）**：(a) `reference-dataset.schema.json` 強制每份參照資料附 sources 與 valid_from/valid_to；(b) 測試守門——`monthly_income` 等年度衍生欄位的門檻條件必須用 `ref`，硬編碼 value 直接 fail；(c) 效期 tripwire 測試——參照資料過期（如 116 年公告後）測試即失敗，強迫重新查核。
3. **提問策略**：`_pick_next_field` 改為「先完成最接近可判斷的服務」，且**使用者訊息已命中條件的服務優先**（說了薪水就先補租補缺的租約/年齡，而不是先問只差一欄的長照）。欄位平手時取跨服務共用度最高者。`MAX_QUESTIONS` 3 → 5。
4. 新增 `monthly_income` 追問題（自由輸入，問句已固定「每月」單位，此時裸金額可解析）與 `我的資料`/`修改每月收入` 支援。

## Consequences

### Positive

- 「我年薪四十萬」兩題內（年齡、租約）即可判「可能符合租金補貼」。
- 保守門檻不會產生誤判高收入為符合的假陽性；輸出仍是「可能符合，需承辦確認」三態語意。
- 提問預算導向「完成一個服務」而非平均撒網，減少無效追問。

### Negative

- 參照資料仍需年度人工查核更新，但過期會被 tripwire 測試擋下，不會靜默沿用舊值。
- 個人薪資 ≠ 家庭每人平均所得（家戶人口/其他成員收入未建模）；以 possible 三態 + 承辦查調吸收誤差。

### Neutral / Tradeoffs

- 中文數字解析僅涵蓋萬/千/百/十常見寫法；罕見寫法落回追問，不影響正確性。

## Alternatives Considered

| Option | Pros | Cons | Reason not chosen |
|---|---|---|---|
| 金額→推斷 income_status | 不動規則檔 | 核定身分不可由金額推斷，語意錯誤 | 違反資料正確性 |
| 單一保守門檻寫死規則檔 | 最簡單 | 無來源/效期、年度更新靠人記得、各縣市不精確 | 初版如此，maintainer 退回：不可硬編碼 |
| LLM 抽取金額 | 涵蓋更多口語 | 數值幻覺風險、難驗證 | deterministic pattern 已足夠 |
| 只加大 MAX_QUESTIONS | 簡單 | 不解決提問順序錯置 | 與策略改良併行才有效 |

## Security Review

- Trust boundary impact: 無新增 egress；金額解析為純函式正則。
- Sensitive data impact: monthly_income 屬敏感欄位，僅存 session（in-memory）、可由「清除資料」移除；不進提醒、不進日誌。
- Permission impact: 無。
- Failure mode: 解析失敗/超範圍 → 欄位不設，退回追問；規則端 any 分支未知 → insufficient_data。

## Resource Impact

- Memory impact: profile 多一個 int，可忽略。
- CPU impact: 每則訊息一次正則 + O(len) 數字轉換，可忽略。
- I/O impact: 無。

## Rollback Plan

- 還原租補規則的所得條件為單一 income_status leaf、移除 parser 金額段與 monthly_income 追問題即回退；既有欄位與 API 不受影響。

## References

- 衛福部 115 年臺灣省最低生活費公告（15,515/月）: https://dep.mohw.gov.tw/dosaasw/cp-566-84031-103.html
- 臺北市 115 年度最低生活費 20,744/月: https://service.docms.gov.taipei/attachments/115-income-limit.pdf
- 高雄市政府公報 115 年度最低生活費 16,970/月: https://gaz.kcg.gov.tw/search/view/5f1d09e4-b244-4f61-84be-7feb2040e6ce
