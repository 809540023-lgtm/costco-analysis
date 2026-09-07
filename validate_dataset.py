import json
import sys

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


recs = [json.loads(l) for l in open('products.jsonl', encoding='utf-8')]
check(len(recs) == 49, f'record count {len(recs)} != 49')

required_top = {'dataset_version', 'source', 'segment', 'product', 'variants',
                'price_observations', 'claims', 'content', 'frames', 'flags'}
prev_end = -1
for i, r in enumerate(recs, 1):
    tag = f'record {i}'
    check(required_top <= set(r), f'{tag}: missing top-level keys')
    seg = r['segment']
    check(seg['index'] == i, f'{tag}: index mismatch')
    if seg['start_sec'] < prev_end and not ({'time_overlap_with_neighbor', 'list_order_differs_from_time_order'} & set(r['flags'])):
        failures.append(f'{tag}: overlapping/out-of-order segment ({seg["start_ts"]}) without flag')
    prev_end = seg['end_sec']
    check(seg['transcript_line_start'] > 0, f'{tag}: no transcript line ref')
    check(all('currency' in o and 'price_role' in o for o in r['price_observations']),
          f'{tag}: price obs missing currency/price_role')
    check(all(c.get('claim_author') == 'host' and c.get('verification') == 'unverified'
              for c in r['claims']), f'{tag}: claim not marked host/unverified')
    check('verified' in r['frames'] and not r['frames']['verified'], f'{tag}: frames must be unverified')
    check('currency_unknown' in r['flags'], f'{tag}: currency_unknown flag required')

counts = {'with_price': sum(1 for r in recs if any(o['amount'] for o in r['price_observations'])),
          'claims': sum(len(r['claims']) for r in recs),
          'price_missing': sum(1 for r in recs if 'price_missing' in r['flags'])}
print('OK' if not failures else 'FAIL', counts)
for f in failures:
    print(' -', f)
sys.exit(1 if failures else 0)