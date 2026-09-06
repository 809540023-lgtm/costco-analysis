import re, subprocess, sys, os

md_path, video, img_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(img_dir, exist_ok=True)
text = open(md_path, encoding='utf-8').read()

sections = re.split(r'\n### ', text)
count = 0
for sec in sections:
    m_name = re.match(r'(.+)', sec)
    m_time = re.search(r'\*\*出現時間\*\*：\[(\d+):(\d+)\]', sec)
    if not (m_name and m_time):
        continue
    name = m_name.group(1).strip()[:40]
    name = re.sub(r'[\\/:*?\"<>|＊「」（）()]', '', name).strip()
    ts = int(m_time.group(1)) * 60 + int(m_time.group(2))
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'csv=p=0', video], capture_output=True, text=True).stdout)
    ss = min(ts, max(int(dur) - 3, 0))
    count += 1
    out = os.path.join(img_dir, f'{count:02d}_{name}.jpg')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(ss), '-i', video,
                    '-frames:v', '1', '-q:v', '2', out], check=True)
    print(f'{out} @ {ss}s')
print(f'DONE {count} screenshots')