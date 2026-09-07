# products.jsonl Schema v0.1

每行一個 JSON 物件（共 49 筆，對應 `商品清單.md` 的 49 個商品段）。

## 欄位

| 欄位 | 說明 |
|------|------|
| `dataset_version` | 資料集版本（v0.1） |
| `source` | 來源：video_id、平台、帳號、逐字稿檔、抓取日期、萃取方法 |
| `segment.index` | 段落編號（1-49，對應 markdown 順序與 images/ 幀前綴） |
| `segment.start_sec / end_sec` | 介紹時段（秒）；**是「主播介紹時段」非精確商品曝光 span** |
| `segment.transcript_line_start / _end` | 對應 `transcript_full.txt` 的近似行號（可回溯原文） |
| `product.name_raw` | 原始標題（含音譯、待查證標記） |
| `product.match_status` | 一律 `unverified`（未對應官方 SKU） |
| `product.official_costco_item_number` | 一律 `null`（A 編號是直播編號，不放入此欄） |
| `variants` | 包裝 variant 候選（heuristic_v0：紙盒/鐵盒×N 入），未確認 |
| `price_observations[]` | 見下方價格模型 |
| `claims[]` | 主播宣稱：`claim_author: host`、`verification: unverified` |
| `content.*_raw` | 原始 markdown 欄位文字（features/benefits/positioning/differences） |
| `frames` | 對應 `images/manifest.json` 的幀組，`verified: false` |
| `flags[]` | 品質旗標，見下 |

## 價格模型 price_observations[]

| 欄位 | 說明 |
|------|------|
| `original_text` | 逐字稿整理原文（保留原樣） |
| `amount` | 數字（僅取 3-5 位數；重量等雜數不取） |
| `currency` | 一律 `unknown`（即使原文寫「日圓」也未獨立確認） |
| `currency_in_source` | 原文出現「日圓」時記 `jpy_text`，否則 null |
| `price_role` | `competitor_live`（直播/線上價）／`competitor_mall`（商城價）／`bulk_offer`（多件優惠）／`external_reference`（外面通路）／`not_mentioned`／`unknown_role` |
| `min_quantity` | 達價最低件數（「加 2 盒 650」→ 3） |
| `effective_ts` | 原文提及的報價時間點（如「於 79:43 提及」） |

**價格角色語義**：競業價（live/mall/bulk/external）是市場訊號，**不可替代日本 Costco 採購成本**。

## 旗標 flags[]

| 旗標 | 意義 |
|------|------|
| `currency_unknown` | 幣別未確認（全部記錄都有） |
| `price_missing` | 整段無可解析售價 |
| `long_span_interleaved_possible` | 時段 >5 分鐘，中間可能穿插其他商品（如龜田 A40 186:08–205:41），不可整段視為單品曝光 |
| `time_overlap_with_neighbor` | 與相鄰段時間重疊（直播交接期，屬正常但需知曉） |
| `list_order_differs_from_time_order` | 清單順序≠時間順序（#24/#25），按 `start_sec` 排序消費 |
| `name_unverified` | 標題含「疑為／音譯／ASR」，品牌待查證 |

## 消費規則

1. 按 `segment.start_sec` 排序重建時間軸
2. 任何欄位缺失→保留未知，**不得補 0 或推導**
3. 作為訓練/評估前需先建立人工 gold set；同場分段不可隨機切 train/eval