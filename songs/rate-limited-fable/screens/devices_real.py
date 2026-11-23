"""The other device screens at the real-device standard (rl_screensreal, Nov 15 2026), built on the approved phone_real kit.

Her note (Nov 15 10:39): "The phone screen should look like a phone screen really does. Any apps should also look realistic.
Recognizable immediately not some cheap copy". Approved look: screens/phone_real.py (Nov 15 12:27, "Everything loooks good").
Realism from structure, type, spacing and motion people know by heart; no real app's name, logo, icon set or screen; no maker's
marks; film palette; K.BLUE stays hers alone (only her sent bubbles), so accents here are amber / teal / neutral.

  3C  usage(t, H)        a settings "Usage" page: large title, inset grouped cards, pull-to-refresh with the spoke spinner (x3)
  6B  sleep_story(t, H)  a full-screen audio player (sheet handle, artwork, title, scrubber with "3:58 left", transport)
  8D  notes(t, H)        a notes folder list: large title, search field, "Today" section, newest first, toolbar with the count
  6C  watch_screen(t)    a watch stand reminder (ring + figure, title, body, Dismiss), upright (no CD note asks for upside down)
  5E  editor(t)          a laptop desktop: menu bar, a code editor window (activity bar, explorer, tab, gutter, inline hint,
                         assistant side panel, status bar); the caret blinks on the four beats
  13E prompt(t)          morning: a chat app's empty state, "Where were we?", the composer, she types "Make the font bigger."
Every frame is a pure function of t (audio seconds).
"""
import math, os, sys
from contextlib import nullcontext
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K
import phone_real as P
from phone_real import rr, line, _skip, SW, M, TXT, SUB, DIM, AMBER

BG = P.BG
CARD = (28, 28, 32)                     # inset grouped section (night)
CARD_SEP = (52, 52, 58, 255)
ACC = (240, 178, 60)                    # the notes / settings accent here: amber (blue is hers)
ACC_A = ACC + (255,)
TEAL = (90, 214, 200)


def ellipsize(txt, f, maxw):
    if K.text_w(txt, f) <= maxw:
        return txt
    while txt and K.text_w(txt + '…', f) > maxw:
        txt = txt[:-1]
    return txt.rstrip(' ,') + '…'


def chevron_left(im, x, cy, s, col, w=9):
    line(im, [(x + 28 * s, cy - 30 * s), (x, cy), (x + 28 * s, cy + 30 * s)], w, col)


def chevron_right(im, x, cy, s, col, w=6):
    line(im, [(x - 14 * s, cy - 22 * s), (x, cy), (x - 14 * s, cy + 22 * s)], w, col)


def more_btn(im, cx, cy, col, r=44):
    K.circle(im, cx, cy, r, (40, 40, 46, 255))
    for dx in (-17, 0, 17):
        K.circle(im, cx + dx, cy, 5.5, col)


def roll(im, xy, old, new, p, f, fill):
    """the changing tail of a number rolls up a short way with a fade (a modern counter); the window is the line's own box"""
    if p <= 0:
        ImageDraw.Draw(im).text(xy, old, font=f, fill=fill, anchor='la'); return
    if p >= 1:
        ImageDraw.Draw(im).text(xy, new, font=f, fill=fill, anchor='la'); return
    n = 0
    while n < min(len(old), len(new)) and old[n] == new[n]:
        n += 1
    pre = old[:n]
    ImageDraw.Draw(im).text(xy, pre, font=f, fill=fill, anchor='la')
    x = xy[0] + K.text_w(pre, f); asc, desc = f.getmetrics(); h = asc + desc
    tile = Image.new('RGBA', (int(max(K.text_w(old[n:], f), K.text_w(new[n:], f)) + 10), int(h)), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    e = K.ease_io(p); tr = .55 * h
    with _skip():
        td.text((0, -e * tr), old[n:], font=f, fill=fill[:3] + (int(fill[3] * (1 - e) ** 2),), anchor='la')
        td.text((0, (1 - e) * tr), new[n:], font=f, fill=fill[:3] + (int(fill[3] * e ** .7),), anchor='la')
    im.alpha_composite(tile, (int(x), int(xy[1])))


def spinner(im, cx, cy, t, n_vis=8, a=1.0, r0=15, r1=36):
    """the spoke activity indicator: 8 spokes, the bright one steps round 12 times a second, a fading tail"""
    step = int(t * 12) % 8
    for i in range(8):
        if i >= n_vis:
            continue
        ang = -math.pi / 2 + i * 2 * math.pi / 8
        k = ((step - i) % 8) / 8.0
        alpha = (1 - .75 * k) * a
        line(im, [(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))], 7.5, (170, 171, 178, 255), alpha)


def rec_box(rec, box, name):
    return rec.container(box, name) if rec is not None else nullcontext()


# =================================================================== 3C: Usage (pull to refresh on each 'retry')
def _usage_offset(t, pulls):
    """drag down (rubber band, 0.24 s to the snap on the stressed 'try'), hold with the spinner, spring back"""
    off = 0.0; spin = 0.0; nvis = 0
    for ts in pulls:
        t0 = ts - .24
        if t < t0 or t > ts + .34:
            continue
        if t <= ts:
            p = K.ease_out(K.lin(t, t0, ts)); o = 168 * p; nv = int(math.ceil(8 * p)); sp = K.clamp(p * 1.3)
        elif t <= ts + .15:
            o = 168; nv = 8; sp = 1.0
        else:
            q = K.ease_io(K.lin(t, ts + .15, ts + .33)); o = 168 * (1 - q); nv = 8; sp = 1 - K.clamp(q * 1.4)
        if o > off:
            off, spin, nvis = o, sp, nv
    return off, spin, nvis


def usage_cues(sid='3C'):
    s = K.shot(sid); b = K.beats_in(sid) + [s['end']]
    pulls = [K.onset(sid, f'refresh {i + 1}', b[i]) for i in range(3)]
    t_after = min(K.onset(sid, 'page changes', b[3] if len(b) > 3 else s['end'] - .5) - .08, s['end'] - .30)
    return pulls, t_after


