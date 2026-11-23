"""Her phone, real-phone standard (rl_phonereal, Nov 15 2026). A reusable kit: device parts + a group-chat app of our own.

Her note (Nov 15 10:39): "The phone screen should look like a phone screen really does. Any apps should also look realistic.
Recognizable immediately not some cheap copy". Realism comes from structure, type, spacing and motion, never branding:
no real app's name, logo, icon set or screen copied; the film's palette (her sent bubbles K.BLUE, night mode at 4 a.m.).

Units: the screen is drawn at 3 px per point (a current 6.7-6.9" phone, 440 x 956 pt = 1320 x 2868 px, 19.5:9, corner 168 px).
Text runs at the phone's larger-text setting (messages 21 pt = 64 px; nothing under 14 pt = 42 px), so it holds up in the frame.
The kit is parametric in screen height (H): the 9:16 frame uses H = 2347 (the screen is the frame), the 3D phone mesh H = 2772.

Parts
  status_bar(im, clock)      time, signal, wifi, battery (low-power amber, 3%)
  home_indicator(im, y)      the bar at the bottom
  keyboard(...)              a dark QWERTY with the prediction row (cached per state)
  banner(im, t, t0, ...)     a notification banner that springs down from the top (overshoot, settle)
  Chat: items (divider, incoming, outgoing, typing, receipt, delivered) laid out from the bottom up, with sender
        grouping (name on the first bubble, avatar + tail on the last), entering items pushing the list up with a scroll
        ease, a translucent nav bar over the list (back chevron + unread count, group avatars, name, member count).
  phone_body(screen)         our own device: black border glass, graphite frame, side buttons, no marks
Every frame is a pure function of t (seconds, audio time).
"""
import math, os, sys
from contextlib import nullcontext
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K
from studio import textfit

SW, SH = 1320, 2868                    # the screen, px (19.5:9)
CORNER = 168                           # screen corner radius, px
U = 3                                  # px per point
STATUS_H = 162                         # 54 pt
NAV_H = 222                            # 74 pt
M = 42                                 # side margin, 14 pt

# night-mode palette (the film's: near-black, her blue, our greys)
BG = (8, 8, 11)
IN_B = (40, 41, 47)                    # incoming bubble
OUT_B = K.BLUE                         # her sent bubbles (approved close frame)
TXT = K.W()
SUB = (150, 151, 160, 255)
DIM = (112, 113, 122, 255)
TINT = (110, 168, 255, 255)            # nav tint
SEP = (46, 47, 54, 255)
AMBER = (240, 178, 60)
FRIENDS = {'Maya': (242, 160, 120), 'Jo': (150, 210, 170), 'Priya': (190, 170, 250)}

F_MSG = ('reg', 64); F_NAME = ('med', 42); F_META = ('med', 42); F_METAB = ('semi', 42)


def F(spec):
    return K.font(*spec)


def _skip():
    r = textfit.Recorder.active
    return r.skip() if (r is not None and not r.paused) else nullcontext()      # nested skips must not un-pause the outer one


# ------------------------------------------------------------------ cached shape masks (4x supersampled)
_MASKS = {}


def rmask(w, h, r):
    k = ('r', int(round(w)), int(round(h)), int(round(r)))
    if k not in _MASKS:
        _MASKS[k] = K.rrect_mask(w, h, r)
    return _MASKS[k]


def rr(im, box, r, fill, alpha=1.0):
    x0, y0, x1, y1 = box
    K.paste_mask(im, rmask(x1 - x0, y1 - y0, r), (x0, y0), fill, alpha)


def _bez(p0, p1, p2, p3, n=14):
    return [((1 - s) ** 3 * p0[0] + 3 * (1 - s) ** 2 * s * p1[0] + 3 * (1 - s) * s * s * p2[0] + s ** 3 * p3[0],
             (1 - s) ** 3 * p0[1] + 3 * (1 - s) ** 2 * s * p1[1] + 3 * (1 - s) * s * s * p2[1] + s ** 3 * p3[1]) for s in np.linspace(0, 1, n)]


