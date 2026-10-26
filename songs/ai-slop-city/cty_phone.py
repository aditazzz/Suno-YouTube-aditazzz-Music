"""Her phone. A fictional feed app called "more" (as in "so I made you a hundred more"), drawn as clean UI at any scale:
feed posts with the glossy slop pictures, a comments sheet, an assistant chat, the lock screen, a low-battery alert.

Everything is laid out in points on a 390 x 844 screen and rendered at `scale` pixels per point. The status bar clock
and battery follow the story's clock.
"""
import math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import cty_slop as SL

F32 = np.float32
AA = cv2.LINE_AA
SW, SH = 390, 844
import os
from studio.core import FONTS
FONT_DIR = os.path.join(FONTS, '')
F_REG = FONT_DIR + 'Inter-Regular.otf'
F_MED = FONT_DIR + 'Inter-Medium.otf'
F_SEMI = FONT_DIR + 'Inter-SemiBold.otf'
F_BOLD = FONT_DIR + 'InterDisplay-Bold.otf'
F_BLACK = FONT_DIR + 'InterDisplay-Black.otf'
F_SERIF = FONT_DIR + 'EBGaramond-SemiBold.ttf'


def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)


@lru_cache(maxsize=256)
def font(path, px):
    return ImageFont.truetype(path, max(4, int(round(px))))


LIGHT = dict(bg=hexc('ffffff'), fg=hexc('101014'), sub=hexc('76767f'), line=hexc('e6e6ea'), card=hexc('f4f4f6'), accent=hexc('ff3b5c'), blue=hexc('3a6cff'))
DARK = dict(bg=hexc('0c0c10'), fg=hexc('f4f4f6'), sub=hexc('8e8e98'), line=hexc('24242c'), card=hexc('18181e'), accent=hexc('ff3b5c'), blue=hexc('5a86ff'))


