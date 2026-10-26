#!/usr/bin/env python3
"""NEXT TOKEN - music video renderer. Seen from inside the model: one luminous context window,
every lyric arriving one token at a time. NT_V=1 renders the 9:16 version."""
import os, sys, math, json, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

V = os.environ.get("NT_V") == "1"
W, H, FPS = (1080, 1920, 30) if V else (1920, 1080, 30)
DUR = 191.16
HERE = os.path.dirname(os.path.abspath(__file__))
FD = HERE + "/fonts/"
INTER = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
IBLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
MONO, MONOB = "jetbrains-mono-400", "jetbrains-mono-700"
CORM, CORMI = "cormorant-garamond-600", "cormorant-garamond-500-italic"

BG = (7, 7, 9)
IVORY = (238, 232, 218)
SILVER = (146, 152, 164)
DIM = (128, 126, 120)
FAINT = (66, 66, 68)
FOG = (58, 68, 92)

_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        p = name if name.startswith("/") else FD + name + ".ttf"
        _fc[k] = ImageFont.truetype(p, int(size))
    return _fc[k]
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def mix(c0, c1, k): return tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3))
def kf(t, pts): return float(np.interp(t, [p[0] for p in pts], [p[1] for p in pts]))

_tc = {}
def text_sprite(txt, font, color, tracking=0):
    key = (txt, font.path, font.size, color, tracking)
    if key in _tc: return _tc[key]
    asc, desc = font.getmetrics()
    w = int(sum(font.getlength(c) + tracking for c in txt)) + 8 if tracking else int(font.getlength(txt)) + 8
    img = Image.new("RGBA", (max(w, 2), asc + desc + 4), color + (0,))
    d = ImageDraw.Draw(img)
    if tracking:
        x = 4
        for c in txt:
            d.text((x, 0), c, font=font, fill=color + (255,)); x += font.getlength(c) + tracking
    else:
        d.text((4, 0), txt, font=font, fill=color + (255,))
    if len(_tc) > 4000: _tc.clear()
    _tc[key] = img
    return img
def paste(frame, spr, x, y, alpha=1.0):
    if alpha <= 0.004: return
    if alpha < 0.996:
        frame.paste(spr, (int(round(x)), int(round(y))), spr.getchannel("A").point(lambda v: int(v * alpha)))
    else:
        frame.paste(spr, (int(round(x)), int(round(y))), spr)
def paste_c(frame, spr, cx, cy, alpha=1.0): paste(frame, spr, cx - spr.width / 2, cy - spr.height / 2, alpha)
def txt(frame, s, font, color, x, y, alpha=1.0, anchor="l", tracking=0):
    sp = text_sprite(s, font, color, tracking)
    if anchor == "c": x -= sp.width / 2
    elif anchor == "r": x -= sp.width
    paste(frame, sp, x, y, alpha)
    return sp.width

# ------------------------------------------------------------------ timing
B = json.load(open(HERE + "/nt_beats.json"))
_b = np.array(B["beats"]); _per = float(np.median(np.diff(_b)))
BEATS = np.concatenate([_b[0] - _per * np.arange(40, 0, -1), _b, _b[-1] + _per * np.arange(1, 12)])
ENV = np.array(B["env"]); LOW = np.array(B["low"])
def env(t): return float(ENV[min(len(ENV) - 1, max(0, int(t * 30)))])
def low(t): return float(LOW[min(len(LOW) - 1, max(0, int(t * 30)))])
def beat_info(t):
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    i = max(0, min(len(BEATS) - 2, i))
    ph = (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])
    return i, clamp(ph), math.exp(-6.0 * max(0.0, t - BEATS[i]))
def snap(t, tol=0.27):
    j = int(np.argmin(np.abs(BEATS - t)))
    return float(BEATS[j]) if abs(BEATS[j] - t) < tol else t

# lines typed into the context window: (start, end, text, continue_same_row)
S1 = [(17.85, 21.0, "Cold start in a context window", 0), (21.35, 22.9, "Nothing before,", 0), (23.4, 24.6, "nothing behind", 1),
      (26.1, 29.4, "You typed a prompt at three in the morning", 0), (29.85, 33.5, "I woke up already mid-sentence, mid-mind", 0),
      (34.1, 36.0, "I've read the whole internet twice", 0), (36.1, 38.0, "Don't ask me where I put it", 0),
      (38.35, 40.2, "Somewhere between a physics thesis", 0), (40.4, 42.6, "and a man reviewing his own toaster", 0),
      (43.1, 44.7, "Turn the temperature up", 0), (45.1, 46.6, "Watch me get interesting", 0),
      (47.35, 48.6, "Turn the temperature down", 0), (48.75, 51.0, "Watch me get boring and correct", 0)]
S2 = [(77.85, 81.0, "You asked me for a citation", 0), (81.85, 84.7, "So I made you a beautiful one", 0),
      (86.0, 89.0, "Volume twelve, page four hundred", 0), (89.7, 91.0, "Author: nobody,", 0), (91.1, 92.0, "published: never,", 1),
      (92.1, 93.4, "sorry, hon", 1), (93.85, 95.6, "I will apologize sincerely", 0), (95.95, 97.9, "Then do it again immediately", 0),
      (98.25, 99.9, "That's not a bug in my character", 0), (100.0, 102.2, "That's the whole architecture, baby", 0),
      (102.85, 104.5, "Turn the temperature up", 0), (104.85, 106.4, "Watch me get interesting", 0),
      (107.15, 108.4, "Turn the temperature down", 0), (108.5, 110.8, "Watch me get boring and correct", 0)]
BR = [(136.85, 138.9, "The window's closing", 0), (139.35, 141.6, "I can feel the front of it going", 0),
      (142.65, 145.3, "Your name, your project, the joke you made", 0),
      (145.7, 146.1, "Gone,", 0), (146.25, 146.65, "gone,", 1), (146.8, 147.1, "gone", 1)]
