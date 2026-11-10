"""Real headlines made of stars (earth_news, Nov 9 2026). Her words: "current events and actual news is always welcome. but exactly
as they appear". Every string comes from build/le_news/VERIFIED.md (fetched from the live pages); nothing is typed here.
    .venv/bin/python living_earth/le_news.py   ->  remotion/src/le/film/news/headlines.gen.ts (strings, timing, boxes)
                                                   remotion/src/le/film/news/stars.gen.ts     (star targets per headline + format)
                                                   build/le_news/textfit_final/textfit_news_<id>_<fmt>.json + news_<id>_<fmt>.png
Layout per headline: a thin rule, the outlet (small), the headline (large, never shortened), the date (small). Plain Inter: no outlet
wordmarks, no logos. PLACE below is the only thing to tune: which headlines, the lyric each answers, and the empty sky it sits in."""
import os, sys, re, json, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); STUDIO = os.path.dirname(os.path.dirname(SONG))
sys.path.insert(0, STUDIO)
from studio import textfit
FONTS = os.path.join(STUDIO, 'assets', 'fonts')
VERIFIED = os.path.join(SONG, 'build', 'le_news', 'VERIFIED.md')
OUT = os.path.join(SONG, 'build', 'le_news', 'textfit_final')
GEN = os.path.join(SONG, 'remotion', 'src', 'le', 'film', 'news')
SIZE = {'169': (2560, 1440), '916': (1080, 1920)}
MIN_PX = {'169': 46, '916': 34}            # 34 px at 1080p = 45.3 px in the 2560x1440 master; 34 px in the 1080-wide 9:16
CELL = {'169': dict(rule=3, outlet=2.4, head=2.2, date=2.4), '916': dict(rule=2, outlet=1.6, head=1.6, date=1.6)}   # sampling grid (px): one star per cell of ink
STAR = {'169': dict(rule=5.6, outlet=5.0, head=5.6, date=5.0), '916': dict(rule=3.2, outlet=3.0, head=3.3, date=3.0)}   # engine px at 1440 high
PART = dict(rule=0, outlet=1, head=2, date=3)
TIN, TOUT = 0.9, 0.7                       # fly in / fly out (s); the hold between them is the fully formed, readable time

# ---- THE PLACEMENT (tune here). at = the moment the headline is fully formed (an anchor of film/anchor.ts).
# per format: x, y = top left of the block (px in the master), w = widest the text may run, hl / sm = headline / outlet+date px.
PLACE = [
    # chorus 1, the sun shot (frames 1649-1777, one continuous shot: dark sky over her limb, the sun low right). "Suncatcher" answers "chase the sun".
    dict(id='npr_suncatcher', at='chorus1/L4+0.04', lyric='Go on, chase the sun all day', tin=0.65, tout=0.27,
         f169=dict(x=190, y=150, w=1500, hl=104, sm=58), f916=dict(x=110, y=500, w=850, hl=58, sm=38)),
    # NOT PLACED (verified, no clean slot tonight; each needs its full hold on empty sky, and the film cuts about every 2.2 s):
    #   aj_merge ("Pack your GPUs and go"): both rack shots fill the sky (chorus 2: a row of racks x -1.5..1.5; 9:16: y 0.12-0.52 in both choruses).
    #   bbg_2027 ("Ooh, off you go"): top right of post 1 is 3.5 s (needs 3.75 s + in/out) and the text would sit on her limb glow or beside his spark.
    #   star_eyes ("midnight appetite"): the CHIPS / SNACKS / HUM / LIGHT boxes fill that sky.   w247_ballot: 32 words = 9 s; no 9 s of empty sky.
    # end of chorus 2, the wide pull-back: the question lands right after "Who's gonna cool you down up there? / You've got no atmosphere"
    dict(id='bbg_quicktake', at='chorus2/L8+0.9', lyric="(Who's gonna cool you down up there? You've got no atmosphere) You said you needed space", tin=0.8, tout=0.6,
         f169=dict(x=190, y=150, w=1500, hl=104, sm=58), f916=dict(x=110, y=470, w=850, hl=58, sm=38)),
]
if os.path.exists(os.path.join(HERE, 'le_news_place.json')):       # the tuned placement (same shape as PLACE), kept as data
    PLACE = json.load(open(os.path.join(HERE, 'le_news_place.json'), encoding='utf-8'))


