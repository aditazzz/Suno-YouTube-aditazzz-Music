"""The feed banner made of stars (earth_proof30): lay the banner out with PIL through studio.textfit (every text block is
measured against its box and recorded), then sample it into star targets. One design per format, at the master's size.
    .venv/bin/python living_earth/proof30_banner.py   ->  remotion/src/le/film/sections/proof30_banner.gen.ts
                                                          build/le_proof30/textfit/textfit_banner_<fmt>.json + banner_<fmt>.png
Copy approved on the pitch page (beats/02): NEW POST / now / Moving to space!   No real app, no logo (a four-point sparkle)."""
import os, sys, json, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); STUDIO = os.path.dirname(os.path.dirname(SONG))
sys.path.insert(0, STUDIO)
from studio import textfit
FONTS = os.path.join(STUDIO, 'assets', 'fonts')
OUT = os.path.join(SONG, 'build', 'le_proof30', 'textfit'); os.makedirs(OUT, exist_ok=True)
COPY = dict(app='NEW POST', when='now', body='Moving to space!')
# per format: frame size, banner box (px), scale of the 1440p design, sampling cell (px) per part, star size (engine px at 1440-high)
FMT = {
    '169': dict(size=(2560, 1440), box=(440, 150, 2120, 553), k=1.0, cell=dict(frame=3, tile=3, glyph=3, head=2, body=3), star=dict(frame=6.0, tile=6.0, glyph=6.4, head=4.6, body=6.2)),
    '916': dict(size=(1080, 1920), box=(97, 330, 983, 543), k=0.5274, cell=dict(frame=2, tile=2, glyph=2, head=2, body=2), star=dict(frame=3.3, tile=3.3, glyph=3.5, head=3.0, body=3.4)),
}
ORDER = dict(frame=0.0, tile=0.10, glyph=0.20, head=0.22, body=0.38)
PART = dict(frame=0, tile=1, glyph=2, head=3, body=4)


