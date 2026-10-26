"""Mirror, Mirror, Look at Us — The Comment Section (version 3 of 3). See NOTES.md for the beats.

The page (the post + its comment section, an invented app) is drawn flat in page coordinates, then photographed by a
perspective camera: it floats in a dark room above a glossy black floor that reflects it. Lyrics are replies from the
artist typed on their sung times; the crowd's comments give themselves away."""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui as U
import script as SC
from script import LN, wt, ls
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C

F32 = np.float32
TM = C.Timing(HERE)
SONG = TM.duration; TAIL = 5.0; DUR = SONG + TAIL; T_END = 261.0
BEATS = np.array(TM.beats); DOWN = np.array(TM.downbeats)
ACC = C.hexc("4da3ff")

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k)
def ease_io(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def lerp(a, b, k): return a + (b - a) * k
def since(arr, t):
    i = int(np.searchsorted(arr, t + 1e-6)) - 1
    return t - arr[i] if i >= 0 else 1e9

# ================================================================ layout
LAY = {
    "16x9": dict(PW=1920, PH=1080, px=110, py=60, img=700, cx=990, cw=830, head=60, view=(150, 930), inp=958, comp=(560, 930),
                 cap=48),
    "9x16": dict(PW=1080, PH=1920, px=220, py=64, img=640, cx=50, cw=980, head=950, view=(1040, 1600), inp=1622, comp=(1150, 1600),
                 cap=48),
}
def fmt_of(W, H): return "16x9" if W >= H else "9x16"

# ================================================================ times
CHORUS = {"CH1", "CH2", "FINAL"}
FLIPS = []                                   # light-mode flashes on every sung "mirror" in the choruses
for i, L in enumerate(LN):
    if L["sec"] in CHORUS or i == 33:
        for w, tt in zip(L["words"], L["wt"]):
            if w.lower().strip(",.").startswith("mirror"): FLIPS.append(tt)
def theme_at(t):
    v = 0.0
    for tf in FLIPS:
        if tf - 0.05 <= t <= tf + 0.55: v = max(v, sstep(tf - 0.05, tf + 0.02, t) * (1 - sstep(tf + 0.40, tf + 0.50, t)))
    return v

def _lines_with(txt): return [i for i, L in enumerate(LN) if L["text"].startswith(txt)]
MIRROR_WIN = [(ls(i) + 0.35, LN[i]["e"] + 0.35) for i in _lines_with("Funny how the mirror")] + [SC.MIRROR_PRE2]
def mirror_amt(t):
    return max([sstep(a, a + 0.45, t) * (1 - sstep(b, b + 0.4, t)) for a, b in MIRROR_WIN] + [0.0])

FACE_WAVES = []
for c0 in (13, 35, 65):
    FACE_WAVES.append((wt(c0, 2), ls(c0 + 1) + 1.0))
    FACE_WAVES.append((wt(c0 + 8, 0), wt(c0 + 8, 2) + 0.7))
    FACE_WAVES.append((wt(c0 + 8, 3), wt(c0 + 8, 5) + 0.9))
FACE_WAVES.append((wt(64, 6), 208.9))

# ================================================================ entry state
ENT = SC.ENT
for e in ENT:
    if e.kind == "crowd" and e.t < SC.AI_BADGE_T: e.badges.append((SC.AI_BADGE_T, "AI-assisted"))
TRAINED = [e for e in ENT if e.t < SC.TRAIN[0] - 0.7]      # everything before "We asked it to learn" goes into the mirror
# the outro: everything still up is deleted, newest first
_tids = set(id(e) for e in TRAINED)
_dl = [e for e in ENT if id(e) not in _tids and e.t < SC.DELETE[0] - 0.2]
for k, e in enumerate(sorted(_dl, key=lambda e: -e.t)):
    e.deleted_t = min(SC.DELETE[1], SC.DELETE[0] + k * 0.38)
CLEAR_T = (256.1, 257.0)                      # the outro replies leave too: "No comments yet."
TAG = SC.E(SC.TAG_POST_T, "lyric", "aditazzz", LN[80]["text"], "artist", reply=False, likes=[(SC.TAG_POST_T, 0)], line=80, flip=False)
TAG.id = len(ENT)
ALL = ENT + [TAG]

def badges_at(e, t):
    out = [lab for tb, lab in e.badges if t >= tb]
    if e is SC.NINA and t >= ls(6):
        n = 1 + int(29 * clamp((t - ls(6)) / (wt(6, 6) - ls(6))) ** 1.3)
        out.insert(min(1, len(out)), f"Take {n}/30")
    return tuple(out)

def card_state(e, t, theme, fmt):
    """(sprite, info) for an entry at time t."""
    deleted = e.deleted_t is not None and t >= e.deleted_t
    if e.kind == "lyric" and not deleted:
        n = len(LN[e.line]["words"])
        if e is TAG: k = n
        else: k = sum(1 for tt in LN[e.line]["wt"] if t >= tt - 0.04)
        return U.lyric_card(fmt, theme, LN[e.line]["text"], k, reply=e.reply)
    if e.kind == "system":
        return sys_card(e, t, theme, fmt)
    top = e.top_t is not None and t >= e.top_t
    chips = e.chips if (e.chips and t >= ls(3)) else ()
    sel = 0 if (e.chip_sel_t is not None and t >= e.chip_sel_t) else -1
    edited = e.kind == "crowd" and e.t < SC.CH1_EDIT_T <= t < 116.0
    user = (e.user if e.kind != "lyric" else "aditazzz") if not deleted else "[deleted]"
    text = e.text if e.kind != "lyric" else LN[e.line]["text"]
    return U.crowd_card(fmt, theme, user, text, badges_at(e, t) if not deleted else (), top and not deleted, edited,
                        chips if not deleted else (), sel, deleted, e.reply)

def sys_card(e, t, theme, fmt):
    if e.sys in ("guidelines", "guidelines2"):
        n = sum(1 for tt in SC.GUIDE_CHECKS if t >= tt) if e.sys == "guidelines" else 4
        spr = U.guidelines_card(fmt, theme, n)
    elif e.sys == "report":
        base = e.t + 0.2
        ck = [tt - ls(18) + base for tt in SC.REPORT_CHECKS]
        spr = U.report_sheet(fmt, theme, sum(1 for tt in ck if t >= tt))
    else:
        k = clamp((t - ls(50) - 0.1) / (wt(50, 3) - ls(50)))
        spr = U.insights_card(fmt, theme, int(round(ease_io(k) * 20)))
    return spr, dict(h=spr[1].shape[0], w=spr[1].shape[1], av=None)

# ---------------------------------------------------------------- slot heights over time (for layout and scroll)
GAP = 16
def _change_times(e):
    ts = [e.t]
    if e.top_t: ts.append(e.top_t)
    if e.chips: ts.append(ls(3))
    ts += [tb for tb, _ in e.badges]
    if e is SC.NINA: ts.append(ls(6))
    if e.deleted_t: ts.append(e.deleted_t)
    return sorted(set(ts))

# ---------------------------------------------------------------- the pinned top comment
PINS = SC.PINS                                # [(entry, pinned at, unpinned at)]
PIN_OF = {id(e): (a, b) for e, a, b in PINS}
PIN_RISE = 0.42
def pinned_state(e, t, theme, fmt):
    badges = badges_at(e, t)
    chips = e.chips if (e.chips and t >= ls(3) and not badges) else ()   # one receipts row: a badge replaces the chips
    sel = 0 if (e.chip_sel_t is not None and t >= e.chip_sel_t) else -1
    return U.pinned_card(fmt, theme, e.user, e.text, chips, sel, badges)

@lru_cache(2)
def pin_track(fmt):
    """keyframes [(t, h)] of the pinned area's height (card + gap), 0 when nothing is pinned."""
    ks = []
    for e, a, b in PINS:
        times = [a] + [tc for tc in _change_times(e) + ([ls(3)] if e.chips else []) if a < tc < b]
        for tc in sorted(set(times)):
            spr, info = pinned_state(e, tc + 0.01, 0, fmt); ks.append((tc, float(info["h"] + GAP)))
        if not any(abs(a2 - b) < 1e-6 for _, a2, _ in PINS): ks.append((b, 0.0))
    return sorted(ks, key=lambda k: k[0])

def pin_h(fmt, t): return _h_at(pin_track(fmt), t)

def _h_grid(ks, ts):
    h = np.zeros_like(ts); prev = 0.0
    for tk, hk in ks:
        k = np.clip((ts - tk) / 0.22, 0, 1); k = k * k * k * (k * (6 * k - 15) + 10)
        h = np.where(ts >= tk, prev + (hk - prev) * k, h); prev = hk
    return h

@lru_cache(2)
def height_tracks(fmt):
    """per entry: keyframes [(t, h)] of its slot height (0 before posting, 0 after flying into the mirror / clearing,
    0 once pinned: the pinned card lives above the thread)."""
    tracks = []
    for e in ALL:
        ks = [(e.t - 0.001, 0.0)]
        pin = PIN_OF.get(id(e))
        for tc in _change_times(e):
            if pin and tc >= pin[0]: continue
            spr, info = card_state(e, tc + 0.01, 0, fmt)
            ks.append((tc, float(info["h"] + GAP)))
        if pin: ks.append((pin[0], 0.0))
        if e.deleted_t is not None or (e.t >= SC.DELETE[0] - 0.2 and e is not TAG):
            ks.append((CLEAR_T[0], ks[-1][1])); ks.append((CLEAR_T[1], 0.0))
        tracks.append(ks)
    return tracks

def _h_at(ks, t):
    """smooth step between keyframe heights (0.22 s), so slots grow and collapse instead of jumping."""
    h = 0.0
    for i, (tk, hk) in enumerate(ks):
        if t < tk: break
        prev = ks[i - 1][1] if i > 0 else 0.0
        h = lerp(prev, hk, ease_io((t - tk) / 0.22))
    return h

GRID = 1 / 60.0
@lru_cache(2)
def scroll_track(fmt):
    """the scroll offset over the whole song (computed once; frames render in any order). The newest comment stays
    anchored just above the comment box: new cards grow in from the bottom (their own 0.22 s ease is the scroll
    motion) and slots that collapse above are compensated exactly, so the line being sung never jumps."""
    Lo = LAY[fmt]; VH = Lo["view"][1] - Lo["view"][0]
    ts = np.arange(0, DUR + 1, GRID)
    tot = np.zeros_like(ts)
    for ks in height_tracks(fmt): tot += _h_grid(ks, ts)
    P = _h_grid(pin_track(fmt), ts)              # (a pinned card covers the top of the view; short threads start below it)
    out = np.maximum(-P, tot - VH + 18)
    return ts, out, tot

def scroll_at(fmt, t):
    ts, out, _ = scroll_track(fmt); return float(np.interp(t, ts, out))

def counts_at(t):
    """the comment counter in the header and under the post."""
    if t < 8.6: return 0
    if t < 12.24: return sum(1 for e in ENT if e.kind == "crowd" and e.t <= t)
    if t < 48.41: return int(12400 + (t - 12.24) * 62 + (sstep(37.8, 39.7, t) * 3100))
    if t < 51.12: return int(lerp(16700, 999999, ease_in((t - 48.41) / 2.71)))
    if t < SC.DELETE[0]: return 999999
    if t < SC.TAG_POST_T: return int(999999 * (1 - ease_io((t - SC.DELETE[0]) / (CLEAR_T[1] - SC.DELETE[0]))))
    return 1

def post_likes(t):
    return int(4200 + 480 * t + 60 * t * t / 10)

# ================================================================ the post image
@lru_cache(4)
def cover_imgs(size):
    def load(n):
        im = cv2.cvtColor(cv2.imread(os.path.join(HERE, "assets", n)), cv2.COLOR_BGR2RGB)
        return cv2.resize(im, (size, size), interpolation=cv2.INTER_AREA).astype(F32) / 255
    return load("cover_clean.png"), load("cover_cracked.png")

@lru_cache(4)
def round_mask(size, r):
    m = np.zeros((size * 4, size * 4), np.uint8)
    cv2.rectangle(m, (r * 4, 0), (size * 4 - r * 4, size * 4), 255, -1); cv2.rectangle(m, (0, r * 4), (size * 4, size * 4 - r * 4), 255, -1)
    for cx, cy in ((r, r), (size - r, r), (r, size - r), (size - r, size - r)): cv2.circle(m, (cx * 4, cy * 4), r * 4, 255, -1)
    return cv2.resize(m, (size, size), interpolation=cv2.INTER_AREA).astype(F32) / 255

@lru_cache(2)
def crack_paths():
    import json
    d = json.load(open(os.path.join(HERE, "assets", "crack_track.json")))
    paths = [np.array([(x, y) for x, y, v in d["main"]], F32), np.array([(x, y) for x, y, v in d["branch"]], F32)]
    return paths, [np.array([(x, y) for x, y, v in seg], F32) for seg in d.get("extra", [])]

def crack_mask(size, k):
    (main, br), extra = crack_paths(); s = size / 1254.0
    out = np.zeros((size, size), np.uint8); w = max(2, int(round(14 * s)))
    n1 = int(round(len(main) * clamp(k / 0.82)))
    if n1 > 1: cv2.polylines(out, [np.round(main[:n1] * s * 4).astype(np.int32)], False, 255, w * 4, cv2.LINE_8, shift=2)
    if k > 0.7:
        n2 = int(round(len(br) * clamp((k - 0.7) / 0.3)))
        if n2 > 1: cv2.polylines(out, [np.round(br[:n2] * s * 4).astype(np.int32)], False, 255, w * 4, cv2.LINE_8, shift=2)
        for seg in extra:
            n3 = int(round(len(seg) * clamp((k - 0.8) / 0.2)))
            if n3 > 1: cv2.polylines(out, [np.round(seg[:n3] * s * 4).astype(np.int32)], False, 255, w * 4, cv2.LINE_8, shift=2)
    return cv2.GaussianBlur(out, (0, 0), 1.5).astype(F32) / 255

@lru_cache(8)
def _crack_glow(S, kq):
    m = crack_mask(S, kq / 20.0)
    return np.clip(m * 0.6 + cv2.GaussianBlur(m, (0, 0), max(1.5, S / 230.0)) * 1.1, 0, 1).astype(F32)
def crack_glow(S, k): return _crack_glow(S, int(round(clamp(k) * 20)))

GLASS = (307, 152, 948, 1012)                  # the mirror's glass in the 1254-px cover
def post_image(fmt, t, thread_snap):
    """the cover as it is at time t: clean -> cracked on "mad"; the thread reflected in its glass; lights on the beat."""
    Lo = LAY[fmt]; S = Lo["img"]; clean, cracked = cover_imgs(S)
    if t < SC.CRACK_T: img = clean.copy()
    elif t < SC.CRACK_T + 0.35:
        m = crack_mask(S, ease_out((t - SC.CRACK_T) / 0.32))[..., None]; img = clean * (1 - m) + cracked * m
    else: img = cracked.copy()
    if t >= SC.CRACK_T:                          # the crack catches the light: a flash along it on "mad", then a glint
        u = t - SC.CRACK_T
        g = crack_glow(S, ease_out(u / 0.32)) if u < 0.35 else crack_glow(S, 1.0)
        amt = 0.14 + 0.55 * math.exp(-u / 0.30) + 0.10 * math.exp(-since(BEATS, t) / 0.18) * (u > 0.4)
        img = np.minimum(img + g[..., None] * (amt * np.array([1.0, 0.93, 0.80], F32)), 1.0)
    s = S / 1254.0; gx0, gy0, gx1, gy1 = (int(round(v * s)) for v in GLASS)
    ma = mirror_amt(t)
    if ma > 0.01 and thread_snap is not None:
        g = cv2.resize(thread_snap, (gx1 - gx0, gy1 - gy0), interpolation=cv2.INTER_AREA)[:, ::-1]
        reg = img[gy0:gy1, gx0:gx1]
        tint = g * np.array([0.82, 0.9, 1.0], F32) * 0.92
        img[gy0:gy1, gx0:gx1] = reg * (1 - 0.82 * ma) + (tint * 0.85 + reg * 0.15) * 0.82 * ma
    # the bulbs breathe on the beat in the choruses
    if any(a <= t < b for a, b in ((44.16, 82.57), (116.19, 156.18), (208.98, 247.39))):
        p = 0.10 * math.exp(-since(BEATS, t) / 0.14) + 0.12 * math.exp(-since(DOWN, t) / 0.2)
        img = np.minimum(img * (1 + p * bulb_map(S)[..., None]), 1.0)
    return img

@lru_cache(4)
def bulb_map(S):
    import json
    b = json.load(open(os.path.join(HERE, "assets", "bulbs.json"))); s = S / 1254.0
    yy, xx = np.mgrid[0:S, 0:S].astype(F32); m = np.zeros((S, S), F32)
    for d in b:
        x, y, r = d["x"] * s, d["y"] * s, d["r"] * s
        m += np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * 2.2) ** 2))
    return np.clip(m, 0, 1)