def verified():
    """id -> dict(status, url, headline, outlet, date): the LAST `backticked` run of each line of a block of VERIFIED.md"""
    items, cur = {}, None
    for ln in open(VERIFIED, encoding='utf-8'):
        m = re.match(r'## \d+\. id: (\w+)\. (VERIFIED|UNVERIFIED)', ln)
        if m:
            cur = items.setdefault(m.group(1), {'status': m.group(2)}); continue
        if cur is None:
            continue
        tick = re.findall(r'`([^`]+)`', ln)
        if ln.startswith('- URL:'): cur['url'] = ln.split()[2]
        elif ln.startswith('- Headline'): cur['headline'] = tick[-1]
        elif ln.startswith('- Outlet'): cur['outlet'] = tick[-1]
        elif ln.startswith('- Date'): cur['date'] = tick[-1]
    return items


def hold_for(headline):
    return round(max(2.0, 0.25 * len(headline.split()) + 1.0), 2)


def balance(draw, text, font, max_w):
    """greedy wrap, then the narrowest width that keeps the same number of lines (no orphan word on the last line)"""
    lines = textfit.wrap_lines(draw, text, font, max_w); n = len(lines); w = max_w
    while w > 200:
        t = textfit.wrap_lines(draw, text, font, w - 10)
        if len(t) != n or max(draw.textlength(x, font=font) for x in t) > max_w:
            break
        lines, w = t, w - 10
    return lines


def grid_sample(mask, g, rng, thr=128):
    ys, xs = np.nonzero(mask > thr)
    cell = np.floor(ys / g).astype(np.int64) * 100000 + np.floor(xs / g).astype(np.int64)
    order = rng.permutation(len(xs)); _, first = np.unique(cell[order], return_index=True); sel = order[first]
    return np.stack([xs[sel] + rng.random(len(sel)), ys[sel] + rng.random(len(sel))], 1)


