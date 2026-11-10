"""him_closeups.py: full-resolution crops around him from film stills (contact dir of him_contact.sh), one sheet <= 1600 px.
  .venv/bin/python living_earth/him3d/him_closeups.py <contact dir> <169|916> <out.jpg> <frame> [...]"""
import cv2, json, numpy as np, os, sys, glob
SONG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); MAN = os.path.join(SONG, 'build/him_wire/manifest')
d, fmt, out = sys.argv[1:4]; frames = [int(x) for x in sys.argv[4:]]; mans = [json.load(open(p)) for p in glob.glob(MAN + f'/*_{fmt}.json')]; tiles = []
name = 'LivingEarthFilm' if fmt == '169' else 'LivingEarthFilm916'; cw, ch = (880, 620) if fmt == '169' else (620, 620)
for f in frames:
    im = cv2.imread(os.path.join(d, f'f{fmt}', f'{name}_f{f:05d}.png')); e = next((m['frames'][str(f)] for m in mans if str(f) in m['frames']), None)
    if im is None or e is None: print('skip', f); continue
    H, W = im.shape[:2]; cx, cy = e[0] + e[2] / 2, e[1] + e[3] / 2; x0 = int(np.clip(cx - cw / 2, 0, W - cw)); y0 = int(np.clip(cy - ch / 2, 0, H - ch))
    t = im[y0:y0 + ch, x0:x0 + cw].copy(); cv2.putText(t, f'{f} ({fmt})', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 230, 255), 2, cv2.LINE_AA); tiles.append(t)
cols = 4 if fmt == '169' else 5; tw = 1600 // cols; rows = []
tiles = [cv2.resize(t, (tw, int(t.shape[0] * tw / t.shape[1])), interpolation=cv2.INTER_AREA) for t in tiles]
for i in range(0, len(tiles), cols):
    r = tiles[i:i + cols]
    while len(r) < cols: r.append(np.zeros_like(r[0]))
    rows.append(np.concatenate(r, axis=1))
cv2.imwrite(out, np.concatenate(rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)
