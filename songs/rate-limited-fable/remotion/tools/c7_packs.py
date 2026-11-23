#!/usr/bin/env python3
"""public/c7/**/pack.json (tools/slice_plate.py output) -> src/data/c7packs.json, the SliceCam registry, and src/data/c7files.json (every image under public/c7, for has()) (key = pack dir under public/).
Re-run whenever a 3D lane lands a pack (rl7_ra / R-B own running it). A pack listed here is drawn sliced; else SliceCam draws the flat plate."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
out = {}
for f in sorted((P / 'public/c7').glob('**/pack.json')):
    d = json.loads(f.read_text()); key = str(f.parent.relative_to(P / 'public'))
    k = 2560 / d['w']   # bbox in stage px (the pack is drawn 2560 wide)
    out[key] = {'w': d['w'], 'h': d['h'], 'slices': [{'src': f'{key}/{s["src"]}', 'name': s['name'], 'par': s['par'],
                                                      'bbox': [round(v * k, 1) for v in s.get('bbox', [0, 0, d['w'], d['h']])]} for s in d['slices']]}
(P / 'src/data/c7packs.json').write_text(json.dumps(out, indent=1))
files = sorted(str(f.relative_to(P / 'public')) for f in (P / 'public/c7').glob('**/*') if f.is_file() and f.suffix.lower() in ('.png', '.jpg', '.json'))
(P / 'src/data/c7files.json').write_text(json.dumps(files, indent=0))
print(len(out), 'packs:', ', '.join(out), f'| {len(files)} files under public/c7')
