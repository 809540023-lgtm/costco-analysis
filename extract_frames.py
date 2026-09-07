import argparse
import json
import os
import re
import subprocess
import sys


def probe_duration(video):
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'ffprobe failed: {r.stderr}')
    return float(r.stdout.strip())


def parse_products(md_path):
    text = open(md_path, encoding='utf-8').read()
    sections = re.split(r'\n### ', text)
    out = []
    for sec in sections:
        m_name = re.match(r'(.+)', sec)
        m_time = re.search(r'\*\*出現時間\*\*：\[?\(?(\d+):(\d+)\]?\s*-\s*\[?(\d+):(\d+)\]?', sec)
        if not (m_name and m_time):
            continue
        name = re.sub(r'[\\/:*?"<>|＊「」（）()/]', '', m_name.group(1).strip()[:40]).strip()
        s = int(m_time.group(1)) * 60 + int(m_time.group(2))
        e = int(m_time.group(3)) * 60 + int(m_time.group(4))
        out.append({'name': name, 'start': s, 'end': e})
    return out


def grab(video, ss, out):
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-i', video,
                        '-frames:v', '1', '-q:v', '2', out], capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out)


def main():
    ap = argparse.ArgumentParser(description='Extract candidate product frames from a live video')
    ap.add_argument('--md', required=True, help='product list markdown')
    ap.add_argument('--video', required=True)
    ap.add_argument('--out', required=True, help='image output dir')
    ap.add_argument('--video-id', default='', help='source video id for manifest')
    ap.add_argument('--points', default='0.30,0.55,0.80',
                    help='relative positions inside each segment span to sample')
    args = ap.parse_args()

    duration = probe_duration(args.video)
    os.makedirs(args.out, exist_ok=True)
    products = parse_products(args.md)
    if not products:
        sys.exit('no product sections parsed from markdown')

    manifest = {'video_id': args.video_id, 'video_duration_sec': round(duration, 1),
                'sample_points': args.points, 'verified': False, 'frames': []}
    for i, p in enumerate(products, 1):
        span = max(p['end'] - p['start'], 1)
        entry = {'index': i, 'product': p['name'], 'segment_start': p['start'],
                 'segment_end': p['end'], 'candidates': [], 'status': 'ok'}
        if p['start'] >= duration:
            entry['status'] = 'out_of_range_pending_review'
            manifest['frames'].append(entry)
            print(f"[SKIP] {i:02d} start beyond video end", file=sys.stderr)
            continue
        for pos in (float(x) for x in args.points.split(',')):
            ss = int(p['start'] + span * pos)
            ss = min(ss, int(duration) - 3)
            fn = os.path.join(args.out, f'{i:02d}_{p["name"]}_p{int(pos*100)}.jpg')
            ok = grab(args.video, ss, fn)
            entry['candidates'].append({'file': os.path.basename(fn), 'frame_time': ss,
                                        'relative_pos': pos, 'grabbed': ok,
                                        'match_confidence': None, 'verified': False})
            if not ok:
                entry['status'] = 'grab_failed'
        manifest['frames'].append(entry)

    with open(os.path.join(args.out, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    n_ok = sum(1 for fr in manifest['frames'] if fr['status'] == 'ok')
    print(f'DONE {n_ok}/{len(products)} products -> manifest.json')


if __name__ == '__main__':
    main()