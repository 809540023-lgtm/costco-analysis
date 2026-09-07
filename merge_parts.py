import argparse
import json
import os
import re

# Boundary merges: title-substring of the DUPLICATE section -> replacement text.
# Keep in one auditable map instead of scattered string surgery.
MERGE_MAP = [
    {
        'file': 'products_part2.md',
        'remove_marker': '### 奇奇與蒂蒂（Chip',
        'remove_until': '### 哈利波特聯名萬聖節造型軟糖',
        'reason': 'continuation of Part 1 chip & dale cookie',
    },
    {
        'file': 'products_part3.md',
        'remove_marker': '### A33-1 角落縫隙除塵刷',
        'remove_until': '### 日本好市多限定 蒟蒻果凍',
        'reason': 'continuation of Part 2 dust brush',
    },
    {
        'file': 'products_part4.md',
        'remove_marker': '### 北海道紅豆・紅芋地瓜大福',
        'remove_until': '### 薯條造型餅乾',
        'reason': 'continuation of Part 3 kuze-fuku daifuku',
    },
]

REPLACEMENTS = [
    {'file': 'products_part1.md',
     'marker': '### 東京香蕉 × 奇奇蒂蒂（チップとデール）巧克力香蕉夾心餅乾',
     'until': '\n---\n',
     'text': """### 東京香蕉 × 奇奇蒂蒂（チップとデール）巧克力香蕉夾心餅乾（紙盒 8 入／鐵盒 12 入）
- **出現時間**：[75:58] - [83:21]
- **特色/內容物**：同款兩種包裝：紙盒 8 入、鐵盒 12 入（內容餅乾相同）；外層巧克力餅乾、內餡香蕉醬；外包裝與個別包裝都印奇奇蒂蒂圖案；鐵盒四面不同夏日海灘主題圖案、吃完可重複利用，每盒附紙袋；賞味期到 2026/10/24。
- **介紹的好處**：餅乾超脆（薄燒口感）、香蕉巧克力內餡不甜膩；鐵盒可收藏重複利用、圖案療癒可愛；期間限定數量有限。
- **售價**：紙盒 8 入 499 元（商城 590）；鐵盒 12 入 899 元（商城 989）。
- **販售定位**：期間限定（夏季聯名款）難買，疑似最後一批（官方已改推玩具總動員系列），約販售至 10 月底～11 月。
- **差異性**：台灣買不到的東京車站聯名伴手禮。
"""},
    {'file': 'products_part2.md',
     'marker': '### 高密度纖毛除塵清潔刷',
     'until': '\n---\n',
     'text': """### 高密度纖毛除塵清潔刷（附自潔集塵盒）（A33／A33-1）
- **出現時間**：[156:11] - [163:01]
- **特色/內容物**：高密度極細刷毛地板清潔刷＋特殊專利纖維刷頭（非毛巾材質），附可重複使用集塵盒（放入一壓，灰塵毛髮自動脫落集中）；海綿可拆、可翻面；刷頭髒了直接換。
- **介紹的好處**：日本家庭主婦救星、好市多清潔用品銷售前幾名；高彈性刷頭深入吸塵器/拖把到不了的角落、櫃下縫隙；毛髮灰塵一掃即上、不用水洗、可重複使用十幾二十次。
- **售價**：外面通路 790；本場商城 499／線上 469（二哥現場加碼「買一送一」）。
- **販售定位**：未提及
- **差異性**：外面賣 790，商城直接便宜近一半；網路評價幾乎零負評。
"""},
    {'file': 'products_part3.md',
     'marker': '### 久世福商店 大福麻糬',
     'until': '\n## 備註',
     'text': """### 久世福商店 大福麻糬（北海道紅豆／鹿兒島紅芋，48 顆）（A45）
- **出現時間**：[233:50] - [240:25]
- **特色/內容物**：一箱 6 袋、每袋 8 顆共 48 顆獨立包裝；兩口味：北海道產紅豆、鹿兒島紅芋（紅はるか，最新口味）；職人手工調製、Q 彈糯米外皮一口大小。
- **介紹的好處**：Q 彈不黏牙、不會太甜、紅豆香濃；獨立包裝不怕回潮；配抹茶、伯爵奶茶很對味；日本經典伴手禮、送禮方便。
- **售價**：商城 799／線上 699；加 2 盒以上每盒 650（約一袋 108）。
- **販售定位**：未提及
- **差異性**：日本外面一袋約 290-390，此價划算；台灣蛋黃酥建議買台灣的即可。
"""},
]

HEADER = """# 🛒 日本好市多直播 商品清單

> **來源影片**：Facebook「SkyBlue.fans」日本好市多代購直播（影片 ID 1993293861646570，全長 4 小時 31 分）
> **逐字稿**：faster-whisper 轉錄 271 分鐘（12,838 行），商品名已依上下文修正錯字並以網路查證品牌
> **總計**：**49 個商品段**（≠49 個確認 SKU；同款不同包裝為 variant，A 編號是直播編號非 Costco item number）
> **商品截圖**：`images/` 資料夾（每段 3 幀候選＋manifest.json，未人工驗證）
> 💰 **售價角色**：報價分「直播價（線上價）」與「商城價」兩種，皆為直播間代購售價；部分條目照抄逐字稿寫「日圓／圓」，**幣別未經獨立確認（currency=unknown）**，日本採購成本需另取官方證據
> 🗣️ **宣稱標記**：「台灣買不到」「銷售 No.1」「零負評」「孕婦兒童適用」等皆為**主播宣稱**（claim_author=host，verification=unverified），未經獨立查證，不可直接作為商城文案

---
"""


def cut(text, start_marker, end_marker):
    i = text.index(start_marker)
    j = text.index(end_marker, i + len(start_marker))
    return text[:i], text[i:j], text[j:]


def main():
    ap = argparse.ArgumentParser(description='Merge per-part product lists into 商品清單.md')
    ap.add_argument('--data-dir', required=True)
    ap.add_argument('--out', required=True, help='output markdown path')
    args = ap.parse_args()

    parts = {}
    for n in range(1, 5):
        fn = os.path.join(args.data_dir, f'products_part{n}.md')
        t = open(fn, encoding='utf-8').read().split('\n', 1)[1]  # drop H1
        parts[f'products_part{n}.md'] = t

    merge_log = []
    for rule in MERGE_MAP:
        pre, sec, post = cut(parts[rule['file']], rule['remove_marker'], rule['remove_until'])
        parts[rule['file']] = pre + post
        merge_log.append({'removed': rule['remove_marker'], 'reason': rule['reason']})
    for rule in REPLACEMENTS:
        pre, sec, post = cut(parts[rule['file']], rule['marker'], rule['until'])
        parts[rule['file']] = pre + rule['text'] + post
        merge_log.append({'replaced': rule['marker'], 'reason': 'cross-part merge with continuation'})

    order = ['products_part1.md', 'products_part2.md', 'products_part3.md', 'products_part4.md']
    full = HEADER + '\n\n---\n\n'.join(parts[f].rstrip() for f in order) + '\n'
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(full)
    with open(os.path.join(args.data_dir, 'merge_map.json'), 'w', encoding='utf-8') as f:
        json.dump(merge_log, f, ensure_ascii=False, indent=1)
    print(f'MERGED -> {args.out}, sections: {full.count(chr(10) + "### ")}, merges: {len(merge_log)}')


if __name__ == '__main__':
    main()