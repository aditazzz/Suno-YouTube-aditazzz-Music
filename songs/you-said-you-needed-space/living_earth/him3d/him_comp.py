"""him_comp.py: look-dev composites of the 3D "him" over frames of the cut-1 master (Nov 9). Not part of the film.
  .venv/bin/python living_earth/him3d/him_comp.py <shots.json>
Each shot: plate (png), him (RGBA png, straight alpha), out; optional paint_out box (removes the old star drawing), crop916 centre x.
His real lights (eye, status lights, beacon, engine) bloom a little into the plate, as the film's own lights do.
"""
import cv2, json, numpy as np, sys, os

def load_rgba(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED).astype(np.float32); im /= 65535.0 if im.max() > 255 else 255.0
    return im[..., :3], im[..., 3:4]

def paint_out(plate, box, thread_y=540):
    """Remove the old star drawing inside box (x0, y0, x1, y1): a clean sky (the plate's own large-scale colour + stars taken
    from a clean patch of the same frame), the cyan threads below thread_y kept, the box edges feathered."""
    x0, y0, x1, y1 = box; reg = plate[y0:y1, x0:x1]; b, g, r = reg[..., 0], reg[..., 1], reg[..., 2]
    lum = 0.2 * r + 0.7 * g + 0.1 * b; cyan = (b > r * 1.3) & (g > r * 1.2) & (lum > 0.10)
    mask = cv2.dilate((lum > 0.07).astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
    u8 = np.clip(reg * 255, 0, 255).astype(np.uint8); base = cv2.inpaint(cv2.resize(u8, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA), cv2.resize(mask, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST), 4, cv2.INPAINT_TELEA)
    base = cv2.GaussianBlur(cv2.resize(base, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255, (0, 0), 40)
    ph, pw = y1 - y0, 620; patch = plate[0:ph, 20:20 + pw]; stars = np.clip(patch - cv2.GaussianBlur(patch, (0, 0), 6), 0, 1)
    tiles = [stars, stars[:, ::-1], stars[::-1], stars[::-1, ::-1]]; row = np.concatenate([tiles[i % 4] for i in range((x1 - x0) // pw + 1)], axis=1)[:, :x1 - x0]
    clean = base + row
    yy = np.arange(y0, y1)[:, None]; ramp = np.clip((yy - 700) / 130.0, 0, 1)       # the threads fade out as they reach him
    th = (cv2.GaussianBlur(cv2.dilate(cyan.astype(np.float32), np.ones((5, 5), np.uint8)), (0, 0), 1.5) * ramp)[..., None]
    clean = clean * (1 - th) + reg * th
    f = 70.0; xs = np.arange(x1 - x0)[None, :]; ys = np.arange(y1 - y0)[:, None]
    w = np.clip(np.minimum(np.minimum(xs, (x1 - x0 - 1) - xs), (y1 - y0 - 1) - ys) / f, 0, 1); w = (w * w * (3 - 2 * w))[..., None]
    out = plate.copy(); out[y0:y1, x0:x1] = reg * (1 - w) + clean * w; return out

def comp(s):
    plate = cv2.imread(s['plate']).astype(np.float32) / 255
    if s.get('paint_out'): plate = paint_out(plate, s['paint_out'])
    if s.get('inpaint'):                                    # the old spark he replaces: [[x, y, r], ...]
        m = np.zeros(plate.shape[:2], np.uint8)
        for x, y, r in s['inpaint']: cv2.circle(m, (int(x), int(y)), int(r), 255, -1)
        plate = cv2.inpaint(np.clip(plate * 255, 0, 255).astype(np.uint8), m, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255
    rgb, a = load_rgba(s['him'])
    if rgb.shape[:2] != plate.shape[:2]: rgb = cv2.resize(rgb, plate.shape[1::-1], interpolation=cv2.INTER_AREA); a = cv2.resize(a, plate.shape[1::-1], interpolation=cv2.INTER_AREA)[..., None]
    k = plate.shape[1] / 2560; pm = cv2.GaussianBlur(np.concatenate([rgb * a, a], axis=2), (0, 0), 0.55 * k); a = pm[..., 3:4]; rgb = pm[..., :3] / np.maximum(a, 1e-4)   # sit in the plate: as soft as the master
    out = plate * (1 - a) + rgb * a
    band = a * np.clip(1 - cv2.GaussianBlur(a, (0, 0), 14 * k)[..., None], 0, 1) * 2                # light wrap: the plate's glow spills over his edges
    out = out + cv2.GaussianBlur(plate, (0, 0), 30 * k) * band * s.get('wrap', 0.4)
    lum = rgb.max(axis=2, keepdims=True); hot = rgb * a * np.clip((lum - 0.80) / 0.2, 0, 1)        # only what is really bright: his lights, sun glints
    bloom = 0.55 * cv2.GaussianBlur(hot, (0, 0), 7 * k) + 0.45 * cv2.GaussianBlur(hot, (0, 0), 26 * k) + 0.25 * cv2.GaussianBlur(hot, (0, 0), 70 * k)
    out = 1 - (1 - np.clip(out, 0, 1)) * (1 - np.clip(bloom * s.get('bloom', 1.0), 0, 1))
    u8 = np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8); cv2.imwrite(s['out'], u8)
    if s.get('crop916') is not None:
        h, w = u8.shape[:2]; cw = int(round(h * 9 / 16)); x0 = int(np.clip(s['crop916'] * w / 2560 - cw / 2, 0, w - cw))
        cv2.imwrite(s['out'].replace('.png', '_9x16.png'), cv2.resize(u8[:, x0:x0 + cw], (1080, 1920), interpolation=cv2.INTER_LANCZOS4))
    print('[him_comp]', s['out'])

if __name__ == '__main__':
    for s in json.load(open(sys.argv[1])): comp(s)
