"""Her phone: screens of our own (rl_screens). One design system, night mode (it is 2 to 5 AM), no maker's marks, no real logos.

Each screen is a function of time drawn on the phone's screen texture (1320 x 2868). run_phone.py writes, per insert:
  screen/  the texture (RGB), for a 3D phone and as the source
  16x9/    2560 x 1440: the phone close, filling the frame, her room soft behind (the 2D insert)
  9x16/    1080 x 1920: the screen is the frame (key lines inside the safe zone)
Body text is 54 px on the texture: 61 px in the 16:9 insert, 44 px in 9:16. Nothing is smaller than 42 px on the texture.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

SW, SH = 1320, 2772                 # the yoga-block phone in blroom: RM_phone_s 0.060 x 0.126 m
BG = (14, 15, 20); CARD = (30, 32, 40); CARD2 = (40, 43, 53); TXT = K.W(); SUB = (150, 154, 166, 255); DIM = (104, 108, 120, 255)
AMBER = (240, 170, 60)
SIDE = 72                        # side margin


def status_bar(im, clock, battery=3):
    d = ImageDraw.Draw(im); f = K.font('semi', 52)
    d.text((SIDE + 40, 92), clock, font=f, fill=TXT, anchor='lm')
    K.circle(im, SW / 2, 92, 22, (4, 4, 6, 255))                                   # the camera
    x = SW - SIDE - 40
    # battery: 3%, the charger is across the room
    K.rrect(im, (x - 108, 70, x - 12, 114), 13, (120, 124, 134, 255)); K.rrect(im, (x - 104, 74, x - 16, 110), 10, BG + (255,))
    K.rrect(im, (x - 100, 78, x - 100 + max(6, 84 * battery / 100), 106), 7, AMBER + (255,)); K.rrect(im, (x - 8, 84, x - 2, 100), 3, (120, 124, 134, 255))
    d.text((x - 124, 92), f'{battery}%', font=K.font('semi', 44), fill=AMBER + (255,), anchor='rm')
    for i in range(4):                                                               # signal
        h = 14 + i * 9; K.rrect(im, (x - 300 + i * 20, 106 - h, x - 286 + i * 20, 106), 4, TXT)


def card(im, box, r=54, fill=CARD):
    K.rrect(im, box, r, fill + (255,))


def label(d, xy, txt, f=None, fill=SUB, anchor='la'):
    d.text(xy, txt, font=f or K.font('semi', 42), fill=fill, anchor=anchor)


def spinner(im, cx, cy, t, a):
    for i in range(8):
        ang = i / 8 * 2 * math.pi; k = ((i / 8) - t * 1.6) % 1.0
        x0, y0 = cx + math.cos(ang) * 26, cy + math.sin(ang) * 26; x1, y1 = cx + math.cos(ang) * 46, cy + math.sin(ang) * 46
        m = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(m).line([(x0, y0), (x1, y1)], fill=K.W(int(255 * a * (.25 + .75 * k))), width=10)
        im.alpha_composite(m.crop((int(cx - 60), int(cy - 60), int(cx + 60), int(cy + 60))), (int(cx - 60), int(cy - 60)))


def rolling_text(im, xy, old, new, p, f, fill, anchor='la'):
    """digits that changed roll up (old out the top, new in from below); p 0..1"""
    d = ImageDraw.Draw(im)
    if p <= 0 or old == new:
        d.text(xy, old if p <= 0 else new, font=f, fill=fill, anchor=anchor); return
    # common prefix stays; the changed tail rolls inside a clip
    n = 0
    while n < min(len(old), len(new)) and old[n] == new[n]:
        n += 1
    pre = old[:n]; d.text(xy, pre, font=f, fill=fill, anchor=anchor)
    x = xy[0] + K.text_w(pre, f); asc, desc = f.getmetrics(); h = asc + desc
    # the window is exactly this line's box, so a roll never reaches the line below; a short travel with a fade, like a modern counter
    tile = Image.new('RGBA', (int(max(K.text_w(old[n:], f), K.text_w(new[n:], f)) + 10), int(h)), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    e = K.ease_io(p); tr = .55 * h
    td.text((0, -e * tr), old[n:], font=f, fill=fill[:3] + (int(fill[3] * (1 - e) ** 2),), anchor='la'); td.text((0, (1 - e) * tr), new[n:], font=f, fill=fill[:3] + (int(fill[3] * e ** .7),), anchor='la')
    im.alpha_composite(tile, (int(x), int(xy[1])))


# ------------------------------------------------------------------ 3C: the usage page, pulled to refresh three times
def usage(t, sid='3C', rec=None):
    s = K.shot(sid); b = K.beats_in(sid) + [s['end']]
    pulls = [K.onset(sid, f'refresh {i + 1}', b[i]) for i in range(3)]; t_after = min(K.onset(sid, 'page changes', b[3] if len(b) > 3 else s['end'] - .5) - .08, s['end'] - .30)   # 'after' is sung 2 frames past the cut: the minute turns just before it
    off = 0.0; spin_a = 0.0
    for tp in pulls:                                    # each pull: drag down (0.18 s), hold with the spinner, spring back
        if t >= tp:
            x = t - tp
            down = K.ease_out(K.lin(x, 0, .16)); back = K.spring(t, tp + .30, 3.0, .62)
            o = 250 * down * (1 - back); off = max(off, o); spin_a = max(spin_a, K.clamp(o / 200))
    minute_p = K.ease_io(K.lin(t, t_after, t_after + .22))
    im = Image.new('RGBA', (SW, SH), BG + (255,)); status_bar(im, '2:08')
    if spin_a > .01:
        spinner(im, SW / 2, 330 + off * .45, t, spin_a)
    page = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(page)
    d.text((SIDE, 250), '‹ Settings', font=K.font('med', 54), fill=(120, 170, 255, 255), anchor='lm')
    d.text((SIDE, 400), 'Usage', font=K.font('bold', 120), fill=TXT, anchor='lm')
    # the hero card
    cy0 = 520; cy1 = 1480; card(page, (SIDE, cy0, SW - SIDE, cy1))
    label(d, (SIDE + 64, cy0 + 70), 'CURRENT SESSION')
    K.rrect(page, (SW - SIDE - 64 - 190, cy0 + 52, SW - SIDE - 64, cy0 + 128), 38, K.RED + (255,))
    d.text((SW - SIDE - 64 - 95, cy0 + 90), '429', font=K.font('bold', 56), fill=TXT, anchor='mm')
    d.text((SIDE + 64, cy0 + 230), 'Usage limit reached', font=K.font('bold', 86), fill=TXT, anchor='lm')
    K.rrect(page, (SIDE + 64, cy0 + 330, SW - SIDE - 64, cy0 + 372), 21, (60, 30, 32, 255)); K.rrect(page, (SIDE + 64, cy0 + 330, SW - SIDE - 64, cy0 + 372), 21, K.RED + (255,))
    label(d, (SIDE + 64, cy0 + 410), '100% used', K.font('semi', 46), SUB); label(d, (SW - SIDE - 64, cy0 + 410), 'since 11:58 PM', K.font('semi', 46), SUB, 'ra')
    d.line([(SIDE + 64, cy0 + 520), (SW - SIDE - 64, cy0 + 520)], fill=(52, 55, 66, 255), width=3)
    label(d, (SIDE + 64, cy0 + 570), 'RESETS IN')
    rolling_text(page, (SIDE + 60, cy0 + 640), '3h 52m', '3h 51m', minute_p, K.font('bold', 190), TXT)
    rolling_text(page, (SIDE + 64, cy0 + 870), 'Retry-After: 13920', 'Retry-After: 13860', minute_p, K.font('mono', 46), DIM)
    # this week
    wy0 = cy1 + 48; wy1 = wy0 + 440; card(page, (SIDE, wy0, SW - SIDE, wy1))
    label(d, (SIDE + 64, wy0 + 70), 'THIS WEEK')
    d.text((SIDE + 64, wy0 + 190), '64% used', font=K.font('bold', 72), fill=TXT, anchor='lm')
    K.rrect(page, (SIDE + 64, wy0 + 270, SW - SIDE - 64, wy0 + 302), 16, (52, 55, 66, 255)); K.rrect(page, (SIDE + 64, wy0 + 270, SIDE + 64 + int((SW - 2 * SIDE - 128) * .64), wy0 + 302), 16, (120, 170, 255, 255))
    label(d, (SIDE + 64, wy0 + 330), 'Resets Thursday, 9:00 AM', K.font('semi', 46), SUB)
    # a tip
    ty0 = wy1 + 48; ty1 = ty0 + 260; card(page, (SIDE, ty0, SW - SIDE, ty1))
    gx, gy = SIDE + 120, ty0 + 130                                   # a glass of water, drawn
    K.poly(page, [(gx - 40, gy - 62), (gx + 40, gy - 62), (gx + 31, gy + 62), (gx - 31, gy + 62)], (120, 170, 255, 255), .30)
    K.poly(page, [(gx - 35, gy - 20), (gx + 35, gy - 20), (gx + 30, gy + 56), (gx - 30, gy + 56)], (120, 170, 255, 255), .75)
    d.text((SIDE + 220, ty0 + 96), 'While you wait', font=K.font('semi', 54), fill=TXT, anchor='lm')
    d.text((SIDE + 220, ty0 + 168), 'Maybe drink some water.', font=K.font('reg', 50), fill=SUB, anchor='lm')
    if rec is not None:
        _rec_texts(rec, d, [((SIDE + 64, cy0 + 230), 'Usage limit reached', K.font('bold', 86), 'lm', (SIDE, cy0, SW - SIDE, cy1)),
                            ((SIDE + 60, cy0 + 640), '3h 51m', K.font('bold', 190), 'la', (SIDE, cy0, SW - SIDE, cy1)),
                            ((SIDE + 64, cy0 + 870), 'Retry-After: 13860', K.font('mono', 46), 'la', (SIDE, cy0, SW - SIDE, cy1)),
                            ((SIDE + 220, ty0 + 168), 'Maybe drink some water.', K.font('reg', 50), 'lm', (SIDE, ty0, SW - SIDE, ty1)),
                            ((SIDE + 64, wy0 + 330), 'Resets Thursday, 9:00 AM', K.font('semi', 46), 'la', (SIDE, wy0, SW - SIDE, wy1))])
    im.alpha_composite(page, (0, int(off)))
    return im


def _rec_texts(rec, d, items):
    for xy, txt, f, anc, box in items:
        rec.add(txt, d.textbbox(xy, txt, font=f, anchor=anc), box, 'card')


# ------------------------------------------------------------------ 6B: the wind-down app offers a sleep story; it ticks honestly
def sleep_story(t, sid='6B', rec=None):
    s = K.shot(sid); t58 = K.onset(sid, 'fifty-eight', s['start'] + .12); t57 = t58 + 1.0
    y = np.linspace(0, 1, SH)[:, None]; x = np.linspace(0, 1, SW)[None, :]
    g = np.zeros((SH, SW, 3), np.float32); g[..., 0] = 22 + 20 * (1 - y) + 6 * x; g[..., 1] = 18 + 12 * (1 - y); g[..., 2] = 52 + 46 * (1 - y)
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA')
    # the moon and a few stars, very soft (our own drawing)
    glow = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((330, 330, 990, 990), fill=(200, 190, 255, 60)); im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    K.circle(im, SW / 2, 660, 210, (232, 226, 246, 255)); K.circle(im, SW / 2 + 92, 610, 190, (40, 34, 86, 255))   # a crescent
    for i, (sx, sy, r) in enumerate(((260, 420, 7), (1080, 360, 6), (1010, 900, 5), (300, 980, 6), (1150, 640, 4), (190, 700, 4), (860, 300, 5))):
        tw_ = .55 + .45 * math.sin(t * 2.1 + i * 1.7); K.circle(im, sx, sy, r, (230, 226, 250, 255), tw_)
    status_bar(im, '3:59')
    d = ImageDraw.Draw(im)
    d.text((SW / 2, 1080), 'SLEEP STORY', font=K.font('semi', 48), fill=(186, 176, 236, 255), anchor='mm')
    d.text((SW / 2, 1210), 'The Lighthouse', font=K.font('bold', 96), fill=TXT, anchor='mm')
    d.text((SW / 2, 1320), 'That Logged Off', font=K.font('bold', 96), fill=TXT, anchor='mm')
    d.text((SW / 2, 1430), 'Read by a very calm voice', font=K.font('reg', 50), fill=SUB, anchor='mm')
    # the scrubber, barely started
    sx0, sx1, sy = SIDE + 60, SW - SIDE - 60, 1600
    el = 2 + max(0, t - t58)                                        # seconds in
    p = el / (el + 238)
    K.rrect(im, (sx0, sy - 9, sx1, sy + 9), 9, (90, 86, 140, 255)); K.rrect(im, (sx0, sy - 9, sx0 + max(20, (sx1 - sx0) * p), sy + 9), 9, (214, 206, 250, 255))
    K.circle(im, sx0 + (sx1 - sx0) * p, sy, 22, K.W()[:3] + (255,))
    d.text((sx0, sy + 60), f'0:{int(el):02d}', font=K.font('semi', 46), fill=SUB, anchor='la')
    # the line the song sings: big, and honest
    old, new = '3:58 left', '3:57 left'
    rolling_text(im, (SW / 2 - K.text_w(old, K.font('bold', 150)) / 2, 1720), old, new, K.ease_io(K.lin(t, t57, t57 + .2)), K.font('bold', 150), TXT)
    # play/pause
    K.circle(im, SW / 2, 2170, 120, (232, 226, 246, 255))
    for dx in (-26, 26): K.rrect(im, (SW / 2 + dx - 14, 2120, SW / 2 + dx + 14, 2220), 7, (40, 34, 86, 255))
    d.text((SW / 2, 2420), 'Bedtime was 11:00 PM', font=K.font('med', 48), fill=DIM, anchor='mm')
    if rec is not None:
        rec.add('3:58 left', d.textbbox((SW / 2 - K.text_w(old, K.font('bold', 150)) / 2, 1720), old, font=K.font('bold', 150)), (0, 1690, SW, 1920), 'timer band')
        for yy, txt, f in ((1210, 'The Lighthouse', K.font('bold', 96)), (1320, 'That Logged Off', K.font('bold', 96))):
            rec.add(txt, d.textbbox((SW / 2, yy), txt, font=f, anchor='mm'), (SIDE, 1140, SW - SIDE, 1400), 'title band (no box)')
    return im


# ------------------------------------------------------------------ 7G / 7H: the group chat (read receipts in clock order)
GREY_B = (52, 54, 64)


def _chat_bubble(txt, f, maxw, color, tcol=TXT, padx=44, pady=26):
    lines = []
    cur = ''
    for w in txt.split(' '):
        tt = (cur + ' ' + w).strip()
        if K.text_w(tt, f) > maxw - 2 * padx and cur:
            lines.append(cur); cur = w
        else:
            cur = tt
    lines.append(cur)
    lh = int(f.size * 1.28); w = int(max(K.text_w(l, f) for l in lines) + 2 * padx); h = int(lh * len(lines) + 2 * pady - (lh - f.size * 1.18))
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); K.rrect(im, (0, 0, w, h), min(56, h / 2), color + (255,)); d = ImageDraw.Draw(im)
    tb = None
    for i, l in enumerate(lines):
        d.text((padx, pady + i * lh), l, font=f, fill=tcol, anchor='la'); b = d.textbbox((padx, pady + i * lh), l, font=f, anchor='la')
        tb = b if tb is None else (min(tb[0], b[0]), min(tb[1], b[1]), max(tb[2], b[2]), max(tb[3], b[3]))
    return im, tb


def avatar(im, cx, cy, r, ch, col):
    K.circle(im, cx, cy, r, col + (255,)); ImageDraw.Draw(im).text((cx, cy + 2), ch, font=K.font('semi', int(r * 1.0)), fill=(20, 20, 26, 255), anchor='mm')


FRIENDS = {'Maya': ((242, 160, 120), 'M'), 'Jo': ((150, 210, 170), 'J'), 'Priya': ((190, 170, 250), 'P')}


def chat(t, sid='7G', rec=None, reply=False):
    s = K.shot(sid); bts = K.beats_in(sid)
    t_tool = K.onset(sid, 'tool', 120.42)          # 'tool' measured on build/vocals16.wav
    im = Image.new('RGBA', (SW, SH), BG + (255,)); status_bar(im, '4:28' if not reply else '4:35'); d = ImageDraw.Draw(im)
    # header
    d.text((SIDE, 250), '‹', font=K.font('med', 80), fill=(120, 170, 255, 255), anchor='lm')
    for i, (n, (c, ch)) in enumerate(FRIENDS.items()): avatar(im, SW / 2 - 70 + i * 70, 250, 52, ch, c)
    d.text((SW / 2, 370), 'Brunch Committee', font=K.font('semi', 54), fill=TXT, anchor='mm')
    d.line([(0, 440), (SW, 440)], fill=(36, 38, 46, 255), width=3)
    f = K.font('reg', 64); fn = K.font('semi', 44); maxw = 900
    y = 520
    def sep(txt):
        nonlocal y
        d.text((SW / 2, y + 30), txt, font=K.font('semi', 44), fill=DIM, anchor='mm'); y += 110
    def incoming(name, txt, a=1.0, sc=1.0):
        nonlocal y
        c, ch = FRIENDS[name]; spr, tb = _chat_bubble(txt, f, maxw, GREY_B)
        if a > 0:
            lay = Image.new('RGBA', (SW, spr.height + 80), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.text((SIDE + 150, 0), name, font=fn, fill=SUB, anchor='la')
            K.sprite_scaled(lay, spr, (SIDE + 130, 56 + spr.height), (0, 1), sc, 1)
            avatar(lay, SIDE + 50, 56 + spr.height - 50, 50, ch, c)
            if a < 1:
                lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
            im.alpha_composite(lay, (0, int(y)))
            if rec is not None and a >= 1:
                rec.add(txt, (SIDE + 130 + tb[0], y + 56 + tb[1], SIDE + 130 + tb[2], y + 56 + tb[3]), (SIDE + 130, y + 56, SIDE + 130 + spr.width, y + 56 + spr.height), 'bubble')
        y += spr.height + 56 + 34
    sep('Tue 9:14 PM')
    incoming('Maya', 'you alive?')
    sep('Today 4:26 AM')
    incoming('Jo', 'it is 4 am')
    # Priya's line lands on 'tool'
    a = 1.0 if reply else K.fade(t, t_tool - .04, .1); sc = 1.0 if reply else .78 + .22 * K.spring(t, t_tool - .04, 3.4, .45)
    if reply or t >= t_tool - .04:
        incoming('Priya', 'he is A TOOL', a, sc)
    # read receipts under the last message, in clock order
    if reply or t >= t_tool + .25:
        ra = 1.0 if reply else K.fade(t, t_tool + .25, .15)
        lay = Image.new('RGBA', (SW, 70), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((SW - SIDE, 10), 'Seen by Maya 4:27 · Jo 4:27 · you 4:28', font=K.font('med', 42), fill=DIM, anchor='ra')
        if ra < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * ra)))
        im.alpha_composite(lay, (0, int(y - 20)))
        if rec is not None and ra >= 1:
            rec.add('Seen by Maya 4:27 · Jo 4:27 · you 4:28', ImageDraw.Draw(im).textbbox((SW - SIDE, y - 10), 'Seen by Maya 4:27 · Jo 4:27 · you 4:28', font=K.font('med', 42), anchor='ra'), None, 'receipts')
        y += 90
    if reply:
        sid2 = '7H'; s2 = K.shot(sid2); t_send = K.onset(sid2, 'sends', s2['start']) + .03
        if t >= t_send:
            spr, tb = _chat_bubble("Don't talk about him like that.", K.font('reg', 64), SW - 2 * SIDE - 40, K.BLUE)
            sc = .74 + .26 * K.spring(t, t_send, 3.2, .5); a = K.fade(t, t_send, .1)
            K.sprite_scaled(im, spr, (SW - SIDE, y + spr.height), (1, 1), sc, a)
            if rec is not None:
                rec.add("Don't talk about him like that.", (SW - SIDE - spr.width + tb[0], y + tb[1], SW - SIDE - spr.width + tb[2], y + tb[3]), (SW - SIDE - spr.width, y, SW - SIDE, y + spr.height), 'bubble')
            y += spr.height + 20
            if t >= t_send + .6:
                d.text((SW - SIDE - 8, y + 6), 'Delivered', font=K.font('semi', 42), fill=DIM, anchor='ra')
    # the compose bar
    K.rrect(im, (SIDE, SH - 330, SW - SIDE, SH - 200), 65, CARD + (255,))
    d.text((SIDE + 60, SH - 265), 'Message', font=K.font('reg', 54), fill=DIM, anchor='lm')
    return im


# ------------------------------------------------------------------ 8D: the notes app, every note a prompt she could not send
NOTES = [('for later', 'make the font bigger, but tastefully', '2:14 AM'),
         ('for later (2)', 'ok now the OTHER font', '2:31 AM'),
         ('for 6:00', 'pick up exactly where we were', '3:12 AM'),
         ('FINAL', 'the font. final answer.', '3:47 AM'),
         ('FINAL v2', 'the font, but bolder', '4:37 AM')]


def notes(t, sid='8D', rec=None):
    s = K.shot(sid); bts = K.beats_in(sid)
    t_new = bts[1] if len(bts) > 1 else s['start'] + .6                # FINAL v2 slides in on beat 2
    im = Image.new('RGBA', (SW, SH), BG + (255,)); status_bar(im, '4:37'); d = ImageDraw.Draw(im)
    d.text((SIDE, 250), '‹ Folders', font=K.font('med', 54), fill=(240, 196, 90, 255), anchor='lm')
    d.text((SIDE, 410), 'Prompts', font=K.font('bold', 120), fill=TXT, anchor='lm')
    n_vis = 4 + (1 if t >= t_new else 0)
    d.text((SIDE, 530), f'{n_vis} notes · 0 sent', font=K.font('semi', 46), fill=SUB, anchor='lm')
    y0 = 620; rh = 250
    p_new = K.ease_out(K.lin(t, t_new, t_new + .32)); grow = rh * p_new
    total_h = rh * 4 + grow
    card(im, (SIDE, y0, SW - SIDE, y0 + total_h), 50)
    for i, (title, prev, tm) in enumerate(NOTES):
        if i == 4 and t < t_new:
            break
        ry = y0 + i * rh; a = 1.0 if i < 4 else K.fade(t, t_new + .08, .18)
        lay = Image.new('RGBA', (SW, rh), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((SIDE + 60, 70), title, font=K.font('bold', 66), fill=TXT, anchor='lm')
        ld.text((SIDE + 60, 160), tm, font=K.font('semi', 48), fill=SUB, anchor='lm')
        tw = K.text_w(tm, K.font('semi', 48))
        ld.text((SIDE + 60 + tw + 30, 160), prev, font=K.font('reg', 48), fill=DIM, anchor='lm')
        if i < 4:
            ld.line([(SIDE + 60, rh - 2), (SW - SIDE, rh - 2)], fill=(48, 51, 62, 255), width=3)
        if a < 1:
            lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
        if i == 4:
            mask = Image.new('L', lay.size, 0); ImageDraw.Draw(mask).rectangle((0, 0, SW, int(grow)), fill=255)
            lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel('A')), np.asarray(mask))))
        im.alpha_composite(lay, (0, int(ry)))
        if rec is not None and a >= 1:
            rec.add(title, d.textbbox((SIDE + 60, ry + 70), title, font=K.font('bold', 66), anchor='lm'), (SIDE, ry, SW - SIDE, ry + rh), 'note row')
            rec.add(prev, d.textbbox((SIDE + 60 + tw + 30, ry + 160), prev, font=K.font('reg', 48), anchor='lm'), (SIDE, ry, SW - SIDE, ry + rh), 'note row')
    # the new-note button, amber
    K.circle(im, SW - SIDE - 90, SH - 330, 90, (240, 196, 90, 255))
    d.line([(SW - SIDE - 90 - 34, SH - 330), (SW - SIDE - 90 + 34, SH - 330)], fill=(30, 24, 10, 255), width=12); d.line([(SW - SIDE - 90, SH - 364), (SW - SIDE - 90, SH - 296)], fill=(30, 24, 10, 255), width=12)
    return im


# ------------------------------------------------------------------ the 2D inserts: phone close in her room (16:9), screen as the frame (9:16)
_BG = {}


def room_plate():
    if 'p' not in _BG:
        src = os.path.join(K.SONG, 'build', 'sets', 'room', 'room_back_to_back.png')
        im = Image.open(src).convert('RGB'); w, h = im.size
        im = im.crop((int(w * .40), int(h * .25), int(w * .95), int(h * .25) + int(w * .55 * 9 / 16))).resize((2560, 1440), Image.LANCZOS)
        im = im.filter(ImageFilter.GaussianBlur(46))
        a = np.asarray(im).astype(np.float32) * np.array([.34, .33, .38]); _BG['p'] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    return _BG['p']


def phone_body(screen):
    """our own phone: graphite body, a thin satin edge, the screen inset; no marks"""
    bw, bh = SW + 64, SH + 64; R = 186
    body = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    K.rrect(body, (0, 0, bw, bh), R, (58, 60, 66, 255)); K.rrect(body, (4, 4, bw - 4, bh - 4), R - 4, (24, 25, 29, 255))
    m = K.rrect_mask(SW, SH, 150); sc = screen.convert('RGBA'); sc.putalpha(m); body.alpha_composite(sc, (32, 32))
    # the faintest glass sheen across the screen
    sh = Image.new('L', (bw, bh), 0); ImageDraw.Draw(sh).polygon([(bw * .1, 0), (bw * .5, 0), (bw * .1, bh * .55), (0, bh * .55), (0, bh * .2)], fill=12)
    sheen = Image.new('RGBA', (bw, bh), (255, 255, 255, 0)); sheen.putalpha(Image.fromarray(np.minimum(np.asarray(sh.filter(ImageFilter.GaussianBlur(60))), np.asarray(K.rrect_mask(bw, bh, R)))))
    body.alpha_composite(sheen)
    return body


def insert_16x9(screen, t, t0, t1, focus_y, base_sc=1.136):
    """the phone close: screen 1500 px wide, tilted 5 degrees, the focus line of the screen at 46% height; a slow push and drift"""
    p = K.lin(t, t0, t1); sc = base_sc * (1 + .035 * K.ease_io(p)); ang = -5 + 1.2 * K.ease_io(p)
    body = phone_body(screen); bw, bh = body.size
    out = room_plate().copy()
    # the screen's light on the room, very soft
    glow = Image.new('RGBA', (2560, 1440), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((500, -200, 2060, 1640), fill=(120, 140, 200, 34)); out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    bs = body.resize((int(bw * sc), int(bh * sc)), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
    # where the focus point of the screen lands after scale+rotate
    fx, fy = (bw / 2) * sc, (32 + focus_y) * sc; cx0, cy0 = bw * sc / 2, bh * sc / 2; a = math.radians(ang)
    rx = (fx - cx0) * math.cos(a) + (fy - cy0) * math.sin(a); ry = -(fx - cx0) * math.sin(a) + (fy - cy0) * math.cos(a)
    tx = 1280 + 60 * (1 - p) - (bs.width / 2 + rx); ty = 1440 * .46 + 14 * math.sin(p * 2) - (bs.height / 2 + ry)
    sh = Image.new('RGBA', bs.size, (0, 0, 0, 0)); sh.putalpha(bs.getchannel('A').point(lambda v: int(v * .55))); sh = sh.filter(ImageFilter.GaussianBlur(40))
    K._paste_sub(out, sh, tx + 30, ty + 40); K._paste_sub(out, bs, tx, ty)
    return K.clamp_white(out).convert('RGB'), sc


def insert_9x16(screen, t, t0, t1, focus_y):
    """the screen is the frame: full width, the focus line at 42% height (inside 13%..70%), a slow push"""
    p = K.lin(t, t0, t1); sc = 1080 / SW * (1.04 + .03 * K.ease_io(p))
    s = screen.convert('RGB').resize((int(SW * sc), int(SH * sc)), Image.LANCZOS)
    x = (1080 - s.width) / 2; y = 1920 * .42 - focus_y * sc
    y = min(0, max(1920 - s.height, y))
    out = Image.new('RGB', (1080, 1920), BG); out.paste(s, (int(round(x)), int(round(y))))
    return K.clamp_white(out), sc
