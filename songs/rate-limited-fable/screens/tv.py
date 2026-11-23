"""The 4:41 TV (rl_screens): the two approved pictures, in motion. Headlines word for word as approved, with source and date:
  'Jensen Huang summoned to testify before Congress after resigning as Nvidia CEO' (Source: CNN, Nov 11, 2026)
  'Microsoft Outlook outage stretches on for hours' (ABC News, Nov 13, 2026; verified Nov 21. NOTE: tex/tv_news2.png still carries the old
   'stretches on' / ABC7 card; the delivered plates were patched by workers/rl10_fix/tools/headline10.py, whose card_tex() is the corrected card)
The headline cards are the approved textures' own pixels (build/pitch2/tex/tv_news.png, tv_news2.png); only what moves is new:
  9A  the approved picture; light travels along the chip's traces, the chip breathes
  9C  the headline changes (old line up and out, new line up and in) and the party climbs up from below the card
  9D  the party, going: the crowd bounces on the beat, balloons bob, streamers sway, confetti falls
  9G  the party frozen, everyone still (one held frame)
In the approved party picture the crowd's hats cross '4:41 AM'; here a soft scrim keeps LIVE and the time readable.
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

S = 1.5; TW, TH = 2250, 1290; TOP = int(438 * S); KK = 2; U = S * KK
TEX = os.path.join(K.SONG, 'build', 'pitch2', 'tex')
_C = {}


def A():
    if 'A' not in _C: _C['A'] = Image.open(os.path.join(TEX, 'tv_news.png')).convert('RGBA')
    return _C['A']


def B():
    if 'B' not in _C: _C['B'] = Image.open(os.path.join(TEX, 'tv_news2.png')).convert('RGBA')
    return _C['B']


def base():
    """the approved studio gradient and light beams (tv_news_r11.base)"""
    if 'base' not in _C:
        y = np.linspace(0, 1, TH)[:, None]; x = np.linspace(0, 1, TW)[None, :]; bg = np.zeros((TH, TW, 3))
        bg[..., 0] = 10 + 18 * x + 8 * y; bg[..., 1] = 22 + 30 * x + 14 * y; bg[..., 2] = 52 + 60 * x + 30 * (1 - y)
        im = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA'); ov = Image.new('RGBA', (TW, TH), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for x0, wd, a in ((180, 150, 26), (520, 90, 18), (820, 220, 22), (1180, 120, 16)):
            d.polygon([(x0 * S, 0), ((x0 + wd) * S, 0), ((x0 + wd - 260) * S, TH), ((x0 - 260) * S, TH)], fill=(120, 170, 255, a))
        im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(18 * S))); _C['base'] = im
    return _C['base']


# ------------------------------------------------------------------ 9A: light along the traces
CX, CY, CR = 1130, 232, 92
TRACES = [(CX + CR + 34, CY - 48, [(90, 0), (140, -50), (250, -50)]), (CX + CR + 34, CY + 24, [(120, 0), (170, 50), (250, 50)]),
          (CX - CR - 34, CY - 24, [(-70, 0), (-120, -60), (-230, -60)]), (CX - CR - 34, CY + 48, [(-60, 0), (-100, 40), (-200, 40)]),
          (CX - 24, CY - CR - 34, [(0, -40), (-50, -90)])]


def _along(path, u):
    segs = list(zip(path[:-1], path[1:])); L = [math.dist(a, b) for a, b in segs]; tot = sum(L); d = u * tot
    for (a, b), l in zip(segs, L):
        if d <= l:
            k = d / l if l else 0; return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        d -= l
    return path[-1]


def tv_9A(t):
    im = A().copy(); gl = Image.new('RGBA', (TW, TOP), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
    for i, (x0, y0, pts) in enumerate(TRACES):
        path = [(x0, y0)] + [(x0 + a, y0 + b) for a, b in pts]
        u = ((t * .62) + i * .23) % 1.0; x, y = _along(path, u); a = math.sin(u * math.pi)
        r = 16 * S; g.ellipse(((x * S) - r, (y * S) - r, (x * S) + r, (y * S) + r), fill=(170, 244, 255, int(200 * a)))
    br = .5 + .5 * math.sin(t * 2 * math.pi / 1.74)                   # the chip breathes, slowly
    g.rounded_rectangle(((CX - CR - 20) * S, (CY - CR - 20) * S, (CX + CR + 20) * S, (CY + CR + 20) * S), radius=int(30 * S), fill=(140, 230, 255, int(40 * br)))
    gl = gl.filter(ImageFilter.GaussianBlur(10 * S))
    im.alpha_composite(gl, (0, 0))
    return K.clamp_white(im)


# ------------------------------------------------------------------ the party, as sprites (our own clay office crowd, as in round 12)
HOOD = [(242, 122, 168), (86, 170, 222), (245, 190, 70), (120, 200, 150), (170, 130, 230)]; HAT = [(245, 190, 70), (242, 122, 168), (120, 200, 150), (86, 170, 222), (255, 255, 255)]
SKIN = (233, 227, 218)


def _person_sprite(sc, k, arms, shade):
    """one guest drawn at 2x, cached; the body runs long below so a bounce never shows its end"""
    key = ('p', round(sc, 3), k, arms, round(shade, 2))
    if key in _C: return _C[key]
    bw, bh, hr = 118 * sc, 230 * sc, 50 * sc; Wd, Hd = int(420 * sc * U), int((bh + hr * 2.6 + 160 * sc + 300) * U)
    im = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); p = ImageDraw.Draw(im); cx = Wd / U / 2; top = hr * 2.6 + 110 * sc; base_ = top + bh
    col = tuple(int(v * shade) for v in HOOD[k % 5]); sk = tuple(int(v * shade) for v in SKIN) + (255,)
    for sgn, (ax, ay) in zip((-1, 1), arms):
        x0, y0 = cx + sgn * bw * .42, top + 34 * sc; x1, y1 = cx + sgn * ax * sc, top - ay * sc
        p.line([(x0 * U, y0 * U), (x1 * U, y1 * U)], fill=col, width=int(40 * sc * U)); p.ellipse(((x0 - 20 * sc) * U, (y0 - 20 * sc) * U, (x0 + 20 * sc) * U, (y0 + 20 * sc) * U), fill=col)
        p.ellipse(((x1 - 23 * sc) * U, (y1 - 23 * sc) * U, (x1 + 23 * sc) * U, (y1 + 23 * sc) * U), fill=sk)
    p.rounded_rectangle(((cx - bw / 2) * U, top * U, (cx + bw / 2) * U, (base_ + 300) * U), radius=int(46 * sc * U), fill=col)
    hy = top - hr * .72; p.ellipse(((cx - hr) * U, (hy - hr) * U, (cx + hr) * U, (hy + hr) * U), fill=sk)
    for sgn in (-1, 1): p.ellipse(((cx + sgn * 17 * sc - 5 * sc) * U, (hy - 6 * sc) * U, (cx + sgn * 17 * sc + 5 * sc) * U, (hy + 6 * sc) * U), fill=(40, 36, 34, 255))
    p.chord(((cx - 19 * sc) * U, (hy - 6 * sc) * U, (cx + 19 * sc) * U, (hy + 30 * sc) * U), start=10, end=170, fill=(40, 36, 34, 255))
    hc = tuple(int(v * shade) for v in HAT[k % 5]); tipx, tipy = cx + 10 * sc, hy - hr - 62 * sc
    p.polygon([((cx - 30 * sc) * U, (hy - hr * .72) * U), ((cx + 34 * sc) * U, (hy - hr * .80) * U), (tipx * U, tipy * U)], fill=hc)
    p.ellipse(((tipx - 10 * sc) * U, (tipy - 10 * sc) * U, (tipx + 10 * sc) * U, (tipy + 10 * sc) * U), fill=(255, 255, 255, 255))
    _C[key] = (im, cx, base_)                                          # anchor: (cx, base_) in 1500-units inside the sprite
    return _C[key]


def _crowd():
    if 'crowd' in _C: return _C['crowd']
    rnd = random.Random(7); out = []; k = 0
    for row, (n, sc, base_, x0, x1, shade) in enumerate(((13, .50, 262, 40, 1460, .74), (10, .68, 338, 70, 1430, .87), (7, .92, 440, 150, 1350, 1.0))):
        for i in range(n):
            cx = x0 + (x1 - x0) * i / (n - 1) + rnd.uniform(-16, 16); s_ = sc * rnd.uniform(.94, 1.06)
            lift = 0
            if cx < 470: s_ = min(s_, .86); lift = 46 if row < 2 else 0          # keep heads clear of LIVE and the time
            arms = ((round(rnd.uniform(60, 125)), round(rnd.uniform(55, 105))), (round(rnd.uniform(60, 125)), round(rnd.uniform(55, 105))))
            out.append(dict(row=row, cx=cx, base=base_ + lift + rnd.uniform(-8, 8), sc=s_, k=k, arms=arms, shade=shade, ph=rnd.uniform(0, 1))); k += 1
    rnd2 = random.Random(11)
    balloons = []
    for j in range(11):
        bx, by, br = 90 + j * 132 + rnd2.uniform(-30, 30), rnd2.uniform(60, 150), rnd2.uniform(34, 46)
        if bx < 470 and by < 190: by += 120
        balloons.append(dict(x=bx, y=by, r=br, col=HOOD[(j * 2 + 1) % 5], ph=rnd2.uniform(0, 6.28), sx=rnd2.uniform(-14, 14)))
    streamers = []
    for j in range(16):
        x = 60 + j * 90 + rnd2.uniform(-25, 25)
        if x < 470: continue
        streamers.append(dict(x=x, col=HOOD[j % 5], L=rnd2.uniform(160, 330), ph=rnd2.uniform(0, 6), dr=rnd2.choice((-1, 1)) * rnd2.uniform(4, 14)))
    conf = [dict(x=rnd2.uniform(30, 1470), y0=rnd2.uniform(-440, 430), w=rnd2.uniform(8, 16), h=rnd2.uniform(5, 9), col=rnd2.choice(HOOD + [(255, 255, 255)]),
                 v=rnd2.uniform(60, 120), rot=rnd2.uniform(0, 180), spin=rnd2.uniform(-260, 260), sway=rnd2.uniform(6, 20), ph=rnd2.uniform(0, 6.28)) for _ in range(330)]
    _C['crowd'] = (out, balloons, streamers, conf)
    return _C['crowd']


BEAT = 0.5785


def party_layer(t, rise=1.0, frozen=False, rows_rise=None):
    """the top region (above the card) at 2x, downsampled: everything a pure function of t. rise 0..1 brings the crowd up from below."""
    people, balloons, streamers, conf = _crowd()
    pl = Image.new('RGBA', (int(TW * KK), int(TOP * KK)), (0, 0, 0, 0)); p = ImageDraw.Draw(pl)
    if 'glow' not in _C:
        gw = Image.new('RGBA', pl.size, (0, 0, 0, 0)); ImageDraw.Draw(gw).ellipse((60 * U, 10 * U, 1440 * U, 660 * U), fill=(255, 214, 150, 90)); _C['glow'] = gw.filter(ImageFilter.GaussianBlur(70 * U))
    g = _C['glow'].copy()
    if rise < 1: g.putalpha(g.getchannel('A').point(lambda v: int(v * rise)))
    pl.alpha_composite(g)
    tt = 0 if frozen else t
    for bl in balloons:                                                # balloons bob on their strings
        by = bl['y'] + 6 * math.sin(tt * 1.7 + bl['ph']) + (1 - rise) * 520; bx = bl['x'] + 4 * math.sin(tt * 1.1 + bl['ph'])
        p.line([(bx * U, (by + bl['r']) * U), ((bx + bl['sx']) * U, (by + bl['r'] + 150) * U)], fill=(230, 232, 240, 200), width=int(2.5 * U))
        p.ellipse(((bx - bl['r']) * U, (by - bl['r'] * 1.15) * U, (bx + bl['r']) * U, (by + bl['r'] * 1.15) * U), fill=tuple(int(v * .86) for v in bl['col']) + (255,))
        p.ellipse(((bx - bl['r'] * .55) * U, (by - bl['r'] * .8) * U, (bx - bl['r'] * .15) * U, (by - bl['r'] * .3) * U), fill=(255, 255, 255, 90))
    for q in people:                                                   # rows back to front; each guest bounces on the beat
        spr, acx, abase = _person_sprite(q['sc'], q['k'], q['arms'], q['shade'])
        ph = ((tt / BEAT) + q['ph'] * .35) % 1.0; bounce = 0 if frozen else -abs(math.sin(ph * math.pi)) * (16 + 10 * q['row']) * q['sc']
        rr = rise if rows_rise is None else rows_rise[q['row']]
        dy = (1 - rr) * (260 + 120 * q['row'])
        x = (q['cx'] - acx) * U; y = (q['base'] - abase + bounce + dy) * U
        pl.alpha_composite(spr, (int(x), int(y))) if x >= 0 and y >= 0 and x + spr.width <= pl.width and y + spr.height <= pl.height else K._paste_clip(pl, spr, int(x), int(y))
    if rise > .3:
        for s_ in streamers:                                           # streamers sway
            pts = []
            for i in range(40):
                u = i / 39; sw = 24 * (.35 + .65 * u) * math.sin(u * 7 + s_['ph'] - (0 if frozen else tt * 2.4))       # a wave travelling down from the top
                pts.append(((s_['x'] + sw + u * s_['dr']) * U, (u * s_['L'] * min(1, (rise - .3) / .7)) * U))
            p.line(pts, fill=s_['col'] + (255,), width=int(9 * U), joint='curve')
        for c in conf:                                                 # confetti falls through the top region and wraps
            y = ((c['y0'] + (0 if frozen else tt * c['v'])) % 880) - 440 + (0 if rise >= 1 else 0)
            if y < 10 or y > TOP / S - 6: continue
            x = c['x'] + c['sway'] * math.sin((0 if frozen else tt) * 2 + c['ph'])
            if x < 470 and y < 130: continue
            a = math.radians(c['rot'] + (0 if frozen else tt * c['spin'])); w, h = c['w'] * U / 2, c['h'] * U / 2 * abs(math.cos(a * .7)) + 1.5 * U
            ca, sa = math.cos(a), math.sin(a); cxp, cyp = x * U, y * U
            p.polygon([(cxp + dx * ca - dy * sa, cyp + dx * sa + dy * ca) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))], fill=c['col'] + (int(255 * min(1, rise)),))
    return pl.resize((TW, TOP), Image.LANCZOS)


def live_badge(im):
    """LIVE and the time over a soft scrim so the crowd never crosses them"""
    sc = Image.new('RGBA', (TW, TOP), (0, 0, 0, 0)); ImageDraw.Draw(sc).rounded_rectangle((40 * S, 34 * S, 420 * S, 132 * S), radius=int(40 * S), fill=(10, 20, 44, 225))
    im.alpha_composite(sc.filter(ImageFilter.GaussianBlur(18 * S)), (0, 0))
    d = ImageDraw.Draw(im); ft = K.font('bold', int(40 * S))
    K.rrect(im, (60 * S, 50 * S, 206 * S, 116 * S), 12 * S, (206, 32, 44, 255))
    d.text((133 * S, 83 * S), 'LIVE', font=ft, fill='white', anchor='mm'); d.text((232 * S, 83 * S), '4:41 AM', font=ft, fill=(230, 236, 246, 255), anchor='lm')


def card_lines(src):
    """the approved headline card's text block (its own pixels), and the card box"""
    return src.crop((int(78 * S), int(440 * S), int(TW - 60 * S), int(800 * S)))


