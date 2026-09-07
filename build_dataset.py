import json
import re

MD = '商品清單.md'
TS = 'transcript_full.txt'
OUT = 'products.jsonl'
VERSION = 'v0.1'

FIELD_MAP = {
    '特色/內容物': 'features',
    '介紹的好處': 'benefits',
    '售價': 'price',
    '販售定位': 'positioning',
    '差異性': 'differences',
    '出現時間': '_time',
}

CLAIM_PATTERNS = [
    ('台灣買不到', 'availability_tw'), ('買不到', 'availability'),
    ('No.1', 'bestseller'), ('第一名', 'bestseller'), ('銷售前幾名', 'bestseller'),
    ('零負評', 'zero_negative_reviews'), ('救星', 'host_praise'),
    ('孕婦', 'suitability_pregnant'), ('兒童', 'suitability_children'),
    ('買一送一', 'promo'), ('最後一批', 'scarcity'), ('限定', 'limited_edition'),
]


def load_transcript_index():
    idx = []
    for i, ln in enumerate(open(TS, encoding='utf-8'), 1):
        m = re.match(r'\[(\d+):(\d+)\]', ln)
        if m:
            idx.append((int(m.group(1)) * 60 + int(m.group(2)), i))
    return idx


def line_for_sec(idx, sec):
    lo, hi = 0, len(idx)
    while lo < hi:
        mid = (lo + hi) // 2
        if idx[mid][0] < sec:
            lo = mid + 1
        else:
            hi = mid
    return idx[lo][1] if lo < len(idx) else idx[-1][1]


def parse_prices(raw):
    obs = []
    raw = raw.replace('（商城', '；（商城').replace('(商城', '；(商城')
    for clause in re.split(r'[；;]', raw):
        clause = clause.strip('。 \n')
        if not clause:
            continue
        nums = [int(n) for n in re.findall(r'\d{3,5}', clause)]
        role = 'external_reference' if re.search(r'外面|原價|日本一|環球', clause) else \
               'bulk_offer' if re.search(r'加\s*\d|以上|以上每|兩罐以上|加2|加二', clause) else \
               'competitor_mall' if '商城' in clause else \
               'competitor_live' if re.search(r'直播|線上|本場', clause) else 'unknown_role'
        if not nums and '未提及' in clause:
            obs.append({'original_text': clause, 'amount': None, 'currency': 'unknown',
                        'currency_in_source': None, 'price_role': 'not_mentioned',
                        'min_quantity': None, 'variant': None, 'effective_ts': None,
                        'transcript_line': None})
            continue
        m_ts = re.search(r'(\d{1,2}:\d{2})', clause)
        qty = re.search(r'加\s*(\d+)\s*(盒|包|袋|罐|份)?', clause)
        obs.append({'original_text': clause,
                    'amount': nums[0] if nums else None,
                    'currency': 'unknown',
                    'currency_in_source': 'jpy_text' if '日圓' in clause else None,
                    'price_role': role,
                    'min_quantity': int(qty.group(1)) + 1 if qty else 1,
                    'variant': None,
                    'effective_ts': m_ts.group(1) if m_ts else None,
                    'transcript_line': None})
    return obs


def extract_variants(text):
    found, seen = [], set()
    for m in re.finditer(r'(紙盒|鐵盒|罐裝|袋裝)\s*(\d+\s*入?)', text):
        v = m.group(0).replace(' ', '')
        if v not in seen:
            seen.add(v)
            found.append({'label': v, 'source_text': m.group(0), 'price': None})
    return found


def extract_clauses(sec):
    out = {}
    for line in sec.splitlines():
        m = re.match(r'\s*-\s*\*\*(.+?)\*\*：(.*)', line)
        if m and m.group(1) in FIELD_MAP:
            out[FIELD_MAP[m.group(1)]] = m.group(2).strip()
    return out


def main():
    idx = load_transcript_index()
    text = open(MD, encoding='utf-8').read()
    sections = re.split(r'\n### ', text)
    records = []
    for sec in sections:
        title = sec.split('\n', 1)[0].strip()
        m_time = re.search(r'\[?\(?(\d+):(\d+)\]?\s*-\s*\[?(\d+):(\d+)\]?', sec)
        if not m_time or not title or title.startswith('#'):
            continue
        s = int(m_time.group(1)) * 60 + int(m_time.group(2))
        e = int(m_time.group(3)) * 60 + int(m_time.group(4))
        c = extract_clauses(sec)
        rec = {
            'dataset_version': VERSION,
            'source': {
                'video_id': 'FB_1993293861646570', 'platform': 'facebook',
                'account': 'SkyBlue.fans', 'transcript_file': TS,
                'capture_date': '2026-09-06', 'extraction_method': 'faster-whisper-small + LLM + human merge',
            },
            'segment': {
                'index': len(records) + 1,
                'start_sec': s, 'end_sec': e,
                'start_ts': f'[{s // 60:02d}:{s % 60:02d}]', 'end_ts': f'[{e // 60:02d}:{e % 60:02d}]',
                'transcript_line_start': line_for_sec(idx, s),
                'transcript_line_end': line_for_sec(idx, e),
                'live_item_code': None,
            },
            'product': {
                'name_raw': title,
                'match_status': 'unverified',
                'official_costco_item_number': None,
                'note': 'A編號為直播編號；名稱含音譯待查證',
            },
            'variants': {'extraction': 'heuristic_v0', 'items': extract_variants(sec)},
            'price_observations': parse_prices(c.get('price', '未提及')),
            'claims': [],
            'content': {
                'features_raw': c.get('features', ''), 'benefits_raw': c.get('benefits', ''),
                'positioning_raw': c.get('positioning', ''), 'differences_raw': c.get('differences', ''),
            },
            'frames': {'manifest_ref': f'images/manifest.json#frames[{len(records)}]',
                       'verified': False},
            'flags': [],
        }
        rec['claims'] = [{'keyword': kw, 'claim_type': typ, 'claim_author': 'host',
                          'verification': 'unverified'}
                         for kw, typ in CLAIM_PATTERNS if kw in sec]
        flags = []
        if not any(o['amount'] for o in rec['price_observations']):
            flags.append('price_missing')
        if e - s > 300:
            flags.append('long_span_interleaved_possible')
        if '疑' in title or '音譯' in title or 'ASR' in title:
            flags.append('name_unverified')
        flags.append('currency_unknown')
        rec['flags'] = flags
        rec['_range'] = (s, e)
        records.append(rec)

    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if a['_range'][0] < b['_range'][1] and b['_range'][0] < a['_range'][1]:
                a['flags'].append('time_overlap_with_neighbor')
                b['flags'].append('time_overlap_with_neighbor')
    for i in range(1, len(records)):
        if records[i]['_range'][0] < records[i - 1]['_range'][1] and \
           'time_overlap_with_neighbor' not in records[i]['flags']:
            records[i]['flags'].append('list_order_differs_from_time_order')
    for r in records:
        r.pop('_range')

    with open(OUT, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    n_price = sum(1 for r in records if any(o['amount'] for o in r['price_observations']))
    n_claims = sum(len(r['claims']) for r in records)
    n_var = sum(len(r['variants']['items']) for r in records)
    print(f'WROTE {len(records)} records -> {OUT} | with price: {n_price} | claims: {n_claims} | variants: {n_var}')


if __name__ == '__main__':
    main()