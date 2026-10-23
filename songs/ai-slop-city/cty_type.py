"""Lyric typography for the city: EB Garamond, warm white, words easing up as they're sung; whispered asides and the
spoken break in italic. Each shot says where the words sit (place = (cx, cy, maxw) as fractions of the frame), so the
lyrics dodge the phone, her, and the 9:16 platform buttons."""
import math
import numpy as np, cv2
from studio import core as C

F_LYR = C.os.path.join(C.FONTS, 'EBGaramond-SemiBold.ttf')
F_ITAL = C.os.path.join(C.FONTS, 'EBGaramond-MediumItalic.ttf')
WARM = C.hexc('f7f1e6')
AMBER = C.hexc('f2b46d')
ITALIC_SECS = ('BREAK',)


def _italic(L):
    return L['sec'] in ITALIC_SECS or L['text'].strip().startswith('(')


def _layout(words, fs, maxw, path):
    sp = C.text_w(' ', path, fs)
    rows = [[]]; cw = 0
    for w, tt in words:
        ww = C.text_w(w, path, fs)
        if rows[-1] and cw + sp + ww > maxw:
            rows.append([]); cw = 0
        rows[-1].append((w, tt, ww)); cw += ww + (sp if len(rows[-1]) > 1 else 0)
    return rows, sp


def lyrics(img, t, W, H, timing, place=None, active=AMBER, band=0.5, skip_word=None, hide=lambda L: False, scale=1.0):
    """Draw the current lyric line(s). place = (cx, cy, maxw) fractions; default lower third (16:9) / mid-low (9:16)."""
    if C.STATE['clean']: return
    vert = H > W; ts = min(W, H) / 1080
    cx, cy, mw = place or ((0.5, 0.84, 0.8) if not vert else (0.47, 0.70, 0.80))
    fs0 = int((70 if not vert else 64) * ts * scale)
    vis = [L for L in timing.lines if not hide(L)]
    drew = False
    for li, L in enumerate(vis):
        nxt = vis[li + 1]['s'] if li + 1 < len(vis) else 1e9
        prv_out = (vis[li - 1]['e'] + 0.45) if li > 0 else -1e9
        if prv_out > L['s'] - 0.3: a0, a1 = L['s'] - 0.07, L['s'] + 0.05
        else: a0, a1 = L['s'] - 0.3, L['s']
        if L['e'] + 0.45 > nxt - 0.3: b0, b1 = nxt - 0.17, nxt - 0.07
        else: b0, b1 = L['e'] + 0.1, L['e'] + 0.55
        if not (a0 <= t <= b1): continue
        opl = C.sstep(a0, a1, t) * (1 - C.sstep(b0, b1, t))
        if opl <= 0.003: continue
        ital = _italic(L)
        path = F_ITAL if ital else F_LYR
        fs = int(fs0 * (0.96 if ital else 1.0))
        words = [(w, tt) for w, tt in zip(L['words'], L['wt']) if not (skip_word and C.norm(w) == skip_word)]
        if not words: continue
        rows, sp = _layout(words, fs, W * mw, path)
        lh = fs * 1.18
        y0 = H * cy - (len(rows) - 1) * lh / 2 - lh * 0.55 - lh * 0.25 * (1 - opl)
        if band > 0 and not drew:
            yb0 = max(0, int(y0 - lh * 0.9)); yb1 = min(H, int(y0 + len(rows) * lh + lh * 0.9))
            prof = np.sin(np.linspace(0, math.pi, yb1 - yb0)) ** 1.5
            img[yb0:yb1] *= (1 - band * opl * 0.55 * prof)[:, None, None]
        drew = True
        for ri, row in enumerate(rows):
            tw = sum(r[2] for r in row) + sp * (len(row) - 1)
            x = W * cx - tw / 2
            for w, tt, ww in row:
                k = C.sstep(tt - 0.16, tt + 0.08, t)
                act = math.exp(-max(0.0, t - tt) * 2.4) if t >= tt - 0.05 else 0.0
                col = WARM * (1 - act * 0.55) + active * act * 0.55
                op = opl * (0.28 + 0.72 * k)
                dy = (1 - k) * 12 * ts
                C.shadow(img, C.sprite(w, path, fs, 12), x, y0 + ri * lh + dy + 3 * ts, 0.9 * op)
                C.blit(img, C.sprite(w, path, fs, 4), x, y0 + ri * lh + dy, col, op, 0.18 * act, glow_color=active)
                x += ww + sp


def title_card(img, W, H, lines, op, cy=0.5, size=0.07, path=None, col=WARM, gap=1.25):
    """Simple centred text block (used for the in-world asides and the end card)."""
    if op <= 0.01: return
    ts = min(W, H) / 1080
    fs = int(H * size) if W > H else int(W * size * 1.3)
    path = path or F_LYR
    y = H * cy - (len(lines) - 1) * fs * gap / 2 - fs * 0.6
    for l in lines:
        tw = C.text_w(l, path, fs)
        C.shadow(img, C.sprite(l, path, fs, 12), W / 2 - tw / 2, y + 3 * ts, 0.9 * op)
        C.blit(img, C.sprite(l, path, fs, 4), W / 2 - tw / 2, y, col, op)
        y += fs * gap
