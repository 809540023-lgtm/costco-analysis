# costco-analysis — 日本好市多代購直播商品分析

競業直播（Facebook「SkyBlue.fans」）的商品資訊整理資料集。
**定位：Competitor Live Commerce Dataset v0（未驗證候選資料）** — 供選品研究與後續比對，不可直接作為 gold labels、成本資料或自動發布文案。

## 來源

| 項目 | 值 |
|------|-----|
| 影片 | Facebook 直播 ID `1993293861646570`（SkyBlue.fans） |
| 長度 | 4 小時 31 分（16,260 秒） |
| 轉錄 | faster-whisper `small`（CPU int8，zh），271 分鐘 → 12,838 行 |
| 直播日期 | 2026-09-06（影片下載日，未獨立核實原發布日） |
| 整理日期 | 2026-09-06～07 |

> 🗑️ **直播畫面截圖已刪除**（2026-09-07 依用戶要求：截圖含直播主肖像，不宜公開保存）。
> 現行商品圖為 `official-images/`（48/49 來自品牌官網／Costco Japan 官網，來源逐筆記錄於 `download_manifest.json`；#44 薯條造型餅乾未找到官方圖）。
> 如需重建直播截圖，用 `extract_frames.py` 從本地影片重抓即可。

## 重現流程

```bash
# 1. 下載影片（約 1GB，不入庫）
yt-dlp --no-playlist -f "best[ext=mp4][height<=720]/best" -o skyblue_costco.mp4 "<FB影片網址>"

# 2. 抽音訊 + 轉錄（沿用 video-analysis/transcribe.py，約 2.5 小時）
ffmpeg -y -i skyblue_costco.mp4 -vn -b:a 64k skyblue_costco_audio.mp3
../video-analysis/venv/bin/python ../video-analysis/transcribe.py \
  skyblue_costco_audio.mp3 transcript_full.txt full small

# 3. 切 20 分鐘分段（chunks/）
python3 split_chunks.py   # 或見 repo 歷史，規則：[MM:SS] // 1200

# 4. 逐段 LLM 萃取 → products_part1~4.md（人工審核後）
# 5. 合併（跨段重複商品以 merge_map.json 記錄）
python3 merge_parts.py --data-dir . --out 商品清單.md

# 6. 商品截圖：每段 3 幀候選（段內 30%/55%/80%）+ manifest.json
python3 extract_frames.py --md 商品清單.md --video skyblue_costco.mp4 \
  --out images --video-id "FB_1993293861646570"
```

## 資料品質狀態（重要）

- **幣別未確認（currency=unknown）**：售價是直播間代購報價（直播價／商城價兩種角色）；條目中出現的「日圓／圓」照抄逐字稿，未經獨立確認，**不表示日本採購成本**。
- **主播宣稱未驗證**：「台灣買不到」「No.1」「零負評」「孕婦兒童適用」等皆為 host 宣稱（verification=unverified），不可生成商城承諾。
- **49 段 ≠ 49 SKU**：A 編號是直播編號非 Costco item number；同款不同包裝（紙盒/鐵盒、6/12 袋）是 variant。品牌音譯（如「疑為 AWATAMA」）保留原文待查證。
- **截圖未驗證**：`images/` 每段 3 幀候選（`_p30/_p55/_p80`），manifest.json 含 `verified: false`；段起點常還在講上一個商品，故以段內中後段為主，仍需人工挑選正確幀。
- **時間範圍是「介紹時段」**：同一商品可能斷續出現；龜田米果等長時段中間穿插其他商品，勿整段視為單品曝光。

## 檔案

```
商品清單.md          主檔：49 個商品段（時間/特色/好處/售價/定位/差異性）
products.jsonl       ⭐ 結構化資料集 v0.1（schema 見 SCHEMA.md，validator: validate_dataset.py）
products_part1~4.md  分區原始檔（含備註）
transcript_full.txt  完整逐字稿（[MM:SS] 每行）
chunks/              14 個 20 分鐘分段
images/              （已刪除：直播截圖，extract_frames.py 可隨時從本地影片重建）
official-images/     ⭐ 48 張官方商品圖 + download_manifest.json（含每張來源網頁）
finalize_images.py   官方圖整合＋舊截圖刪除流程
merge_map.json       跨段合併記錄
merge_parts.py       合併腳本（CLI）
build_dataset.py     markdown → JSONL 轉換器（重跑即重建 products.jsonl）
extract_frames.py    截圖腳本（CLI，多幀 + manifest）
.github/workflows/validate.yml  CI：重建＋驗證 JSONL
```

## 已知未做（Roadmap）

- ~~P1：版本化 JSONL schema~~ ✅ `products.jsonl` v0.1（build_dataset.py / validate_dataset.py / SCHEMA.md / CI）
- P1：小型人工 gold set（商品/variant 配對率、幣別正確率、圖片錯配率）— 需人工核對 147 幀候選
- P1：真實留言資料（本場次僅語音逐字稿，主播代讀留言需標 indirect）
- P2：冪等寫入 `jp-costco-shop` 的 private staging（禁止直接 published）
- 影片/音訊檔不入庫（GitHub 100MB 上限），僅存本地