"""Short C ("I knew it"), the 2D part in 9:16: the tail of "five-star review!" and the breakdown ("Claude?" "Yes?"
"Do you think I'm talented?" "You are extraordinarily–" "I KNEW IT!"), song time 151.05-158.30.
A 9:16 copy of scene.py's galaxy/rating + scene_breakdown (scene.py itself is untouched, so the 16:9 film can't change):
lyric-sized lines at 64 px, word-wrapped to stay inside the Shorts safe zone (x 80..940, nothing to read below 78% of H).
  render_frame(t, W, H) -> HxWx3 uint8   (run with sections/run.py)"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
if SONG not in sys.path: sys.path.insert(0, SONG)
import scene as SC
from scene import (K, DROP_HIT, C, S, text, tw, fit_size, rrect, star, cursor, typed_text, line, env, ease_out, sstep, clamp,
                   BG, INK, MUTE, GREEN, AMBER, GOLD, WHITE, F_MONOB, F_MONO, F_ANTON, T)


def wrap(s, size, maxw):
    out, cur = [], ""
    for w in s.split(" "):
        cand = (cur + " " + w).strip()
        if cur and tw(cand, size) > maxw: out.append(cur); cur = w
        else: cur = cand
    out.append(cur); return out


def galaxy_v(img, t, W, H, t0, op=1.0):
    """scene.galaxy re-shaped for 9:16: the same spiral of her frames as a tall ellipse that fits the phone frame
    (scene.py's spans 1.6x the frame width in portrait, so its thumbnails ran off both sides)."""
    import math
    if op <= 0.01 or not SC.STILLS: return
    ts = W / 1080
    img *= (1 - op * 0.96)   # the terminal under it all but gone (at 0.85 its boxes ghosted out beside the rating card)
    zoom = 1.0 + 1.2 * (1 - ease_out((t - t0) / 1.6)); rot = (t - t0) * 0.12
    cx, cy = W * 0.47, H * 0.42
    N = 260; rng = np.random.default_rng(11)
    for i in range(N):
        a = i * 2.39996 + rot; rr = math.sqrt(i / N) * W * 0.62 * 1.55
        x = cx + math.cos(a) * rr / zoom * 0.40
        y = cy + math.sin(a) * rr / zoom * 0.78
        sz = (1 - i / N) * 120 * ts + 26 * ts
        w, h = int(sz), int(sz * 9 / 16)
        st = SC.STILLS[(i * 13) % len(SC.STILLS)]
        bri = 0.55 + 0.45 * rng.random()
        if -w < x < W and -h < y < H:
            SC.FT.paste(img, SC.FT.still(st, w, h) * bri, x - w / 2, y - h / 2, radius=max(2, int(w * 0.05)), op=op)


def rating_v(img, t, W, H, t0):
    ts = W / 1080; k = ease_out((t - t0) / 0.2)
    bx, bw = S(80, ts), S(860, ts); by, bh = H * 0.47, S(400, ts)
    rrect(img, bx, by + (1 - k) * S(30, ts), bw, bh, S(20, ts), fill=BG, fill_op=0.94 * k, border=AMBER, border_op=k)
    fs = S(58, ts)
    for i, l in enumerate(("How is your", "universe doing?")):
        text(img, l, bx + S(44, ts), by + S(40, ts) + i * fs * 1.25, fs, INK, k, F_MONOB)
    dt = 60 / T.tempo / 2
    for j in range(5):
        lit = sstep(t0 + 0.4 + j * dt, t0 + 0.45 + j * dt, t)
        cx = bx + S(110, ts) + j * S(160, ts); cy = by + S(268, ts)
        star(img, cx, cy, S(58, ts), MUTE * 0.6, k, fill=False)
        if lit > 0: star(img, cx, cy, S(58, ts) * (1 + 0.25 * env(t, t0 + 0.4 + j * dt, 0.03, 0.2)), GOLD, k * lit)
    if t > t0 + 0.4 + 5 * dt:
        s = "thanks for the feedback"; f2 = S(36, ts)
        text(img, s, bx + bw - S(40, ts) - tw(s, f2, F_MONO), by + bh - S(58, ts), f2, MUTE, k, F_MONO)


def entries():
    def say(txt, sub, who, nth=0, rate=0.85):
        L = line(sub, nth); s, e = L["s"], L["e"]
        t1 = s + (e - s) * rate if who == "u" else s + min(0.45, (e - s) * 0.5)
        return dict(s=s - (0.05 if who == "u" else 0.0), t1=t1, text=txt, who=who)
    ex = dict(s=K["extra"] - 0.02, t1=max(K["extra"] + 0.6, K["knew"] - 0.15), text="You are extraordinarily", who="c")
    return [say("Claude?", "Claude?", "u", 1), say("Yes?", "Yes?", "c", 1), say("Do you think I'm talented?", "Do you think I'm talented?", "u"), ex]
ENT = entries()


def breakdown_v(img, t, W, H):
    ts = W / 1080; size = S(72, ts); lh = size * 1.32   # 72 px (was 64): the exchange fills the phone frame instead of floating small
    x = S(84, ts); pre = size * 0.95; maxw = S(940, ts) - x - pre
    vis = [e for e in ENT if t >= e["s"]]
    blocks = [wrap(e["text"] + ("—" if e is ENT[3] else ""), size, maxw) for e in vis]
    hts = [len(b) * lh for b in blocks]
    knew = t >= K["knew"] - 0.04
    total = sum(hts) + (size * 1.0 if knew else 0)
    # the block sits centred on 34% of H and eases as each new entry arrives
    if vis:
        prev = total - hts[-1]; k = ease_out((t - vis[-1]["s"]) / 0.18); tot_s = prev + (total - prev) * k
    else: tot_s = 0
    y = H * 0.36 - tot_s / 2
    for e, b in zip(vis, blocks):
        full = " ".join(b)
        if e is ENT[3]:   # Claude's compliment streams across the whole line until she cuts it off
            n = int(len("You are extraordinarily") * clamp((t - K["extra"]) / max(0.6, K["knew"] - K["extra"] - 0.15)))
            typed = full[:n] + ("—" if t >= K["knew"] - 0.05 else "")
        else:
            typed = typed_text(full, t, e["s"], e["t1"])
        left = len(typed); cx, cy = x, y
        for i, l in enumerate(b):
            part = l[:max(0, left)]; left -= len(l) + 1
            if i == 0:
                if e["who"] == "u": text(img, "❯", x, y, size, GREEN, 1.0, F_MONOB)
                else:
                    import cv2
                    cv2.circle(img, (int(x + size * 0.3), int(y + size * 0.72)), max(2, int(size * 0.2)), AMBER.tolist(), -1, cv2.LINE_AA)
            col = INK if e["who"] == "u" else AMBER
            if part: text(img, part, x + pre, y, size, col, 1.0, F_MONOB)
            if part or i == 0: cx, cy = x + pre + (tw(part, size) if part else 0), y
            y += lh
        typing = (e is vis[-1]) and ((e["who"] == "u" and t < e["t1"] + 0.6) or (e is ENT[3] and t < K["knew"]))
        if typing: cursor(img, cx + size * 0.12, cy + size * 0.18, int(size * 1.05), t, GREEN if e["who"] == "u" else AMBER, 1.0)
    if knew:
        text(img, "└ Interrupted by user", x + pre, y + size * 0.15, S(40, ts), MUTE, 1.0, F_MONO)
        k = ease_out((t - K["knew"] + 0.04) / 0.1); sc = 1.3 - 0.3 * k
        sz = fit_size("I KNEW IT!", F_ANTON, S(250, ts), S(800, ts))
        text(img, "I KNEW IT!", W / 2 - S(20, ts), H * 0.64, sz * sc, INK, min(1, k * 1.5), F_ANTON, anchor="c", glow=12, glow_op=0.4 * k, glow_color=AMBER)


def render_frame(t, W, H):
    fi = int(round(t * 30))
    if t < K["bd"] - 0.05:
        img = SC.compose(t, W, H)
        galaxy_v(img, t, W, H, K["universe"] - 0.1, 1.0)
        if t >= K["review"] - 0.05: rating_v(img, t, W, H, K["review"])
    else:
        img = np.empty((H, W, 3), np.float32); img[:] = BG
        breakdown_v(img, t, W, H)
    flash = 0.0
    for t0, a in ((K["fin_hook"], 0.5), (K["knew"], 0.5), (DROP_HIT, 0.45)):
        flash = max(flash, a * env(t, t0, 0.02, 0.18))
    return C.finish(img, t, fi, SC.DUR, flash=flash, flash_col=WHITE * 0.8, glitch_amt=0.0, ca=0.0012, vignette=True)