# ================================================================ drawing the page
def theme_col(theme, k): return np.array(U.th(theme, k), F32) / 255

@lru_cache(4)
def page_alpha(PW, PH):
    m = np.zeros((PH, PW), np.uint8); r = 40
    cv2.rectangle(m, (r, 0), (PW - r, PH), 255, -1); cv2.rectangle(m, (0, r), (PW, PH - r), 255, -1)
    for cx, cy in ((r, r), (PW - r, r), (r, PH - r), (PW - r, PH - r)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m.astype(F32) / 255

def nina_av(e, t): return "filt:3" if (e is SC.NINA and t >= wt(5, 1)) else e.av

def flip_k(e, t, y_screen, VH):
    """how far this entry's avatar has flipped to the face (0..1), for the chorus waves."""
    if e.kind == "system": return 0.0
    k = 0.0
    for a, b in FACE_WAVES:
        st = a + 0.45 * clamp(y_screen / max(1, VH))
        if st <= t <= b + 0.9:
            k = max(k, ease_io((t - st) / 0.32) * (1 - ease_io((t - b - 0.45 * clamp(y_screen / max(1, VH))) / 0.32)))
    return k

def draw_thread(pg, fmt, t, theme):
    """the comment column (cards, avatars, likes, karaoke, stamps) into the page. returns (snapshot of the column for
    the mirror, list of pointing arrows to draw, list of flying cards)."""
    Lo = LAY[fmt]; v0, v1 = Lo["view"]; VH = v1 - v0; X = Lo["cx"]
    tracks = height_tracks(fmt); sc = scroll_at(fmt, t)
    y = 0.0; arrows = []; flying = []
    M = U.card_metrics(fmt)
    any_vis = False
    vp = v0 + pin_h(fmt, t)                      # the thread shows below the pinned card
    pin_from = {}
    for e, ks in zip(ALL, tracks):
        h = _h_at(ks, t)
        if e.t > t + 0.001: continue
        slot_y = y; y += h
        pin = PIN_OF.get(id(e))
        if pin and t >= pin[0]:
            pin_from[id(e)] = slot_y - sc + v0; continue
        if e in TRAINED_SET and t >= SC.TRAIN[0]:
            fl = flight(fmt, e)
            if fl is None or t >= fl[1]: continue
            if t >= fl[0]: flying.append((e, fl[2])); continue
            if fl[2] < v0 - 100: continue          # pulled from above later: not on screen now
        if h < 1.0: continue
        sy = slot_y - sc + v0
        if sy > v1 or sy + h < vp: continue
        clr = 1 - sstep(CLEAR_T[0], CLEAR_T[1] - 0.3, t) if (e is not TAG and t >= CLEAR_T[0]) else 1.0
        age = t - e.t; op = ease_out(age / 0.25) * clr
        if op <= 0.01: continue
        any_vis = True
        spr, info = card_state(e, t, theme, fmt)
        x = X + (M["indent"] if e.reply else 0) + (1 - ease_out(age / 0.3)) * 40
        U.blit_clip(pg, spr, x, sy, (vp, v1), op, fade=26)
        if info.get("av") is not None and not (e.deleted_t is not None and t >= e.deleted_t):
            ax, ay = x + info["av"][0], sy + info["av"][1]
            if vp - 10 <= ay <= v1 - 40:
                fk = flip_k(e, t, ay - v0, VH)
                if fk > 0: U.flip_avatar(pg, (nina_av(e, t)), f"face:{e.id % 6}", M["av"], ax, ay, fk)
                else: U.blit(pg, U.avatar(nina_av(e, t), M["av"]), ax, ay, op)
            # likes
            hx, hy = x + info["heart"][0], sy + info["heart"][1]
            if vp + 8 <= hy <= v1:
                n = likes_at(e, t)
                hs = heart_state(e, t)
                if hs != "outline":
                    U.blit(pg, U.heart_sprite(38, theme, hs), hx - 19, hy - 19, op)
                if n > 0:
                    col = U.PINK if hs != "outline" else U.th(theme, "muted")
                    U.blit(pg, U.text_sprite(U.fmt_count(n), U.F_SB, 34, col), x + info["count"][0], hy - 23, op)
        if e.kind == "lyric" and e is not TAG and not (e.deleted_t is not None and t >= e.deleted_t):
            karaoke(pg, e, t, x, sy, info, theme, (vp, v1))
        if e.stamp_t and t >= e.stamp_t:
            u = t - e.stamp_t; scl = 1 + 0.7 * math.exp(-u / 0.05)
            sp = U.stamp("FAKE", 88, -7 + (e.id % 5) * 3)
            spw = sp[1].shape[1] * scl; sph = sp[1].shape[0] * scl
            cx = x + info["w"] - 110; cy = sy + info["h"] * 0.5 + 6
            inside = clamp((cy - sph / 2 - vp) / 30 + 1) * clamp((v1 - cy - sph / 2) / 30 + 1)
            if inside > 0.01: U.blit(pg, sp, cx - spw / 2, cy - sph / 2, clamp(u / 0.04) * clr * inside, scl)
        if e.underline_t and t >= e.underline_t:
            k = ease_out((t - e.underline_t) / 0.6)
            yl = sy + info["h"] - 74; x0 = x + 102; x1 = x0 + (info["w"] - 140) * k
            pts = np.array([(x0 + (x1 - x0) * u, yl + 5 * math.sin(u * 7.0 + 1)) for u in np.linspace(0, 1, 24)], F32)
            if vp + 30 <= yl <= v1 - 6: cv2.polylines(pg, [np.round(pts * 4).astype(np.int32)], False, (0.95, 0.15, 0.2, 1.0), 9 * 1, cv2.LINE_AA, shift=2)
        if e.point_t and e.point_t <= t < e.point_t + 2.6 and sy + 40 >= vp:
            arrows.append((x + 40, sy + 40, (t - e.point_t), e.id))
    draw_pinned(pg, fmt, t, theme, pin_from)
    snap = pg[v0:v1, X:X + M["w"], :3].copy() if mirror_amt(t) > 0.01 else None
    return snap, arrows, flying, any_vis

def draw_pinned(pg, fmt, t, theme, pin_from):
    """the pinned top comment: rises from its place in the thread to the top, leaves upward under the header."""
    Lo = LAY[fmt]; v0, v1 = Lo["view"]; X = Lo["cx"]; P = U.pin_metrics(fmt)
    ys = {}
    for e, a, b in PINS:                         # where each pinned card is (the rising one first)
        if a <= t < a + PIN_RISE:
            h = pinned_state(e, t, theme, fmt)[1]["h"]
            ys[id(e)] = lerp(pin_from.get(id(e), v1 - h), v0, ease_io((t - a) / PIN_RISE))
    for e, a, b in PINS:
        if not (a <= t < b + 0.35): continue
        spr, info = pinned_state(e, min(t, b), theme, fmt)
        if t < a + PIN_RISE: y = ys[id(e)]; op = 1.0
        elif t < b: y = v0; op = 1.0
        else:
            k = (t - b) / 0.35; y = v0 - 70 * ease_in(k); op = 1 - ease_out(k)
            nxt = [ys[id(e2)] for e2, a2, _ in PINS if abs(a2 - b) < 1e-6 and id(e2) in ys]
            if nxt: y = min(y, nxt[0] - info["h"] - GAP)
        # a soft shadow on the thread below it
        yb = int(round(y + info["h"])); sh = 26
        if yb < v1 and op > 0.02:
            y0s, y1s = max(v0, yb), min(v1, yb + sh)
            if y1s > y0s:
                g = (1 - (np.arange(y0s, y1s, dtype=F32) - yb) / sh) * U.th(theme, "shadow") * 0.8 * op
                pg[y0s:y1s, X + 10:X + info["w"] - 10, :3] *= (1 - g)[:, None, None]
        U.blit_clip(pg, spr, X, y, (v0, v1), op)
        ax, ay = X + info["av"][0], y + info["av"][1]
        if ay >= v0 - 4:
            U.blit(pg, U.avatar(nina_av(e, t), P["av"]), ax, ay, op)
        hx, hy = X + info["heart"][0], y + info["heart"][1]
        if hy >= v0 + 10:
            hs = heart_state(e, t)
            if hs != "outline":
                pp = heart_pop(e, t); U.blit(pg, U.heart_sprite(38, theme, hs), hx - 19 * pp, hy - 19 * pp, op, pp)
            n = likes_at(e, t)
            if n > 0:
                col = U.PINK if hs != "outline" else U.th(theme, "muted")
                U.blit(pg, U.text_sprite(U.fmt_count(n), U.F_SB, 34, col), X + info["count"][0], hy - 23, op)

class _IdSet:
    def __init__(s, items): s.ids = set(id(x) for x in items)
    def __contains__(s, e): return id(e) in s.ids
TRAINED_SET = _IdSet(TRAINED)

@lru_cache(2)
def flight_plan(fmt):
    """(start, end, start screen y) for the cards pulled into the mirror: the ones on screen first (top to bottom), then
    a stream of older comments pulled down from above the viewport, newest first."""
    Lo = LAY[fmt]; v0, v1 = Lo["view"]; t0 = SC.TRAIN[0]
    tracks = height_tracks(fmt); sc = scroll_at(fmt, t0); y = 0.0; pos = {}
    for e, ks in zip(ALL, tracks):
        if e.t > t0: continue
        h = _h_at(ks, t0); pos[id(e)] = (y - sc + v0, h); y += h
    vis = sorted([(pos[id(e)][0], e) for e in TRAINED if pos.get(id(e), (0, 0))[1] > 1 and
                  pos[id(e)][0] + pos[id(e)][1] > v0 - 40 and pos[id(e)][0] < v1], key=lambda p: p[0])
    vis_ids = set(id(e) for _, e in vis)
    rest = [e for e in sorted(TRAINED, key=lambda e: -e.t) if id(e) not in vis_ids and e.kind != "system"][:16]
    seq = [(sy, e) for sy, e in vis] + [(v0 - 140.0, e) for e in rest]
    out = {}; span = SC.TRAIN[1] - SC.TRAIN[0] - 0.9
    for k, (sy, e) in enumerate(seq):
        st = t0 + 0.15 + span * k / max(1, len(seq) - 1); out[id(e)] = (st, st + 0.9, sy)
    return out

def flight(fmt, e): return flight_plan(fmt).get(id(e))

def likes_at(e, t):
    if e is SC.LAUGH:
        if t < ls(26): return 0
        n = int(np.searchsorted(BEATS, min(t, 97.2)) - np.searchsorted(BEATS, ls(26)))
        return int(n * 420 + 30)
    xs = [k[0] for k in e.likes]; ys = [k[1] for k in e.likes]
    return int(np.interp(t, xs, ys))

def heart_pop(e, t):
    if e is not SC.TOP: return 1.0
    tc = max([x for x in (16.35, wt(2, 5)) if x <= t] + [-9.0])
    return 1 + 0.55 * math.exp(-max(0.0, t - tc) / 0.11) * (1 if t - tc < 1.0 else 0)

def heart_state(e, t):
    if e is SC.TOP:
        if t < 16.35: return "outline"
        if t < wt(2, 5): return "liked"
        return f"broken:{1 + min(3, int((t - wt(2, 5)) / 0.12))}"
    return "outline"

def karaoke(pg, e, t, x, sy, info, theme, clip):
    """the word just sung, in the accent, fading to the card's text colour; a blinking caret while the line is typed."""
    L = LN[e.line]; ws = info["words"]; fs = info["lfs"]
    for k, (w, wx, wy, ww) in enumerate(ws):
        tt = L["wt"][k]
        if t < tt - 0.04: break
        act = math.exp(-max(0.0, t - tt) / 0.38)
        if act > 0.03 and clip[0] <= sy + wy + fs * 0.6 <= clip[1]:
            U.blit(pg, U.word_sprite(w, fs, U.ACCENT), x + wx, sy + wy, act)
    last = L["wt"][-1]
    if t < last + 0.5:
        k = sum(1 for tt in L["wt"] if t >= tt - 0.04)
        if 0 < k <= len(ws):
            w, wx, wy, ww = ws[k - 1]
            if int(t * 3.2) % 2 == 0 and clip[0] <= sy + wy <= clip[1] - 40:
                cv2.rectangle(pg, (int(x + wx + ww + 8), int(sy + wy + 10)), (int(x + wx + ww + 14), int(sy + wy + fs * 1.05)),
                              (0.30, 0.64, 1.0, 1.0), -1)

def draw_post(pg, fmt, t, theme, snap):
    Lo = LAY[fmt]; X, Y, S = Lo["px"], Lo["py"], Lo["img"]
    tc = U.th(theme, "text"); mc = U.th(theme, "muted")
    U.blit(pg, U.avatar("artist", 60), X, Y + 6)
    U.blit(pg, U.text_sprite("@aditazzz", U.F_SB, 38, tc), X + 76, Y + 14)
    cw = U.font(U.F_SB, 38).getlength("@aditazzz")
    U.blit(pg, U.label_chip("Creator", 28, U.ACCENT), X + 90 + cw, Y + 15)
    U.blit(pg, U.text_sprite("· 2h", U.F_MD, 36, mc), X + 90 + cw + 150, Y + 14)
    img = post_image(fmt, t, snap)
    iy = Y + 82
    m = round_mask(S, 26)
    reg = pg[iy:iy + S, X:X + S]
    reg[..., :3] = reg[..., :3] * (1 - m[..., None]) + img * m[..., None]; reg[..., 3] = np.maximum(reg[..., 3], m)
    # labels on the post
    if SC.AI_LABEL_T <= t < 183.2:
        op = sstep(SC.AI_LABEL_T, SC.AI_LABEL_T + 0.2, t) * (1 - sstep(182.6, 183.2, t))
        U.blit(pg, U.label_chip("AI-generated?", 34, (240, 180, 40), (20, 20, 20)), X + 24, iy + 24, op)
    if SC.COUNTERFEIT_T <= t < 183.6:
        u = t - SC.COUNTERFEIT_T; scl = 1 + 0.7 * math.exp(-u / 0.05)
        sp = U.stamp("COUNTERFEIT?", 96 if fmt == "16x9" else 92, -8)
        w, h = sp[1].shape[1] * scl, sp[1].shape[0] * scl
        U.blit(pg, sp, X + S / 2 - w / 2, iy + S * 0.52 - h / 2, clamp(u / 0.04) * (1 - sstep(183.0, 183.6, t)), scl)
    if SC.SEARCH[0] + 2.0 <= t < SC.SEARCH[1]:
        op = sstep(SC.SEARCH[0] + 2.0, SC.SEARCH[0] + 2.2, t) * (1 - sstep(SC.SEARCH[1] - 0.3, SC.SEARCH[1], t))
        cv2.rectangle(pg, (X - 8, iy - 8), (X + S + 8, iy + S + 8), (0.30, 0.64, 1.0, op), 8, cv2.LINE_AA)
        U.blit(pg, U.label_chip("someone to blame: 1 result", 34, U.ACCENT), X + 24, iy + S - 84, op)
    if SC.TRAIN[0] - 0.2 <= t < SC.TRAIN[1] + 0.6:
        k = clamp((t - SC.TRAIN[0]) / (SC.TRAIN[1] - SC.TRAIN[0]))
        op = sstep(SC.TRAIN[0] - 0.2, SC.TRAIN[0], t) * (1 - sstep(SC.TRAIN[1] + 0.2, SC.TRAIN[1] + 0.6, t))
        sp = U.training_chip(fmt, theme, int(round(k * 40)))
        U.blit(pg, sp, X + S / 2 - sp[1].shape[1] / 2, iy + S - 170, op)
    # actions + caption
    ay = iy + S + 14
    U.blit(pg, U.heart_sprite(44, theme, "liked"), X, ay)
    U.blit(pg, U.text_sprite(U.fmt_count(post_likes(t)), U.F_SB, 36, tc), X + 56, ay + 1)
    bx = X + 210
    U.blit(pg, bubble_icon(theme), bx, ay + 4)
    U.blit(pg, U.text_sprite(U.fmt_count(counts_at(t)), U.F_SB, 36, tc), bx + 54, ay + 1)
    cap = "psst, this song isn't real"; words = LN[0]["words"]
    k = sum(1 for tt in LN[0]["wt"] if t >= tt - 0.03)
    txt = " ".join(["psst,", "this", "song", "isn't", "real"][:k])
    if txt: U.blit(pg, U.text_sprite(txt, U.F_SB, Lo["cap"], tc), X, ay + 62)
    if 0 < k < 5 or (k == 5 and t < LN[0]["wt"][-1] + 0.6):
        if int(t * 3.2) % 2 == 0:
            cxp = X + U.font(U.F_SB, Lo["cap"]).getlength(txt) + 8
            cv2.rectangle(pg, (int(cxp), int(ay + 66)), (int(cxp + 6), int(ay + 62 + Lo["cap"] * 1.2)), (0.30, 0.64, 1.0, 1.0), -1)
    return (X + S / 2, iy + S / 2)

@lru_cache(4)
def bubble_icon(theme):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (44, 44), (0, 0, 0, 0)); U.draw_bubble(ImageDraw.Draw(im), 3, 3, 38, U.rgba(U.th(theme, "text")), 4)
    return U.to_sprite(im)