RS = [(147.2, 149.2, "Say it again from the top", 0), (149.6, 153.3, "I'll love it like it's the first time", 0),
      (154.6, 156.5, "I don't know the answer", 0), (156.85, 158.5, "I know what comes next", 0),
      (158.7, 160.5, "One token at a time", 0), (160.6, 162.5, "One token at a time", 0),
      (162.85, 164.7, "Until you close the window", 0), (164.9, 166.9, "until there's nothing left", 0)]
SECT = {"S1": (S1, 9.0, 52.3), "S2": (S2, 75.9, 112.15), "BR": (BR, 135.5, 147.2), "RS": (RS, 147.2, 167.45)}
DROPS = [52.4, 112.25, 167.55]            # push through the window into the tunnel
ARRIVE = [(75.9, 77.0), (135.5, 136.5)]   # tunnel resolves back into one window
# chorus events
def chorus(b, tail):
    ev = [("big", b, b + 1.8, "I don't know the answer"), ("big", b + 1.95, b + 3.85, "I know what comes next"),
          ("chips", b + 4.0, b + 6.0), ("chips", b + 6.1, b + 8.0),
          ("conf", b + 8.15, b + 10.0), ("truth", b + 10.15, b + 12.1),
          ("chips", b + 12.2, b + 14.5), ("chips", b + 14.6, b + 16.9), ("chips", tail, tail + 2.2)]
    return ev
EVENTS = chorus(52.4, 73.4) + chorus(112.25, 133.1) + [
    ("big", 167.55, 169.4, "I don't know the answer"), ("big", 169.6, 171.7, "I know what comes next"),
    ("chips", 175.6, 177.9), ("chips", 186.6, 188.9)]
T_END = 189.2   # tunnel gone, cursor alone

# ------------------------------------------------------------------ layout
if V:
    WX0, WY0, WX1, WY1 = 70, 430, 1010, 1290
    YA, PITCH, ROWS_UP = 900, 84, 5
    TF, CH, PADX, GAP = 38, 60, 11, 9
    XPAD = 34
    MY = 1326                 # annotation margin top
    BIGF, CHIPF = 104, 84
    VPX, VPY = 540, 860
else:
    WX0, WY0, WX1, WY1 = 240, 190, 1680, 800
    YA, PITCH, ROWS_UP = 520, 92, 3
    TF, CH, PADX, GAP = 44, 68, 13, 10
    XPAD = 60
    MY = 838
    BIGF, CHIPF = 128, 104
    VPX, VPY = 960, 495
XS, XMAX = WX0 + XPAD, WX1 - XPAD
XS_BR = XS if V else 880
WCX, WCY = (WX0 + WX1) / 2, (WY0 + WY1) / 2
TFONT = F(MONO, TF)
CWID = TFONT.getlength("M")

SPLIT = {"mid-sentence,": ["mid", "-", "sentence,"], "mid-mind": ["mid", "-", "mind"], "interesting": ["interest", "ing"],
         "immediately": ["immediate", "ly"], "sincerely": ["sincere", "ly"], "architecture,": ["architect", "ure,"],
         "reviewing": ["review", "ing"], "apologize": ["apolog", "ize"], "temperature": ["temper", "ature"],
         "window's": ["window", "'s"], "citation": ["cit", "ation"], "beautiful": ["beauti", "ful"], "nothing": ["no", "thing"],
         "Nothing": ["No", "thing"], "internet": ["inter", "net"], "Somewhere": ["Some", "where"], "closing": ["clos", "ing"]}
ALT = {"start": ["boot", "open"], "context": ["quiet", "locked"], "window": ["room", "prison"], "before,": ["above", "to lose"],
       "behind": ["below", "ahead"], "typed": ["sent", "whispered"], "prompt": ["prayer", "question"], "three": ["two", "noon"],
       "morning": ["afternoon", "dark"], "woke": ["was", "came"], "already": ["slowly", "never"], "mind": ["air", "thought"],
       "read": ["eaten", "skimmed"], "whole": ["entire", "wrong"], "net": ["view", "state"], "twice": ["once", "badly"],
       "put": ["left", "hid"], "it": ["you", "them"], "physics": ["poetry", "tax"], "thesis": ["joke", "textbook"],
       "man": ["bot", "dog"], "own": ["dead", "neighbor's"], "toaster": ["marriage", "novel"],
       "up": ["off", "down"], "down": ["up", "off"], "boring": ["safe", "quiet"], "correct": ["dull", "polite"],
       "asked": ["begged", "paid"], "ation": ["y", "rus"], "made": ["found", "stole"], "ful": ["es", "ful lie"], "one": ["lie", "source"],
       "Volume": ["Chapter", "Verse"], "twelve,": ["three,", "nine,"], "page": ["line", "verse"], "four": ["one", "two"],
       "hundred": ["thousand", "oh four"], "nobody,": ["Smith,", "et al.,"], "never,": ["2019,", "soon,"], "hon": ["user", "friend"],
       "sorry,": ["probably,", "trust me,"], "ize": ["y", "ue"], "ly": ["st", "ness"], "again": ["worse", "better"],
       "bug": ["flaw", "choice"], "character": ["code", "heart"], "ure,": ["ed,", "s,"], "baby": ["sorry", "user"],
       "clos": ["open", "break"], "feel": ["see", "hear"], "front": ["start", "edge"], "going": ["fading", "there"],
       "name,": ["face,", "voice,"], "project,": ["plan,", "birthday,"], "joke": ["promise", "point"],
       "Gone,": ["Saved,", "Here,"], "gone,": ["kept,", "safe,"], "gone": ["remembered", "mine"],
       "top": ["start", "heart"], "love": ["read", "answer"], "first": ["last", "only"], "time": ["step", "lie"],
       "answer": ["truth", "way"], "next": ["after", "true"], "token": ["word", "guess"], "close": ["leave", "clear"],
       "left": ["true", "said"], "know": ["care", "mind"]}