def grid_sample(mask, g, rng, thr=128):
    ys, xs = np.nonzero(mask > thr)
    cell = (ys // g).astype(np.int64) * 100000 + (xs // g).astype(np.int64)
    order = rng.permutation(len(xs)); _, first = np.unique(cell[order], return_index=True); sel = order[first]
    return np.stack([xs[sel] + rng.random(len(sel)), ys[sel] + rng.random(len(sel))], 1)


def design(fmt):
    F = FMT[fmt]; W, H = F['size']; x0, y0, x1, y1 = F['box']; k = F['k']
    rec = textfit.Recorder((W, H), 'banner_%s' % fmt)
    parts = {}
    new = lambda: (lambda im: (im, ImageDraw.Draw(im)))(Image.new('L', (W, H), 0))
    lw = max(3, round(6 * k)); rad = round(85 * k)
    im, d = new(); d.rounded_rectangle((x0, y0, x1, y1), radius=rad, outline=255, width=lw); parts['frame'] = np.array(im)
    isz = round(237 * k); ix0 = x0 + round(61 * k); iy0 = (y0 + y1) // 2 - isz // 2
    im, d = new(); d.rounded_rectangle((ix0, iy0, ix0 + isz, iy0 + isz), radius=round(56 * k), outline=255, width=lw); parts['tile'] = np.array(im)
    im, d = new(); c = (ix0 + isz / 2, iy0 + isz / 2); R, q = 83 * k, 17 * k
    d.polygon([(c[0], c[1] - R), (c[0] + q, c[1] - q), (c[0] + R, c[1]), (c[0] + q, c[1] + q), (c[0], c[1] + R), (c[0] - q, c[1] + q), (c[0] - R, c[1]), (c[0] - q, c[1] - q)], fill=255)
    parts['glyph'] = np.array(im)
    tx0 = ix0 + isz + round(40 * k); xr = x1 - round(40 * k)
    f_app = ImageFont.truetype(os.path.join(FONTS, 'Inter-SemiBold.otf'), round(67 * k))
    f_body = ImageFont.truetype(os.path.join(FONTS, 'InterDisplay-Bold.otf'), round(149 * k))
    hy0, hy1 = y0 + round(40 * k), y0 + round(150 * k)
    im, d = new()
    r1 = textfit.fit_text(d, COPY['app'], (tx0, hy0, tx0 + round(560 * k), hy1), f_app, min_px=34, fill=255, align='l', recorder=rec)
    r2 = textfit.fit_text(d, COPY['when'], (xr - round(250 * k), hy0, xr, hy1), f_app, min_px=34, fill=255, align='r', recorder=rec)
    parts['head'] = np.array(im)
    im, d = new()
    r3 = textfit.fit_text(d, COPY['body'], (tx0, y0 + round(146 * k), xr, y1 - round(30 * k)), f_body, min_px=58 if fmt == '916' else 84, fill=255, align='l', recorder=rec)
    parts['body'] = np.array(im)
    probs = rec.problems(); rec.save(OUT)
    assert not probs, probs
    Image.fromarray(np.maximum.reduce(list(parts.values()))).save(os.path.join(OUT, 'banner_%s.png' % fmt))
    print(fmt, 'text px:', r1['size'], r2['size'], r3['size'], 'problems:', len(probs))
    return parts


def build(fmt, seed):
    F = FMT[fmt]; W, H = F['size']; A = W / H; rng = np.random.default_rng(seed); parts = design(fmt)
    x0, y0, x1, y1 = F['box']
    T, P, O, S = [], [], [], []
    for name, m in parts.items():
        p = grid_sample(m, F['cell'][name], rng)
        T.append(p); P.append(np.full(len(p), PART[name])); O.append(np.full(len(p), ORDER[name])); S.append(np.full(len(p), F['star'][name]))
    T = np.concatenate(T); P = np.concatenate(P); O = np.concatenate(O); S = np.concatenate(S); K = len(T)
    sx = lambda x: (x / W * 2 - 1) * A; sy = lambda y: 1 - y / H * 2                 # px -> screen units (y up, half height = 1)
    tx, ty = sx(T[:, 0]), sy(T[:, 1])
    # homes: stars of the sky above her (never from behind her limb), nearer the banner = likelier
    hx = (rng.random(K) * 2 - 1) * A * 1.06; hy = -0.12 + 1.2 * rng.random(K) ** 0.8
    ao = np.argsort(hx + rng.normal(0, 0.11, K)); to = np.argsort(tx + rng.normal(0, 0.07, K))   # pair by x rank: the streams do not cross
    HX = np.zeros(K); HY = np.zeros(K); HX[to] = hx[ao]; HY[to] = hy[ao]
    xn = (T[:, 0] - x0) / (x1 - x0)
    dl = O * 0.9 + 0.55 * xn * (O > 0.3) + 0.25 * xn * (O <= 0.3) + rng.random(K) * 0.22
    dl = dl / dl.max()
    curl = np.clip(0.16 + rng.normal(0, 0.07, K), -0.1, 0.4)
    arr = np.stack([HX, HY, tx, ty, dl, curl, S / 10.0, P / 10.0], 1)
    q = np.clip(np.round(arr * 10000), -32767, 32767).astype('<i2')
    print(fmt, 'stars:', K)
    return dict(n=int(K), b64=base64.b64encode(q.tobytes()).decode())


if __name__ == '__main__':
    out = {f: build(f, 5 + i) for i, f in enumerate(FMT)}
    box = {f: [((FMT[f]['box'][0] / FMT[f]['size'][0]) * 2 - 1) * FMT[f]['size'][0] / FMT[f]['size'][1], 1 - FMT[f]['box'][3] / FMT[f]['size'][1] * 2,
               ((FMT[f]['box'][2] / FMT[f]['size'][0]) * 2 - 1) * FMT[f]['size'][0] / FMT[f]['size'][1], 1 - FMT[f]['box'][1] / FMT[f]['size'][1] * 2] for f in FMT}
    p = os.path.join(SONG, 'remotion', 'src', 'le', 'film', 'sections', 'proof30_banner.gen.ts')
    with open(p, 'w') as fh:
        fh.write('// GENERATED by living_earth/proof30_banner.py (the feed banner as star targets; layout measured by studio.textfit). Do not edit.\n')
        fh.write('// per star, 8 int16 / 10000: home x, y, target x, y (screen units, y up), delay 0..1, curl, size / 10, part / 10 (0 frame, 1 tile, 2 glyph, 3 head, 4 body)\n')
        fh.write('export const BANNER: Record<string, { n: number; b64: string; box: number[] }> = ' + json.dumps({f: dict(out[f], box=[round(v, 4) for v in box[f]]) for f in out}) + ';\n')
    print('wrote', p)