def draw_header(pg, fmt, t, theme):
    Lo = LAY[fmt]
    if SC.SEARCH[0] <= t < SC.SEARCH[1]:
        n = int(np.interp(t, [SC.SEARCH[0] + 0.3, wt(34, 4), wt(34, 5), wt(34, 6), wt(34, 6) + 0.3], [0, 8, 11, 13, 16]))
        U.blit(pg, U.search_bar(fmt, theme, "someone to blame"[:max(0, n)], int(t * 3.2) % 2 == 0), Lo["cx"], Lo["head"] - 4)
        return
    sort = "Recommended" if t >= SC.SORT_T else "Top"
    n = counts_at(t)
    U.blit(pg, U.header(fmt, theme, U.fmt_count(n) if n else "", sort), Lo["cx"], Lo["head"])

def draw_input(pg, fmt, t, theme):
    Lo = LAY[fmt]
    txt = ""; sug = False; hot = False
    if SC.SUGGEST_T[0] <= t < SC.SUGGEST_T[1] + 0.25:
        k = clamp((t - SC.SUGGEST_T[0]) / 0.5); txt = "this is soulless"[:int(round(16 * k))]; sug = True; hot = t > SC.SUGGEST_T[1] - 0.2
    U.blit(pg, U.input_box(fmt, theme, txt, bool(txt) and int(t * 3.2) % 2 == 0, True, hot, sug), Lo["cx"], Lo["inp"])