class Screen:
    """A float RGB canvas in points*scale with helpers; text goes through PIL."""

    def __init__(self, scale, theme, h_pt=SH):
        self.s = scale; self.T = theme
        self.W = int(round(SW * scale)); self.H = int(round(h_pt * scale))
        self.img = np.ones((self.H, self.W, 3), F32) * theme['bg']

    def P(self, v): return v * self.s

    def rrect(self, x, y, w, h, r, col, alpha=1.0):
        s = self.s
        x0, y0, x1, y1 = x * s, y * s, (x + w) * s, (y + h) * s
        rr = min(r * s, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = []
        for cx, cy, a0 in ((x1 - rr, y0 + rr, -90), (x1 - rr, y1 - rr, 0), (x0 + rr, y1 - rr, 90), (x0 + rr, y0 + rr, 180)):
            for a in np.linspace(a0, a0 + 90, 8):
                pts.append((cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))))
        self.poly(pts, col, alpha, pixel=True)

    def _roi_blend(self, mask, x0, y0, col):
        h, w = mask.shape
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(self.W, x0 + w), min(self.H, y0 + h)
        if X1 <= X0 or Y1 <= Y0: return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None]
        self.img[Y0:Y1, X0:X1] = self.img[Y0:Y1, X0:X1] * (1 - m) + np.asarray(col, F32) * m

    def poly(self, pts, col, alpha=1.0, pixel=False):
        P = np.asarray(pts, np.float64) * (1 if pixel else self.s)
        x0, y0 = int(math.floor(P[:, 0].min())) - 2, int(math.floor(P[:, 1].min())) - 2
        x1, y1 = int(math.ceil(P[:, 0].max())) + 2, int(math.ceil(P[:, 1].max())) + 2
        if x1 <= 0 or y1 <= 0 or x0 >= self.W or y0 >= self.H: return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(m, [np.round((P - [x0, y0]) * 16).astype(np.int32)], 255, AA, shift=4)
        self._roi_blend(m.astype(F32) / 255 * alpha, x0, y0, col)

    def circle(self, x, y, r, col, alpha=1.0):
        a = np.linspace(0, 2 * math.pi, max(16, int(r * self.s)), endpoint=False)
        self.poly(np.stack([x + np.cos(a) * r, y + np.sin(a) * r], 1), col, alpha)

    def polyline(self, pts, col, w=1.0, closed=False, alpha=1.0):
        P = np.asarray(pts, np.float64) * self.s
        pad = int(w * self.s) + 3
        x0, y0 = int(math.floor(P[:, 0].min())) - pad, int(math.floor(P[:, 1].min())) - pad
        x1, y1 = int(math.ceil(P[:, 0].max())) + pad, int(math.ceil(P[:, 1].max())) + pad
        if x1 <= 0 or y1 <= 0 or x0 >= self.W or y0 >= self.H: return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.polylines(m, [np.round((P - [x0, y0]) * 16).astype(np.int32)], closed, 255, max(1, int(round(w * self.s))), AA, shift=4)
        self._roi_blend(m.astype(F32) / 255 * alpha, x0, y0, col)

    def line(self, x0, y0, x1, y1, col, w=1.0):
        self.polyline([(x0, y0), (x1, y1)], col, w)

    def paste(self, im, x, y, w, h, r=0.0, alpha=1.0):
        s = self.s
        x0, y0 = int(round(x * s)), int(round(y * s)); ww, hh = int(round(w * s)), int(round(h * s))
        if ww <= 0 or hh <= 0: return
        src = cv2.resize(im, (ww, hh), interpolation=cv2.INTER_AREA if im.shape[1] > ww else cv2.INTER_LINEAR)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(self.W, x0 + ww), min(self.H, y0 + hh)
        if X1 <= X0 or Y1 <= Y0: return
        sub = src[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        if r > 0:
            m = np.zeros((hh, ww), np.uint8)
            rr = int(r * s)
            cv2.rectangle(m, (rr, 0), (ww - rr, hh), 255, -1); cv2.rectangle(m, (0, rr), (ww, hh - rr), 255, -1)
            for cx, cy in ((rr, rr), (ww - rr, rr), (rr, hh - rr), (ww - rr, hh - rr)):
                cv2.circle(m, (cx, cy), rr, 255, -1, AA)
            mm = (m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(F32) / 255 * alpha)[..., None]
        else:
            mm = alpha
        self.img[Y0:Y1, X0:X1] = self.img[Y0:Y1, X0:X1] * (1 - mm) + sub * mm

    def text(self, x, y, s_, size, col, path=F_MED, anchor='la', alpha=1.0, maxw=None, spacing=1.25):
        """Draw text (points). Returns the width in points. Wraps to maxw if given; returns (w, h)."""
        f = font(path, size * self.s)
        lines_ = [s_]
        if maxw:
            words = s_.split(' '); lines_ = []; cur = ''
            for w in words:
                t = (cur + ' ' + w).strip()
                if f.getlength(t) / self.s > maxw and cur:
                    lines_.append(cur); cur = w
                else:
                    cur = t
            lines_.append(cur)
        tw = max(f.getlength(l) for l in lines_) / self.s
        lh = size * spacing
        th = lh * len(lines_)
        X, Y = int(math.ceil((tw + 4) * self.s)), int(math.ceil((th + size * 0.5) * self.s))
        lay = Image.new('L', (X, Y), 0)
        d = ImageDraw.Draw(lay)
        for i, l in enumerate(lines_):
            d.text((1 * self.s, (i * lh) * self.s), l, font=f, fill=255)
        m = np.asarray(lay, F32) / 255 * alpha
        ox = x - (tw if anchor[0] == 'r' else (tw / 2 if anchor[0] == 'm' else 0))
        oy = y - (size * 0.5 * 0 if anchor[1] == 'a' else 0)
        x0, y0 = int(round(ox * self.s)), int(round(oy * self.s))
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(self.W, x0 + X), min(self.H, y0 + Y)
        if X1 > X0 and Y1 > Y0:
            mm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None]
            self.img[Y0:Y1, X0:X1] = self.img[Y0:Y1, X0:X1] * (1 - mm) + np.asarray(col, F32) * mm
        return tw, th