def line(im, pts, width, fill, alpha=1.0):
    """an antialiased polyline with round joints"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; pad = width + 4
    x0, y0 = int(min(xs) - pad), int(min(ys) - pad); w, h = int(max(xs) - x0 + pad), int(max(ys) - y0 + pad)
    S = K.SS; m = Image.new('L', (w * S, h * S), 0); d = ImageDraw.Draw(m)
    q = [((x - x0) * S, (y - y0) * S) for x, y in pts]
    d.line(q, fill=255, width=int(width * S), joint='curve')
    for x, y in (q[0], q[-1]):
        d.ellipse((x - width * S / 2, y - width * S / 2, x + width * S / 2, y + width * S / 2), fill=255)
    K.paste_mask(im, m.resize((w, h), Image.LANCZOS), (x0, y0), fill, alpha)


# ------------------------------------------------------------------ the device
def status_bar(im, clock, battery=3, low_power=True):
    d = ImageDraw.Draw(im); cy = 84
    d.text((M + 66, cy), clock, font=K.font('semi', 51), fill=TXT, anchor='lm')
    K.circle(im, SW / 2, cy - 2, 33, (0, 0, 0, 255))                                       # the front camera, a punch hole
    x = SW - M - 28
    # battery: outline, nub, a sliver of fill (low power = amber), the percent beside it
    bx1 = x; bx0 = x - 84
    rr(im, (bx0, cy - 20, bx1, cy + 20), 12, (160, 161, 168, 255), .55); rr(im, (bx0 + 4, cy - 16, bx1 - 4, cy + 16), 9, BG + (255,))
    rr(im, (bx0 + 8, cy - 12, bx0 + 8 + max(8, 68 * battery / 100), cy + 12), 6, (AMBER if low_power else (230, 230, 230)) + (255,))
    rr(im, (bx1 + 4, cy - 7, bx1 + 9, cy + 7), 3, (160, 161, 168, 255), .55)
    d.text((bx0 - 14, cy + 1), f'{battery}%', font=K.font('semi', 42), fill=TXT, anchor='rm')
    pw = K.text_w(f'{battery}%', K.font('semi', 42))
    # wifi: three arcs and a dot
    wx = bx0 - 14 - pw - 62; wy = cy + 18
    for i, r in enumerate((14, 30, 46)):
        if i == 0:
            K.circle(im, wx, wy - 4, 7.5, TXT)
        else:
            K.ring(im, wx, wy, r, 8.5, TXT, start=-135, end=-45)
    # signal: four bars
    sx = wx - 70 - 4 * 15
    for i in range(4):
        h = 13 + i * 8; rr(im, (sx + i * 15, cy + 16 - h, sx + i * 15 + 10, cy + 16), 3, TXT if i < 3 else (90, 91, 98, 255))


def home_indicator(im, y=None, fill=None):
    y = SH - 26 if y is None else y
    rr(im, (SW / 2 - 207, y - 8, SW / 2 + 207, y + 7), 7, fill or (232, 232, 236, 255))


# ------------------------------------------------------------------ keyboard (dark), prediction row on top
KB_BG = (26, 26, 30); KEY = (86, 86, 92); KEY2 = (54, 54, 59); KEY_T = (236, 236, 236, 255)
ROWS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']
KB_H = 912


KB_TALL = 120                          # the 9:16 frame uses the keyboard's 'tall' height (keys +30 px): it lifts the newest messages
                                       # and receipts above half height, out of the Shorts like column (CD should-note, rl_screensreal)


def keyboard_img(suggestions=('I', 'The', "I'm"), shift=True, tall=False):
    """the keyboard as an RGBA image 1320 x KB_H (+KB_TALL when tall) (cached per state)"""
    k = ('kb', tuple(suggestions), shift, tall)
    if k in _MASKS:
        return _MASKS[k]
    kbh = KB_H + (KB_TALL if tall else 0)
    im = Image.new('RGBA', (SW, kbh), KB_BG + (255,)); d = ImageDraw.Draw(im)
    with _skip():
        # prediction row
        cw = SW / 3
        for i, s in enumerate(suggestions):
            d.text((cw * i + cw / 2, 68), s, font=K.font('reg', 52), fill=KEY_T, anchor='mm')
            if i:
                d.line([(cw * i, 34), (cw * i, 102)], fill=(70, 70, 76, 255), width=3)
        top = 140; kh = 126 + (30 if tall else 0); gx = 18; gy = 34; side = 9
        kw = (SW - 2 * side - 9 * gx) / 10
        fk = K.font('reg', 68)
        for r, row in enumerate(ROWS):
            y0 = top + r * (kh + gy); n = len(row)
            x0 = (SW - (n * kw + (n - 1) * gx)) / 2
            if r == 2:
                x0 = side + kw * 1.36 + gx * 1.6 + (SW - 2 * side - 2 * (kw * 1.36 + gx * 1.6) - (n * kw + (n - 1) * gx)) / 2
                # shift and delete
                rr(im, (side, y0, side + kw * 1.36, y0 + kh), 16, ((236, 236, 236) if shift else KEY2) + (255,))
                cx = side + kw * .68; cyy = y0 + kh / 2
                K.poly(im, [(cx, cyy - 28), (cx + 27, cyy + 2), (cx + 12, cyy + 2), (cx + 12, cyy + 26), (cx - 12, cyy + 26), (cx - 12, cyy + 2), (cx - 27, cyy + 2)],
                       ((30, 30, 34) if shift else (236, 236, 236)) + (255,))
                dx1 = SW - side; dx0 = dx1 - kw * 1.36
                rr(im, (dx0, y0, dx1, y0 + kh), 16, KEY2 + (255,))
                cx = (dx0 + dx1) / 2 + 4
                K.poly(im, [(cx - 40, cyy), (cx - 18, cyy - 24), (cx + 30, cyy - 24), (cx + 30, cyy + 24), (cx - 18, cyy + 24)], (236, 236, 236, 255))
                line(im, [(cx - 8, cyy - 11), (cx + 14, cyy + 11)], 5, (40, 40, 44, 255)); line(im, [(cx + 14, cyy - 11), (cx - 8, cyy + 11)], 5, (40, 40, 44, 255))
            for i, ch in enumerate(row):
                kx = x0 + i * (kw + gx)
                K.shadow(im, (kx, y0, kx + kw, y0 + kh), 16, 1, (0, 3), .5)
                rr(im, (kx, y0, kx + kw, y0 + kh), 16, KEY + (255,))
                d.text((kx + kw / 2, y0 + kh / 2 + 2), ch.upper() if shift else ch, font=fk, fill=KEY_T, anchor='mm')
        # bottom row: 123, space, return
        y0 = top + 3 * (kh + gy); w123 = kw * 2.2 + gx; wret = kw * 2.2 + gx
        rr(im, (side, y0, side + w123, y0 + kh), 16, KEY2 + (255,)); d.text((side + w123 / 2, y0 + kh / 2), '123', font=K.font('reg', 50), fill=KEY_T, anchor='mm')
        sx0 = side + w123 + gx; sx1 = SW - side - wret - gx
        rr(im, (sx0, y0, sx1, y0 + kh), 16, KEY + (255,)); d.text(((sx0 + sx1) / 2, y0 + kh / 2), 'space', font=K.font('reg', 50), fill=KEY_T, anchor='mm')
        rr(im, (SW - side - wret, y0, SW - side, y0 + kh), 16, KEY2 + (255,)); d.text((SW - side - wret / 2, y0 + kh / 2), 'return', font=K.font('reg', 50), fill=KEY_T, anchor='mm')
        # the strip under the keys: emoji (left), dictation (right), home indicator
        by = y0 + kh + 78
        K.ring(im, 104, by, 34, 6, (190, 190, 196, 255)); K.circle(im, 92, by - 9, 5, (190, 190, 196, 255)); K.circle(im, 116, by - 9, 5, (190, 190, 196, 255))
        K.ring(im, 104, by + 2, 18, 5, (190, 190, 196, 255), start=20, end=160)
        mic(im, SW - 104, by, 1.0, (190, 190, 196, 255))
    home_indicator(im, kbh - 26)
    _MASKS[k] = im
    return im


def mic(im, cx, cy, s, fill):
    rr(im, (cx - 11 * s, cy - 28 * s, cx + 11 * s, cy + 6 * s), 11 * s, fill)
    K.ring(im, cx, cy - 6 * s, 21 * s, 5 * s, fill, start=10, end=170)
    rr(im, (cx - 2.5 * s, cy + 14 * s, cx + 2.5 * s, cy + 26 * s), 2, fill)


# ------------------------------------------------------------------ notification banner (for 3C / 6B / 8D later)
def banner(im, t, t0, app, title, body, when='now', icon=(120, 170, 255), y_rest=60, rec=None):
    """slides down from above the screen on a spring (one small overshoot, settle); app icon is a plain tile of our own"""
    if t < t0:
        return
    p = K.spring(t, t0, 2.6, .55); h = 300; x0, x1 = M - 10, SW - M + 10
    y = -h - 40 + (y_rest + h + 40) * p
    lay = Image.new('RGBA', (SW, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    K.shadow(lay, (x0, 20, x1, 20 + h), 72, 26, (0, 10), .45)
    rr(lay, (x0, 20, x1, 20 + h), 72, (44, 45, 52, 255), .96)
    rr(lay, (x0 + 42, 20 + 48, x0 + 42 + 120, 20 + 168), 30, icon + (255,))
    with _skip():
        d.text((x0 + 196, 20 + 76), title, font=K.font('semi', 48), fill=TXT, anchor='lm')
        d.text((x1 - 48, 20 + 76), when, font=K.font('reg', 42), fill=SUB, anchor='rm')
        d.text((x0 + 196, 20 + 146), body, font=K.font('reg', 48), fill=TXT, anchor='lm')
        d.text((x0 + 196, 20 + 214), app, font=K.font('reg', 42), fill=SUB, anchor='lm')
    K._paste_sub(im, lay, 0, y - 20)
    if rec is not None and p > .999:
        for (xy, txt, f, anc) in (((x0 + 196, y + 76), title, K.font('semi', 48), 'lm'), ((x0 + 196, y + 146), body, K.font('reg', 48), 'lm')):
            rec.add(txt, d.textbbox(xy, txt, font=f, anchor=anc), (x0, y, x1, y + h), 'banner')


# ------------------------------------------------------------------ chat parts
def wrap(txt, f, maxw):
    lines, cur = [], ''
    for w in txt.split(' '):
        tt = (cur + ' ' + w).strip()
        if K.text_w(tt, f) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = tt
    return lines + [cur]


PADX, PADY, LH = 40, 26, 80
MAXW = 1040


def bubble_size(txt):
    f = F(F_MSG); lines = wrap(txt, f, MAXW - 2 * PADX)
    return int(max(K.text_w(l, f) for l in lines) + 2 * PADX), int(LH * len(lines) + 2 * PADY), lines


def bubble_img(txt, color, side, tail):
    """the bubble as an RGBA sprite (w + 24 for the tail); side 'in' (tail bottom-left) or 'out' (bottom-right)"""
    w, h, lines = bubble_size(txt); T = 24
    S = K.SS; m = Image.new('L', ((w + T) * S, h * S), 0); d = ImageDraw.Draw(m)
    bx0 = T if side == 'in' else 0
    d.rounded_rectangle((bx0 * S, 0, (bx0 + w) * S - 1, h * S - 1), radius=min(h / 2, 60) * S, fill=255)
    if tail:
        # the tail: grows out of the bottom corner and curls under
        if side == 'in':
            x0, y1 = bx0, h
            pts = [(x0 + 64, y1 - 64), (x0, y1 - 64)] + _bez((x0, y1 - 30), (x0, y1 - 8), (x0 - 10, y1 - 1), (x0 - 22, y1)) + \
                  _bez((x0 - 22, y1), (x0 - 2, y1 + .5), (x0 + 10, y1 - 4), (x0 + 22, y1 - 9)) + [(x0 + 44, y1 - 1), (x0 + 64, y1)]
        else:
            x1, y1 = bx0 + w, h
            pts = [(x1 - 64, y1 - 64), (x1, y1 - 64)] + _bez((x1, y1 - 30), (x1, y1 - 8), (x1 + 10, y1 - 1), (x1 + 22, y1)) + \
                  _bez((x1 + 22, y1), (x1 + 2, y1 + .5), (x1 - 10, y1 - 4), (x1 - 22, y1 - 9)) + [(x1 - 44, y1 - 1), (x1 - 64, y1)]
        d.polygon([(x * S, y * S) for x, y in pts], fill=255)
    m = m.resize((w + T, h), Image.LANCZOS)
    im = Image.new('RGBA', (w + T, h), color + (255,)); im.putalpha(m)
    return im, bx0, w, h, lines


def avatar(im, cx, cy, r, name, ring_col=None):
    c = FRIENDS[name]
    if ring_col is not None:
        K.circle(im, cx, cy, r + 6, ring_col + (255,))
    # a soft top-to-bottom shade, like a contact monogram
    K.circle(im, cx, cy, r, tuple(int(v * .86) for v in c) + (255,)); K.circle(im, cx, cy - r * .06, r * .94, c + (255,))
    with _skip():
        ImageDraw.Draw(im).text((cx, cy + 1), name[0], font=K.font('semi', int(r * .95)), fill=(22, 22, 28, 255), anchor='mm')


def typing_dots(im, x0, y1, t, a=1.0):
    """the typing bubble: three dots in a travelling pulse, with the tail"""
    w, h = 196, 128
    spr = Image.new('RGBA', (w + 24, h), (0, 0, 0, 0))
    b, bx0, _, _, _ = bubble_img('xx', IN_B, 'in', True)
    b = b.resize((w + 24, h), Image.LANCZOS); spr.alpha_composite(b)
    for i in range(3):
        ph = (t * 1.5 - i * .18) % 1.0; k = .5 + .5 * math.cos(2 * math.pi * min(ph / .6, 1.0)) if ph < .6 else 0.0
        K.circle(spr, 24 + 54 + i * 44, h / 2 - 3 * (1 - k), 13, (150, 151, 160, 255), .38 + .62 * (1 - k) * 1)
    K.sprite_scaled(im, spr, (x0 - 24, y1), (0, 1), 1, a)


class Item:
    def __init__(self, kind, text='', who=None, t_in=None, t_out=None, h_from=0):
        self.kind, self.text, self.who, self.t_in, self.t_out, self.h_from = kind, text, who, t_in, t_out, h_from
        self.first = self.last = True


def group(items):
    for i, it in enumerate(items):
        if it.kind != 'in':
            continue
        prev = next((p for p in reversed(items[:i]) if p.kind not in ('receipt',)), None)
        nxt = items[i + 1] if i + 1 < len(items) else None
        it.first = not (prev and prev.kind == 'in' and prev.who == it.who)
        it.last = not (nxt and nxt.kind == 'in' and nxt.who == it.who)
    for i, it in enumerate(items):
        if it.kind == 'out':
            nxt = items[i + 1] if i + 1 < len(items) else None
            it.last = not (nxt and nxt.kind == 'out')
    return items


AV_R = 40; BX = M + 2 * AV_R + 26           # incoming bubbles start here


def item_h(it):
    if it.kind == 'div':
        return 124
    if it.kind == 'in':
        return (56 if it.first else 0) + bubble_size(it.text)[1] + (30 if it.last else 8)
    if it.kind == 'out':
        return bubble_size(it.text)[1] + (30 if it.last else 8)
    if it.kind == 'typing':
        return 128 + 30
    if it.kind in ('receipt', 'delivered'):
        return 62
    return 0


def scroll_p(t, t0):
    """the list's push when an item arrives: a critically-damped-looking spring (no visible overshoot), ~0.35 s"""
    return min(1.0, K.spring(t, t0, 1.9, .88))