# ---------------------------------------------------------------- the composer (bridge, tag) and the discard dialog
BRIDGE_LINES = list(range(53, 61))
@lru_cache(64)
def composer(fmt, theme, text, nwords, caret, post_hot, to_user):
    from PIL import Image, ImageDraw
    M = U.card_metrics(fmt); T = U.THEMES[theme]; W = M["w"]; pad = 30
    fl = U.font(U.F_SB, M["lfs"]); fm = U.font(U.F_MD, 34)
    words = text.split(" ") if text else []; lines = U.wrap_words(words, fl, W - 2 * pad - 10) if words else [[]]
    lh = int(M["lfs"] * 1.16); h = pad + 52 + max(2, len(lines)) * lh + 90
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 30, fill=U.rgba(T["card2"]), outline=U.rgba(U.ACCENT), width=3)
    d.text((pad, pad + 18), f"Replying to @{to_user}" if to_user else "Add a comment", font=fm, fill=U.rgba(T["muted"]), anchor="lm")
    y = pad + 52; k = 0; last = None
    for ln in lines:
        for w, x in ln:
            if k < nwords: d.text((pad + x, y), w, font=fl, fill=U.rgba(T["text"])); last = (pad + x + fl.getlength(w), y)
            k += 1
        y += lh
    if caret:
        cx, cy = last if last else (pad, pad + 52)
        d.rectangle((cx + 8, cy + 10, cx + 14, cy + M["lfs"] * 1.05), fill=U.rgba(U.ACCENT))
    fb = U.font(U.F_SB, 40)
    d.text((W - pad, h - 44), "Post", font=fb, fill=U.rgba(U.ACCENT if post_hot else T["muted"]), anchor="rm")
    return U.to_sprite(im)