# ------------------------------------------------------------------ icons
def heart_pts(cx, cy, r):
    t = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    x = 16 * np.sin(t) ** 3; y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return np.stack([cx + x / 17 * r, cy + y / 17 * r - r * 0.05], 1)


def heart(sc, cx, cy, r, col, filled=True, w=1.6):
    pts = heart_pts(cx, cy, r)
    if filled: sc.poly(pts, col)
    else: sc.polyline(pts, col, w, closed=True)


def bubble_icon(sc, cx, cy, r, col, w=1.6):
    a = np.linspace(0.35, 2 * math.pi - 0.1, 40)
    pts = np.stack([cx + np.cos(a) * r, cy + np.sin(a) * r * 0.92], 1)
    pts = np.vstack([pts, [(pts[-1][0] + r * 0.2, pts[-1][1] + r * 0.45), (cx + r * 1.05, cy + r * 0.95), tuple(pts[0])]])
    sc.polyline(pts, col, w)


def share_icon(sc, cx, cy, r, col, w=1.6):
    sc.polyline([(cx - r, cy + r * 0.2), (cx + r, cy - r * 0.8), (cx + r * 0.1, cy + r * 0.9), (cx - 0.1 * r, cy + r * 0.05)], col, w, closed=True)


def status_bar(sc, clock, battery, dark=False, low=False):
    T = sc.T
    sc.text(28, 15, clock, 15.5, T['fg'], F_SEMI)
    # signal bars
    for k in range(4):
        h = 4 + k * 2.4
        sc.rrect(286 + k * 5.2, 26 - h, 3.4, h, 0.8, T['fg'])
    # wifi
    for k, r in enumerate((10.5, 7.0, 3.6)):
        a = np.linspace(-2.36, -0.78, 16)
        sc.polyline(np.stack([316 + np.cos(a) * r, 27 + np.sin(a) * r], 1), T['fg'], 1.6)
    # battery
    col = hexc('ff3b30') if low else T['fg']
    sc.rrect(334, 16, 26, 12.5, 3.5, T['sub'] * 0.6 + T['bg'] * 0.4)
    sc.rrect(336, 18, max(1.2, 22 * battery / 100), 8.5, 2.0, col)
    sc.rrect(361, 20, 2, 4.5, 1, T['sub'])
    sc.text(332, 17.5, f'{int(round(battery))}', 8.5, T['bg'] if battery > 25 else T['fg'], F_SEMI, anchor='ra', alpha=0.0)


# ------------------------------------------------------------------ the feed
AVATAR_COLS = ['ff9a5c', '5cc8ff', 'b07cff', '5be3a4', 'ffd34d', 'ff5f9e', '7a9cff']


def avatar(sc, x, y, r, seed, shadow=False):
    if shadow:
        sc.circle(x, y, r, hexc('1b1625'))
        sc.circle(x + r * 0.02, y - r * 0.18, r * 0.36, hexc('3a3048'))
        sc.poly([(x - r * 0.62, y + r * 0.9), (x - r * 0.5, y + r * 0.32), (x + r * 0.5, y + r * 0.32), (x + r * 0.62, y + r * 0.9)], hexc('3a3048'))
        return
    c1 = hexc(AVATAR_COLS[seed % len(AVATAR_COLS)]); c2 = hexc(AVATAR_COLS[(seed * 3 + 2) % len(AVATAR_COLS)])
    sc.circle(x, y, r, c1)
    sc.circle(x + r * 0.25, y + r * 0.25, r * 0.6, c2, 0.7)