def draw_item(lay, it, top, t, entering, rec_ok):
    d = ImageDraw.Draw(lay); h = item_h(it)
    if it.kind == 'div':
        day, _, rest = it.text.partition(' ')
        fb, fr = F(F_METAB), F(F_META); w = K.text_w(day + ' ', fb) + K.text_w(rest, fr); x = SW / 2 - w / 2; y = top + 62
        if True:
            d.text((x, y), day, font=fb, fill=SUB, anchor='lm'); d.text((x + K.text_w(day + ' ', fb), y), rest, font=fr, fill=SUB, anchor='lm')
        return
    if it.kind in ('receipt', 'delivered'):
        a = K.fade(t, it.t_in, .14) if it.t_in is not None else 1.0
        if a <= 0:
            return
        f = F(F_META)
        if a >= 1:
            if True:
                d.text((SW - M - 6, top + 24), it.text, font=f, fill=DIM, anchor='rm')
        else:
            l2 = Image.new('RGBA', (SW, h), (0, 0, 0, 0)); ImageDraw.Draw(l2).text((SW - M - 6, 24), it.text, font=f, fill=DIM, anchor='rm')
            l2.putalpha(l2.getchannel('A').point(lambda v: int(v * a))); lay.alpha_composite(l2, (0, int(top)))
        return
    if it.kind == 'typing':
        typing_dots(lay, BX, top + 128, t, 1.0 if it.t_in is None else K.fade(t, it.t_in, .12))
        avatar(lay, M + AV_R, top + 128 - AV_R, AV_R, it.who)
        return
    side = it.kind
    spr, bx0, w, hb, lines = bubble_img(it.text, IN_B if side == 'in' else OUT_B, side, it.last)
    y_b = top + (56 if side == 'in' and it.first else 0)
    if side == 'in':
        if it.first:
            if True:
                d.text((BX + 30, top + 26), it.who, font=F(F_NAME), fill=SUB, anchor='lm')
        if it.last:
            avatar(lay, M + AV_R, y_b + hb - AV_R, AV_R, it.who)
        x_left = BX
    else:
        x_left = SW - M - w
    sc, a = 1.0, 1.0
    if entering and it.t_in is not None:
        sc = .82 + .18 * K.spring(t, it.t_in, 3.4, .55); a = K.fade(t, it.t_in, .08)
    tc = TXT
    if sc >= .999 and a >= .999:
        lay.alpha_composite(spr, (int(x_left - bx0), int(y_b)))
        with (rec_ok.container((x_left, y_b, x_left + w, y_b + hb), 'bubble') if rec_ok else nullcontext()):
            for i, l in enumerate(lines):
                d.text((x_left + PADX, y_b + PADY + LH * i + LH / 2), l, font=F(F_MSG), fill=tc, anchor='lm')
    else:
        s2 = spr.copy(); sd = ImageDraw.Draw(s2)
        with _skip():
            for i, l in enumerate(lines):
                sd.text((bx0 + PADX, PADY + LH * i + LH / 2), l, font=F(F_MSG), fill=tc, anchor='lm')
        piv = (0, 1) if side == 'in' else (1, 1)
        anchor = (x_left - bx0, y_b + hb) if side == 'in' else (x_left + w + 24, y_b + hb)
        K.sprite_scaled(lay, s2, anchor, piv, sc, a)