def composer_state(t):
    """(text, nwords, words times, to_user, post_hot, opacity) or None."""
    if 181.6 <= t < 195.5:
        cur = None
        for i in BRIDGE_LINES:
            if t >= LN[i]["s"] - 0.25: cur = i
        op = sstep(181.6, 182.0, t) * (1 - sstep(195.1, 195.45, t))
        if cur is None: return ("", 0, "realart_only", False, op)
        L = LN[cur]; n = sum(1 for tt in L["wt"] if t >= tt - 0.04)
        nxt = LN[cur + 1]["s"] - 0.25 if cur + 1 in BRIDGE_LINES else 1e9
        if t > nxt - 0.12: n = 0                     # select-all, delete, start the next line
        return (L["text"], n, "realart_only", n > 0, op)
    if 258.7 <= t < SC.TAG_POST_T + 0.05:
        L = LN[80]; n = sum(1 for tt in L["wt"] if t >= tt - 0.04)
        op = sstep(258.7, 259.0, t) * (1 - sstep(SC.TAG_POST_T - 0.05, SC.TAG_POST_T + 0.05, t))
        return (L["text"], n, "", t > L["wt"][-1] + 0.15, op)
    return None

def draw_composer(pg, fmt, t, theme):
    st = composer_state(t)
    if st is None: return False
    text, n, to_user, hot, op = st
    Lo = LAY[fmt]
    sp = composer(fmt, theme, text, n, int(t * 3.2) % 2 == 0, hot, to_user)
    h = sp[1].shape[0]
    # dim the thread behind it
    v0, v1 = Lo["view"]
    pg[v0:v1, Lo["cx"]:Lo["cx"] + U.card_metrics(fmt)["w"], :3] *= (1 - 0.45 * op)
    y = Lo["comp"][1] - h
    U.blit(pg, sp, Lo["cx"], y + (1 - ease_out(op)) * 60, op)
    if 194.5 <= t < 195.5:
        dop = sstep(194.5, 194.65, t) * (1 - sstep(195.1, 195.45, t))
        dg = U.dialog(fmt, theme, t >= 194.95)
        U.blit(pg, dg, Lo["cx"] + (U.card_metrics(fmt)["w"] - dg[1].shape[1]) / 2, y - dg[1].shape[0] * 0.2, dop)
    return True