def fmt(n):
    if n >= 1_000_000: return f'{n / 1_000_000:.1f}M'.replace('.0M', 'M')
    if n >= 10_000: return f'{n / 1000:.0f}K'
    if n >= 1000: return f'{n / 1000:.1f}K'.replace('.0K', 'K')
    return f'{int(n)}'


def post(sc, y, P, t=0.0):
    """One post at y (points). P: user, kind, caption, likes, comments, liked, badge, time. Returns its height."""
    T = sc.T
    avatar(sc, 30, y + 26, 16, P.get('seed', 0), P.get('shadow_avatar', False))
    sc.text(54, y + 15, P['user'], 14, T['fg'], F_SEMI)
    sc.text(54 + font(F_SEMI, 14 * sc.s).getlength(P['user']) / sc.s + 6, y + 15, P.get('time', '2h'), 13, T['sub'], F_REG)
    for k in range(3): sc.circle(352 + k * 6, y + 26, 1.6, T['fg'])
    img_y = y + 52
    im = SL.image(P['kind'], 768)
    sc.paste(im, 0, img_y, SW, SW)
    if P.get('img_text'):
        f = P.get('img_font', F_SERIF)
        sc.text(SW / 2, img_y + SW * P.get('img_text_y', 0.38), P['img_text'], P.get('img_text_size', 30), hexc('ffffff'), f, anchor='ma', maxw=320)
    if P.get('badge'):
        b, bc = P['badge']
        w = font(F_SEMI, 12 * sc.s).getlength(b) / sc.s + 18
        sc.rrect(12, img_y + 12, w, 24, 12, hexc(bc), 0.92)
        sc.text(12 + 9, img_y + 16.5, b, 12, hexc('ffffff'), F_SEMI)
    ay = img_y + SW + 14
    liked = P.get('liked', False)
    heart(sc, 26, ay + 10, 11, T['accent'] if liked else T['fg'], filled=liked)
    sc.text(44, ay + 1, fmt(P.get('likes', 0)), 14, T['fg'], F_SEMI)
    bx = 44 + font(F_SEMI, 14 * sc.s).getlength(fmt(P.get('likes', 0))) / sc.s + 20
    bubble_icon(sc, bx + 9, ay + 10, 9.5, T['fg'])
    sc.text(bx + 24, ay + 1, fmt(P.get('comments', 0)), 14, T['fg'], F_SEMI)
    share_icon(sc, bx + 82, ay + 10, 9, T['fg'])
    cy = ay + 30
    h = caption(sc, 16, cy, P['user'], P['caption'], 14, 358)
    if P.get('more_comments'):
        sc.text(16, cy + h + 4, P['more_comments'], 13.5, T['sub'], F_REG)
        h += 20
    return (cy + h + 22) - y


def caption(sc, x, y, user, text, size, maxw):
    """Bold handle followed inline by the caption, wrapped."""
    T = sc.T
    fb = font(F_SEMI, size * sc.s); fr = font(F_REG, size * sc.s)
    uw = fb.getlength(user) / sc.s + size * 0.4
    sc.text(x, y, user, size, T['fg'], F_SEMI)
    words = text.split(' '); line = ''; lines_ = []; avail = maxw - uw
    for w in words:
        t = (line + ' ' + w).strip()
        if fr.getlength(t) / sc.s > avail and line:
            lines_.append(line); line = w; avail = maxw
        else:
            line = t
    lines_.append(line)
    lh = size * 1.3
    for i, l in enumerate(lines_):
        sc.text(x + (uw if i == 0 else 0), y + i * lh, l, size, T['fg'], F_REG)
    return lh * len(lines_)