def usage(t, H=P.SH, rec=None):
    pulls, t_after = usage_cues()
    off, spin, nvis = _usage_offset(t, pulls)
    mp = K.ease_io(K.lin(t, t_after, t_after + .22))
    im = Image.new('RGBA', (SW, H), BG + (255,))
    navb = P.STATUS_H + 120
    if spin > .01:
        spinner(im, SW / 2, navb + 10 + off * .5, t, nvis, spin)
    page = Image.new('RGBA', (SW, H), (0, 0, 0, 0)); d = ImageDraw.Draw(page)
    x0, x1 = M + 6, SW - M - 6; ix = x0 + 48; R = 54
    # large title
    d.text((M + 6, navb + 92), 'Usage', font=K.font('bold', 104), fill=TXT, anchor='lm')
    # CURRENT SESSION
    y = navb + 208
    d.text((ix, y), 'CURRENT SESSION', font=K.font('reg', 42), fill=SUB, anchor='lm')
    c0 = y + 44; c1 = c0 + 940
    rr(page, (x0, c0, x1, c1), R, CARD + (255,))
    with rec_box(rec, (x0, c0, x1, c1), 'session card'):
        d.text((ix, c0 + 96), 'Usage limit reached', font=K.font('bold', 70), fill=TXT, anchor='lm')
    pw = 176; rr(page, (x1 - 48 - pw, c0 + 52, x1 - 48, c0 + 140), 44, K.RED + (255,))
    with rec_box(rec, (x1 - 48 - pw, c0 + 52, x1 - 48, c0 + 140), '429 pill'):
        d.text((x1 - 48 - pw / 2, c0 + 97), '429', font=K.font('bold', 46), fill=TXT, anchor='mm')
    rr(page, (ix, c0 + 176, x1 - 48, c0 + 206), 15, (64, 32, 34, 255)); rr(page, (ix, c0 + 176, x1 - 48, c0 + 206), 15, K.RED + (255,))
    with rec_box(rec, (x0, c0, x1, c1), 'session card'):
        d.text((ix, c0 + 262), '100% used · since 11:58 PM', font=K.font('reg', 48), fill=SUB, anchor='lm')
    d.line([(ix, c0 + 340), (x1, c0 + 340)], fill=CARD_SEP, width=2)
    with rec_box(rec, (x0, c0, x1, c1), 'session card'):
        d.text((ix, c0 + 410), 'Resets in', font=K.font('reg', 48), fill=SUB, anchor='lm')
        roll(page, (ix - 6, c0 + 460), '3h 52m', '3h 51m', mp, K.font('bold', 196), TXT)
        roll(page, (ix, c0 + 730), 'Retry-After: 13920', 'Retry-After: 13860', mp, K.font('mono', 46), DIM)
    d.line([(ix, c0 + 812), (x1, c0 + 812)], fill=CARD_SEP, width=2)
    with rec_box(rec, (x0, c0, x1, c1), 'session card'):
        d.text((ix, c0 + 858), 'Refresh', font=K.font('reg', 54), fill=ACC_A, anchor='lm')
    # THIS WEEK
    y = c1 + 74
    d.text((ix, y), 'THIS WEEK', font=K.font('reg', 42), fill=SUB, anchor='lm')
    w0 = y + 44; w1 = w0 + 300
    rr(page, (x0, w0, x1, w1), R, CARD + (255,))
    with rec_box(rec, (x0, w0, x1, w1), 'week card'):
        d.text((ix, w0 + 84), '64% used', font=K.font('semi', 60), fill=TXT, anchor='lm')
    rr(page, (ix, w0 + 146, x1 - 48, w0 + 168), 11, (58, 58, 64, 255)); rr(page, (ix, w0 + 146, ix + (x1 - 48 - ix) * .64, w0 + 168), 11, (206, 206, 212, 255))
    with rec_box(rec, (x0, w0, x1, w1), 'week card'):
        d.text((ix, w0 + 232), 'Resets Thursday, 9:00 AM', font=K.font('reg', 48), fill=SUB, anchor='lm')
    # a tip row
    t0_ = w1 + 64; t1_ = t0_ + 200
    if t1_ < H - 60:
        rr(page, (x0, t0_, x1, t1_), R, CARD + (255,))
        gx, gy = ix + 50, t0_ + 100
        rr(page, (gx - 50, gy - 50, gx + 50, gy + 50), 24, (40, 120, 120, 255))
        K.poly(page, [(gx - 22, gy - 32), (gx + 22, gy - 32), (gx + 17, gy + 32), (gx - 17, gy + 32)], (220, 236, 236, 255), .45)
        K.poly(page, [(gx - 19, gy - 6), (gx + 19, gy - 6), (gx + 16, gy + 28), (gx - 16, gy + 28)], (220, 236, 236, 255), .9)
        with rec_box(rec, (x0, t0_, x1 - 80, t1_), 'tip row'):
            d.text((ix + 140, t0_ + 68), 'While you wait', font=K.font('semi', 54), fill=TXT, anchor='lm')
            d.text((ix + 140, t0_ + 136), 'Maybe drink some water.', font=K.font('reg', 48), fill=SUB, anchor='lm')
        chevron_right(page, x1 - 48, t0_ + 100, 1.0, (100, 100, 108, 255))
    im.alpha_composite(page, (0, int(round(off))))
    # the fixed nav row (it stays put while the page is pulled)
    chevron_left(im, M + 8, P.STATUS_H + 60, 1.0, ACC_A)
    with _skip():
        ImageDraw.Draw(im).text((M + 52, P.STATUS_H + 61), 'Settings', font=K.font('reg', 54), fill=ACC_A, anchor='lm')
    P.status_bar(im, '2:08')
    P.home_indicator(im, H - 26)
    return im