def layout(items, t, bottom):
    """bottom-up placement; returns [(item, top, entering)] for visible items"""
    vis = [it for it in items if (it.t_in is None or t >= it.t_in) and (it.t_out is None or t < it.t_out)]
    out = []; y = bottom
    for it in reversed(vis):
        h = item_h(it)
        if it.t_in is not None:
            p = scroll_p(t, it.t_in); h_eff = it.h_from + (h - it.h_from) * p
        else:
            p, h_eff = 1.0, h
        top = y - h_eff
        out.append((it, top, p < .999)); y = top
        if y < -400:
            break
    return out


def nav_bar(im, content, name='Brunch Committee', members='4 members', unread='12', rec=None):
    """translucent: the list shows through, blurred and darkened"""
    y1 = STATUS_H + NAV_H
    region = content.crop((0, 0, SW, y1 + 60)).filter(ImageFilter.GaussianBlur(28)).crop((0, 0, SW, y1))
    tint = Image.new('RGBA', (SW, y1), (18, 18, 22, 222)); region.alpha_composite(tint)
    im.alpha_composite(region, (0, 0))
    ImageDraw.Draw(im).line([(0, y1), (SW, y1)], fill=SEP, width=2)
    cy = STATUS_H + NAV_H / 2
    line(im, [(M + 34, cy - 30), (M + 6, cy), (M + 34, cy + 30)], 9, TINT)          # back chevron
    d = ImageDraw.Draw(im)
    d.text((M + 54, cy + 1), unread, font=K.font('reg', 50), fill=TINT, anchor='lm')
    uw = K.text_w(unread, K.font('reg', 50))
    ax = M + 54 + uw + 74
    for i, n in enumerate(('Maya', 'Jo', 'Priya')):
        avatar(im, ax + i * 50, cy, 38, n, ring_col=(20, 20, 24))
    nx = ax + 2 * 50 + 38 + 34
    if True:
        d.text((nx, cy - 26), name, font=K.font('semi', 50), fill=TXT, anchor='lm')
    if True:
        d.text((nx, cy + 32), members, font=K.font('reg', 42), fill=SUB, anchor='lm')
    # video call: a camera body and its lens wedge (drawn, our own)
    vx = SW - M - 96
    line(im, [(vx - 34, cy - 22), (vx + 18, cy - 22), (vx + 18, cy + 22), (vx - 34, cy + 22), (vx - 34, cy - 22)], 7, TINT)
    K.poly(im, [(vx + 26, cy - 6), (vx + 50, cy - 22), (vx + 50, cy + 22), (vx + 26, cy + 6)], TINT)


