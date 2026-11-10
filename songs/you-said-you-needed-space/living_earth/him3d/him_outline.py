"""him_outline.py: his silhouette in the bridge "blueprint" pose (frame 4700, before he wakes), for sections/bridge.ts to draw with her lights.
  .venv/bin/python living_earth/him3d/him_outline.py   -> build/him_wire/positions/br_outline.json (+ br_outline_169.png preview)
Coordinates: n = (dx, dy) from his centre in units of his SPAN (wing tip to wing tip), y up. Screen position in engine units:
  x = cx + n.x * span_units, y = cy + n.y * span_units, with cx, cy, span_units per frame in positions/br.json."""
import cv2, json, numpy as np, os
SONG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); W = os.path.join(SONG, 'build/him_wire')
out = {'note': __doc__.strip().split('\n', 2)[2], 'frame': 4700}
for fmt in ('169', '916'):
    meta = json.load(open(f'{W}/outline/br_{fmt}/meta.json')); m = next(x for x in meta['frames'] if x['f'] == 4700)
    im = cv2.imread(f'{W}/outline/br_{fmt}/him_04700.png', cv2.IMREAD_UNCHANGED); a = (im[..., 3] > (0.5 * (65535 if im.dtype == np.uint16 else 255))).astype(np.uint8)
    cs, hier = cv2.findContours(a, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); span = m['span']; cx, cy = m['px']; polys = []
    for c, h in zip(cs, hier[0]):
        if cv2.contourArea(c) < (0.012 * span) ** 2: continue
        c = cv2.approxPolyDP(c, 0.0015 * span, True)[:, 0, :]
        polys.append({'hole': bool(h[3] >= 0), 'pts': [[round((x - cx) / span, 4), round((cy - y) / span, 4)] for x, y in c]})
    polys.sort(key=lambda p: -len(p['pts'])); out[fmt] = {'span_px': span, 'centre_px': [cx, cy], 'res': meta['res'], 'polys': polys}
    ys, xs = np.nonzero(a); out[fmt]['bbox_n'] = [round((xs.min() - cx) / span, 4), round((cy - ys.max()) / span, 4), round((xs.max() - cx) / span, 4), round((cy - ys.min()) / span, 4)]
    prev = np.zeros((*a.shape, 3), np.uint8); prev[a > 0] = (40, 30, 20)
    for p in polys: cv2.polylines(prev, [np.array([[cx + x * span, cy - y * span] for x, y in p['pts']], np.int32)], True, (255, 230, 60) if not p['hole'] else (255, 120, 200), 3)
    cv2.imwrite(f'{W}/positions/br_outline_{fmt}.png', cv2.resize(prev, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    print(fmt, 'polys', [(len(p['pts']), p['hole']) for p in polys], 'bbox_n', out[fmt]['bbox_n'])
json.dump(out, open(f'{W}/positions/br_outline.json', 'w'))
