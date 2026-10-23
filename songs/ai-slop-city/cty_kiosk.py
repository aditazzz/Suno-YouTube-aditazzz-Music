"""The newsstand insert: yellowed tabloids clipped to the rack, all invented, all decades older than any AI —
'But you've been voting for that feeling / Long before there was me'. Built once as a large flat illustration; the
shot pans and pushes across it."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from cty_eng import F32, hexc, mix, clamp

import os
from studio.core import FONTS
FD = os.path.join(FONTS, '')
PAPERS = [
    ('THE DAILY ECHO', 'VOL. III  ·  APRIL 2, 1957  ·  5¢', ['THE END', 'IS NEAR', '— AGAIN'], 'c8352e'),
    ('TRUTH WEEKLY', 'NO. 214  ·  MAY 4, 1963  ·  10¢', ['SCIENTISTS:', 'YOU WERE', 'RIGHT ALL', 'ALONG'], '1d1d26'),
    ('THE CONFIRMER', 'SEPT. 18, 1979  ·  25¢', ["YOU WON'T", 'BELIEVE', 'WHAT HAPPENS', 'NEXT'], 'c8352e'),
    ('THE ECHO CHAMBER', 'JUNE 9, 1988  ·  50¢', ['EVERYONE', 'AGREES', 'WITH YOU'], '1d1d26'),
    ('TOLD YOU SO TIMES', 'MARCH 1, 1994  ·  75¢', ['THE TRUTH', "THEY DON'T", 'WANT YOU', 'TO KNOW'], 'c8352e'),
]
PW, PHH = 620, 860           # paper size in px (rack image space)
RACK_W, RACK_H = 3600, 1500
_RACK = {}


def _halftone(w, h, seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    # a vague crowd/figure: blobs of tone, then a dot screen
    tone = np.ones((h, w), F32) * 0.75
    for _ in range(7):
        cx, cy = rng.uniform(0.1, 0.9) * w, rng.uniform(0.3, 1.0) * h
        r = rng.uniform(0.12, 0.3) * w
        tone -= 0.5 * np.exp(-(((xx - cx) / r) ** 2 + ((yy - cy) / (r * 1.6)) ** 2))
    tone = np.clip(tone, 0.05, 1)
    p = 7
    gx = (xx % p) - p / 2; gy = (yy % p) - p / 2
    rad = np.sqrt(gx * gx + gy * gy)
    dot = (rad < (1 - tone) * p * 0.62).astype(F32)
    return 1 - dot * 0.85


def paper(i):
    name, date, lines_, mast = PAPERS[i]
    im = Image.new('RGB', (PW, PHH), (236, 226, 196))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(i + 3)
    # masthead
    mc = tuple(int(c * 255) for c in hexc(mast))
    d.rectangle([0, 0, PW, 120], fill=mc)
    f = ImageFont.truetype(FD + 'PlayfairDisplaySC-Regular.ttf', 66)
    while f.getlength(name) > PW - 50:
        f = ImageFont.truetype(FD + 'PlayfairDisplaySC-Regular.ttf', f.size - 3)
    d.text(((PW - f.getlength(name)) / 2, 22), name, font=f, fill=(250, 244, 230))
    fd = ImageFont.truetype(FD + 'SpecialElite-Regular.ttf', 24)
    d.text(((PW - fd.getlength(date)) / 2, 130), date, font=fd, fill=(40, 36, 34))
    d.line([20, 166, PW - 20, 166], fill=(40, 36, 34), width=3)
    # headline
    y = 186
    size0 = int(min(118, 430 / (len(lines_) * 1.04)))
    for l in lines_:
        fh = ImageFont.truetype(FD + 'Anton-Regular.ttf', size0)
        while fh.getlength(l) > PW - 44:
            fh = ImageFont.truetype(FD + 'Anton-Regular.ttf', fh.size - 4)
        d.text(((PW - fh.getlength(l)) / 2, y), l, font=fh, fill=(24, 22, 22))
        y += int(fh.size * 1.04)
    # photo + columns
    ph_y = y + 18
    ph = _halftone(PW - 300, PHH - ph_y - 40, i)
    arr = np.asarray(im, F32) / 255
    arr[ph_y:ph_y + ph.shape[0], 30:30 + ph.shape[1]] *= ph[..., None]
    im = Image.fromarray((arr * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([30, ph_y, 30 + ph.shape[1], ph_y + ph.shape[0]], outline=(40, 36, 34), width=2)
    for k in range((PHH - ph_y - 50) // 16):
        yy = ph_y + 6 + k * 16
        w = rng.uniform(0.6, 1.0) * 220
        d.line([PW - 255, yy, PW - 255 + w, yy], fill=(110, 104, 96), width=5)
    arr = np.asarray(im, F32) / 255
    # age: yellowing, foxing, a fold
    yy, xx = np.mgrid[0:PHH, 0:PW].astype(F32)
    age = 0.9 + 0.1 * np.exp(-(((xx - PW / 2) / PW) ** 2 + ((yy - PHH / 2) / PHH) ** 2) * 3)
    arr *= age[..., None] * np.array([1.0, 0.98, 0.92], F32)
    arr[:, PW // 2 - 1:PW // 2 + 1] *= 0.93
    for _ in range(14):
        cx, cy, r = rng.uniform(0, PW), rng.uniform(0, PHH), rng.uniform(3, 12)
        arr *= (1 - 0.12 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
    return np.clip(arr, 0, 1)


def rack():
    if 'r' in _RACK: return _RACK['r']
    img = np.ones((RACK_H, RACK_W, 3), F32) * hexc('2f5a4c')
    # painted boards
    for k in range(0, RACK_H, 120):
        img[k:k + 3] *= 0.75
    rng = np.random.default_rng(1)
    img *= (0.92 + 0.08 * rng.random((RACK_H, 1, 1))).astype(F32)
    # rail
    img[180:205] = hexc('8a8f96'); img[203:208] = hexc('3a3d44')
    xs = [180 + i * (PW + 70) for i in range(5)]
    pos = []
    for i, x in enumerate(xs):
        p = paper(i)
        ang = [-2.2, 1.5, -1.0, 2.0, -1.6][i]
        M = cv2.getRotationMatrix2D((PW / 2, 0), ang, 1.0)
        pr = cv2.warpAffine(p, M, (PW, PHH + 40), borderValue=(0, 0, 0))
        m = cv2.warpAffine(np.ones((PHH, PW), F32), M, (PW, PHH + 40))
        y = 230
        sh = cv2.GaussianBlur(m, (0, 0), 14)
        img[y + 18:y + 18 + PHH + 40, x + 14:x + 14 + PW] *= (1 - 0.45 * sh)[..., None]
        img[y:y + PHH + 40, x:x + PW] = img[y:y + PHH + 40, x:x + PW] * (1 - m[..., None]) + pr * m[..., None]
        edge = cv2.morphologyEx((m * 255).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(F32) / 255
        img[y:y + PHH + 40, x:x + PW] = img[y:y + PHH + 40, x:x + PW] * (1 - edge[..., None] * 0.8) + hexc('1d1620') * edge[..., None] * 0.8
        # clothes-peg
        cx = x + PW // 2
        cv2.rectangle(img, (cx - 22, 160), (cx + 22, 262), tuple(hexc('b98a5a').tolist()), -1, cv2.LINE_AA)
        cv2.rectangle(img, (cx - 22, 160), (cx + 22, 262), tuple(hexc('1d1620').tolist()), 3, cv2.LINE_AA)
        cv2.line(img, (cx, 166), (cx, 256), tuple(hexc('6a4a30').tolist()), 2, cv2.LINE_AA)
        pos.append((x + PW / 2, y + PHH / 2))
    _RACK['r'] = (img, pos)
    return _RACK['r']


def shot(W, H, k, light=None, sway=0.0):
    """k: 0..1 along the pan (left papers -> right papers), with a slow push."""
    img, pos = rack()
    vert = H > W
    zoom = (1.0 + 0.25 * k) * (W / 1920 if not vert else H / 1920 * 1.05)
    view_w = W / zoom; view_h = H / zoom
    cx = pos[0][0] + (pos[3][0] - pos[0][0]) * k if not vert else pos[1][0] + (pos[3][0] - pos[1][0]) * k
    cy = RACK_H * 0.42
    x0, y0 = cx - view_w / 2, cy - view_h / 2
    M = np.array([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]], F32)
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    L = light or dict(key=np.array([1.0, 0.92, 0.8], F32), shade=np.array([0.55, 0.55, 0.7], F32))
    # canopy shadow across the top, warm afternoon light below
    yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
    sh = 1 - np.clip((yy - 0.16 - 0.04 * math.sin(sway)) / 0.06, 0, 1)
    out = out * (L['key'] * (1 - sh) + L['shade'] * sh)
    return out