INPUT_H = 150


def input_bar(im, y0, text='', caret_on=True, send_press=0.0, rec=None):
    """+ button, the field (placeholder or what she typed), dictation or the send button"""
    d = ImageDraw.Draw(im); cy = y0 + INPUT_H / 2
    K.circle(im, M + 50, cy, 50, (44, 45, 52, 255))
    line(im, [(M + 50, cy - 22), (M + 50, cy + 22)], 7, (200, 200, 206, 255)); line(im, [(M + 28, cy), (M + 72, cy)], 7, (200, 200, 206, 255))
    fx0, fx1 = M + 128, SW - M; fy0, fy1 = cy - 58, cy + 58
    rr(im, (fx0, fy0, fx1, fy1), 58, (62, 63, 70, 255)); rr(im, (fx0 + 3, fy0 + 3, fx1 - 3, fy1 - 3), 55, (16, 16, 20, 255))
    f = K.font('reg', 54)
    if text:
        with (rec.container((fx0, fy0, fx1 - 110, fy1), 'input field') if rec else nullcontext()):
            d.text((fx0 + 40, cy), text, font=f, fill=TXT, anchor='lm')
        s = 1 - .12 * send_press
        K.circle(im, fx1 - 56, cy, 40 * s, OUT_B + (255,))
        line(im, [(fx1 - 56, cy + 18 * s), (fx1 - 56, cy - 18 * s)], 7, (240, 240, 240, 255))
        line(im, [(fx1 - 72 * 1, cy - 3 * s), (fx1 - 56, cy - 19 * s), (fx1 - 40, cy - 3 * s)], 7, (240, 240, 240, 255))
    else:
        with (rec.container((fx0, fy0, fx1 - 110, fy1), 'input field') if rec else nullcontext()):
            d.text((fx0 + 40, cy), 'Message', font=f, fill=DIM, anchor='lm')
        mic(im, fx1 - 60, cy + 4, .95, (150, 151, 160, 255))
    if caret_on:
        cx = fx0 + 36 + (K.text_w(text, f) + 4 if text else 0)
        rr(im, (cx, cy - 34, cx + 5, cy + 34), 2, OUT_B + (255,))