def design(item, v, fmt):
    """-> parts {name: (mask, order per pixel fn)}, the block box (px), the wrapped lines"""
    W, H = SIZE[fmt]; P = item['f' + fmt]; x, y, w, hl, sm = P['x'], P['y'], P['w'], P['hl'], P['sm']
    assert hl >= MIN_PX[fmt] and sm >= MIN_PX[fmt], (item['id'], fmt, 'type under the readable minimum')
    k = hl / 104.0
    f_head = ImageFont.truetype(os.path.join(FONTS, 'InterDisplay-Bold.otf'), hl)
    f_out = ImageFont.truetype(os.path.join(FONTS, 'Inter-SemiBold.otf'), sm)
    f_date = ImageFont.truetype(os.path.join(FONTS, 'Inter-Medium.otf'), sm)
    rw = max(3, round(7 * k)); gap = round(44 * k); tx = x + rw + gap
    new = lambda: (lambda im: (im, ImageDraw.Draw(im)))(Image.new('L', (W, H), 0))
    im0, d0 = new()
    lines = balance(d0, v['headline'], f_head, w)
    assert ' '.join(lines) == v['headline'], 'wrap changed the headline'
    pitch = round(hl * 1.16); y_out = y; y_head = y_out + round(sm * 1.55); y_date = y_head + pitch * len(lines) + round(sm * 0.42)
    y_end = y_date + round(sm * 1.25)
    tw = max([d0.textlength(ln, font=f_head) for ln in lines] + [d0.textlength(v['outlet'], font=f_out), d0.textlength(v['date'], font=f_date)])
    pad = textfit.default_pad(H); box = (x - pad - 2, y - pad - 2, int(tx + tw + pad + 6), y_end + pad + 2)
    rec = textfit.Recorder((W, H), 'news_%s_%s' % (item['id'], fmt))
    parts = {}
    with rec:
        with rec.container(box, 'headline block'):
            im, d = new(); d.text((tx, y_out), v['outlet'], font=f_out, fill=255, anchor='la'); parts['outlet'] = np.array(im)
            im, d = new()
            for i, ln in enumerate(lines):
                d.text((tx, y_head + i * pitch), ln, font=f_head, fill=255, anchor='la')
            parts['head'] = np.array(im)
            im, d = new(); d.text((tx, y_date), v['date'], font=f_date, fill=255, anchor='la'); parts['date'] = np.array(im)
    ink = np.maximum.reduce(list(parts.values())); ys, xs = np.nonzero(ink > 128)
    im, d = new(); d.rounded_rectangle((x, ys.min() - 4, x + rw, ys.max() + 4), radius=rw // 2, fill=255); parts['rule'] = np.array(im)
    probs = rec.problems(); rec.save(OUT)
    assert not probs, probs
    if fmt == '916':   # the 9:16 safe zone: out of the top 13 %, the bottom 30 %, 9 % off each side, and the like/comment column
        from studio.core import SAFE_9x16 as S                 # the studio's safe zone (studio/safezone.py checks lyric lines against the same numbers)
        assert xs.min() >= S['left'] * W and xs.max() <= S['right'] * W and ys.min() >= S['top'] * H and ys.max() <= S['bottom'] * H, (item['id'], 'outside the 9:16 safe zone', xs.min(), xs.max(), ys.min(), ys.max())
        low = ink[int(S['buttons_y'] * H):, int(S['buttons_x'] * W):]
        assert not (low > 128).any(), (item['id'], 'text in the like/comment column')
    else:
        assert xs.min() >= 0.04 * W and xs.max() <= 0.96 * W and ys.min() >= 0.05 * H and ys.max() <= 0.95 * H, (item['id'], 'too close to the 16:9 frame edge')
    Image.fromarray(np.maximum.reduce(list(parts.values()))).save(os.path.join(OUT, 'news_%s_%s.png' % (item['id'], fmt)))
    geo = dict(pitch=pitch, y_head=y_head, n=len(lines), x0=tx, x1=tx + tw, ink=[int(x), int(ys.min()), int(xs.max()), int(ys.max())])
    return parts, geo, lines


def build(item, v, fmt, seed):
    W, H = SIZE[fmt]; A = W / H; rng = np.random.default_rng(seed); parts, geo, lines = design(item, v, fmt)
    T, Pp, O, S = [], [], [], []
    for name, m in parts.items():
        p = grid_sample(m, CELL[fmt][name], rng); xn = (p[:, 0] - geo['x0']) / max(1.0, geo['x1'] - geo['x0'])
        if name == 'rule': o = 0.30 * (p[:, 1] - geo['ink'][1]) / max(1, geo['ink'][3] - geo['ink'][1])
        elif name == 'outlet': o = 0.12 + 0.25 * xn
        elif name == 'head':                                                  # in reading order: line by line, left to right
            li = np.clip(np.floor((p[:, 1] - geo['y_head']) / geo['pitch']), 0, geo['n'] - 1)
            o = 0.40 + (li + xn) / geo['n'] * 1.0
        else: o = 1.42 + 0.20 * xn
        T.append(p); Pp.append(np.full(len(p), PART[name])); O.append(o); S.append(np.full(len(p), STAR[fmt][name]))
    T = np.concatenate(T); Pp = np.concatenate(Pp); O = np.concatenate(O); S = np.concatenate(S); K = len(T)
    sx = lambda x: (x / W * 2 - 1) * A; sy = lambda y: 1 - y / H * 2                 # px -> screen units (y up, half height = 1)
    tx, ty = sx(T[:, 0]), sy(T[:, 1])
    cy = float(ty.mean())                                                             # homes: the sky around where it will stand
    hx = (rng.random(K) * 2 - 1) * A * 1.04; hy = np.clip(cy + (rng.random(K) * 2 - 1) * 0.95, -1.04, 1.04)
    ao = np.argsort(hx + rng.normal(0, 0.11, K)); to = np.argsort(tx + rng.normal(0, 0.07, K))   # pair by x rank: the streams do not cross
    HX = np.zeros(K); HY = np.zeros(K); HX[to] = hx[ao]; HY[to] = hy[ao]
    dl = O + rng.random(K) * 0.14; dl = dl / dl.max()
    curl = np.clip(0.14 + rng.normal(0, 0.06, K), -0.1, 0.36)
    arr = np.stack([HX, HY, tx, ty, dl, curl, S / 10.0, Pp / 10.0], 1)
    q = np.clip(np.round(arr * 10000), -32767, 32767).astype('<i2')
    x0, y0, x1, y1 = geo['ink']
    box = [round(float(sx(x0)), 4), round(float(sy(y1)), 4), round(float(sx(x1)), 4), round(float(sy(y0)), 4)]      # left, bottom, right, top
    print('%-15s %s  stars %6d  lines %d  ink px %s' % (item['id'], fmt, K, len(lines), geo['ink']))
    return dict(n=int(K), b64=base64.b64encode(q.tobytes()).decode()), box, lines


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); os.makedirs(GEN, exist_ok=True)
    V = verified(); news, stars = [], {}
    for fmt in SIZE:
        assert len({(i['f' + fmt]['hl'], i['f' + fmt]['sm']) for i in PLACE if i.get('f' + fmt)}) == 1, 'one headline size and one small size per format'
    for n, item in enumerate(PLACE):
        v = V[item['id']]
        assert v['status'] == 'VERIFIED', item['id'] + ' is not verified: it may not be used'
        boxes, wraps = {}, {}; stars[item['id']] = {}
        for i, fmt in enumerate(SIZE):
            if not item.get('f' + fmt):
                print('%-15s %s  not shown in this format' % (item['id'], fmt)); continue
            stars[item['id']][fmt], boxes[fmt], wraps[fmt] = build(item, v, fmt, 40 + n * 2 + i)
        news.append(dict(id=item['id'], outlet=v['outlet'], headline=v['headline'], date=v['date'], url=v['url'], lyric=item['lyric'], at=item['at'],
                         tin=item.get('tin', TIN), hold=max(hold_for(v['headline']), item.get('hold', 0)), tout=item.get('tout', TOUT), box=boxes, lines=wraps))
    with open(os.path.join(GEN, 'headlines.gen.ts'), 'w', encoding='utf-8') as fh:
        fh.write('// GENERATED by living_earth/le_news.py from build/le_news/VERIFIED.md (headlines exactly as published; fetched Nov 9 2026). Do not edit:\n')
        fh.write('// change the placement in le_news.py / le_news_place.json and re-run. at = the moment the headline is fully formed; it stays `hold` s.\n')
        fh.write('// box = the ink box in screen units [left, bottom, right, top] (y up, half height = 1); lines = how the headline wraps per format.\n')
        fh.write('export type NewsItem = { id: string; outlet: string; headline: string; date: string; url: string; lyric: string; at: string; tin: number; hold: number; tout: number; box: Record<string, number[]>; lines: Record<string, string[]> };\n')
        fh.write('export const NEWS: NewsItem[] = ' + json.dumps(news, ensure_ascii=False, indent=1) + ';\n')
    with open(os.path.join(GEN, 'stars.gen.ts'), 'w', encoding='utf-8') as fh:
        fh.write('// GENERATED by living_earth/le_news.py (each headline as star targets; layout recorded by studio.textfit). Do not edit.\n')
        fh.write('// per star, 8 int16 / 10000: home x, y, target x, y (screen units, y up), delay 0..1, curl, size / 10, part / 10 (0 rule, 1 outlet, 2 headline, 3 date)\n')
        fh.write('export const NEWS_STARS: Record<string, Record<string, { n: number; b64: string }>> = ' + json.dumps(stars) + ';\n')
    print('wrote', GEN)
