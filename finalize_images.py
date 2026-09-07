import json
import glob
import os
import shutil
import subprocess
import sys

D = '/Users/linemily/costco-analysis/'
OIMG = D + 'official-images/'

parts = []
for n in range(1, 5):
    fn = OIMG + f'manifest_g{n}.json'
    if os.path.exists(fn):
        parts.extend(json.load(open(fn, encoding='utf-8')))

by_idx = {}
for e in parts:
    i = e['index']
    if i not in by_idx or e.get('downloaded') and not by_idx[i].get('downloaded'):
        by_idx[i] = e

ok = [i for i, e in sorted(by_idx.items()) if e.get('downloaded')]
missing = [i for i in range(1, 50) if i not in by_idx or not by_idx[i].get('downloaded')]
print(f'manifest entries: {len(parts)}, downloaded: {len(ok)}, missing: {missing}')

# verify each downloaded file is a real image
bad = []
for i, e in sorted(by_idx.items()):
    if not e.get('downloaded') or not e.get('file'):
        continue
    f = OIMG + e['file']
    if not os.path.exists(f):
        bad.append((i, 'file_missing'))
        continue
    t = subprocess.run(['file', '-b', f], capture_output=True, text=True).stdout
    if not any(k in t for k in ('JPEG', 'PNG', 'WebP', 'Web/P', 'GIF')):
        bad.append((i, f'not_image: {t.strip()[:50]}'))
print('bad files:', bad if bad else 'none')

if bad:
    print('ABORT: fix bad files before deleting frames')
    sys.exit(1)

# merge manifest with provenance
final = {'generated_by': 'official image search agents',
         'note': '直播畫面截圖已依用戶要求刪除（含主播人像）；圖片來源見每筆 source_page',
         'entries': [by_idx[i] for i in sorted(by_idx)]}
json.dump(final, open(OIMG + 'download_manifest.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# delete live-stream frames (recoverable from local video if ever needed)
for f in os.listdir(D + 'images'):
    p = D + 'images/' + f
    os.remove(p) if os.path.isfile(p) else shutil.rmtree(p)
os.rmdir(D + 'images')
for n in range(1, 5):
    os.remove(OIMG + f'manifest_g{n}.json')
print('DELETED images/ (live frames) and group manifests; official images kept')

# update products.jsonl frames refs
recs = [json.loads(l) for l in open(D + 'products.jsonl', encoding='utf-8')]
for r in recs:
    i = r['segment']['index']
    e = by_idx.get(i, {})
    r['frames'] = {'official_image': e.get('file'), 'source_page': e.get('source_page'),
                   'source_type': e.get('source_type'), 'verified': False}
    if not e.get('downloaded'):
        r['flags'] = sorted(set(r['flags'] + ['official_image_not_found']))
with open(D + 'products.jsonl', 'w', encoding='utf-8') as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print('products.jsonl frames -> official images')