# ------------------------------------------------------------------ the chat screen (one function for any shot)
def chat_screen(t, items, clock, H=SH, field_text='', field_until=None, send_t=None, kb=True, rec=None):
    if True:
        im = Image.new('RGBA', (SW, H), BG + (255,))
        tall = (H == H9); kb_h = KB_H + (KB_TALL if tall else 0)
        kb_top = H - kb_h if kb else H
        in_top = kb_top - INPUT_H - (0 if kb else 70)
        list_bottom = in_top - 6
        lay = Image.new('RGBA', (SW, H), (0, 0, 0, 0))
        placed = layout(items, t, list_bottom)
        content_top = STATUS_H + NAV_H
        for it, top, entering in placed:
            ok = rec if (rec is not None and not entering and top >= content_top + 4 and top + item_h(it) <= list_bottom) else None
            if ok is None and rec is not None:
                with rec.skip():
                    draw_item(lay, it, top, t, entering, None)
            else:
                draw_item(lay, it, top, t, entering, ok)
        # the list lives above the input bar
        clip = Image.new('L', (SW, H), 0); ImageDraw.Draw(clip).rectangle((0, 0, SW, in_top), fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel('A')), np.asarray(clip))))
        im.alpha_composite(lay)
        nav_bar(im, im.copy(), rec=rec)
        status_bar(im, clock)
        showing = field_text if (field_until is None or t < field_until) else ''
        press = 0.0 if send_t is None else max(0.0, 1 - abs(t - (send_t - .04)) / .1)
        caret = (int(t * 1.9) % 2 == 0)
        input_bar(im, in_top, showing, caret, press, rec=rec)
        if kb:
            im.alpha_composite(keyboard_img(shift=not showing, tall=tall), (0, kb_top))
        else:
            home_indicator(im, H - 26)
        return im