def draw_arrows(pg, arrows, target):
    for (x, y, age, i) in arrows:
        k = ease_out(age / 0.35); op = 1 - sstep(2.0, 2.6, age)
        tx, ty = target[0] + ((i * 97) % 160 - 80), target[1] + ((i * 53) % 160 - 80)
        mx, my = (x + tx) / 2, min(y, ty) - 120
        pts = []
        for u in np.linspace(0, k, 28):
            pts.append(((1 - u) ** 2 * x + 2 * (1 - u) * u * mx + u * u * tx, (1 - u) ** 2 * y + 2 * (1 - u) * u * my + u * u * ty))
        pts = np.array(pts, F32)
        if len(pts) > 1:
            col = (0.95 * op, 0.20 * op, 0.25 * op, op)
            cv2.polylines(pg, [np.round(pts * 4).astype(np.int32)], False, col, 7, cv2.LINE_AA, shift=2)
            if k > 0.95:
                d = pts[-1] - pts[-3]; d /= (np.linalg.norm(d) + 1e-6); n = np.array([-d[1], d[0]])
                tip = pts[-1]; a = tip - d * 26 + n * 14; b = tip - d * 26 - n * 14
                cv2.fillPoly(pg, [np.round(np.array([tip, a, b]) * 4).astype(np.int32)], col, cv2.LINE_AA, shift=2)

def draw_flying(pg, fmt, t, theme, flying, target):
    for e, sy in flying:
        a, b, _ = flight(fmt, e); u = clamp((t - a) / (b - a))
        kp = ease_io(u); ks = ease_in(u)
        spr, info = card_state(e, min(t, e.t + 30), theme, fmt)
        x0 = LAY[fmt]["cx"] + (U.card_metrics(fmt)["indent"] if e.reply else 0)
        sc = lerp(1.0, 0.04, ks); w, h = info["w"] * sc, info["h"] * sc
        x = lerp(x0, target[0] - w / 2, kp); y = lerp(sy, target[1] - h / 2, kp) - math.sin(u * math.pi) * 90
        U.blit(pg, spr, x, y, (1 - 0.4 * ks) * sstep(0, 0.08, u), scale=sc)

def render_page(fmt, t, theme):
    Lo = LAY[fmt]; PW, PH = Lo["PW"], Lo["PH"]
    pg = np.empty((PH, PW, 4), F32)
    pg[..., :3] = theme_col(theme, "bg"); pg[..., 3] = 1.0
    snap, arrows, flying, any_vis = draw_thread(pg, fmt, t, theme)
    v0, v1 = Lo["view"]
    if t < 9.0 or (CLEAR_T[1] - 0.3 <= t < SC.TAG_POST_T and composer_state(t) is None):
        op = 1 - sstep(8.6, 9.0, t) if t < 9.0 else sstep(CLEAR_T[1] - 0.3, CLEAR_T[1], t)
        sp = U.text_sprite("No comments yet.", U.F_SB, 46, U.th(theme, "muted"))
        U.blit(pg, sp, Lo["cx"] + (U.card_metrics(fmt)["w"] - sp[1].shape[1]) / 2, (v0 + v1) / 2 - 60, op)
        sp = U.text_sprite("Start the conversation.", U.F_MD, 38, U.th(theme, "muted"))
        U.blit(pg, sp, Lo["cx"] + (U.card_metrics(fmt)["w"] - sp[1].shape[1]) / 2, (v0 + v1) / 2 + 4, op)
    draw_header(pg, fmt, t, theme)
    comp = draw_composer(pg, fmt, t, theme)
    if not comp: draw_input(pg, fmt, t, theme)
    target = draw_post(pg, fmt, t, theme, snap)
    draw_arrows(pg, arrows, target)
    draw_flying(pg, fmt, t, theme, flying, target)
    pg[..., 3] *= page_alpha(PW, PH)
    return pg

