import re

d = '/Users/linemily/costco-analysis/'

merged1 = """### 東京香蕉 × 奇奇蒂蒂（チップとデール）巧克力香蕉夾心餅乾（紙盒 8 入／鐵盒 12 入）
- **出現時間**：[75:58] - [83:21]
- **特色/內容物**：同款兩種包裝：紙盒 8 入、鐵盒 12 入（內容餅乾相同）；外層巧克力餅乾、內餡香蕉醬；外包裝與個別包裝都印奇奇蒂蒂圖案；鐵盒四面不同夏日海灘主題圖案、吃完可重複利用，每盒附紙袋；賞味期到 2026/10/24。
- **介紹的好處**：餅乾超脆（薄燒口感）、香蕉巧克力內餡不甜膩；鐵盒可收藏重複利用、圖案療癒可愛；期間限定數量有限。
- **售價**：紙盒 8 入 499 元（商城 590）；鐵盒 12 入 899 元（商城 989）。
- **販售定位**：期間限定（夏季聯名款）難買，疑似最後一批（官方已改推玩具總動員系列），約販售至 10 月底～11 月。
- **差異性**：台灣買不到的東京車站聯名伴手禮。
"""

merged2 = """### 高密度纖毛除塵清潔刷（附自潔集塵盒）（A33／A33-1）
- **出現時間**：[156:11] - [163:01]
- **特色/內容物**：高密度極細刷毛地板清潔刷＋特殊專利纖維刷頭（非毛巾材質），附可重複使用集塵盒（放入一壓，灰塵毛髮自動脫落集中）；海綿可拆、可翻面；刷頭髒了直接換。
- **介紹的好處**：日本家庭主婦救星、好市多清潔用品銷售前幾名；高彈性刷頭深入吸塵器/拖把到不了的角落、櫃下縫隙；毛髮灰塵一掃即上、不用水洗、可重複使用十幾二十次。
- **售價**：外面通路 790；本場商城 499／線上 469（二哥現場加碼「買一送一」）。
- **販售定位**：未提及
- **差異性**：外面賣 790，商城直接便宜近一半；網路評價幾乎零負評。
"""

merged3 = """### 久世福商店 大福麻糬（北海道紅豆／鹿兒島紅芋，48 顆）（A45）
- **出現時間**：[233:50] - [240:25]
- **特色/內容物**：一箱 6 袋、每袋 8 顆共 48 顆獨立包裝；兩口味：北海道產紅豆、鹿兒島紅芋（紅はるか，最新口味）；職人手工調製、Q 彈糯米外皮一口大小。
- **介紹的好處**：Q 彈不黏牙、不會太甜、紅豆香濃；獨立包裝不怕回潮；配抹茶、伯爵奶茶很對味；日本經典伴手禮、送禮方便。
- **售價**：商城 799／線上 699；加 2 盒以上每盒 650（約一袋 108）。
- **販售定位**：未提及
- **差異性**：日本外面一袋約 290-390，此價划算；台灣蛋黃酥建議買台灣的即可。
"""

def load(part):
    t = open(d + part, encoding='utf-8').read()
    return t.split('\n', 1)[1]  # drop H1 line

p1, p2, p3, p4 = load('products_part1.md'), load('products_part2.md'), load('products_part3.md'), load('products_part4.md')

def cut(text, start_marker, end_marker):
    i = text.index(start_marker)
    j = text.index(end_marker, i + len(start_marker))
    return text[:i], text[i:j], text[j:]

# 1) replace P1's chip&dale section with merged1
pre, sec, post = cut(p1, '### 東京香蕉 × 奇奇蒂蒂（チップとデール）巧克力香蕉夾心餅乾', '\n---\n')
p1 = pre + merged1 + post

# 2) drop P2's duplicate chip&dale section
pre, sec, post = cut(p2, '### 奇奇與蒂蒂（Chip', '### 哈利波特聯名萬聖節造型軟糖')
p2 = pre + post
# replace P2's dust brush with merged2
pre, sec, post = cut(p2, '### 高密度纖毛除塵清潔刷', '\n---\n')
p2 = pre + merged2 + post

# 3) drop P3's duplicate dust brush section
pre, sec, post = cut(p3, '### A33-1 角落縫隙除塵刷', '### 日本好市多限定 蒟蒻果凍')
p3 = pre + post
# replace P3's kuze-fuku daifuku with merged3
pre, sec, post = cut(p3, '### 久世福商店 大福麻糬', '\n## 備註')
p3 = pre + merged3 + post

# 4) drop P4's duplicate daifuku section
pre, sec, post = cut(p4, '### 北海道紅豆・紅芋地瓜大福', '### 薯條造型餅乾')
p4 = pre + post

header = """# 🛒 日本好市多直播 商品清單

> **來源影片**：Facebook「SkyBlue.fans」日本好市多代購直播（影片 ID 1993293861646570，全長 4 小時 31 分）
> **逐字稿**：faster-whisper 轉錄 271 分鐘（12,838 行），商品名已依上下文修正錯字並以網路查證品牌
> **總計**：**49 個商品**，每項含「出現時間／特色／好處／售價／販售定位／差異性」
> **商品截圖**：`images/` 資料夾（依出現時間自動擷取影片畫面）
> 💰 售價為直播主開賣報價（代購商城價／線上價），個別條目寫「圓」沿用原始記錄

---
"""

full = header + p1.rstrip() + '\n\n---\n\n' + p2.rstrip() + '\n\n---\n\n' + p3.rstrip() + '\n\n---\n\n' + p4.rstrip() + '\n'
open(d + '商品清單.md', 'w', encoding='utf-8').write(full)
n = full.count('\n### ')
print(f'MERGED, total sections: {n}')