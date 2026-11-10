"""him_sheet.py: a contact sheet (<=1600 px wide) of RGBA him frames over a dark sky, or of opaque frames as they are.
  .venv/bin/python living_earth/him3d/him_sheet.py <out.jpg> <cols> <tile width> <png> [<png> ...]   (crop=x0,y0,x1,y1 in 0..1 as a first arg optional)"""
import cv2, numpy as np, sys
args = sys.argv[1:]; crop = None
if args[0].startswith('crop='): crop = [float(v) for v in args.pop(0)[5:].split(',')]
out, cols, tw = args[0], int(args[1]), int(args[2]); tiles = []
for p in args[3:]:
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None: continue
    im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    if im.shape[2] == 4:
        a = im[..., 3:4]; bg = np.zeros_like(im[..., :3]); bg[:] = (0.10, 0.045, 0.03); im = im[..., :3] * a + bg * (1 - a)
    if crop: h, w = im.shape[:2]; im = im[int(crop[1] * h):int(crop[3] * h), int(crop[0] * w):int(crop[2] * w)]
    h, w = im.shape[:2]; im = cv2.resize(im, (tw, int(round(h * tw / w))), interpolation=cv2.INTER_AREA)
    im = (np.clip(im, 0, 1) * 255).astype(np.uint8); cv2.putText(im, p.split('/')[-1][-22:-4], (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 220, 255), 1, cv2.LINE_AA); tiles.append(im)
rows = []
for i in range(0, len(tiles), cols):
    r = tiles[i:i + cols]; hh = max(t.shape[0] for t in r)
    r = [cv2.copyMakeBorder(t, 0, hh - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in r]
    while len(r) < cols: r.append(np.zeros_like(r[0]))
    rows.append(np.concatenate(r, axis=1))
cv2.imwrite(out, np.concatenate(rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)