def tv_party(t, rise=1.0, frozen=False, rows_rise=None, card='B', swap=None, bg=None):
    im = base().copy()
    if bg is not None: im.alpha_composite(bg, (0, 0))
    im.alpha_composite(party_layer(t, rise, frozen, rows_rise), (0, 0))
    lower = B().crop((0, TOP, TW, TH)); im.paste(lower, (0, TOP))
    if swap is not None:                                                # the headline change: old text up and out, new text up and in
        x0, y0, x1, y1 = int(78 * S), int(440 * S), int(TW - 60 * S), int(800 * S)
        cardbg = Image.new('RGBA', (x1 - x0, y1 - y0), (245, 246, 248, 255)); oldt, newt = card_lines(A()), card_lines(B())
        e1 = K.ease_io(K.clamp(swap / .26)); e2 = K.ease_out(K.clamp((swap - .30) / .36))          # out, then in: never both
        if e1 < 1:
            o = oldt.copy(); o.putalpha(o.getchannel('A').point(lambda v: int(v * (1 - e1)))); cardbg.alpha_composite(o, (0, int(-e1 * 60)))
        if e2 > 0:
            n_ = newt.copy(); n_.putalpha(n_.getchannel('A').point(lambda v: int(v * e2))); cardbg.alpha_composite(n_, (0, int((1 - e2) * 60)))
        # keep the card's own white where text slid away
        im.paste(cardbg.convert('RGB'), (x0, y0))
    live_badge(im)
    return K.clamp_white(im)


def tv_9C(t, sid='9C'):
    """before the change: the approved first picture; the change on beat 2; the party climbs up, rows staggered, over the studio as it fades"""
    s = K.shot(sid); bts = K.beats_in(sid); tc = bts[1] if len(bts) > 1 else s['start'] + .58
    if t < tc:
        return tv_9A(t)
    x = t - tc
    rows = [K.spring(t, tc + .10 + .12 * r, 1.9, .55) for r in range(3)]
    rows = [min(1.0, max(0.0, v)) if v < 1 else v for v in rows]
    rise = K.ease_out(K.clamp(x / .6))
    # the studio picture fades out behind the crowd as it climbs up (the crowd is always in front)
    fade_old = 1 - K.ease_io(K.clamp((x - .15) / .5))
    bg = None
    if fade_old > 0:
        bg = tv_9A(t).crop((0, 0, TW, TOP)); bg.putalpha(int(255 * fade_old))
    return tv_party(t, rise=rise, rows_rise=rows, swap=x, bg=bg)


def tv_9D(t):
    return tv_party(t)
