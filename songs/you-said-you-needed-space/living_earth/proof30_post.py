"""The feed post made of stars (earth_c2_open, Nov 9 2026; replaces the invented NEW POST banner of proof30_banner.py).
Her mark on cut 1 (p04_v1_feed, 0:31), verbatim: "This needs to be literally be Elon's post on X that he made a couple days ago. Literally."
The post, word for word (checked against the embed on ibtimes.co.uk/...-1830323, Nov 9): display name, handle, text, date. NOTHING else is
attributed to him: no replies, counts, likes, views, no time of day. Studio rules: no logo, no wordmark, no verified badge, no photo
(the avatar is a plain disc of stars).
    .venv/bin/python living_earth/proof30_post.py   ->  remotion/src/le/film/sections/proof30_banner.gen.ts  (OUT_TS=<path> to write elsewhere)
                                                        build/le_c2_open/textfit/textfit_post_<fmt>.json + post_<fmt>.png
Laid out with PIL through studio.textfit (every text block measured against its box and recorded), then sampled into star targets.
Same data format as proof30_banner.py, so Extra.tsx draws it unchanged (part colours: 0 frame, 2 gold = his, 3 small grey text, 4 white text)."""
import os, sys, json, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); STUDIO = os.path.dirname(os.path.dirname(SONG))
sys.path.insert(0, STUDIO)
from studio import textfit
FONTS = os.path.join(STUDIO, 'assets', 'fonts')
OUT = os.path.join(SONG, 'build', 'le_c2_open', 'textfit'); os.makedirs(OUT, exist_ok=True)
OUT_TS = os.environ.get('OUT_TS') or os.path.join(SONG, 'remotion', 'src', 'le', 'film', 'sections', 'proof30_banner.gen.ts')

# ---- THE COPY: the only place it lives. Exactly as it appears; do not edit a character. ----
POST_NAME = 'Elon Musk'
POST_HANDLE = '@elonmusk'
POST_TEXT = 'Data centers in space looking pretty appealing right now'
POST_DATE = 'Nov 4, 2026'          # verified by the cloud chat 01:27 and on the news page's embed ("November 4, 2026"); no time of day
SOURCE = 'https://x.com/elonmusk/status/2117862462976594112'
# line breaks only (no word changed), chosen per format so no line is a lone word
LINES = {'169': ['Data centers in space looking', 'pretty appealing right now'], '916': ['Data centers in', 'space looking pretty', 'appealing right now']}
for _f, _l in LINES.items(): assert ' '.join(_l) == POST_TEXT, _f

# per format: frame size, card box (px), layout numbers (px), sampling cell and star size per kind
FMT = {
    '169': dict(size=(2560, 1440), box=(400, 96, 2160, 746), rad=70, lw=6, P=72, av=176, av_y=56, name=(50, 104, 86), handle=(146, 86, 60), body=(246, 290, 110, 84), date=(540, 86, 60),
                cell=dict(frame=3, avatar=3, big=3, small=2), star=dict(frame=6.0, avatar=6.2, big=6.2, small=4.6)),
    '916': dict(size=(1080, 1920), box=(108, 280, 972, 890), rad=40, lw=4, P=44, av=124, av_y=40, name=(26, 96, 58), handle=(106, 78, 40), body=(196, 320, 72, 58), date=(510, 78, 40),
                cell=dict(frame=2, avatar=2, big=2, small=2), star=dict(frame=3.3, avatar=3.4, big=3.5, small=3.1)),
}
# what each element is drawn as: (shader part, sampling kind, when it arrives 0..1)
EL = dict(frame=(0, 'frame', 0.0), avatar=(2, 'avatar', 0.10), name=(4, 'big', 0.18), handle=(3, 'small', 0.24), date=(3, 'small', 0.62))