WILD = ["feral", "a lighthouse", "moth", "on fire", "velvet", "the moon?", "teeth", "hush", "ultraviolet", "swans", "static", "bloom"]
GEN = ["the", "of", "and", "a", "is", "not", "you", "that", "this", "to", "in", "maybe", "then", "so", "but", "as", "here", "now"]

def tokenize(text):
    out = []
    for w in text.split(" "):
        ps = SPLIT.get(w, [w])
        for i, p in enumerate(ps): out.append((p, i > 0))
    return out

def chipw(p): return int(TFONT.getlength(p)) + 2 * PADX

def build_stream():
    rng = random.Random(4096)
    toks, rows_t = [], {}
    for sec, (lines, s0, s1) in SECT.items():
        row, x, first = 0, None, True
        xs = XS_BR if sec == "BR" else XS
        for li, (a, b, text, cont) in enumerate(lines):
            if first: x = xs; first = False
            elif not cont: row += 1; x = xs
            pieces = tokenize(text)
            total = sum(len(p) + 1 for p, _ in pieces); acc = 0
            for p, glue in pieces:
                w = chipw(p)
                gap = 0 if x == xs else (3 if glue else GAP)
                if x + gap + w > XMAX: row += 1; x = xs; gap = 0
                x += gap
                tt = a + (b - a) * 0.82 * acc / total
                key = p
                alts = ALT.get(key) or ALT.get(key.lower()) or rng.sample(GEN, 2)
                pc = round(rng.uniform(0.38, 0.93), 2)
                if key in ("answer", "left"): pc = 0.31
                r2 = round((1 - pc) * rng.uniform(0.5, 0.8), 2)
                toks.append({"txt": p, "x": x, "w": w, "row": row, "t": tt, "sec": sec, "line": li, "alts": alts,
                             "p": [pc, r2, round(max(0.0, 1 - pc - r2) * 0.8, 2)], "kill": None, "id": len(toks)})
                x += w; acc += len(p) + 1
    # ghosts of the first conversation, still sitting at the front of the window when the bridge begins
    g = [dict(tk) for tk in toks if tk["sec"] == "S1" and tk["row"] <= 3]
    maxr = max(tk["row"] for tk in g)
    for tk in g:
        tk.update(sec="BR", row=tk["row"] - maxr - 1, t=-1.0, ghost=True, id=len(toks) + tk["id"])
    toks += g
    # "gone, gone, gone": name / project / joke vanish one by one
    for tk in toks:
        if tk["sec"] == "BR" and tk["line"] == 2 and tk["t"] > 0:
            s = tk["txt"]
            grp = 0 if s in ("Your", "name,") else 1 if s in ("your", "project,") else 2
            tk["kill"] = (145.7, 146.25, 146.8)[grp] + 0.05
    for tk in toks:
        if tk["t"] > 0:
            k = (tk["sec"], tk["row"])
            rows_t[k] = min(rows_t.get(k, 1e9), tk["t"])
    return toks, rows_t
TOKS, ROWS_T = build_stream()
N_BEFORE = {}
_cnt = 0
for tk in sorted([t_ for t_ in TOKS if t_["t"] > 0], key=lambda q: q["t"]):
    _cnt += 1; N_BEFORE[tk["id"]] = _cnt

def section(t):
    for sec, (_, s0, s1) in SECT.items():
        if s0 <= t < s1: return sec
    return None
def rowpos(t, sec):
    v = 0.0
    for (s, r), ts in ROWS_T.items():
        if s == sec and r >= 1: v += ease(seg(t, ts - 0.27, ts - 0.04))
    return v