def feed_header(sc, title='more'):
    T = sc.T
    sc.img[:int(98 * sc.s)] = T['bg']
    sc.text(18, 50, title, 27, T['fg'], F_BLACK)
    w = font(F_SEMI, 14 * sc.s).getlength('Following') / sc.s
    sc.text(SW - 18 - w - 18 - font(F_SEMI, 14 * sc.s).getlength('For You') / sc.s, 60, 'Following', 14, T['sub'], F_SEMI)
    fw = font(F_SEMI, 14 * sc.s).getlength('For You') / sc.s
    sc.text(SW - 18 - fw, 60, 'For You', 14, T['fg'], F_SEMI)
    sc.rrect(SW - 18 - fw, 81, fw, 2.5, 1.2, T['fg'])
    sc.line(0, 96, SW, 96, T['line'], 0.6)


_PAGE = {}


def feed_page(posts, scale, dark):
    """Render a whole scroll of posts once (cached): returns (image, list of post top y in points)."""
    key = (tuple(tuple(sorted((k, str(v)) for k, v in p.items())) for p in posts), round(scale, 3), dark)
    if key in _PAGE: return _PAGE[key]
    total = 98
    tmp = Screen(scale, DARK if dark else LIGHT, 4000)
    tops = []
    y = 98
    for P in posts:
        tops.append(y)
        y += post(tmp, y, P)
        if y > 3900: break
    out = (tmp.img[:int(y * scale)].copy(), tops, y)
    _PAGE[key] = out
    return out


def feed(scale, posts, scroll, clock, battery, dark=False, overlays=(), t=0.0):
    """The feed scrolled by `scroll` points, with the header and status bar on top, then overlays (callables)."""
    T = DARK if dark else LIGHT
    sc = Screen(scale, T)
    page, tops, total = feed_page(posts, scale, dark)
    y0 = int(round(scroll * scale))
    h = min(sc.H, page.shape[0] - y0)
    if h > 0: sc.img[:h] = page[y0:y0 + h]
    feed_header(sc)
    status_bar(sc, clock, battery, dark, battery <= 10)
    for ov in overlays: ov(sc)
    return sc.img


# ------------------------------------------------------------------ overlays
def big_heart(k, cy=None):
    """Double-tap: a big heart pops (k 0..1 over ~0.8 s)."""
    def f(sc):
        if not 0 < k < 1: return
        s = (1 - (1 - min(1, k * 3)) ** 3) * (1 - max(0, k - 0.7) / 0.3 * 0.3)
        a = 1 - max(0, (k - 0.6) / 0.4)
        r = 70 * s
        y = cy if cy is not None else 98 + 52 + SW / 2
        sc.poly(heart_pts(SW / 2, y, r * 1.06), hexc('ffffff'), a * 0.9)
        sc.poly(heart_pts(SW / 2, y, r), hexc('ff3b5c'), a)
    return f


def dwell_meter(secs, y=420):
    """'I learned the shape of every pause': the app quietly timing her pause."""
    def f(sc):
        T = sc.T
        sc.rrect(SW - 150, y, 136, 46, 12, hexc('000000'), 0.55)
        sc.text(SW - 140, y + 7, 'dwell', 11, hexc('cfcfd6'), F_MED)
        sc.text(SW - 140, y + 21, f'{secs:0.1f}s', 17, hexc('ffffff'), F_SEMI)
        sc.rrect(SW - 74, y + 26, 54, 5, 2.5, hexc('ffffff'), 0.25)
        sc.rrect(SW - 74, y + 26, 54 * min(1, secs / 3.0), 5, 2.5, hexc('7af0ff'))
    return f


def pill(text, y, col='111116', fg='ffffff', alpha=0.85, x=None, size=13):
    def f(sc):
        w = font(F_SEMI, size * sc.s).getlength(text) / sc.s + 26
        xx = (SW - w) / 2 if x is None else x
        sc.rrect(xx, y, w, size + 17, (size + 17) / 2, hexc(col), alpha)
        sc.text(xx + 13, y + 7.5, text, size, hexc(fg), F_SEMI, alpha=min(1, alpha * 1.2))
    return f


