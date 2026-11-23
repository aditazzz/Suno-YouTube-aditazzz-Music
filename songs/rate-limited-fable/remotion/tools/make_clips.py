#!/usr/bin/env python3
"""clips.yaml for studio.review_video from a whole-film code cut: parts split on section boundaries (~30-40 s each,
so every part stays under 8 MB at 720p), with each part's shots listed so her frame notes map to shot ids.
  python3 tools/make_clips.py <film.mp4> <out clips.yaml> [--heading ...]
"""
import json, os, string, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
d = json.load(open(os.path.join(PROJ, 'src/data/shots.json')))
src, out = os.path.abspath(sys.argv[1]), sys.argv[2]
heading = sys.argv[sys.argv.index('--heading') + 1] if '--heading' in sys.argv else 'Rate Limited, code animatic v0'
fps = d['fps']
shots = d['shots']

# group sections into parts of <= ~40 s
secs = []
for s in shots:
    if not secs or secs[-1]['sec'] != s['sec']:
        secs.append({'sec': s['sec'], 'name': s['section'], 'shots': []})
    secs[-1]['shots'].append(s)
parts, cur = [], []
for sc in secs:
    span = lambda g: (g[-1]['shots'][-1]['to'] - g[0]['shots'][0]['from']) / fps
    if cur and span(cur + [sc]) > 40:
        parts.append(cur); cur = []
    cur.append(sc)
if cur:
    parts.append(cur)

tc = lambda f: f'{int(f / fps // 60)}:{int(f / fps % 60):02d}'
clips = []
for i, g in enumerate(parts, 1):
    a, b = g[0]['shots'][0]['from'], g[-1]['shots'][-1]['to'] - 1
    names = ' / '.join(string.capwords(x['name'].split(':', 1)[-1].strip().lower()) for x in g)
    clips.append({'id': f'p{i}', 'title': f'Part {i}: {names} ({tc(a)} to {tc(b + 1)})', 'src': src, 'trim': [a, b],
                  'shots': [{'id': s['id'], 'a': s['from'], 'b': s['to'] - 1} for s in sum((x['shots'] for x in g), [])]})
spec = {
    'heading': heading, 'page_title': 'Rate Limited code animatic', 'fps': fps,
    'covers': 'The whole song as the code film will cut it: every shot on its beat-grid frames, each on its approved still '
              'with a simple camera move. Slates show the shot id and clock; "NEW PICTURE" cards mark shots whose still '
              'does not exist yet. Pause anywhere and leave a note on that frame.',
    'top_notes': ['Rough on purpose: one still per shot, simple pushes and drifts, no inserts, clocks, neon or type yet. '
                  'Judge the order and the timing.'],
    'listen': {'src': src, 'label': 'The whole animatic, start to finish'},
    'clips': clips,
}
yaml.safe_dump(spec, open(out, 'w'), sort_keys=False, allow_unicode=True, width=150)
print(f'{len(clips)} parts -> {out}')