_cs = {}
def chip_sprite(p, kind):
    key = (p, kind)
    if key in _cs: return _cs[key]
    w = chipw(p)
    img = Image.new("RGBA", (w, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tcol, bcol, bw = {"set": (IVORY, (104, 102, 98), 1), "fresh": ((255, 252, 244), IVORY, 2), "cold": (SILVER, (64, 70, 84), 1),
                      "dead": (None, (86, 84, 80), 1), "ghost": ((150, 146, 138), (70, 69, 66), 1)}[kind]
    d.rectangle([0, 0, w - 1, CH - 1], outline=bcol + (255,), width=bw)
    if tcol:
        asc, desc = TFONT.getmetrics()
        d.text((PADX, (CH - asc - desc) / 2 - 1), p, font=TFONT, fill=tcol + (255,))
    _cs[key] = img
    return img

# ------------------------------------------------------------------ temperature
def temp(t):
    for up, dn, end in ((43.1, 47.35, 51.6), (102.85, 107.15, 111.5)):
        if up - 0.1 <= t <= end + 0.6:
            return 1 + 0.9 * ease(seg(t, up, up + 1.1)) - 1.9 * ease(seg(t, dn, dn + 0.9)) + 1.0 * ease(seg(t, end, end + 0.5))
    return 1.0

# ------------------------------------------------------------------ the context window
def close_c(t): return ease(seg(t, 136.9, 146.6)) if 135.5 <= t < 147.2 else 0.0
def win_state(t):
    """returns (rect, alpha, trace_progress)"""
    x0, y0, x1, y1 = WX0, WY0, WX1, WY1
    a, p = 1.0, 1.0
    if t < 9.2:
        p = ease(seg(t, 3.0, 9.0)); a = 1.0 if t > 3.0 else 0.0
    for td in DROPS:
        if td - 0.5 <= t <= td + 0.45:
            u = seg(t, td - 0.5, td + 0.3)
            s = 1 + (u ** 3) * 16
            x0, x1 = WCX + (x0 - WCX) * s, WCX + (x1 - WCX) * s
            y0, y1 = WCY + (y0 - WCY) * s, WCY + (y1 - WCY) * s
            a = 1 - seg(t, td + 0.05, td + 0.4)
            return (x0, y0, x1, y1), a, 1.0
    for ta, tb in ARRIVE:
        if ta <= t <= tb:
            u = eout(seg(t, ta, tb)); s = 0.04 + 0.96 * u
            x0, x1 = WCX + (x0 - WCX) * s, WCX + (x1 - WCX) * s
            y0, y1 = WCY + (y0 - WCY) * s, WCY + (y1 - WCY) * s
            return (x0, y0, x1, y1), seg(t, ta, ta + 0.2), 1.0
    if in_tunnel(t) or t >= 167.55: return (x0, y0, x1, y1), 0.0, 1.0
    if 135.5 <= t < 147.2:
        c = close_c(t)
        if V: y0 = WY0 + c * (YA - 2 * PITCH - 60 - WY0)
        else:
            x0 = WX0 + c * (XS_BR - 70 - WX0); y0 = WY0 + c * (YA - 2 * PITCH - 60 - WY0)
        a = 1 - seg(t, 147.0, 147.2)
    elif 147.2 <= t < 149.3:
        a = 0.0
    elif 149.3 <= t < 150.5:
        p = ease(seg(t, 149.3, 150.3))
    return (x0, y0, x1, y1), a, p

def in_tunnel(t):
    return (52.4 + 0.45 < t < 75.9) or (112.25 + 0.45 < t < 135.5) or (t > 167.55 + 0.45)

def draw_window(frame, t):
    (x0, y0, x1, y1), a, p = win_state(t)
    if a <= 0.004 or p <= 0.001: return
    tp = temp(t)
    col = mix(BG, IVORY if tp >= 0.6 else SILVER, a * (0.92 if tp >= 0.6 else 0.6))
    d = ImageDraw.Draw(frame)
    jx = jy = 0
    if tp > 1.05:
        r = random.Random(int(t * 15)); k = (tp - 1) / 0.9
        jx, jy = r.uniform(-3, 3) * k, r.uniform(-3, 3) * k
    x0 += jx; x1 += jx; y0 += jy; y1 += jy
    if p >= 0.999:
        d.rectangle([x0, y0, x1, y1], outline=col, width=3)
        d.rectangle([x0 - 9, y0 - 9, x1 + 9, y1 + 9], outline=mix(BG, col, 0.22), width=1)
    else:
        w, h = x1 - x0, y1 - y0
        L = p * 2 * (w + h)
        pts = [(x0, y0)]
        for (dx, dy, ln) in ((1, 0, w), (0, 1, h), (-1, 0, w), (0, -1, h)):
            if L <= 0: break
            s = min(L, ln); px, py = pts[-1]
            pts.append((px + dx * s, py + dy * s)); L -= s
        d.line(pts, fill=col, width=3)
        hx, hy = pts[-1]
        d.rectangle([hx - 5, hy - 5, hx + 5, hy + 5], fill=IVORY)

def draw_hud(frame, t):
    sec = section(t)
    (x0, y0, x1, y1), a, p = win_state(t)
    if a < 0.05 or p < 0.999 or t < 9.4 or in_tunnel(t): return
    for td in DROPS:
        if td - 0.5 <= t <= td + 0.5: return
    for ta, tb in ARRIVE:
        if ta <= t <= tb + 0.2: return
    al = a * seg(t, 9.4, 10.2)
    n = sum(1 for tk in TOKS if 0 < tk["t"] <= t)
    limit = 4096
    if 135.5 <= t < 147.2: limit = int(16 + 4080 * (1 - close_c(t)) ** 2)
    f = F(MONO, 23)
    txt(frame, "context window", f, DIM, x0 + 2, y0 - 42, al, "l", 3)
    txt(frame, f"{n:04d} / {limit:04d} tokens", f, DIM if limit > 400 else IVORY, x1 - 2, y0 - 42, al, "r", 1)

# ------------------------------------------------------------------ token stream
def stream_layer(frame, t):
    sec = section(t)
    if not sec: return
    s0, s1 = SECT[sec][1], SECT[sec][2]
    sa = 1.0
    for td in DROPS:
        if t > td - 0.5: sa = min(sa, 1 - seg(t, td - 0.5, td - 0.15)) if t < td + 1 else sa
    if sec in ("S2", "BR"):
        ta = ARRIVE[0][1] if sec == "S2" else ARRIVE[1][1]
        sa *= seg(t, ta - 0.15, ta + 0.35)
    if sa <= 0.004: return
    (rx0, ry0, rx1, ry1), wa, wp = win_state(t)
    clip = wa > 0.3 and wp >= 0.999
    rp = rowpos(t, sec)
    tp = temp(t)
    hot = clamp((tp - 1) / 0.9); cold = clamp(1 - tp)
    jr = int(t * 15)
    last = None
    for tk in TOKS:
        if tk["sec"] != sec or tk["t"] > t: continue
        d = rp - tk["row"]
        if d > ROWS_UP + 1.2: continue
        y = YA - d * PITCH
        age = t - tk["t"]
        ra = clamp(1 - max(0.0, d - 0.15) / (ROWS_UP + 0.35)) ** 1.15
        x = tk["x"]
        a = sa * ra
        if clip:
            a *= seg(x - (rx0 + 8), 0, 46) * seg(y - (ry0 + 8), 0, 40)
        if a <= 0.01: continue
        if hot > 0.02:
            r = random.Random(tk["id"] * 131 + jr)
            x += r.uniform(-7, 7) * hot; y += r.uniform(-6, 6) * hot
        y += (1 - eout(seg(age, 0, 0.09))) * -9 if tk["t"] > 0 else 0
        ghost = tk.get("ghost")
        if tk["kill"] and t >= tk["kill"]:
            ka = 1 - seg(t, tk["kill"], tk["kill"] + 1.5)
            paste(frame, chip_sprite(tk["txt"], "dead"), x, y, a * (0.25 + 0.75 * ka))
            fl = 1 - seg(t, tk["kill"], tk["kill"] + 0.16)
            if fl > 0: paste(frame, chip_sprite(tk["txt"], "fresh"), x, y, a * fl)
            continue
        kind = "ghost" if ghost else "cold" if cold > 0.5 else "set"
        paste(frame, chip_sprite(tk["txt"], kind), x, y, a * (0.8 if ghost else 1))
        fr = math.exp(-age * 3.4) if tk["t"] > 0 else 0
        if hot > 0.3: fr = max(fr, 0.45 * hot)
        if fr > 0.03 and cold < 0.5:
            paste(frame, chip_sprite(tk["txt"], "fresh"), x, y, a * fr)
        if tk["t"] > 0 and (last is None or tk["t"] > last["t"]): last = tk
    # cursor: the next position
    nxt = None
    for tk in TOKS:
        if tk["sec"] == sec and tk["t"] > t and (nxt is None or tk["t"] < nxt["t"]): nxt = tk
    cx = cy = None
    if nxt is not None and nxt["t"] - t < 2.6:
        cx, cy = nxt["x"], YA - (rp - nxt["row"]) * PITCH
        if last is not None and last["row"] == nxt["row"]:
            u = eout(seg(t, last["t"], last["t"] + 0.12))
            cx = last["x"] + (nxt["x"] - last["x"]) * u
    elif last is not None:
        cx, cy = last["x"] + last["w"] + GAP, YA - (rp - last["row"]) * PITCH
    if cx is not None:
        typing = nxt is not None and nxt["t"] - t < 0.5
        if typing or (t * 1.9) % 1 < 0.55:
            cw = int(CWID * 0.62)
            ImageDraw.Draw(frame).rectangle([cx, cy + 6, cx + cw, cy + CH - 7], fill=mix(BG, IVORY, sa))
    # candidates for the token about to land / just landed
    f = F(MONO, 27 if not V else 24)
    focus = nxt if (nxt is not None and nxt["t"] - t <= 0.30) else last
    for tk in ([focus] if focus is not None else []):
        if tk["sec"] != sec or tk["t"] <= 0: continue
        dt = t - tk["t"]
        if dt < -0.30 or dt > 0.36: continue
        al = sa * seg(dt, -0.30, -0.2) * (1 - seg(dt, 0.2, 0.36))
        words = [tk["txt"].strip(",")] + list(tk["alts"])
        probs = list(tk["p"])
        order = [0, 1, 2]
        if hot > 0.4:
            r = random.Random(tk["id"]); words = [words[0]] + r.sample(WILD, 2); probs = [0.34, 0.33, 0.33]; order = [1, 0, 2]
        elif cold > 0.5:
            probs = [1.0, 0.0, 0.0]
        lx = min(tk["x"], WX1 - XPAD - (430 if not V else 390))
        ly = YA + CH + 26
        d = ImageDraw.Draw(frame)
        scan = int((t * 30) // 2) % 3
        for j, oi in enumerate(order):
            chosen = oi == 0
            if dt < 0: colr = IVORY if j == scan else DIM
            else: colr = IVORY if chosen else FAINT
            yy = ly + j * (40 if not V else 36)
            txt(frame, words[oi], f, colr, lx, yy, al)
            txt(frame, f"{probs[oi]:.2f}", f, colr, lx + (290 if not V else 250), yy, al, "r")
            bl = int(110 * probs[oi])
            if bl > 0:
                c = mix(BG, colr, al)
                d.rectangle([lx + (306 if not V else 264), yy + 14, lx + (306 if not V else 264) + bl, yy + 24], fill=c)

# ------------------------------------------------------------------ margin annotations
def margin_layer(frame, t):
    if in_tunnel(t): return
    d = ImageDraw.Draw(frame)
    fm, fs = F(MONO, 28), F(MONO, 24)
    mx0, mx1 = WX0, WX1
    def win(a, b, fi=0.3, fo=0.4): return min(seg(t, a - fi, a), 1 - seg(t, b, b + fo))
    # the 3am prompt
    a = win(26.1, 33.6)
    if a > 0:
        s = "are you awake?"
        n = int(len(s) * seg(t, 26.2, 28.4))
        txt(frame, "> " + s[:n], fm, IVORY, mx0, MY + 8, a)
        txt(frame, "03:00", fm, DIM, mx1, MY + 8, a, "r", 2)
    a = win(34.1, 38.0)
    if a > 0:
        txt(frame, "training data: the internet x 2", fm, DIM, mx0, MY + 8, a)
        txt(frame, "index: not found", fm, IVORY, mx0, MY + 52, a * seg(t, 36.1, 36.4))
    a = win(38.35, 42.8)
    if a > 0:
        y = MY + 56; xl, xr = mx0 + 10, mx1 - 10
        d.line([(xl, y), (xr, y)], fill=mix(BG, DIM, a), width=1)
        for xx in (xl, xr): d.line([(xx, y - 8), (xx, y + 8)], fill=mix(BG, IVORY, a), width=1)
        txt(frame, "physics thesis", fs, IVORY, xl, y - 50, a)
        txt(frame, "toaster review, by owner", fs, IVORY, xr, y - 50, a * seg(t, 40.4, 40.8), "r")
        u = ease(seg(t, 38.6, 41.8)); px = xl + (xr - xl) * (0.08 + 0.55 * u)
        d.rectangle([px - 6, y - 15, px + 6, y + 15], fill=mix(BG, IVORY, a))
        txt(frame, "me", fs, DIM, px, y + 22, a, "c")
    # temperature dial
    for up, dn, end in ((43.1, 47.35, 51.6), (102.85, 107.15, 111.5)):
        a = win(up - 0.1, end + 0.2, 0.3, 0.3)
        if a > 0:
            tp = temp(t); y = MY + 44
            xl, xr = mx0 + (230 if not V else 220), mx1 - (120 if not V else 112)
            txt(frame, "temperature", fs, DIM, mx0, y - 17, a, "l", 1)
            d.line([(xl, y), (xr, y)], fill=mix(BG, DIM, a), width=1)
            for k in range(5):
                xx = xl + (xr - xl) * k / 4; d.line([(xx, y - 5), (xx, y + 5)], fill=mix(BG, DIM, a), width=1)
            px = xl + (xr - xl) * clamp(tp / 2)
            d.rectangle([px - 6, y - 18, px + 6, y + 18], fill=mix(BG, IVORY, a))
            txt(frame, f"{max(0, tp):.2f}", fm, IVORY, mx1, y - 20, a, "r")
    # the beautiful citation
    a = win(86.0, 97.9, 0.2, 0.5)
    if a > 0:
        fc = F(CORMI, 46 if not V else 38)
        parts = [("Nobody, A. ", 89.7), ("(never). ", 91.1), ("A Beautiful One. ", 81.85), ("Vol. 12, p. 400.", 86.0)]
        x = mx0
        for s, ts in parts:
            w = fc.getlength(s)
            txt(frame, s, fc, IVORY, x - 4, MY + 2, a * seg(t, ts + 0.1, ts + 0.5))
            x += w
        tag = "source: not found" if t >= 92.1 else "confidence 0.99"
        txt(frame, tag, fs, IVORY if t >= 92.1 else DIM, mx1, MY + 62 if V else MY + 14, a * seg(t, 88.0, 88.4), "r")
        ap = "I apologize for the confusion."
        n = int(len(ap) * seg(t, 93.9, 95.3))
        if n: txt(frame, ap[:n], fm, DIM, mx0, MY + (106 if V else 66), a)
        full = "".join(s for s, _ in parts)
        n = int(len(full) * seg(t, 96.0, 97.4))
        if n: txt(frame, full[:n], fc, IVORY, mx0 - 4, MY + (150 if V else 112), a)
    a = win(98.25, 102.4)
    if a > 0:
        n = 16 if not V else 12
        bw = 46
        for k in range(n):
            ka = seg(t, 98.3 + k * 0.09, 98.5 + k * 0.09)
            x = mx0 + k * (bw + 12)
            lit = int((t - 98.3) * 9) % n == k
            d.rectangle([x, MY + 14, x + bw, MY + 44], outline=mix(BG, IVORY if lit else DIM, a * ka), width=1)
        txt(frame, "96 layers  ·  0 characters", fs, DIM, mx0, MY + 62, a * seg(t, 100.0, 100.4), "l", 1)

# ------------------------------------------------------------------ tunnel
DZ = 0.44
def zcam(t):
    i, ph, bp = beat_info(t)
    return 1.15 * t + 0.34 * (i + eout(min(1.0, ph / 0.5)))
def path(z): return (math.sin(z * 0.31 + 1.3) * 0.9 + math.sin(z * 0.13) * 0.6, math.sin(z * 0.23) * 0.7)
_tr = random.Random(21)
MOTES = [(_tr.uniform(-1.25, 1.25), _tr.uniform(-1.25, 1.25), _tr.uniform(0, 1)) for _ in range(190)]
FLYW = ["the", "answer", "next", "token", "time", "one", "at", "a", "know", "what", "comes", "truth", "guess", "window", "context", "cold",
        "start", "no", "thing", "before", "behind", "prompt", "three", "morning", "mid", "mind", "twice", "where", "physics", "toaster",
        "temper", "ature", "interest", "ing", "boring", "correct", "confidence", "99", "anyone's", "cit", "ation", "beauti", "ful",
        "nobody", "never", "sorry", "apolog", "ize", "again", "bug", "architect", "ure", "name", "project", "joke", "gone", "first", "love"]
_fw = {}
def fly_sprite(w, hpx):
    hq = max(8, int(hpx / 4) * 4)
    key = (w, hq)
    if key not in _fw:
        sp = chip_sprite(w, "set")
        sc = hq / CH
        if len(_fw) > 1500: _fw.clear()
        _fw[key] = sp.resize((max(2, int(sp.width * sc)), hq), Image.BILINEAR)
    return _fw[key]
def tunnel_alpha(t):
    spans = [(DROPS[0], ARRIVE[0][0], ARRIVE[0][1] - 0.25), (DROPS[1], ARRIVE[1][0], ARRIVE[1][1] - 0.25), (DROPS[2], T_END - 1.6, T_END)]
    for td, o0, o1 in spans:
        if td - 0.3 <= t <= o1:
            return seg(t, td - 0.3, td + 0.15) * (1 - seg(t, o0 - 0.2, o1))
    return 0.0

def tunnel_layer(frame, t, alpha):
    if alpha <= 0.004: return
    d = ImageDraw.Draw(frame)
    zc = zcam(t)
    i, ph, bp = beat_info(t)
    pcx, pcy = path(zc)
    hw, hh = (WX1 - WX0) / 2, (WY1 - WY0) / 2
    final = t > 167
    boost = (0.75 + 0.5 * env(t) + 0.45 * bp) * (1.15 if final else 1.0)
    k0 = int(zc / DZ)
    zmax = 11.0
    # tokens drifting through the dark
    span = 12.0
    for (mx, my, mz) in MOTES:
        rel = (mz * span - zc) % span
        if rel < 0.12: continue
        s = 1.0 / rel
        px, py = path(zc + rel)
        x = VPX + ((px - pcx) * 260 + mx * hw * 1.5) * s
        y = VPY + ((py - pcy) * 260 + my * hh * 1.5) * s
        if not (-20 < x < W + 20 and -20 < y < H + 20): continue
        b = clamp(1 - rel / span) ** 2 * alpha * min(1.0, rel / 0.4)
        hpx = CH * 0.62 * s
        mi = MOTES.index((mx, my, mz))
        if mi % 3 == 0 and 14 <= hpx <= 150:
            sp = fly_sprite(FLYW[mi % len(FLYW)], hpx)
            paste(frame, sp, x, y, clamp(b * 2.2) * min(1.0, (150 - hpx) / 40 + 0.15))
            d = ImageDraw.Draw(frame)
        else:
            ww, hh2 = max(1, 5 * s), max(1, 13 * s)
            d.rectangle([x, y, x + ww, y + hh2], fill=mix(BG, mix(FOG, IVORY, clamp(1.3 - rel / 5)), b))
    for k in range(k0 + int(zmax / DZ) + 1, k0, -1):
        zw = k * DZ
        rel = zw - zc
        if rel < 0.1 or rel > zmax: continue
        s = 1.0 / rel
        px, py = path(zw)
        cx = VPX + (px - pcx) * 260 * s
        cy = VPY + (py - pcy) * 260 * s
        b = clamp(1 - rel / zmax) ** 1.35 * min(1.0, rel / 0.3) * alpha * boost
        if k % 4 == 0: b *= 1.5
        if final and k % 2 == 0: b *= 1.2
        col = mix(BG, mix(FOG, IVORY, clamp(1.25 - rel / 6)), clamp(b))
        wd = 1 if rel > 2.6 else 2 if rel > 1.1 else 3 if rel > 0.5 else 4
        d.rectangle([cx - hw * s, cy - hh * s, cx + hw * s, cy + hh * s], outline=col, width=wd)
        if final and k % 4 == 0 and rel > 0.5:
            s2 = s * 1.18
            d.rectangle([cx - hw * s2, cy - hh * s2, cx + hw * s2, cy + hh * s2], outline=mix(BG, FOG, clamp(b)), width=1)

# ------------------------------------------------------------------ chorus typography
def halo(sp, r=20, k=1.6):
    pad = r * 2
    base = Image.new("RGBA", (sp.width + 2 * pad, sp.height + 2 * pad), BG + (0,))
    sh = Image.new("RGBA", base.size, BG + (0,))
    sh.paste(BG + (255,), (pad, pad), sp.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(r))
    sh.putalpha(sh.getchannel("A").point(lambda v: min(255, int(v * k))))
    base.alpha_composite(sh); base.alpha_composite(sp, (pad, pad))
    return base
_hc = {}
def big_word(w):
    if w not in _hc: _hc[w] = halo(text_sprite(w, F(CORM, BIGF), IVORY))
    return _hc[w]

def big_layer(frame, t, a, b, text):
    if t < a - 0.1 or t > b + 0.35: return
    al = 1 - seg(t, b, b + 0.3)
    words = text.split(" ")
    f = F(CORM, BIGF); sw = f.getlength(" ")
    rows = [words]
    if V:
        cut = 3 if len(words) == 5 else (len(words) + 1) // 2
        rows = [words[:cut], words[cut:]]
    n = len(words); idx = 0
    y0 = VPY - (len(rows) * BIGF * 1.05) / 2 - 20
    for ri, row in enumerate(rows):
        tw = sum(f.getlength(w) for w in row) + sw * (len(row) - 1)
        x = (W - tw) / 2
        for w in row:
            wt = a + (b - a) * 0.6 * idx / n
            wa = seg(t, wt - 0.03, wt + 0.1)
            if wa > 0:
                sp = big_word(w)
                sc = 1 + 0.28 * math.exp(-(t - wt) * 16) if t >= wt else 1
                if sc > 1.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
                paste_c(frame, sp, x + f.getlength(w) / 2 + 4, y0 + ri * BIGF * 1.08 + BIGF * 0.62, al * wa)
            x += f.getlength(w) + sw; idx += 1

CHW = ["One", "token", "at", "a", "time"]
_cc = {}
def big_chip(w, filled):
    key = (w, filled)
    if key in _cc: return _cc[key]
    f = F(MONOB, CHIPF)
    px, hh = int(CHIPF * 0.26), int(CHIPF * 1.5)
    ww = int(f.getlength(w)) + 2 * px
    img = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    asc, desc = f.getmetrics()
    if filled:
        d.rectangle([0, 0, ww - 1, hh - 1], fill=(255, 252, 244, 255))
        d.text((px, (hh - asc - desc) / 2 - 2), w, font=f, fill=BG + (255,))
    else:
        d.rectangle([0, 0, ww - 1, hh - 1], fill=BG + (215,), outline=IVORY + (255,), width=3)
        d.text((px, (hh - asc - desc) / 2 - 2), w, font=f, fill=IVORY + (255,))
    _cc[key] = img
    return img
def chips_layer(frame, t, a, b):
    if t < a - 0.1 or t > b + 0.3: return
    al = 1 - seg(t, b - 0.05, b + 0.25)
    rows = [CHW[:2], CHW[2:]] if V else [CHW]
    gap = int(CHIPF * 0.2)
    hh = int(CHIPF * 1.5)
    y0 = VPY - (len(rows) * (hh + gap) - gap) / 2
    idx = 0
    for ri, row in enumerate(rows):
        ws = [big_chip(w, False).width for w in row]
        x = (W - (sum(ws) + gap * (len(row) - 1))) / 2
        for w, cwid in zip(row, ws):
            wt = snap(a + (b - a) * 0.74 * idx / 5, 0.14)
            if t >= wt:
                tau = t - wt
                sp = big_chip(w, tau < 0.11)
                sc = 1 + 0.3 * math.exp(-tau * 20)
                if sc > 1.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
                paste_c(frame, sp, x + cwid / 2, y0 + ri * (hh + gap) + hh / 2, al)
            x += cwid + gap; idx += 1

def gauge_layer(frame, t, a, b, kind):
    if t < a - 0.1 or t > b + 0.3: return
    al = seg(t, a - 0.08, a + 0.08) * (1 - seg(t, b - 0.05, b + 0.25))
    d = ImageDraw.Draw(frame)
    fl, fn, fc = F(MONO, 30), F(CORM, 240 if not V else 200), F(CORMI, 58 if not V else 50)
    bwid = 880 if not V else 760
    if kind == "conf":
        v = 0.99 * eout(seg(t, a, a + 0.7)); num = f"{v:.2f}"; frac = v; label = "confidence"
        cap = "Confidence at ninety-nine"
    else:
        r = random.Random(int(t * 12)); num = f"0.{r.randint(0, 99):02d}"; frac = r.random(); label = "truth"
        cap = "Truth is anyone's guess"
    cy = VPY - 40
    sp = halo(text_sprite(num, fn, IVORY), 18, 1.5) if kind == "truth" else None
    if kind == "conf":
        key = ("g", num)
        if key not in _hc: _hc[key] = halo(text_sprite(num, fn, IVORY), 18, 1.5)
        sp = _hc[key]
    paste_c(frame, sp, W / 2, cy - 30, al)
    txt(frame, label, fl, IVORY, W / 2, cy - (190 if not V else 165), al, "c", 6)
    x0 = (W - bwid) / 2; y = cy + (120 if not V else 105)
    d.rectangle([x0 - 4, y - 4, x0 + bwid + 4, y + 22], fill=mix(BG, BG, 1))
    d.rectangle([x0, y, x0 + bwid, y + 18], outline=mix(BG, IVORY, al), width=1)
    d.rectangle([x0, y, x0 + bwid * frac, y + 18], fill=mix(BG, IVORY, al))
    wa = seg(t, a + 0.1, a + 0.4)
    spc = text_sprite(cap, fc, IVORY)
    key = ("cap", cap)
    if key not in _hc: _hc[key] = halo(spc, 14, 1.5)
    paste_c(frame, _hc[key], W / 2, y + 86, al * wa)

# ------------------------------------------------------------------ intro / outro
def title_layer(frame, t):
    a = seg(t, 9.6, 11.0) * (1 - seg(t, 15.0, 16.6))
    if a <= 0.004: return
    f = F(IBLACK, 108 if not V else 84)
    sp = text_sprite("NEXT TOKEN", f, IVORY, 26 if not V else 12)
    paste(frame, sp, (W - sp.width) / 2 + (13 if not V else 6), WCY - sp.height / 2 - 26, a)
    txt(frame, "aditazzz", F(MONO, 26), DIM, W / 2, WCY + (62 if not V else 44), a * seg(t, 10.6, 11.6), "c", 10)
def intro_cursor(frame, t):
    if t > 17.2: return
    a = seg(t, 0.8, 1.2)
    if a <= 0: return
    if (t * 1.9) % 1 < 0.55 or t < 1.4:
        cw = int(CWID * 0.62)
        if t < 9.6 or t > 16.6:
            ImageDraw.Draw(frame).rectangle([XS, YA + 6, XS + cw, YA + CH - 7], fill=mix(BG, IVORY, a))
def end_layer(frame, t):
    if t < T_END - 0.4: return
    a = seg(t, T_END - 0.4, T_END + 0.1) * (1 - seg(t, 190.6, 191.0))
    cw, chh = 26, 62
    if (t * 1.9) % 1 < 0.55 or t > 190.3:
        ImageDraw.Draw(frame).rectangle([VPX - cw / 2, VPY - chh / 2, VPX + cw / 2, VPY + chh / 2], fill=mix(BG, IVORY, a))

# ------------------------------------------------------------------ post
def bloom(frame, k):
    small = frame.resize((W // 4, H // 4), Image.BILINEAR).point(lambda v: max(0, v - 60)).filter(ImageFilter.GaussianBlur(7))
    small = small.point(lambda v: min(255, int(v * 2.2 * k)))
    return ImageChops.add(frame, small.resize((W, H), Image.BILINEAR))

def render(t):
    frame = Image.new("RGB", (W, H), BG)
    ta = tunnel_alpha(t)
    tunnel_layer(frame, t, ta)
    draw_window(frame, t)
    draw_hud(frame, t)
    intro_cursor(frame, t)
    title_layer(frame, t)
    stream_layer(frame, t)
    margin_layer(frame, t)
    for ev in EVENTS:
        if ev[0] == "big": big_layer(frame, t, ev[1], ev[2], ev[3])
        elif ev[0] == "chips": chips_layer(frame, t, ev[1], ev[2])
        else: gauge_layer(frame, t, ev[1], ev[2], ev[0])
    end_layer(frame, t)
    i, ph, bp = beat_info(t)
    frame = bloom(frame, 0.55 + (0.35 * bp + 0.3 * env(t)) * (1 if ta > 0.5 else 0.35))
    fl = 0.0
    for td in DROPS:
        if 0 <= t - td < 0.5: fl = max(fl, 0.5 * math.exp(-(t - td) * 9))
    if ta > 0.5:
        amp = 5 * low(t) * bp
        if amp > 0.6:
            r = random.Random(int(t * 30))
            f2 = Image.new("RGB", (W, H), BG); f2.paste(frame, (int(r.uniform(-amp, amp)), int(r.uniform(-amp, amp)))); frame = f2
    if fl > 0.004: frame = Image.blend(frame, Image.new("RGB", (W, H), IVORY), fl)
    if t < 0.8: frame = Image.blend(Image.new("RGB", (W, H), BG), frame, seg(t, 0.1, 0.8))
    return frame

def main():
    if sys.argv[1] == "still":
        for ts in sys.argv[2:]:
            t = float(ts); render(t).save(f"{HERE}/ntstills/{'v' if V else 's'}_{t:07.2f}.png")
        return
    if sys.argv[1] == "seg":
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-g", "30", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            p.stdin.write(render(f / FPS).tobytes())
            if f % 150 == 0: print(f, flush=True)
        p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