# ------------------------------------------------------------------ comments, chat, lock screen
def comments(scale, rows, scroll, clock, battery, dark=False, title='Comments', highlight=None, overlays=()):
    T = DARK if dark else LIGHT
    sc = Screen(scale, T)
    y = 112 - scroll
    for i, R in enumerate(rows):
        if y > SH + 60: break
        if y > 40:
            if highlight is not None and i == highlight:
                sc.rrect(8, y - 8, SW - 16, 70, 14, T['card'])
            avatar(sc, 32, y + 16, 15, R.get('seed', i), R.get('shadow', False))
            sc.text(56, y + 2, R['user'], 13, T['fg'], F_SEMI)
            sc.text(56 + font(F_SEMI, 13 * sc.s).getlength(R['user']) / sc.s + 6, y + 2, R.get('time', '1m'), 12.5, T['sub'], F_REG)
            sc.text(56, y + 20, R['text'], 14.5, T['fg'], F_REG, maxw=280)
            if R.get('tag'):
                tw = font(F_SEMI, 11 * sc.s).getlength(R['tag']) / sc.s + 14
                sc.rrect(56, y + 42, tw, 18, 9, T['accent'], 0.14)
                sc.text(63, y + 44.5, R['tag'], 11, T['accent'], F_SEMI)
            heart(sc, SW - 26, y + 18, 8, T['accent'] if R.get('liked') else T['sub'], filled=R.get('liked', False), w=1.3)
            sc.text(SW - 26, y + 30, fmt(R.get('likes', 0)), 11, T['sub'], F_MED, anchor='ma')
        y += R.get('h', 66)
    sc.img[:int(100 * sc.s)] = T['bg']
    sc.rrect(SW / 2 - 18, 52, 36, 4.5, 2.2, T['line'] * 0.7 + T['sub'] * 0.3)
    sc.text(SW / 2, 68, title, 15, T['fg'], F_SEMI, anchor='ma')
    sc.line(0, 98, SW, 98, T['line'], 0.6)
    status_bar(sc, clock, battery, dark, battery <= 10)
    for ov in overlays: ov(sc)
    return sc.img


def compose_bar(text, caret=True, y=None, dark=False):
    """Her typing into the comment box (with a keyboard)."""
    def f(sc):
        T = sc.T
        ky = SH - 290 if y is None else y
        sc.rrect(0, ky - 62, SW, 62, 0, T['bg'])
        sc.line(0, ky - 62, SW, ky - 62, T['line'], 0.6)
        avatar(sc, 30, ky - 31, 15, 0, True)
        sc.rrect(54, ky - 50, 270, 38, 19, T['card'])
        tw, _ = sc.text(70, ky - 41, text if text else 'Add a comment...', 14.5, T['fg'] if text else T['sub'], F_REG)
        if caret and text is not None:
            sc.rrect(70 + (tw if text else 0) + 1.5, ky - 41, 1.6, 19, 0.8, T['blue'])
        sc.text(SW - 24, ky - 41, 'Post', 14.5, T['blue'] if text else T['sub'], F_SEMI, anchor='ra')
        # keyboard
        kb = hexc('d1d3d9') if not dark else hexc('2a2a30')
        sc.rrect(0, ky, SW, SH - ky, 0, kb)
        rows_ = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']
        kc = hexc('ffffff') if not dark else hexc('4a4a52')
        for r, keys in enumerate(rows_):
            n = len(keys); kw = 33.5; gap = 5.5
            x0 = (SW - (n * kw + (n - 1) * gap)) / 2
            for k, ch in enumerate(keys):
                x = x0 + k * (kw + gap); yy = ky + 10 + r * 54
                sc.rrect(x, yy, kw, 44, 6, kc)
                sc.text(x + kw / 2, yy + 11, ch, 19, T['fg'] if dark else hexc('101014'), F_REG, anchor='ma')
        sc.rrect(96, ky + 10 + 3 * 54, 198, 44, 6, kc)
    return f