# ================================================================ camera
#                (t,      zoom,  cx,   cy,  yaw, pitch, ease)
SHOTS16 = [(0.0, 0.60, 960, 560, -10, 3, "lin"), (4.2, 0.64, 960, 560, -7, 3, "io"), (5.0, 1.32, 470, 950, -2, 0, "lin"),
           (7.4, 1.34, 480, 946, -1.5, 0, "io"), (8.4, 1.0, 975, 545, 2, 0, "lin"), (12.24, 1.03, 985, 545, 2, 0, "lin"),
           (37.78, 1.08, 1000, 545, -2, 0, "io"), (40.0, 1.04, 980, 540, 3, 0, "io"), (44.16, 1.02, 965, 540, 0, 0, "io"),
           (55.0, 1.1, 948, 520, -3, 0, "io"), (58.4, 1.02, 965, 540, 2, 0, "io"), (64.8, 1.05, 980, 540, 0, 0, "io"),
           (71.12, 1.08, 955, 530, -2, 0, "io"), (77.4, 1.0, 960, 540, 0, 0, "io"), (82.57, 1.03, 985, 545, 2, 0, "io"),
           (83.45, 0.92, 975, 506, 1, 0, "lin"), (88.5, 0.93, 980, 510, 0, 0, "io"), (89.6, 1.04, 988, 545, 1, 0, "lin"),
           (109.78, 1.07, 995, 545, -3, 0, "io"), (113.0, 1.1, 948, 520, 2, 0, "io"), (114.9, 1.05, 985, 540, 0, 0, "io"),
           (116.19, 1.02, 965, 540, 0, 0, "io"), (127.0, 1.1, 948, 520, -3, 0, "io"), (130.4, 1.02, 965, 540, 2, 0, "io"),
           (136.8, 1.05, 980, 540, 0, 0, "io"), (143.2, 1.08, 955, 530, -2, 0, "io"), (149.6, 1.0, 960, 540, 0, 0, "io"),
           (154.1, 1.0, 960, 540, 0, 0, "io"), (155.45, 0.72, 960, 560, 8, 3, "io"), (156.85, 1.04, 980, 545, 0, 0, "io"), (178.6, 1.1, 950, 520, 0, 0, "io"),
           (181.6, 1.04, 1000, 560, 0, 0, "io"), (190.0, 1.1, 1040, 600, -2, 0, "io"), (193.6, 1.1, 1040, 600, -2, 0, "lin"),
           (195.0, 1.1, 1040, 600, -2, 0, "io"), (195.9, 1.0, 2650, 560, 26, 0, "io"), (196.15, 1.0, 2650, 560, 26, 0, "io"),
           (197.6, 1.04, 980, 545, 0, 0, "io"),
           (199.2, 1.18, 960, 480, -2, 0, "io"), (202.2, 1.05, 960, 540, 0, 0, "io"), (208.98, 1.02, 965, 540, 0, 0, "io"),
           (218.2, 1.1, 948, 520, -3, 0, "io"), (221.44, 1.02, 965, 540, 2, 0, "io"), (228.0, 1.05, 980, 540, 0, 0, "io"),
           (234.4, 1.1, 955, 525, -2, 0, "io"), (240.8, 1.0, 960, 540, 0, 0, "io"), (247.3, 1.02, 975, 545, 0, 0, "io"),
           (255.6, 1.0, 965, 545, 0, 0, "io"), (257.6, 0.66, 960, 560, -6, 3, "io"), (258.9, 1.0, 1010, 610, -1, 0, "io"), (260.6, 1.0, 1010, 610, -1, 0, "io"),
           (261.5, 0.52, 0, 560, -6, 2, "io"), (300, 0.52, 0, 560, -6, 2, "lin")]     # end card: the page clears the headline
SHOTS9 = [(0.0, 0.64, 540, 980, -9, 3, "lin"), (4.2, 0.68, 540, 980, -6, 3, "io"), (5.0, 1.3, 520, 900, -2, 0, "lin"),
          (7.4, 1.32, 525, 898, -1.5, 0, "io"), (8.4, 1.0, 540, 960, 2, 0, "lin"), (12.24, 1.02, 540, 975, 2, 0, "lin"),
          (37.78, 1.05, 540, 990, -2, 0, "io"), (40.0, 1.03, 540, 975, 3, 0, "io"), (44.16, 1.0, 540, 960, 0, 0, "io"),
          (55.0, 1.06, 540, 930, -3, 0, "io"), (58.4, 1.0, 540, 960, 2, 0, "io"), (71.12, 1.05, 540, 975, -2, 0, "io"),
          (77.4, 1.0, 540, 960, 0, 0, "io"), (82.57, 1.02, 540, 975, 2, 0, "lin"), (109.78, 1.05, 540, 990, -3, 0, "io"),
          (113.0, 1.06, 540, 930, 2, 0, "io"), (114.9, 1.03, 540, 975, 0, 0, "io"), (116.19, 1.0, 540, 960, 0, 0, "io"),
          (127.0, 1.06, 540, 930, -3, 0, "io"), (130.4, 1.0, 540, 960, 2, 0, "io"), (143.2, 1.05, 540, 975, -2, 0, "io"),
          (149.6, 1.0, 540, 960, 0, 0, "io"), (154.1, 1.0, 540, 960, 0, 0, "io"), (155.45, 0.74, 540, 990, 8, 3, "io"),
          (156.85, 1.02, 540, 975, 0, 0, "io"),
          (178.6, 1.06, 540, 930, 0, 0, "io"), (181.6, 1.02, 540, 990, 0, 0, "io"), (193.6, 1.06, 540, 1050, -2, 0, "lin"),
          (195.0, 1.06, 540, 1050, -2, 0, "io"), (195.9, 1.0, 1320, 990, 26, 0, "io"), (196.15, 1.0, 1320, 990, 26, 0, "io"),
          (197.6, 1.02, 540, 975, 0, 0, "io"),
          (199.2, 1.1, 540, 860, -2, 0, "io"), (202.2, 1.02, 540, 960, 0, 0, "io"), (208.98, 1.0, 540, 960, 0, 0, "io"),
          (218.2, 1.06, 540, 930, -3, 0, "io"), (221.44, 1.0, 540, 960, 2, 0, "io"), (234.4, 1.06, 540, 940, -2, 0, "io"),
          (240.8, 1.0, 540, 960, 0, 0, "io"), (247.3, 1.0, 540, 965, 0, 0, "io"), (255.6, 1.0, 540, 965, 0, 0, "io"),
          (257.6, 0.70, 540, 990, -6, 3, "io"), (258.9, 1.0, 540, 1000, -1, 0, "io"), (260.6, 1.0, 540, 1000, -1, 0, "io"), (262.0, 0.42, 540, -690, -4, 2, "io"),
          (300, 0.42, 540, -690, -4, 2, "lin")]
_E = {"lin": lambda x: x, "io": ease_io}
KICKS = [(SC.CRACK_T, 0.07), (SC.COUNTERFEIT_T, 0.05)] + [(tf, 0.02) for tf in FLIPS]
SHAKES = [(SC.CRACK_T, 18.0, 0.32)]