def grid_sample(mask, g, rng, thr=128):
    ys, xs = np.nonzero(mask > thr)
    cell = (ys // g).astype(np.int64) * 100000 + (xs // g).astype(np.int64)
    order = rng.permutation(len(xs)); _, first = np.unique(cell[order], return_index=True); sel = order[first]
    return np.stack([xs[sel] + rng.random(len(sel)), ys[sel] + rng.random(len(sel))], 1)


def design(fmt):
    F = FMT[fmt]; W, H = F['size']; x0, y0, x1, y1 = F['box']; P = F['P']
    rec = textfit.Recorder((W, H), 'post_%s' % fmt)
    new = lambda: (lambda im: (im, ImageDraw.Draw(im)))(Image.new('L', (W, H), 0))
    font = lambda name, px: ImageFont.truetype(os.path.join(FONTS, name), px)
    parts = []   # (mask, shader part, sampling kind, order)
    im, d = new(); d.rounded_rectangle((x0, y0, x1, y1), radius=F['rad'], outline=255, width=F['lw']); parts.append((np.array(im), *EL['frame']))
    ax0, ay0 = x0 + P, y0 + F['av_y']
    im, d = new(); d.ellipse((ax0, ay0, ax0 + F['av'], ay0 + F['av']), fill=255); parts.append((np.array(im), *EL['avatar']))   # a plain disc: no photo
    tx0 = ax0 + F['av'] + round(P * 0.4); xr = x1 - P + 12
    sizes = {}
    for key, text, fname, mn in (('name', POST_NAME, 'InterDisplay-Bold.otf', 58), ('handle', POST_HANDLE, 'Inter-Medium.otf', 34)):
        yo, hh, px = F[key]; im, d = new()
        sizes[key] = textfit.fit_text(d, text, (tx0, y0 + yo, xr, y0 + yo + hh), font(fname, px), min_px=mn, fill=255, align='l', recorder=rec)['size']
        parts.append((np.array(im), *EL[key]))
    yo, hh, px, mn = F['body']; im, d = new()
    r = textfit.fit_text(d, '\n'.join(LINES[fmt]), (x0 + P - 12, y0 + yo, xr, y0 + yo + hh), font('InterDisplay-Bold.otf', px), min_px=mn, fill=255, align='l', line_gap=1.2, recorder=rec)
    assert r['lines'] == LINES[fmt], r['lines']          # the fitter kept my line breaks (no re-wrap, no orphan word)
    sizes['body'] = r['size']; body = np.array(im)
    pitch = round(r['size'] * 1.2); top = r['bbox'][1]
    for i in range(len(LINES[fmt])):                      # written line by line, left to right
        m = np.zeros_like(body); a = int(top + i * pitch - pitch * 0.15); b = int(top + (i + 1) * pitch - pitch * 0.15) if i + 1 < len(LINES[fmt]) else H
        m[max(a, 0) if i else 0:b] = body[max(a, 0) if i else 0:b]; parts.append((m, 4, 'big', 0.34 + 0.085 * i))
    yo, hh, px = F['date']; im, d = new()
    sizes['date'] = textfit.fit_text(d, POST_DATE, (x0 + P - 12, y0 + yo, xr, y0 + yo + hh), font('Inter-Medium.otf', px), min_px=34, fill=255, align='l', recorder=rec)['size']
    parts.append((np.array(im), *EL['date']))
    assert sum(int((p[0] > 128).sum()) for p in parts[4:4 + len(LINES[fmt])]) == int((body > 128).sum()), 'body split lost ink'
    probs = rec.problems(); rec.save(OUT)
    assert not probs, probs
    Image.fromarray(np.maximum.reduce([p[0] for p in parts])).save(os.path.join(OUT, 'post_%s.png' % fmt))
    print(fmt, 'text px:', sizes, 'problems:', len(probs))
    return parts


def build(fmt, seed):
    F = FMT[fmt]; W, H = F['size']; A = W / H; rng = np.random.default_rng(seed); parts = design(fmt)
    x0, y0, x1, y1 = F['box']
    T, Pn, O, S = [], [], [], []
    for m, part, kind, order in parts:
        p = grid_sample(m, F['cell'][kind], rng)
        T.append(p); Pn.append(np.full(len(p), part)); O.append(np.full(len(p), order)); S.append(np.full(len(p), F['star'][kind]))
    T = np.concatenate(T); Pn = np.concatenate(Pn); O = np.concatenate(O); S = np.concatenate(S); K = len(T)
    sx = lambda x: (x / W * 2 - 1) * A; sy = lambda y: 1 - y / H * 2                 # px -> screen units (y up, half height = 1)
    tx, ty = sx(T[:, 0]), sy(T[:, 1])
    # homes: stars of the sky above her (never from behind her limb), nearer the card = likelier
    hx = (rng.random(K) * 2 - 1) * A * 1.06; hy = -0.12 + 1.2 * rng.random(K) ** 0.8
    ao = np.argsort(hx + rng.normal(0, 0.11, K)); to = np.argsort(tx + rng.normal(0, 0.07, K))   # pair by x rank: the streams do not cross
    HX = np.zeros(K); HY = np.zeros(K); HX[to] = hx[ao]; HY[to] = hy[ao]
    xn = (T[:, 0] - x0) / (x1 - x0)
    dl = O * 0.9 + 0.50 * xn * (O > 0.3) + 0.22 * xn * (O <= 0.3) + rng.random(K) * 0.20
    dl = dl / dl.max()
    curl = np.clip(0.16 + rng.normal(0, 0.07, K), -0.1, 0.4)
    arr = np.stack([HX, HY, tx, ty, dl, curl, S / 10.0, Pn / 10.0], 1)
    q = np.clip(np.round(arr * 10000), -32767, 32767).astype('<i2')
    print(fmt, 'stars:', K)
    return dict(n=int(K), b64=base64.b64encode(q.tobytes()).decode())


if __name__ == '__main__':
    out = {f: build(f, 5 + i) for i, f in enumerate(FMT)}
    box = {f: [((FMT[f]['box'][0] / FMT[f]['size'][0]) * 2 - 1) * FMT[f]['size'][0] / FMT[f]['size'][1], 1 - FMT[f]['box'][3] / FMT[f]['size'][1] * 2,
               ((FMT[f]['box'][2] / FMT[f]['size'][0]) * 2 - 1) * FMT[f]['size'][0] / FMT[f]['size'][1], 1 - FMT[f]['box'][1] / FMT[f]['size'][1] * 2] for f in FMT}
    with open(OUT_TS, 'w') as fh:
        fh.write('// GENERATED by living_earth/proof30_post.py (the feed post as star targets; layout measured by studio.textfit). Do not edit.\n')
        fh.write('// The copy is the real post, word for word (source: %s): %s / %s / "%s" / %s. No logo, no badge, no photo, nothing else attributed.\n' % (SOURCE, POST_NAME, POST_HANDLE, POST_TEXT, POST_DATE))
        fh.write('// per star, 8 int16 / 10000: home x, y, target x, y (screen units, y up), delay 0..1, curl, size / 10, part / 10 (0 frame, 2 avatar disc, 3 handle + date, 4 name + text)\n')
        fh.write('export const BANNER: Record<string, { n: number; b64: string; box: number[] }> = ' + json.dumps({f: dict(out[f], box=[round(v, 4) for v in box[f]]) for f in out}) + ';\n')
    print('wrote', OUT_TS)