# ------------------------------------------------------------------ 7G / 7H: Brunch Committee at 4 a.m.
T_TOOL = 120.152                        # beat 4 of 7G (CD should-note, rl_screensreal): 'tool' sung at 120.42 lands 0.3 s before the cut, so Priya lands on the beat


def chat_items(sid):
    s7g = K.shot('7G'); b = K.beats_in('7G')
    t_jo = b[1]; t_typ = b[2]; t_msg = T_TOOL - .04
    items = [Item('div', 'Sat 10:41 AM'),
             Item('in', 'sunday 11? usual place', 'Priya'),
             Item('in', 'in', 'Jo'),
             Item('in', "I'll bring the jam", 'Jo'),
             Item('out', "can't this week, sorry!"),
             Item('div', 'Tue 9:14 PM'),
             Item('in', 'you alive?', 'Maya'),
             Item('div', 'Today 4:26 AM'),
             Item('in', 'it is 4 am', 'Jo', t_in=t_jo),
             Item('typing', '', 'Priya', t_in=t_typ, t_out=t_msg),
             Item('in', 'he is A TOOL', 'Priya', t_in=t_msg, h_from=128 + 30),
             Item('receipt', 'Seen by Maya 4:27 · Jo 4:27 · you 4:28', t_in=t_msg + .17)]
    if sid == '7H':
        for it in items:
            it.t_in = None if it.kind != 'typing' else it.t_in
        items = [it for it in items if it.kind != 'typing']
        t_send = K.onset('7H', 'sends', K.shot('7H')['start']) + .03
        items += [Item('out', "Don't talk about him like that.", t_in=t_send), Item('delivered', 'Delivered', t_in=t_send + .62)]
    return group(items)


def chat_7g(t, H=SH, rec=None):
    return chat_screen(t, chat_items('7G'), '4:28', H=H, rec=rec)


def chat_7h(t, H=SH, rec=None):
    t_send = K.onset('7H', 'sends', K.shot('7H')['start']) + .03
    return chat_screen(t, chat_items('7H'), '4:35', H=H, field_text="Don't talk about him like that.", field_until=t_send, send_t=t_send, rec=rec)


# ------------------------------------------------------------------ the device and the inserts
BEZ = 30; FR = 14