def camera(fmt, t):
    sh = SHOTS16 if fmt == "16x9" else SHOTS9
    i = max(0, int(np.searchsorted([s[0] for s in sh], t, side="right")) - 1)
    a = sh[i]; b = sh[min(i + 1, len(sh) - 1)]
    k = _E[a[6]](clamp((t - a[0]) / max(1e-3, b[0] - a[0]))) if b is not a else 0.0
    z, cx, cy, yaw, pitch = (lerp(a[j], b[j], k) for j in range(1, 6))
    for tk, amp in KICKS:
        if tk <= t < tk + 1.0: z *= 1 + amp * clamp((t - tk) / 0.03) * math.exp(-(t - tk) / 0.16)
    cx += 6 * math.sin(t * 0.31) + 3 * math.sin(t * 0.73 + 1); cy += 4 * math.sin(t * 0.27 + 2)
    yaw += 0.6 * math.sin(t * 0.21); pitch += 0.3 * math.sin(t * 0.17 + 1)
    for ts, amp, dec in SHAKES:
        if ts <= t < ts + 1.5:
            e_ = amp * math.exp(-(t - ts) / dec); cx += e_ * math.sin(t * 71); cy += e_ * math.cos(t * 83)
    return z, cx, cy, yaw, pitch

D_CAM = 2600.0
def homography(W, H, PW, PH, z, cx, cy, yaw, pitch, src=None):
    s = (H / PH if W >= H else W / PW) * z; f = s * D_CAM
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    src = src if src is not None else np.array([(0, 0), (PW, 0), (PW, PH), (0, PH)], F32)
    dst = []
    for u, v in src:
        X, Y, Z = u - cx, v - cy, 0.0
        X, Z = X * cy_ + Z * sy_, -X * sy_ + Z * cy_
        Y, Z = Y * cp - Z * sp, Y * sp + Z * cp
        d = D_CAM + Z
        dst.append((W / 2 + f * X / d, H / 2 + f * Y / d))
    return cv2.getPerspectiveTransform(src, np.array(dst, F32)), s

@lru_cache(4)
def room(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    g = (0.020 + 0.016 * (1 - yy / H))[..., None] * np.array([0.85, 0.9, 1.0], F32)
    return np.ascontiguousarray(np.broadcast_to(g, (H, W, 3))).astype(F32)

@lru_cache(4)
def refl_fade(PW, PH):
    r = np.arange(PH, dtype=F32)
    return (0.42 * np.exp(-r / (PH * 0.30)))[:, None, None].astype(F32)

def hdr_at(t, W, H):
    fmt = fmt_of(W, H); Lo = LAY[fmt]; PW, PH = Lo["PW"], Lo["PH"]
    th = theme_at(t)
    if th <= 0.001: pg = render_page(fmt, t, 0)
    elif th >= 0.999: pg = render_page(fmt, t, 1)
    else: pg = render_page(fmt, t, 0) * (1 - th) + render_page(fmt, t, 1) * th
    z, cx, cy, yaw, pitch = camera(fmt, t)
    Hm, s = homography(W, H, PW, PH, z, cx, cy, yaw, pitch)
    img = room(W, H).copy()
    # the page's glow on the room
    pc = Hm @ np.array([PW / 2, PH / 2, 1.0]); pc = pc[:2] / pc[2]
    glow_room(img, pc, s, PW, PH, th)
    # floor reflection (only when the floor is in view)
    bl = Hm @ np.array([PW / 2, PH, 1.0]); bl = bl[:2] / bl[2]
    if bl[1] < H - 4:
        small = cv2.resize(pg, (PW // 2, PH // 2), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 2.5)
        R = cv2.resize(np.ascontiguousarray(small[::-1]), (PW, PH), interpolation=cv2.INTER_LINEAR) * refl_fade(PW, PH)
        T = np.array([[1, 0, 0], [0, 1, PH + 70], [0, 0, 1]], np.float64)
        rw = cv2.warpPerspective(R, Hm @ T, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        img = img * (1 - rw[..., 3:4]) + rw[..., :3]
    pw = cv2.warpPerspective(pg, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = pw[..., 3:4]
    img = img * (1 - a) + pw[..., :3]
    # a soft drop shadow under the floating page is implied by the dark room; a faint light bloom for the bright bits
    return img

def glow_room(img, pc, s, PW, PH, th):
    H, W = img.shape[:2]
    rx, ry = PW * s * 0.75, PH * s * 0.75
    x0, x1 = int(max(0, pc[0] - rx * 1.6)), int(min(W, pc[0] + rx * 1.6)); y0, y1 = int(max(0, pc[1] - ry * 1.6)), int(min(H, pc[1] + ry * 1.6))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
    g = np.exp(-(((xx - pc[0]) / rx) ** 2 + ((yy - pc[1]) / ry) ** 2))
    col = np.array([0.10, 0.13, 0.20], F32) * (1 + 3.0 * th)
    img[y0:y1, x0:x1] += g[..., None] * col

@lru_cache(4)
def vignette(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return np.clip(1 - 0.22 * d ** 2.4, 0, 1)[..., None].astype(F32)

def subtitles(img, t, W, H):
    """lyrics as on-screen subtitles only where the camera has looked away from the comment section."""
    if C.STATE["clean"]: return
    flt = C.STATE["lyric_filter"]
    L = LN[60]
    if flt is not None and not flt(L): return
    if not (L["s"] - 0.2 <= t <= 196.3): return
    vert = H > W; fs = 64 if not vert else 58
    op = sstep(L["s"] - 0.2, L["s"], t) * (1 - sstep(195.9, 196.3, t))
    words = L["words"]; xs = []
    tw = sum(C.text_w(w, C.F_INTER, fs) for w in words) + C.text_w(" ", C.F_INTER, fs) * (len(words) - 1)
    x = (W - tw) / 2; y = H * (0.80 if not vert else 0.70)
    for w, tt in zip(words, L["wt"]):
        k = sstep(tt - 0.12, tt + 0.05, t); act = math.exp(-max(0, t - tt) * 2.2) if t >= tt - 0.05 else 0
        col = C.IVORY * (1 - act) + ACC * act
        C.shadow(img, C.sprite(w, C.F_INTER, fs, 11), x, y + 2, 0.95 * op)
        C.blit(img, C.sprite(w, C.F_INTER, fs, 5), x, y, col, op * (0.32 + 0.68 * k), 0.4 * act, glow_color=ACC)
        x += C.text_w(w, C.F_INTER, fs) + C.text_w(" ", C.F_INTER, fs)

def render_frame(t, W=1920, H=1080, fi=0):
    img = hdr_at(t, W, H)
    # light bloom: only the brightest bits (the lit bulbs in the cover, white text in light mode is not boosted)
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    br = np.maximum(small - 0.82, 0)
    if br.max() > 0.002:
        img += cv2.resize(cv2.GaussianBlur(br, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR) * 0.9
    out = np.clip(img, 0, 1).astype(F32)
    out *= vignette(W, H)
    p = C.post(W, H)
    out += (cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST) * F32(0.010))[..., None]
    if not C.STATE["clean"]:
        C.subscribe_pill(out, t, W, H, 83.6, 5.0)
        C.end_screen(out, t, W, H, T_END, DUR - T_END, "See you in the comments.",
                     sub_line="Subscribe for a new song every week", title="Mirror, Mirror, Look at Us", accent=ACC)
    out *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