# =================================================================== 6B: the sleep story player (3:58 left -> 3:57 left)
def _art(size, t):
    """our own artwork: a night sea, a lighthouse with its lamp off, a crescent, stars (drawn, no stock)"""
    s = size; im = Image.new('RGBA', (s, s), (0, 0, 0, 255))
    y = np.linspace(0, 1, s)[:, None]; x = np.linspace(0, 1, s)[None, :]
    g = np.zeros((s, s, 3), np.float32)
    g[..., 0] = 30 + 26 * (1 - y) + 8 * x; g[..., 1] = 26 + 18 * (1 - y); g[..., 2] = 74 + 56 * (1 - y)
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA')
    glow = Image.new('RGBA', (s, s), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((s * .52, s * .08, s * .92, s * .48), fill=(210, 200, 255, 70))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(s * .06)))
    K.circle(im, s * .72, s * .27, s * .11, (232, 226, 244, 255)); K.circle(im, s * .765, s * .245, s * .10, (44, 38, 98, 255))
    for i, (sx, sy, r) in enumerate(((.16, .14, 5), (.33, .27, 4), (.49, .11, 4), (.90, .52, 4), (.12, .40, 4), (.40, .45, 3), (.58, .36, 3))):
        K.circle(im, s * sx, s * sy, r * s / 900, (230, 226, 250, 255), .55 + .45 * math.sin(t * 2.1 + i * 1.7))
    # sea
    sea = Image.new('RGBA', (s, s), (0, 0, 0, 0)); sd = ImageDraw.Draw(sea)
    sd.rectangle((0, s * .72, s, s), fill=(20, 22, 54, 255))
    for k in range(7):
        yy = s * (.75 + k * .036); sd.line([(s * .05 + k * 23, yy), (s * .42 - k * 9, yy)], fill=(70, 72, 130, 120), width=max(2, s // 260))
    im.alpha_composite(sea)
    # rock + lighthouse (tapered tower, two bands, the lamp room dark: it logged off)
    K.poly(im, [(s * .12, s * .76), (s * .22, s * .66), (s * .40, s * .64), (s * .52, s * .70), (s * .58, s * .76)], (16, 16, 34, 255))
    K.poly(im, [(s * .27, s * .66), (s * .37, s * .66), (s * .345, s * .33), (s * .295, s * .33)], (196, 192, 214, 255))
    for yy in (.42, .54):
        K.poly(im, [(s * (.287 - (yy - .33) * .07), s * yy), (s * (.353 + (yy - .33) * .07), s * yy),
                    (s * (.355 + (yy - .33) * .07), s * (yy + .045)), (s * (.285 - (yy - .33) * .07), s * (yy + .045))], (150, 70, 80, 255))
    rr(im, (s * .285, s * .27, s * .355, s * .33), 4, (40, 40, 64, 255))
    K.poly(im, [(s * .275, s * .27), (s * .365, s * .27), (s * .32, s * .225)], (120, 118, 150, 255))
    return im


_ART = {}


def sleep_story(t, H=P.SH, rec=None):
    t58 = K.onset('6B', 'fifty-eight', K.shot('6B')['start'] + .12)
    t57 = t58 + 1.0
    # background: the artwork's colours, blurred to a deep wash (as a real player does)
    y = np.linspace(0, 1, H)[:, None]
    g = np.zeros((H, SW, 3), np.float32)
    g[..., 0] = 34 * (1 - y) + 12; g[..., 1] = 28 * (1 - y) + 10; g[..., 2] = 78 * (1 - y) + 24
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(im)
    P.status_bar(im, '3:59')
    # sheet handle + header row
    rr(im, (SW / 2 - 60, 182, SW / 2 + 60, 196), 7, (200, 196, 222, 255), .5)
    line(im, [(M + 30, 262), (M + 58, 290), (M + 86, 262)], 8, (226, 222, 240, 255))
    with _skip():
        d.text((SW / 2, 276), 'SLEEP STORY', font=K.font('semi', 42), fill=(196, 188, 236, 255), anchor='mm')
    K.circle(im, SW - M - 58, 276, 44, (255, 255, 255, 255), .10)
    for dx in (-16, 0, 16):
        K.circle(im, SW - M - 58 + dx, 276, 5.5, (226, 222, 240, 255))
    # artwork: a big rounded square with a soft shadow; it breathes very slightly while playing
    a = 1080 if H >= 2700 else 760
    key = (a, int(t * 4))
    if key not in _ART:
        _ART.clear(); _ART[key] = _art(a, int(t * 4) / 4)
    ax0 = (SW - a) / 2; ay0 = 380
    K.shadow(im, (ax0, ay0, ax0 + a, ay0 + a), 50, 50, (0, 26), .55)
    art = _ART[key].copy(); art.putalpha(P.rmask(a, a, 50)); im.alpha_composite(art, (int(ax0), int(ay0)))
    # title, subtitle (left, as a player lays them out)
    ty = ay0 + a + 120
    tx0 = 120; tx1 = SW - 120
    with rec_box(rec, (tx0 - 30, ty - 70, tx1, ty + 150), 'title block'):
        d.text((tx0, ty), 'The Lighthouse That Logged Off', font=K.font('semi', 58), fill=TXT, anchor='lm')
        d.text((tx0, ty + 82), 'Read by a very calm voice', font=K.font('reg', 48), fill=(186, 180, 214, 255), anchor='lm')
    # scrubber: elapsed left, the honest time left in the middle
    sy = ty + 210
    el = 2 + (1 if t >= t57 else 0)
    p = (2 + K.clamp(t - t58, 0, 1.4)) / 240.0
    rr(im, (tx0, sy - 7, tx1, sy + 7), 7, (255, 255, 255, 255), .22)
    rr(im, (tx0, sy - 7, tx0 + max(16, (tx1 - tx0) * p), sy + 7), 7, (226, 222, 240, 255))
    with rec_box(rec, (tx0 - 30, sy + 20, tx0 + 200, sy + 110), 'elapsed'):
        d.text((tx0, sy + 62), f'0:0{el}', font=K.font('semi', 44), fill=(186, 180, 214, 255), anchor='lm')
    fl = K.font('semi', 56); old, new = '3:58 left', '3:57 left'
    with rec_box(rec, (SW / 2 - 230, sy + 18, SW / 2 + 230, sy + 112), 'time left'):
        roll(im, (SW / 2 - K.text_w(old, fl) / 2, sy + 30), old, new, K.ease_io(K.lin(t, t57, t57 + .2)), fl, TXT)
    # transport: back 15, pause (it is playing), forward 15
    cy = sy + 300; col = (232, 228, 244, 255)
    for sg in (-1, 1):
        cx = SW / 2 + sg * 330
        K.ring(im, cx, cy, 58, 8, col, start=(-60 if sg > 0 else -240), end=(240 if sg > 0 else 60))
        K.poly(im, [(cx + sg * 4, cy - 76), (cx + sg * 4, cy - 40), (cx + sg * 30, cy - 58)] if sg > 0 else [(cx - 4, cy - 76), (cx - 4, cy - 40), (cx - 30, cy - 58)], col)
        with _skip():
            d.text((cx, cy + 4), '15', font=K.font('semi', 42), fill=col, anchor='mm')
    for dx in (-30, 30):
        rr(im, (SW / 2 + dx - 18, cy - 68, SW / 2 + dx + 18, cy + 68), 9, col)
    # volume
    vy = cy + 230
    if vy < H - 260:
        rr(im, (tx0 + 90, vy - 6, tx1 - 90, vy + 6), 6, (255, 255, 255, 255), .22); rr(im, (tx0 + 90, vy - 6, tx0 + 90 + (tx1 - tx0 - 180) * .35, vy + 6), 6, col)
        K.poly(im, [(tx0 + 10, vy - 10), (tx0 + 26, vy - 10), (tx0 + 46, vy - 28), (tx0 + 46, vy + 28), (tx0 + 26, vy + 10), (tx0 + 10, vy + 10)], col, .7)
        K.poly(im, [(tx1 - 66, vy - 10), (tx1 - 50, vy - 10), (tx1 - 30, vy - 28), (tx1 - 30, vy + 28), (tx1 - 50, vy + 10), (tx1 - 66, vy + 10)], col, .7)
        for r_ in (14, 28):
            K.ring(im, tx1 - 30, vy, r_, 5, col, start=-50, end=50, alpha=.7)
    # bottom row: sleep timer (moon) with the bedtime note
    by = H - 150
    if by > vy + 120:
        K.circle(im, SW / 2 - 250, by, 24, col); K.circle(im, SW / 2 - 238, by - 9, 21, (14, 12, 30, 255))
        with rec_box(rec, (SW / 2 - 230, by - 60, SW / 2 + 330, by + 60), 'bedtime'):
            d.text((SW / 2 - 200, by), 'Bedtime was 11:00 PM', font=K.font('med', 44), fill=(170, 164, 200, 255), anchor='lm')
    P.home_indicator(im, H - 26, (210, 206, 228, 255))
    return im


# =================================================================== 8D: the notes folder ("Prompts"), newest first
NOTES = [('FINAL v2', 'the font, but bolder', '4:37 AM'),
         ('FINAL', 'the font. final answer.', '3:47 AM'),
         ('for 6:00', 'pick up exactly where we were', '3:12 AM'),
         ('for later (2)', 'ok now the OTHER font', '2:31 AM'),
         ('for later', 'make the font bigger, but tastefully', '2:14 AM')]
NOTE_RH = 196
PREV_MAX_X = 1040                         # previews truncate here (also keeps 9:16 text out of the like column)


def notes(t, H=P.SH, rec=None):
    bts = K.beats_in('8D'); s = K.shot('8D')
    t_new = bts[1] if len(bts) > 1 else s['start'] + .6         # FINAL v2 arrives at the top on beat 2
    p = K.spring(t, t_new, 2.4, .9) if t >= t_new else 0.0; p = min(1.0, p)
    im = Image.new('RGBA', (SW, H), BG + (255,)); d = ImageDraw.Draw(im)
    nb = P.STATUS_H + 120
    chevron_left(im, M + 8, P.STATUS_H + 60, 1.0, ACC_A)
    with _skip():
        d.text((M + 52, P.STATUS_H + 61), 'Folders', font=K.font('reg', 54), fill=ACC_A, anchor='lm')
    more_btn(im, SW - M - 50, P.STATUS_H + 60, ACC_A)
    d.text((M + 6, nb + 92), 'Prompts', font=K.font('bold', 104), fill=TXT, anchor='lm')
    # search field
    s0 = nb + 186; s1 = s0 + 112
    rr(im, (M + 6, s0, SW - M - 6, s1), 30, (30, 30, 34, 255))
    K.ring(im, M + 62, (s0 + s1) / 2 - 5, 17, 5, (130, 130, 138, 255)); line(im, [(M + 75, (s0 + s1) / 2 + 8), (M + 90, (s0 + s1) / 2 + 23)], 6, (130, 130, 138, 255))
    with rec_box(rec, (M + 6, s0, SW - M - 6, s1), 'search'):
        d.text((M + 112, (s0 + s1) / 2), 'Search', font=K.font('reg', 52), fill=(130, 130, 138, 255), anchor='lm')
    P.mic(im, SW - M - 60, (s0 + s1) / 2 + 6, .85, (130, 130, 138, 255))
    # Today
    hy = s1 + 92
    d.text((M + 6, hy), 'Today', font=K.font('bold', 56), fill=TXT, anchor='lm')
    c0 = hy + 52
    grow = NOTE_RH * p
    n_old = 4
    c1 = c0 + NOTE_RH * n_old + grow
    rr(im, (M + 6, c0, SW - M - 6, c1), 46, CARD + (255,))
    ix = M + 54
    lay = Image.new('RGBA', (SW, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    fT, fS, fP = K.font('semi', 56), K.font('semi', 46), K.font('reg', 46)
    for i, (title, prev, tm) in enumerate(NOTES):
        if i == 0:
            if t < t_new:
                continue
            ry = c0; a = K.fade(t, t_new + .06, .16)
        else:
            ry = c0 + grow + (i - 1) * NOTE_RH; a = 1.0
        row = Image.new('RGBA', (SW, NOTE_RH), (0, 0, 0, 0)); rd = ImageDraw.Draw(row)
        ok = rec is not None and a >= 1 and (i > 0 or p > .999)
        pw_ = ix + K.text_w(tm, fS) + 26; pv = ellipsize(prev, fP, PREV_MAX_X - pw_)
        with _skip():
            rd.text((ix, 66), title, font=fT, fill=TXT, anchor='lm')
            rd.text((ix, 134), tm, font=fS, fill=SUB, anchor='lm')
            rd.text((pw_, 134), pv, font=fP, fill=DIM, anchor='lm')
        if ok:                                                   # record the placed boxes (the row lands at y = ry)
            yy = int(round(ry))
            for xy, tx, ff in (((ix, 66), title, fT), ((ix, 134), tm, fS), ((pw_, 134), pv, fP)):
                bb = rd.textbbox(xy, tx, font=ff, anchor='lm')
                rec.add(tx, (bb[0], bb[1] + yy, bb[2], bb[3] + yy), (M + 6, yy, SW - M - 6, yy + NOTE_RH), 'note row')
        if i < len(NOTES) - 1:
            rd.line([(ix, NOTE_RH - 1), (SW - M - 6, NOTE_RH - 1)], fill=CARD_SEP, width=2)
        if a < 1:
            row.putalpha(row.getchannel('A').point(lambda v: int(v * a)))
        if i == 0 and p < 1:                                     # the new row is revealed by the growing gap
            mk = Image.new('L', row.size, 0); ImageDraw.Draw(mk).rectangle((0, 0, SW, int(grow)), fill=255)
            row.putalpha(Image.fromarray(np.minimum(np.asarray(row.getchannel('A')), np.asarray(mk))))
        lay.alpha_composite(row, (0, int(round(ry))))
    im.alpha_composite(lay)
    # bottom toolbar: the count, compose (square + pencil) on the right
    tb0 = H - 196
    tb = im.crop((0, tb0 - 40, SW, H)).filter(ImageFilter.GaussianBlur(24)).crop((0, 40, SW, H - tb0 + 40))
    tb.alpha_composite(Image.new('RGBA', tb.size, (16, 16, 20, 225))); im.alpha_composite(tb, (0, tb0))
    n_vis = 4 + (1 if t >= t_new + .1 else 0)
    with _skip():
        d.text((SW / 2, tb0 + 66), f'{n_vis} Notes', font=K.font('reg', 42), fill=SUB, anchor='mm')
    cx, cy = SW - M - 64, tb0 + 66
    line(im, [(cx + 6, cy - 34), (cx - 32, cy - 34), (cx - 32, cy + 32), (cx + 32, cy + 32), (cx + 32, cy - 4)], 6, ACC_A)
    line(im, [(cx - 8, cy + 10), (cx + 30, cy - 28)], 7, ACC_A); line(im, [(cx + 30, cy - 28), (cx + 38, cy - 36)], 7, ACC_A)
    P.status_bar(im, '4:37')
    P.home_indicator(im, H - 26)
    return im


# =================================================================== 6C: the watch stand reminder (it is 3:59 AM)
WW, WH = 1000, 1200
WCORNER = 170


def stand_figure(im, cx, cy, s, p, col):
    """a little figure getting up: sitting (p=0) to standing tall, arms up in a stretch (p=1); round caps and joints"""
    w = 24 * s
    hip = (cx, cy + 50 * s * (1 - p) + 20 * s * p); sh = (cx, hip[1] - 120 * s)
    K.circle(im, cx, sh[1] - 52 * s, 32 * s, col)
    line(im, [sh, hip], w, col)
    for sg in (-1, 1):
        knee = (cx + sg * 10 * s * p + 70 * s * (1 - p), hip[1] + 70 * s * p + 6 * s * (1 - p))
        foot = (cx + sg * 30 * s * p + 70 * s * (1 - p), hip[1] + 135 * s * p + 80 * s * (1 - p))
        line(im, [hip, knee, foot], w, col)
        hand = (cx + sg * (40 + 40 * p) * s, sh[1] + (70 - 150 * p) * s)
        line(im, [(cx, sh[1] + 12 * s), hand], w, col)


def watch_screen(t, rec=None):
    s = K.shot('6C'); t_buzz = s['start'] + .04
    wake = K.ease_out(K.lin(t, t_buzz, t_buzz + .22))
    im = Image.new('RGBA', (WW, WH), (0, 0, 0, 255))
    lay = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # the time, top right, as a watch shows it over a notification
    with rec_box(rec, (640, 40, 905, 130), 'time'):
        d.text((890, 86), '3:59', font=K.font('semi', 60), fill=K.W(), anchor='rm')
    # the app glyph, top left: a small ring tile
    K.circle(lay, 150, 90, 46, (24, 52, 50, 255)); K.ring(lay, 150, 90, 28, 9, TEAL + (255,), -90, 200)
    # the ring fills a sliver (0 of 12 hours), the figure stands up as the face wakes
    p = K.ease_io(K.lin(t, t_buzz + .10, t_buzz + .55))
    K.ring(lay, WW / 2, 360, 168, 30, (24, 58, 56, 255)); K.ring(lay, WW / 2, 360, 168, 30, TEAL + (255,), -90, -90 + 360 * .05)
    stand_figure(lay, WW / 2 - 24 * (1 - p), 366, .62, p, TEAL + (255,))
    with rec_box(rec, (60, 580, WW - 60, 720), 'title'):
        d.text((WW / 2, 650), 'Time to Stand!', font=K.font('bold', 104), fill=K.W(), anchor='mm')
    with rec_box(rec, (80, 715, WW - 80, 905), 'body'):
        d.text((WW / 2, 765), "It's 3:59 AM. Stand up", font=K.font('reg', 56), fill=(170, 172, 182, 255), anchor='mm')
        d.text((WW / 2, 840), 'and move for a minute.', font=K.font('reg', 56), fill=(170, 172, 182, 255), anchor='mm')
    bx0, by0, bx1, by1 = 110, 950, WW - 110, 1080
    rr(lay, (bx0, by0, bx1, by1), 65, (44, 46, 52, 255))
    with rec_box(rec, (bx0, by0, bx1, by1), 'Dismiss'):
        d.text((WW / 2, (by0 + by1) / 2 + 2), 'Dismiss', font=K.font('semi', 58), fill=K.W(), anchor='mm')
    if wake < 1:                                                  # before it wakes: the dim always-on time (never blank)
        ao = Image.new('RGBA', (WW, WH), (0, 0, 0, 0))
        with _skip():
            ImageDraw.Draw(ao).text((WW / 2, WH / 2), '3:59', font=K.font('light', 300), fill=(120, 122, 130, int(255 * (1 - wake))), anchor='mm')
        im.alpha_composite(ao)
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * wake)))
    im.alpha_composite(lay)
    return K.clamp_white(im)


def watch_body(screen):
    """our own watch: graphite case with a soft edge highlight, black border glass, a ridged crown + side button, a sport band; no marks"""
    cw, ch = WW + 120, WH + 120; R = WCORNER + 60
    out = Image.new('RGBA', (cw + 70, ch + 900), (0, 0, 0, 0)); oy = 450
    band = Image.new('RGBA', out.size, (0, 0, 0, 0))
    rr(band, (170, 0, cw - 170, out.height), 70, (30, 32, 38, 255))
    for yy in range(30, out.height, 34):
        if abs(yy - (oy + ch / 2)) > ch / 2 + 20:
            line(band, [(200, yy), (cw - 200, yy)], 3, (40, 42, 50, 255))
    out.alpha_composite(band)
    # crown with ridges, then the side button
    rr(out, (cw - 24, oy + 300, cw + 46, oy + 500), 26, (96, 98, 106, 255))
    for k in range(9):
        yy = oy + 318 + k * 20; line(out, [(cw + 10, yy), (cw + 40, yy)], 3, (62, 64, 72, 255))
    rr(out, (cw - 16, oy + 600, cw + 22, oy + 820), 14, (80, 82, 90, 255))
    K.paste_mask(out, P.rmask(cw, ch, R), (0, oy), (100, 102, 110, 255))
    K.paste_mask(out, P.rmask(cw - 8, ch - 8, R - 4), (4, oy + 4), (54, 56, 62, 255))
    K.paste_mask(out, P.rmask(cw - 40, ch - 40, R - 20), (20, oy + 20), (3, 3, 4, 255))
    sc = screen.convert('RGBA'); sc.putalpha(P.rmask(WW, WH, WCORNER)); out.alpha_composite(sc, (60, oy + 60))
    shm = Image.new('L', out.size, 0); ImageDraw.Draw(shm).polygon([(60, oy + 40), (cw * .55, oy + 40), (60, oy + ch * .6)], fill=12)
    sheen = Image.new('RGBA', out.size, (255, 255, 255, 0)); sheen.putalpha(shm.filter(ImageFilter.GaussianBlur(50))); out.alpha_composite(sheen)
    return out, oy


def _buzz(t, t_buzz, amp):
    return math.sin((t - t_buzz) * 2 * math.pi * 24) * amp * (1 - (t - t_buzz) / .45) if t_buzz <= t <= t_buzz + .45 else 0.0


def watch_insert_16x9(screen, t):
    s = K.shot('6C'); t_buzz = s['start'] + .04
    body, oy = watch_body(screen)
    p = K.lin(t, s['start'], s['end']); scl = 1.0 * (1 + .03 * K.ease_io(p))
    b = body.resize((int(body.width * scl), int(body.height * scl)), Image.LANCZOS)
    out = P.room_plate().copy()
    glow = Image.new('RGBA', (2560, 1440), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((780, 100, 1780, 1340), fill=(100, 190, 180, int(26 * K.lin(t, t_buzz, t_buzz + .2))))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    x = 1280 - (60 + WW / 2) * scl + _buzz(t, t_buzz, 9); y = 720 - (oy + 60 + WH / 2) * scl
    sh = Image.new('RGBA', b.size, (0, 0, 0, 0)); sh.putalpha(b.getchannel('A').point(lambda v: int(v * .5))); sh = sh.filter(ImageFilter.GaussianBlur(40))
    K._paste_sub(out, sh, x + 24, y + 30); K._paste_sub(out, b, x, y)
    return K.clamp_white(out).convert('RGB')


def watch_insert_9x16(screen, t):
    """the face 0.72 W wide, a touch left of centre (its text stays clear of the like column), key text inside 13%..70%"""
    s = K.shot('6C'); t_buzz = s['start'] + .04
    body, oy = watch_body(screen); p = K.lin(t, s['start'], s['end'])
    scl = 780 / WW * (1 + .03 * K.ease_io(p))
    b = body.resize((int(body.width * scl), int(body.height * scl)), Image.LANCZOS)
    out = P.room_plate().crop((1280 - 405, 0, 1280 + 405, 1440)).resize((1080, 1920), Image.LANCZOS)
    x = 500 - (60 + WW / 2) * scl + _buzz(t, t_buzz, 6); y = 1920 * .42 - (oy + 60 + WH / 2) * scl
    K._paste_sub(out, b, x, y)
    return K.clamp_white(out).convert('RGB')


# =================================================================== laptops: a desktop of our own
LW, LH = 2560, 1600
MENU_H = 60


def menu_bar(im, app, menus, clock, light=False, battery=None):
    bg = (236, 232, 226, 235) if light else (16, 16, 20, 255); fg = (40, 36, 32, 255) if light else (214, 214, 220, 255)
    ImageDraw.Draw(im).rectangle((0, 0, LW, MENU_H), fill=bg)
    d = ImageDraw.Draw(im); x = 40
    with _skip():
        d.text((x, MENU_H / 2), app, font=K.font('semi', 34), fill=fg, anchor='lm'); x += K.text_w(app, K.font('semi', 34)) + 44
        for m in menus:
            d.text((x, MENU_H / 2), m, font=K.font('reg', 34), fill=fg, anchor='lm'); x += K.text_w(m, K.font('reg', 34)) + 40
        d.text((LW - 40, MENU_H / 2), clock, font=K.font('reg', 34), fill=fg, anchor='rm')
    cw = K.text_w(clock, K.font('reg', 34)); bx1 = LW - 40 - cw - 40; bx0 = bx1 - 52
    rr(im, (bx0, 18, bx1, 42), 7, fg, .6); rr(im, (bx0 + 3, 21, bx1 - 3, 39), 5, bg)
    lvl = .12 if battery is None else battery
    rr(im, (bx0 + 5, 23, bx0 + 5 + max(4, (bx1 - bx0 - 10) * lvl), 37), 4, (AMBER + (255,)) if lvl < .2 else fg)
    wx = bx0 - 50
    for i, r in enumerate((8, 18, 28)):
        if i == 0:
            K.circle(im, wx, 42 - 4, 4.5, fg)
        else:
            K.ring(im, wx, 42, r, 5, fg, start=-135, end=-45)


ED_BG = (24, 24, 28); ED_SIDE = (19, 19, 23); ED_BAR = (15, 15, 18); ED_LINE = (40, 40, 46, 255)
ED_TXT = (206, 206, 214, 255); ED_DIM = (120, 122, 132, 255)
EX0, EX1, ED1 = 100, 560, 1830           # activity bar | explorer | editor | assistant panel
WIN_T = MENU_H + 70                       # window title bar bottom
CODE_X = 760; LINE1_Y = 336


def _icon_files(im, cx, cy, col):
    line(im, [(cx - 16, cy - 26), (cx + 6, cy - 26), (cx + 20, cy - 12), (cx + 20, cy + 26), (cx - 16, cy + 26), (cx - 16, cy - 26)], 5, col)
    line(im, [(cx + 6, cy - 26), (cx + 6, cy - 12), (cx + 20, cy - 12)], 5, col)


def _icon_search(im, cx, cy, col):
    K.ring(im, cx - 4, cy - 4, 17, 5, col); line(im, [(cx + 9, cy + 9), (cx + 22, cy + 22)], 6, col)


def _icon_branch(im, cx, cy, col):
    K.ring(im, cx - 12, cy - 22, 7, 4, col); K.ring(im, cx - 12, cy + 22, 7, 4, col); K.ring(im, cx + 14, cy - 10, 7, 4, col)
    line(im, [(cx - 12, cy - 14), (cx - 12, cy + 14)], 4, col); line(im, [(cx + 14, cy - 2), (cx + 14, cy + 4), (cx - 10, cy + 14)], 4, col)


def _icon_blocks(im, cx, cy, col):
    for (dx, dy) in ((-14, -14), (14, 14), (-14, 14)):
        line(im, [(cx + dx - 10, cy + dy - 10), (cx + dx + 10, cy + dy - 10), (cx + dx + 10, cy + dy + 10), (cx + dx - 10, cy + dy + 10), (cx + dx - 10, cy + dy - 10)], 4, col)
    line(im, [(cx + 14, cy - 26), (cx + 26, cy - 14), (cx + 14, cy - 2), (cx + 2, cy - 14), (cx + 14, cy - 26)], 4, col)


def _icon_spark(im, cx, cy, col, s=1.0):
    K.poly(im, [(cx, cy - 26 * s), (cx + 7 * s, cy - 7 * s), (cx + 26 * s, cy), (cx + 7 * s, cy + 7 * s), (cx, cy + 26 * s), (cx - 7 * s, cy + 7 * s), (cx - 26 * s, cy), (cx - 7 * s, cy - 7 * s)], col)


def editor_cues():
    s = K.shot('5E')
    return [K.onset('5E', f'cursor blink {i + 1}', s['start'] + i * .58) for i in range(4)]


def editor(t, rec=None):
    bl = editor_cues()
    im = Image.new('RGBA', (LW, LH), ED_BG + (255,)); d = ImageDraw.Draw(im)
    menu_bar(im, 'Editor', ['File', 'Edit', 'Selection', 'View', 'Go', 'Run', 'Terminal', 'Window', 'Help'], '3:40 AM')
    # window title bar
    d.rectangle((0, MENU_H, LW, WIN_T), fill=ED_BAR + (255,))
    for i, c in enumerate(((222, 96, 88), (226, 178, 64), (96, 186, 104))):
        K.circle(im, 46 + i * 44, (MENU_H + WIN_T) / 2, 12, c + (255,))
    with rec_box(rec, (600, MENU_H, LW - 600, WIN_T), 'window title'):
        d.text((LW / 2, (MENU_H + WIN_T) / 2), 'do_it_myself.py — do_it_myself', font=K.font('reg', 36), fill=ED_DIM, anchor='mm')
    d.line([(0, WIN_T), (LW, WIN_T)], fill=ED_LINE, width=2)
    SB0 = LH - 56
    # activity bar
    d.rectangle((0, WIN_T, EX0, SB0), fill=ED_BAR + (255,))
    ic = (130, 132, 142, 255)
    rr(im, (0, WIN_T + 20, 6, WIN_T + 100), 3, (220, 220, 228, 255))
    _icon_files(im, EX0 / 2, WIN_T + 60, (220, 220, 228, 255)); _icon_search(im, EX0 / 2, WIN_T + 160, ic)
    _icon_branch(im, EX0 / 2, WIN_T + 260, ic); _icon_blocks(im, EX0 / 2, WIN_T + 360, ic); _icon_spark(im, EX0 / 2, WIN_T + 460, ic, .9)
    # explorer
    d.rectangle((EX0, WIN_T, EX1, SB0), fill=ED_SIDE + (255,)); d.line([(EX1, WIN_T), (EX1, SB0)], fill=ED_LINE, width=2)
    with rec_box(rec, (EX0, WIN_T, EX1, SB0), 'explorer'):
        d.text((EX0 + 36, WIN_T + 50), 'EXPLORER', font=K.font('semi', 34), fill=ED_DIM, anchor='lm')
        d.text((EX0 + 72, WIN_T + 124), 'DO_IT_MYSELF', font=K.font('semi', 34), fill=ED_TXT, anchor='lm')
    line(im, [(EX0 + 34, WIN_T + 116), (EX0 + 44, WIN_T + 128), (EX0 + 54, WIN_T + 116)], 4, ED_TXT)
    rr(im, (EX0 + 10, WIN_T + 162, EX1 - 10, WIN_T + 232), 8, (44, 44, 52, 255))
    rr(im, (EX0 + 76, WIN_T + 182, EX0 + 102, WIN_T + 212), 5, ACC_A)
    with rec_box(rec, (EX0 + 10, WIN_T + 162, EX1 - 10, WIN_T + 232), 'file row'):
        d.text((EX0 + 122, WIN_T + 197), 'do_it_myself.py', font=K.font('reg', 36), fill=ED_TXT, anchor='lm')
    with rec_box(rec, (EX0, SB0 - 150, EX1, SB0), 'outline'):
        d.text((EX0 + 72, SB0 - 110), 'OUTLINE', font=K.font('semi', 34), fill=ED_DIM, anchor='lm')
        d.text((EX0 + 72, SB0 - 46), 'TIMELINE', font=K.font('semi', 34), fill=ED_DIM, anchor='lm')
    for yy in (SB0 - 110, SB0 - 46):
        line(im, [(EX0 + 36, yy - 10), (EX0 + 48, yy), (EX0 + 36, yy + 10)], 4, ED_DIM)
    # tabs + breadcrumb
    TB1 = WIN_T + 84
    d.rectangle((EX1 + 2, WIN_T + 2, ED1, TB1), fill=ED_SIDE + (255,))
    tx1 = EX1 + 2 + 520
    d.rectangle((EX1 + 2, WIN_T + 2, tx1, TB1), fill=ED_BG + (255,)); d.line([(EX1 + 2, WIN_T + 3), (tx1, WIN_T + 3)], fill=ACC_A, width=4)
    rr(im, (EX1 + 34, (WIN_T + TB1) / 2 - 15, EX1 + 60, (WIN_T + TB1) / 2 + 15), 5, ACC_A)
    with rec_box(rec, (EX1 + 2, WIN_T, tx1 - 50, TB1), 'tab'):
        d.text((EX1 + 80, (WIN_T + TB1) / 2), 'do_it_myself.py', font=K.font('reg', 36), fill=ED_TXT, anchor='lm')
    line(im, [(tx1 - 44, (WIN_T + TB1) / 2 - 11), (tx1 - 22, (WIN_T + TB1) / 2 + 11)], 4, ED_DIM); line(im, [(tx1 - 22, (WIN_T + TB1) / 2 - 11), (tx1 - 44, (WIN_T + TB1) / 2 + 11)], 4, ED_DIM)
    with rec_box(rec, (EX1 + 2, TB1 - 6, ED1, TB1 + 70), 'breadcrumb'):
        d.text((EX1 + 40, TB1 + 30), 'do_it_myself  ›  do_it_myself.py', font=K.font('reg', 34), fill=ED_DIM, anchor='lm')
    # line 1: current-line band, gutter, the caret, the inline hint (an empty file's hint, as editors show)
    ly = LINE1_Y
    d.rectangle((EX1 + 2, ly - 32, ED1 - 140, ly + 32), fill=(31, 31, 37, 255))
    fm = K.font('mono', 38)
    with rec_box(rec, (EX1 + 2, ly - 34, CODE_X - 20, ly + 34), 'gutter'):
        d.text((CODE_X - 60, ly), '1', font=fm, fill=(200, 200, 208, 255), anchor='rm')
    on = any(b <= t < b + .30 for b in bl) or t < bl[0] - .3
    if on:
        rr(im, (CODE_X - 2, ly - 26, CODE_X + 2, ly + 26), 2, (226, 226, 234, 255))
    with rec_box(rec, (CODE_X, ly - 34, ED1 - 150, ly + 34), 'inline hint'):
        d.text((CODE_X + 18, ly), 'Assistant is resting.', font=K.font('mono', 38), fill=(104, 106, 118, 255), anchor='lm')
    # minimap rail
    d.rectangle((ED1 - 130, TB1 + 58, ED1, SB0), fill=(22, 22, 26, 255)); d.line([(ED1 - 130, TB1 + 58), (ED1 - 130, SB0)], fill=ED_LINE, width=1)
    rr(im, (ED1 - 120, TB1 + 70, ED1 - 30, TB1 + 82), 3, (80, 80, 88, 255), .5)
    # assistant panel
    d.rectangle((ED1, WIN_T, LW, SB0), fill=ED_SIDE + (255,)); d.line([(ED1, WIN_T), (ED1, SB0)], fill=ED_LINE, width=2)
    px0 = ED1 + 40; px1 = LW - 40
    with rec_box(rec, (ED1, WIN_T, LW - 140, TB1), 'panel header'):
        d.text((px0, (WIN_T + TB1) / 2), 'ASSISTANT', font=K.font('semi', 34), fill=ED_DIM, anchor='lm')
    more = (LW - 70, (WIN_T + TB1) / 2)
    for dx in (-14, 0, 14):
        K.circle(im, more[0] + dx, more[1], 4.5, ED_DIM)
    d.line([(ED1, TB1), (LW, TB1)], fill=ED_LINE, width=2)
    # the last exchange, earlier tonight
    fy = TB1 + 70
    q = 'one more pass on the font?'
    fq = K.font('reg', 36); qw = K.text_w(q, fq) + 64
    rr(im, (px1 - qw, fy, px1, fy + 88), 26, (46, 46, 54, 255))
    with rec_box(rec, (px1 - qw, fy, px1, fy + 88), 'her message'):
        d.text((px1 - qw + 32, fy + 44), q, font=fq, fill=ED_TXT, anchor='lm')
    with rec_box(rec, (px0 - 20, fy + 110, px1, fy + 256), 'assistant reply'):
        d.text((px0, fy + 160), 'Sure. Bumping the base size to', font=fq, fill=ED_TXT, anchor='lm')
        d.text((px0, fy + 212), '18 px and the headings to match.', font=fq, fill=ED_TXT, anchor='lm')
    # the notice card
    n0 = fy + 320; n1 = n0 + 300
    rr(im, (px0, n0, px1, n1), 22, (60, 46, 30, 255)); rr(im, (px0 + 2, n0 + 2, px1 - 2, n1 - 2), 20, (36, 30, 24, 255))
    K.circle(im, px0 + 56, n0 + 66, 22, ACC_A)
    with _skip():
        d.text((px0 + 56, n0 + 67), '!', font=K.font('bold', 32), fill=(36, 30, 24, 255), anchor='mm')
    with rec_box(rec, (px0, n0, px1, n1), 'notice'):
        d.text((px0 + 100, n0 + 66), 'Assistant is resting', font=K.font('semi', 40), fill=ED_TXT, anchor='lm')
        d.text((px0 + 100, n0 + 136), 'Usage limit reached.', font=K.font('reg', 36), fill=ED_DIM, anchor='lm')
        d.text((px0 + 100, n0 + 186), 'Back at 6:00.', font=K.font('reg', 36), fill=ED_DIM, anchor='lm')
        d.text((px0 + 100, n0 + 248), 'You have got this.', font=K.font('semi', 38), fill=ED_TXT, anchor='lm')
    # the composer, disabled
    c1 = SB0 - 40; c0 = c1 - 200
    rr(im, (px0, c0, px1, c1), 24, (52, 52, 60, 255)); rr(im, (px0 + 2, c0 + 2, px1 - 2, c1 - 2), 22, (28, 28, 33, 255))
    with rec_box(rec, (px0, c0, px1, c1), 'composer'):
        d.text((px0 + 36, c0 + 62), 'Back at 6:00 AM', font=K.font('reg', 36), fill=(90, 92, 102, 255), anchor='lm')
    K.circle(im, px1 - 54, c1 - 52, 30, (52, 52, 60, 255))
    line(im, [(px1 - 54, c1 - 38), (px1 - 54, c1 - 66)], 5, (110, 110, 120, 255)); line(im, [(px1 - 66, c1 - 55), (px1 - 54, c1 - 67), (px1 - 42, c1 - 55)], 5, (110, 110, 120, 255))
    # status bar (neutral, not blue)
    d.rectangle((0, SB0, LW, LH), fill=(30, 30, 36, 255)); d.line([(0, SB0), (LW, SB0)], fill=ED_LINE, width=2)
    with _skip():
        _icon_branch(im, 44, SB0 + 28, (190, 190, 198, 255))
        d.text((74, SB0 + 28), 'main', font=K.font('reg', 34), fill=(190, 190, 198, 255), anchor='lm')
        d.text((ED1 - 40, SB0 + 28), 'Ln 1, Col 1    Spaces: 4    UTF-8    Python', font=K.font('reg', 34), fill=(190, 190, 198, 255), anchor='rm')
    _icon_spark(im, LW - 60, SB0 + 28, (226, 160, 60, 255), .7)
    with _skip():
        d.text((LW - 92, SB0 + 28), 'Resting', font=K.font('reg', 34), fill=(226, 160, 60, 255), anchor='rm')
    return K.clamp_white(im)


ED9_BOX = (EX1 - 20, 130, EX1 - 20 + 810, 1570)            # the 9:16 crop of the editor: gutter, caret, the inline hint


# =================================================================== 13E: morning, the first prompt (light, warm)
PR_BG = (238, 234, 227); PR_RAIL = (230, 226, 218); PR_INK = (44, 40, 36, 255); PR_DIM = (134, 128, 120, 255)
CB = (560, 820, LW - 560, 1080)                           # the composer box (same place as the approved layer: the overlay sits on it)


def prompt(t, rec=None, opaque=True):
    s = K.shot('13E'); t_type = s['start'] + 2.4; per = .075; txt = 'Make the font bigger.'
    im = Image.new('RGBA', (LW, LH), (PR_BG + (255,)) if opaque else (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if opaque:
        menu_bar(im, 'Assistant', ['File', 'Edit', 'View', 'Window', 'Help'], '6:00 AM', light=True, battery=1.0)
        # collapsed sidebar rail: toggle, new chat, search; her avatar at the bottom
        d.rectangle((0, MENU_H, 110, LH), fill=PR_RAIL + (255,)); d.line([(110, MENU_H), (110, LH)], fill=(218, 212, 202, 255), width=2)
        rc = (120, 114, 106, 255)
        line(im, [(32, MENU_H + 52), (78, MENU_H + 52), (78, MENU_H + 92), (32, MENU_H + 92), (32, MENU_H + 52)], 4, rc); line(im, [(48, MENU_H + 54), (48, MENU_H + 90)], 4, rc)
        line(im, [(55, MENU_H + 150), (55, MENU_H + 190)], 5, rc); line(im, [(35, MENU_H + 170), (75, MENU_H + 170)], 5, rc)
        K.ring(im, 52, MENU_H + 262, 15, 4, rc); line(im, [(63, MENU_H + 273), (75, MENU_H + 285)], 5, rc)
        K.circle(im, 55, LH - 70, 30, (200, 150, 120, 255))
        with _skip():
            d.text((55, LH - 69), 'A', font=K.font('semi', 32), fill=(250, 246, 240, 255), anchor='mm')
        fs = ImageFont.truetype(os.path.join(K.FD, 'InstrumentSerif-Regular.ttf'), 150)
        with rec_box(rec, (400, 480, LW - 400, 720), 'heading'):
            d.text((LW / 2, 610), 'Where were we?', font=fs, fill=(52, 46, 40, 255), anchor='mm')
    bx0, by0, bx1, by1 = CB
    K.shadow(im, (bx0, by0, bx1, by1), 40, 30, (0, 12), .14)
    rr(im, (bx0, by0, bx1, by1), 40, (214, 208, 198, 255) if opaque else (214, 208, 198, 240))
    rr(im, (bx0 + 2, by0 + 2, bx1 - 2, by1 - 2), 38, (250, 248, 244, 255) if opaque else (250, 248, 244, 240))
    n = int(K.clamp((t - t_type) / per, 0, len(txt))); shown = txt[:n]
    f = K.font('reg', 60)
    with rec_box(rec, (bx0, by0, bx1, by1 - 90), 'composer text'):
        if shown:
            d.text((bx0 + 60, by0 + 84), shown, font=f, fill=(36, 34, 32, 255), anchor='lm')
        elif t < t_type:
            d.text((bx0 + 60, by0 + 84), 'Ask anything', font=f, fill=(150, 144, 136, 255), anchor='lm')
    cx = bx0 + 60 + (K.text_w(shown, f) + 4 if shown else -2)
    if (0 < n < len(txt)) or ((t * 1.9) % 1 < .55):
        rr(im, (cx, by0 + 52, cx + 4, by0 + 116), 2, (36, 34, 32, 255))
    # bottom row of the composer: + (attach), a tools glyph, dictation, send
    ry = by1 - 62; ic = (120, 114, 106, 255)
    K.ring(im, bx0 + 70, ry, 30, 3.5, (200, 194, 184, 255)); line(im, [(bx0 + 70, ry - 14), (bx0 + 70, ry + 14)], 4, ic); line(im, [(bx0 + 56, ry), (bx0 + 84, ry)], 4, ic)
    K.ring(im, bx0 + 150, ry, 30, 3.5, (200, 194, 184, 255))
    for dy in (-9, 0, 9):
        line(im, [(bx0 + 136, ry + dy), (bx0 + 164, ry + dy)], 3.5, ic)
    P.mic(im, bx1 - 186, ry + 5, .8, ic)
    ready = K.fade(t, t_type + per * len(txt), .15)
    col = tuple(int(a + (b - a) * ready) for a, b in zip((206, 200, 190), (52, 46, 40))) + (255,)
    K.circle(im, bx1 - 76, ry, 36, col)
    line(im, [(bx1 - 76, ry + 16), (bx1 - 76, ry - 16)], 6, (250, 248, 244, 255)); line(im, [(bx1 - 92, ry - 1), (bx1 - 76, ry - 17), (bx1 - 60, ry - 1)], 6, (250, 248, 244, 255))
    if opaque:
        # three suggestion chips under the composer
        chips = ['Pick up where we left off', 'Fonts', 'Plan my morning']; fc = K.font('reg', 36)
        ws = [K.text_w(c, fc) + 80 for c in chips]; gap = 24; x = LW / 2 - (sum(ws) + gap * 2) / 2; cy0 = by1 + 60
        for c, w in zip(chips, ws):
            rr(im, (x, cy0, x + w, cy0 + 78), 39, (220, 214, 204, 255)); rr(im, (x + 2, cy0 + 2, x + w - 2, cy0 + 76), 37, PR_BG + (255,))
            with rec_box(rec, (x, cy0, x + w, cy0 + 78), 'chip'):
                d.text((x + w / 2, cy0 + 39), c, font=fc, fill=PR_DIM, anchor='mm')
            x += w + gap
    return K.clamp_white(im)