def chat(scale, msgs, clock, battery, dark=True, typing=None, title='Assistant', overlays=()):
    """Assistant chat: msgs = [(who, text, alpha)] with who in {'me', 'ai'}; typing = dots phase for the AI."""
    T = DARK if dark else LIGHT
    sc = Screen(scale, T)
    sc.text(SW / 2, 58, title, 16, T['fg'], F_SEMI, anchor='ma')
    sc.line(0, 92, SW, 92, T['line'], 0.6)
    y = 120
    for who, txt, a in msgs:
        if a <= 0.01: continue
        f = font(F_REG, 17 * sc.s)
        w = min(260, f.getlength(txt) / sc.s) + 32
        if who == 'me':
            sc.rrect(SW - 16 - w, y, w, 44, 22, T['blue'], a)
            sc.text(SW - 16 - w + 16, y + 11, txt, 17, hexc('ffffff'), F_REG, alpha=a)
        else:
            sc.rrect(16, y, w, 44, 22, T['card'], a)
            sc.text(32, y + 11, txt, 17, T['fg'], F_REG, alpha=a)
        y += 58
    if typing is not None:
        sc.rrect(16, y, 74, 44, 22, T['card'])
        for k in range(3):
            ph = math.sin(typing * 6 - k * 0.9) * 0.5 + 0.5
            sc.circle(36 + k * 15, y + 22 - ph * 3, 4.2, T['sub'] * (0.6 + 0.4 * ph))
    status_bar(sc, clock, battery, dark, battery <= 10)
    for ov in overlays: ov(sc)
    return sc.img


def lock(scale, clock, date, battery, notes=(), dark=True, wall=None):
    """Lock screen: big clock, date, notification banners [(app, title, body, alpha)]."""
    sc = Screen(scale, DARK)
    if wall is not None:
        sc.paste(wall, 0, 0, SW, SH)
        sc.img *= 0.55
    sc.text(SW / 2, 70, date, 17, hexc('ffffff'), F_SEMI, anchor='ma', alpha=0.9)
    sc.text(SW / 2, 92, clock, 86, hexc('ffffff'), F_BOLD, anchor='ma')
    y = 330
    for app, ttl, body, a in notes:
        if a <= 0.01: continue
        sc.rrect(12, y, SW - 24, 76, 20, hexc('2c2c34'), 0.82 * a)
        sc.rrect(26, y + 14, 34, 34, 8, hexc('ff3b5c'), a)
        sc.text(43, y + 20, 'm', 18, hexc('ffffff'), F_BLACK, anchor='ma', alpha=a)
        sc.text(72, y + 13, ttl, 14.5, hexc('ffffff'), F_SEMI, alpha=a)
        sc.text(72, y + 34, body, 14.5, hexc('e6e6ee'), F_REG, alpha=a, maxw=280)
        sc.text(SW - 26, y + 13, 'now', 12.5, hexc('b0b0bc'), F_REG, anchor='ra', alpha=a)
        y += 86
    status_bar(sc, '', battery, True, battery <= 10)
    return sc.img


def battery_alert(k):
    def f(sc):
        if k <= 0: return
        sc.img = sc.img * (1 - 0.45 * k)
        sc.rrect(55, 330, 280, 150, 18, hexc('2a2a30'), 0.96 * k)
        sc.text(SW / 2, 352, 'Low Battery', 17, hexc('ffffff'), F_SEMI, anchor='ma', alpha=k)
        sc.text(SW / 2, 380, '1% battery remaining', 14.5, hexc('d6d6de'), F_REG, anchor='ma', alpha=k)
        sc.line(55, 428, 335, 428, hexc('48484f'), 0.6)
        sc.text(SW / 2, 442, 'Close', 17, hexc('5a86ff'), F_REG, anchor='ma', alpha=k)
    return f