def phone_body(screen):
    """our own phone: a thin black border under the glass, a graphite frame with a soft highlight, side buttons; no marks"""
    sw, sh = screen.size; bw, bh = sw + 2 * (BEZ + FR) + 16, sh + 2 * (BEZ + FR)
    R = CORNER + BEZ + FR; ox = 8
    body = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    # buttons (left: action + two volume; right: power), they sit just proud of the frame
    for (y0, y1, side) in ((.17, .21, 0), (.25, .32, 0), (.34, .41, 0), (.27, .37, 1)):
        x = 0 if side == 0 else bw - 12
        rr(body, (x, sh * y0, x + 12, sh * y1), 5, (64, 66, 72, 255))
    K.paste_mask(body, rmask(bw - 16, bh, R), (ox, 0), (92, 94, 100, 255))                     # frame highlight
    K.paste_mask(body, rmask(bw - 16 - 6, bh - 6, R - 3), (ox + 3, 3), (52, 54, 60, 255))       # graphite frame
    K.paste_mask(body, rmask(bw - 16 - 2 * FR, bh - 2 * FR, R - FR), (ox + FR, FR), (4, 4, 6, 255))   # black border glass
    sc = screen.convert('RGBA'); sc.putalpha(rmask(sw, sh, CORNER)); body.alpha_composite(sc, (ox + FR + BEZ, FR + BEZ))
    # the faintest glass sheen
    shm = Image.new('L', (bw, bh), 0); ImageDraw.Draw(shm).polygon([(bw * .08, 0), (bw * .46, 0), (bw * .06, bh * .5), (0, bh * .5), (0, bh * .2)], fill=10)
    shm = Image.fromarray(np.minimum(np.asarray(shm.filter(ImageFilter.GaussianBlur(60))), np.asarray(rmask(bw, bh, R))))
    sheen = Image.new('RGBA', (bw, bh), (255, 255, 255, 0)); sheen.putalpha(shm); body.alpha_composite(sheen)
    return body, (ox + FR + BEZ, FR + BEZ)


_BG = {}


def room_plate():
    if 'p' not in _BG:
        src = os.path.join(K.SONG, 'build', 'sets', 'room', 'room_back_to_back.png')
        im = Image.open(src).convert('RGB'); w, h = im.size
        im = im.crop((int(w * .40), int(h * .25), int(w * .95), int(h * .25) + int(w * .55 * 9 / 16))).resize((2560, 1440), Image.LANCZOS)
        im = im.filter(ImageFilter.GaussianBlur(46))
        a = np.asarray(im).astype(np.float32) * np.array([.34, .33, .38])
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
        glow = Image.new('RGBA', (2560, 1440), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((560, -200, 2000, 1640), fill=(110, 130, 190, 30))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(170)))
        _BG['p'] = im
    return _BG['p']


def cam_16x9(t, keys):
    """keys: [(t, scale, focus_y_on_screen, angle_deg)], eased between (ease in-out)"""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if t <= tb:
            e = K.ease_io(K.lin(t, ta, tb))
            return tuple(x + (y - x) * e for x, y in zip(a, b))
    return keys[-1][1:]


def insert_16x9(screen, t, keys):
    sc, fy, ang = cam_16x9(t, keys)
    body, (sx, sy) = phone_body(screen); bw, bh = body.size
    out = room_plate().copy()
    bs = body.resize((max(1, int(bw * sc)), max(1, int(bh * sc))), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
    fx, fyy = (bw / 2) * sc, (sy + fy) * sc; cx0, cy0 = bw * sc / 2, bh * sc / 2; a = math.radians(ang)
    rx = (fx - cx0) * math.cos(a) + (fyy - cy0) * math.sin(a); ry = -(fx - cx0) * math.sin(a) + (fyy - cy0) * math.cos(a)
    tx = 1280 - (bs.width / 2 + rx); ty = 720 - (bs.height / 2 + ry)
    shd = Image.new('RGBA', bs.size, (0, 0, 0, 0)); shd.putalpha(bs.getchannel('A').point(lambda v: int(v * .6))); shd = shd.filter(ImageFilter.GaussianBlur(max(6, 50 * sc)))
    K._paste_sub(out, shd, tx + 30 * sc, ty + 46 * sc); K._paste_sub(out, bs, tx, ty)
    return K.clamp_white(out).convert('RGB'), sc


H9 = round(SW * 1920 / 1080)            # 2347: the 9:16 screen is the frame


def insert_9x16(screen9, t, t0, t1):
    """the screen is the frame (a screen recording, which is how a phone reads in vertical video); a slow 2.5% push"""
    p = K.ease_io(K.lin(t, t0, t1)); sc = 1080 / SW * (1 + .025 * p)
    s = screen9.convert('RGB').resize((round(SW * sc), round(H9 * sc)), Image.LANCZOS)
    x = (1080 - s.width) / 2; y = (1920 - s.height) * .55
    out = Image.new('RGB', (1080, 1920), BG); out.paste(s, (int(round(x)), int(round(y))))
    return K.clamp_white(out), sc
