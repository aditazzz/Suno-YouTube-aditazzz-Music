"""The apps on her laptop: the desktop, the meeting app (Huddle), its chat / people / Q&A panel, Notes, Calendar,
notifications and dialogs. All drawn from a state object S (see scene.state)."""
import math
import numpy as np
import ui as U
import avatars as A
from ui import text, rrect, circle, icon, stroke, poly

F32 = np.float32
def H(h): return U.hexc(h)
def mix(a, b, k): return np.asarray(a, F32) * (1 - k) + np.asarray(b, F32) * k

# ---------------------------------------------------------------- theme (light <-> dark)
LIGHT = dict(wall0=H("f2d6c2"), wall1=H("d7c4e6"), win=H("fafafa"), win2=H("f1f1f4"), border=H("d6d6dc"), ink=H("1d1d1f"),
             ink2=H("6b6b74"), menubar=H("f7f2f2"), chip=H("ececf1"), panel=H("ffffff"), bubble=H("ececf1"))
DARK = dict(wall0=H("1b1e30"), wall1=H("2b2140"), win=H("232428"), win2=H("2b2c31"), border=H("3a3b42"), ink=H("f2f2f5"),
            ink2=H("a2a2ab"), menubar=H("1e1f24"), chip=H("34353b"), panel=H("26272c"), bubble=H("34353b"))
ACCENT = H("4f6bed"); GREEN = H("35c47c"); RED = H("e5484d"); AMBER = H("f2a93b"); STAGE = H("141518")
CLIP_RED = H("e0352b")
def th(S, k): return mix(LIGHT[k], DARK[k], S.dark)

PEOPLE_ORDER = ["Ted", "Dana", "Priya", "Marcus", "Sam", "Lee", "Jo", "Me"]
INITIAL_COL = {"Ted": H("d9822b"), "Dana": H("c0577a"), "Priya": H("7a5ad1"), "Marcus": H("3d8fb8"), "Sam": H("4a9a6a"),
               "Lee": H("6b7280"), "Jo": H("b08a3a"), "Me": H("e0352b")}
DISPLAY = {"Me": "You", "Ted": "Ted (host)"}

# ---------------------------------------------------------------- the desktop
def desktop(img, cam, S):
    U.gradient_rect(img, cam, -400, -300, U.DW + 800, U.DH + 600, th(S, "wall0"), th(S, "wall1"))
    # a soft abstract wave on the wallpaper
    xs = np.linspace(-200, U.DW + 200, 60)
    for i, (amp, off, op) in enumerate(((60, 380, 0.10), (80, 470, 0.08), (50, 560, 0.07))):
        P = [(x, off + amp * math.sin(x / 210 + i * 1.7)) for x in xs] + [(U.DW + 200, U.DH + 300), (-200, U.DH + 300)]
        poly(img, cam, [P], (1, 1, 1) if S.dark < 0.5 else (0.6, 0.5, 1.0), op * (1 - 0.4 * S.dark))

def desktop_items(img, cam, S):
    ink = th(S, "ink")
    for i, (lab, kind) in enumerate((("Q4 roadmap", "folder"), ("standup notes", "doc"), ("the file (pending).pdf", "pdf"))):
        x, y = 1218.0, 196.0 + i * 92
        if kind == "folder":
            rrect(img, cam, x - 26, y - 14, 22, 8, 3, H("5aa7f0")); rrect(img, cam, x - 26, y - 10, 52, 36, 5, H("6cb6ff"))
        else:
            rrect(img, cam, x - 20, y - 18, 40, 50, 4, (1, 1, 1), 1.0, H("c9c9cf"), 0.8)
            if kind == "pdf": rrect(img, cam, x - 20, y + 14, 40, 13, 0, H("e5484d")); text(img, cam, "PDF", x, y + 20.5, 8.5, (1, 1, 1), "b", 1, "cm")
            else:
                for j in range(4): stroke(img, cam, [(x - 12, y - 8 + j * 7), (x + 12 - (j == 3) * 8, y - 8 + j * 7)], 1.4, H("b0b0b8"))
        for j, ln in enumerate(U.text_lines(lab, 11, 92, "s")[:2]):
            tw = U.text_w(ln, 11, 1.0, "s")
            rrect(img, cam, x - tw / 2 - 4, y + 36 + j * 14 - 7, tw + 8, 14, 4, (0, 0, 0), 0.18 * (1 - S.dark))
            text(img, cam, ln, x, y + 36 + j * 14, 11, (1, 1, 1) if S.dark > 0.5 else ink, "s", 1, "cm")
    # a sticky note
    x, y = 948.0, 236.0
    U.shadow(img, cam, x, y, 196, 150, 2, 0.18, 10, 6)
    poly(img, cam, [[(x, y), (x + 196, y + 4), (x + 192, y + 154), (x - 3, y + 150)]], H("fde68a"))
    text(img, cam, "ask Ted:", x + 18, y + 34, 26, H("3a3020"), "hand", 1, "lm")
    text(img, cam, "is the file ready??", x + 18, y + 72, 24, H("3a3020"), "hand", 1, "lm")
    stroke(img, cam, [(x + 18, y + 94), (x + 170, y + 92)], 2.0, H("c0392b"), 0.8)
    text(img, cam, "(asked 3x)", x + 18, y + 120, 20, H("6a5a3a"), "hand", 1, "lm")

def menubar(img, cam, S):
    rrect(img, cam, -400, -100, U.DW + 800, 122, 0, th(S, "menubar"), 0.94)
    circle(img, cam, 22, 11, 6.5, th(S, "ink"))
    circle(img, cam, 24.5, 9, 2.6, th(S, "menubar"))
    x = 40
    for i, m in enumerate(["Huddle", "File", "Edit", "View", "Meeting", "Window", "Help"]):
        w = text(img, cam, m, x, 11, 12.5, th(S, "ink"), "b" if i == 0 else "m")
        x += w + 18
    text(img, cam, S.clock_text, U.DW - 14, 11, 12.5, th(S, "ink"), "m", 1.0, "rm")
    icon(img, cam, "battery", U.DW - 150, 11, 15, th(S, "ink"))
    icon(img, cam, "wifi", U.DW - 178, 11, 15, th(S, "ink"))
    icon(img, cam, "search", U.DW - 202, 11, 14, th(S, "ink"))

def dock(img, cam, S):
    apps = [("finder", H("4d8ef0")), ("mail", H("3fa7f4")), ("cal", H("ffffff")), ("notes", H("f6d365")), ("chat", H("8b5cf6")),
            ("huddle", ACCENT), ("music", H("f2547a")), ("trash", H("9aa0a8"))]
    n = len(apps); sz = 40; gap = 10; W_ = n * sz + (n - 1) * gap + 24
    x0 = U.DW / 2 - W_ / 2; y0 = U.DH - 58
    rrect(img, cam, x0, y0, W_, 52, 16, th(S, "menubar"), 0.72, th(S, "border"), 0.8, 0.6)
    for i, (nm, col) in enumerate(apps):
        x = x0 + 12 + i * (sz + gap); y = y0 + 6
        rrect(img, cam, x, y, sz, sz, 10, col)
        cx, cy = x + sz / 2, y + sz / 2
        if nm == "cal":
            rrect(img, cam, x, y, sz, 12, 10, H("ef4444")); rrect(img, cam, x, y + 6, sz, 6, 0, H("ef4444"))
            text(img, cam, S.dock_day, cx, cy + 5, 17, H("1d1d1f"), "b", 1.0, "cm")
        elif nm == "huddle":
            rrect(img, cam, cx - 12, cy - 8, 17, 16, 4, (1, 1, 1)); poly(img, cam, [[(cx + 6, cy - 3), (cx + 13, cy - 8), (cx + 13, cy + 8), (cx + 6, cy + 3)]], (1, 1, 1))
        elif nm == "notes":
            for j in range(3): stroke(img, cam, [(cx - 10, cy - 6 + j * 7), (cx + 10, cy - 6 + j * 7)], 2.0, H("b8892a"))
        elif nm == "chat":
            icon(img, cam, "chat", cx, cy, 24, (1, 1, 1))
        elif nm == "mail":
            rrect(img, cam, cx - 12, cy - 8, 24, 16, 2, (1, 1, 1)); stroke(img, cam, [(cx - 12, cy - 8), (cx, cy + 1), (cx + 12, cy - 8)], 2, col)
        elif nm == "finder":
            rrect(img, cam, cx, y, sz / 2, sz, 0, H("7fb6ff")); circle(img, cam, cx - 8, cy - 4, 2, H("1d1d1f")); circle(img, cam, cx + 8, cy - 4, 2, H("1d1d1f"))
            stroke(img, cam, [(cx - 9, cy + 7), (cx, cy + 10), (cx + 9, cy + 7)], 2, H("1d1d1f"))
        elif nm == "music":
            stroke(img, cam, [(cx - 4, cy + 8), (cx - 4, cy - 9), (cx + 8, cy - 11), (cx + 8, cy + 5)], 2.4, (1, 1, 1))
            circle(img, cam, cx - 7, cy + 8, 3.6, (1, 1, 1)); circle(img, cam, cx + 5, cy + 5, 3.6, (1, 1, 1))
        elif nm == "trash":
            rrect(img, cam, cx - 9, cy - 8, 18, 19, 3, (1, 1, 1), 0.85)
        if nm in S.dock_running: circle(img, cam, cx, y0 + 49, 1.8, th(S, "ink"), 0.7)

# ---------------------------------------------------------------- windows
def window(img, cam, S, x, y, w, h, title, op=1.0, title_wt="s", bar=30):
    if op <= 0.01: return
    U.shadow(img, cam, x, y, w, h, 11, 0.28 * op, 18, 10)
    rrect(img, cam, x, y, w, h, 11, th(S, "win"), op, th(S, "border"), 1.0, 0.9)
    for i, c in enumerate((H("ff5f57"), H("febc2e"), H("28c840"))):
        circle(img, cam, x + 16 + i * 17, y + bar / 2, 5.2, mix(c, th(S, "chip"), 0.55), op)
    text(img, cam, title, x + w / 2, y + bar / 2, 13, th(S, "ink"), title_wt, op, "cm", maxw=w - 140)

# ---------------------------------------------------------------- the meeting app
def tile_layout(S, area):
    if getattr(S, "spk_mix", 0.0) <= 0.0 or getattr(S, "spk_from", None) is None: return _layout(S, area, S.speaker)
    A_ = _layout(S, area, S.spk_from); B_ = _layout(S, area, S.speaker); k = S.spk_mix
    return {p: tuple(np.array(A_.get(p, B_[p])) * (1 - k) + np.array(B_[p]) * k) for p in B_}

def _layout(S, area, spk):
    """tile rects for the visible participants in the current layout"""
    ax, ay, aw, ah = area; out = {}
    people = [p for p in PEOPLE_ORDER if S.present.get(p, 0) > 0.01]
    if not people: return {}
    k = S.speaker_k          # 0 = gallery, 1 = speaker view
    # gallery: 3 per row
    n = len(people); cols = 3 if n > 4 else 2; rows = (n + cols - 1) // cols
    g = 6.0
    tw = min((aw - g * (cols - 1)) / cols, ((ah - g * (rows - 1)) / rows) * 16 / 9); th_ = tw * 9 / 16
    gw = cols * tw + (cols - 1) * g; gh = rows * th_ + (rows - 1) * g
    gx0 = ax + (aw - gw) / 2; gy0 = ay + (ah - gh) / 2
    gal = {}
    for i, p in enumerate(people):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        rx0 = ax + (aw - (in_row * tw + (in_row - 1) * g)) / 2
        gal[p] = (rx0 + c * (tw + g), gy0 + r * (th_ + g), tw, th_)
    # speaker: the speaker big, a filmstrip of the others across the top
    others = [p for p in people if p != spk]
    fh = 0.0 if not others else min(64.0, ah * 0.16); fw = fh * 16 / 9
    fstrip_w = len(others) * fw + max(0, len(others) - 1) * 5
    if fstrip_w > aw: fw = (aw - 5 * (len(others) - 1)) / max(1, len(others)); fh = fw * 9 / 16; fstrip_w = aw
    spk_area_h = ah - (fh + 8 if others else 0)
    sw = min(aw, spk_area_h * 16 / 9); sh = sw * 9 / 16
    spkr = {spk: (ax + (aw - sw) / 2, ay + (fh + 8 if others else 0) + (spk_area_h - sh) / 2, sw, sh)}
    fx0 = ax + (aw - fstrip_w) / 2
    for i, p in enumerate(others): spkr[p] = (fx0 + i * (fw + 5), ay, fw, fh)
    for p in people:
        a, b = np.array(gal[p]), np.array(spkr.get(p, gal[p]))
        out[p] = tuple(a * (1 - k) + b * k)
    return out

def huddle(img, cam, S):
    x, y, w, h = S.hud
    op = S.hud_op
    if op <= 0.01: return
    window(img, cam, S, x, y, w, h, S.title, op)
    # header: timer, end time, view, people
    hy = y + 30 + 17
    tcol = RED if S.timer_red else th(S, "ink")
    rrect(img, cam, x + 12, hy - 12, 96, 24, 12, mix(th(S, "chip"), RED, 0.18 if S.timer_red else 0), op)
    circle(img, cam, x + 26, hy, 4.2, RED if S.timer_red else GREEN, op)
    text(img, cam, S.timer_text, x + 36, hy, 13.5, tcol, "mono", op, "lm")
    text(img, cam, S.ends_text, x + 118, hy, 12.5, RED if S.timer_red else th(S, "ink2"), "m", op, "lm")
    rx = x + w - 14 - S.panel_w
    icon(img, cam, "people", rx - 14, hy, 16, th(S, "ink2"), op)
    text(img, cam, str(S.n_present), rx - 28, hy, 12.5, th(S, "ink2"), "s", op, "rm")
    text(img, cam, "Speaker" if S.speaker_k > 0.5 else "Gallery", rx - 54, hy, 12.5, th(S, "ink2"), "m", op, "rm")
    icon(img, cam, "speaker" if S.speaker_k > 0.5 else "grid", rx - 112, hy, 15, th(S, "ink2"), op)
    if S.rec > 0:
        rrect(img, cam, x + w / 2 + 70, y + 7, 54, 17, 8.5, mix(th(S, "chip"), RED, 0.25), op * S.rec)
        circle(img, cam, x + w / 2 + 80, y + 15.5, 3.4, RED, op * S.rec)
        text(img, cam, "REC", x + w / 2 + 88, y + 15.5, 10.5, RED, "b", op * S.rec, "lm")
    # the stage: video area
    vx, vy, vw, vh = x + 10, y + 64, w - 20 - S.panel_w, h - 64 - 56
    rrect(img, cam, vx, vy, vw, vh, 8, STAGE, op)
    U.CLIP.push(cam, vx, vy, vw, vh)
    tiles = tile_layout(S, (vx + 8, vy + 8, vw - 16, vh - 16))
    S.tiles = tiles
    for p, r in tiles.items():
        draw_tile(img, cam, S, p, r, op * S.present.get(p, 1.0))
    if S.share > 0.01 and S.speaker in tiles:
        share_view(img, cam, S, tiles[S.speaker], op * S.share)
    if S.spinner > 0.01 and S.speaker in tiles:
        tx, ty, tw, th_ = tiles[S.speaker]
        rrect(img, cam, tx, ty, tw, th_, 6, (0, 0, 0), 0.45 * S.spinner * op)
        cx, cy = tx + tw / 2, ty + th_ / 2 - 10
        for i in range(12):
            a = i / 12 * 2 * math.pi + S.t * 7.5; aa = (i / 12) ** 1.4
            circle(img, cam, cx + math.cos(a) * 24, cy + math.sin(a) * 24, 4.2, (1, 1, 1), op * S.spinner * (0.15 + 0.85 * aa))
        text(img, cam, S.spinner_text, cx, cy + 46, 14, (1, 1, 1), "s", op * S.spinner, "cm")
    if S.captions > 0.01 and S.caption_text:
        cw = min(vw - 60, U.text_w(S.caption_text, 15, 1.0, "s") + 40)
        rrect(img, cam, vx + vw / 2 - cw / 2, vy + vh - 44, cw, 32, 6, (0, 0, 0), 0.72 * S.captions * op)
        text(img, cam, S.caption_text, vx + vw / 2, vy + vh - 28, 15, (1, 1, 1), "s", op * S.captions, "cm", maxw=cw - 30)
    U.CLIP.pop()
    # reactions floating up from her tile
    for (kind, k_, px) in S.reactions:
        if "Me" in tiles:
            tx, ty, tw, th_ = tiles[S.react_from] if S.react_from in tiles else tiles["Me"]
            rx_, ry_ = tx + tw * px, ty + th_ - 20 - 150 * k_
            sticker(img, cam, kind, rx_, ry_, 22 * (0.6 + 0.4 * min(1, k_ * 4)), op * (1 - max(0, k_ - 0.7) / 0.3))
    # side panel (chat / people / Q&A)
    if S.panel_w > 10:
        side_panel(img, cam, S, (x + w - 10 - S.panel_w + 6, y + 64, S.panel_w - 6, h - 64 - 56), op)
    # the control bar
    by = y + h - 28
    btns = [("mic" if S.my_mic else "mic_off", "Unmute" if not S.my_mic else "Mute", not S.my_mic), ("cam", "Video", False), ("share", "Share", False),
            ("react", "React", False), ("hand", "Raise", S.my_hand > 0.5), ("cc", "Captions", S.captions > 0.5),
            ("chat", "Chat", S.panel == "chat"), ("people", "People", S.panel == "people"), ("dots", "More", False)]
    n = len(btns); bw = 52; x0 = x + (w - 120) / 2 - n * bw / 2
    S.btn = {}
    for i, (ic, label, active) in enumerate(btns):
        bx = x0 + i * bw + bw / 2
        S.btn[label] = (bx, by)
        hl = S.hover == label
        if active or hl: rrect(img, cam, bx - 22, by - 21, 44, 42, 9, ACCENT if (active and ic not in ("mic_off",)) else th(S, "chip"),
                              op * (0.18 if (active and ic != "mic_off") else 0.9))
        col = RED if ic == "mic_off" else (ACCENT if active else th(S, "ink"))
        icon(img, cam, ic, bx, by - 6, 18, col, op)
        text(img, cam, label, bx, by + 13, 9.5, th(S, "ink2"), "m", op, "cm")
    lx = x + w - 96
    S.btn["Leave"] = (lx + 40, by)
    rrect(img, cam, lx, by - 15, 80, 30, 9, RED, op)
    text(img, cam, "Leave", lx + 40, by, 13, (1, 1, 1), "s", op, "cm")

def draw_tile(img, cam, S, p, r, op):
    x, y, w, h = r
    if op <= 0.01 or w < 4: return
    U.CLIP.push(cam, x, y, w, h)
    if S.cam_on.get(p, 1.0) > 0.5:
        st = S.st.get(p) or A.St()
        bg = S.bg.get(p, p)
        A.room(img, cam, r, bg, S.t, getattr(st, "d", 0.0))
        if p == "Dana" and S.ghost > 0:
            ghost_avatar(img, cam, r, S.ghost)
        else:
            A.draw(img, cam, r, p, st, S.t)
    else:
        A.camera_off(img, cam, r, p, INITIAL_COL[p])
    if p == "Dana" and S.ghost > 0 and S.cam_on.get(p, 1.0) <= 0.5:
        ghost_avatar(img, cam, r, S.ghost)
    U.CLIP.pop()
    k = w / 160.0
    rrect(img, cam, x, y, w, h, 6 * min(1, k), None, op, H("000000"), 1.0, 0.4)
    if S.speaking.get(p, 0) > 0.01:
        rrect(img, cam, x + 1, y + 1, w - 2, h - 2, 6 * min(1, k), None, op * S.speaking[p], GREEN, max(2.0, 1.4 * k))
    # name label
    if w > 60:
        nm = DISPLAY.get(p, p) + (S.name_suffix.get(p, ""))
        fs = max(8.5, min(12.5, 7.2 * k))
        tw = U.text_w(nm, fs, 1.0, "s") + fs * 2.4
        rrect(img, cam, x + 6, y + h - fs * 2.2 - 4, tw, fs * 2.0, fs * 0.5, (0, 0, 0), 0.55 * op)
        icon(img, cam, "mic_off" if S.muted.get(p, True) else "mic", x + 6 + fs * 0.95, y + h - fs * 1.2 - 4, fs * 1.1, RED if S.muted.get(p, True) else (1, 1, 1), op)
        text(img, cam, nm, x + 6 + fs * 1.8, y + h - fs * 1.2 - 4, fs, (1, 1, 1), "s", op, "lm")
    if S.hands.get(p, 0) > 0.01:
        hs = max(16.0, 11 * k)
        rrect(img, cam, x + w - hs * 1.6, y + 6, hs * 1.3, hs * 1.3, hs * 0.35, AMBER, op * S.hands[p])
        icon(img, cam, "hand", x + w - hs * 0.95, y + 6 + hs * 0.65, hs, (1, 1, 1), op * S.hands[p])

def ghost_avatar(img, cam, r, k):
    x, y, w, h = r; s = w / 160.0
    cx, cy = x + w / 2, y + h * 0.5 + 3 * math.sin(k * 20) * s
    pts = [(cx - 26 * s, cy + 30 * s)]
    for i in range(7): pts.append((cx - 26 * s + i * 8.7 * s, cy + (34 + 5 * (1 if i % 2 else -1)) * s))
    pts += [(cx + 26 * s, cy + 30 * s), (cx + 27 * s, cy - 8 * s), (cx + 15 * s, cy - 30 * s), (cx, cy - 36 * s), (cx - 15 * s, cy - 30 * s), (cx - 27 * s, cy - 8 * s)]
    poly(img, cam, [U.smooth(pts, 4)], (0.95, 0.95, 1.0), 0.88 * k)
    for dx in (-8, 8): poly(img, cam, [U.ellipse(cx + dx * s, cy - 10 * s, 3.6 * s, 5.6 * s, n=14)], H("2a2a33"), k)
    poly(img, cam, [U.ellipse(cx, cy + 6 * s, 4 * s, 5 * s, n=14)], H("2a2a33"), k * 0.8)

def sticker(img, cam, kind, x, y, r, op):
    """a reaction: drawn emoji-like stickers (laugh, cricket, sleepy, clap, eyes, ghost)"""
    if op <= 0.01: return
    if kind in ("laugh", "sleepy", "eyes"):
        circle(img, cam, x, y, r, H("ffcc33"), op)
        if kind == "laugh":
            for dx in (-1, 1): stroke(img, cam, [(x + dx * r * 0.52, y - r * 0.18), (x + dx * r * 0.32, y - r * 0.32), (x + dx * r * 0.12, y - r * 0.18)], r * 0.12, H("5a3a10"), op)
            poly(img, cam, [[(x - r * 0.55, y + r * 0.08), (x + r * 0.55, y + r * 0.08), (x + r * 0.32, y + r * 0.55), (x - r * 0.32, y + r * 0.55)]], H("5a3a10"), op)
            for dx in (-1, 1): poly(img, cam, [U.ellipse(x + dx * r * 0.82, y - r * 0.02, r * 0.14, r * 0.26, n=12)], H("5ab4ff"), op)
        elif kind == "sleepy":
            for dx in (-1, 1): stroke(img, cam, [(x + dx * r * 0.55, y - r * 0.12), (x + dx * r * 0.18, y - r * 0.08)], r * 0.11, H("5a3a10"), op)
            circle(img, cam, x, y + r * 0.38, r * 0.16, H("5a3a10"), op)
            text(img, cam, "z", x + r * 0.9, y - r * 0.9, r * 0.7, H("6b8cff"), "k", op, "cm")
        else:
            for dx in (-1, 1): circle(img, cam, x + dx * r * 0.38, y - r * 0.1, r * 0.3, (1, 1, 1), op); circle(img, cam, x + dx * r * 0.38 + r * 0.1, y - r * 0.1, r * 0.14, H("2a2a2a"), op)
    elif kind == "cricket":
        poly(img, cam, [U.ellipse(x, y, r * 0.95, r * 0.38, -0.2, n=24)], H("5f9a3a"), op)
        circle(img, cam, x + r * 0.95, y - r * 0.28, r * 0.30, H("4f8a2e"), op)
        for dx in (-0.4, 0.1, 0.5): stroke(img, cam, [(x + dx * r, y + r * 0.25), (x + (dx - 0.25) * r, y + r * 0.85)], r * 0.08, H("3e6e22"), op)
        stroke(img, cam, [(x - r * 0.3, y), (x - r * 0.9, y - r * 0.8), (x - r * 1.2, y + r * 0.6)], r * 0.12, H("3e6e22"), op)
        stroke(img, cam, [(x + r * 1.1, y - r * 0.5), (x + r * 1.6, y - r * 1.2)], r * 0.05, H("3e6e22"), op)
        stroke(img, cam, [(x + r * 1.0, y - r * 0.5), (x + r * 1.3, y - r * 1.4)], r * 0.05, H("3e6e22"), op)
    elif kind == "ghost":
        pts = [(x - r * 0.8, y + r * 0.9)] + [(x - r * 0.8 + i * r * 0.27, y + r * (1.0 + 0.15 * (1 if i % 2 else -1))) for i in range(7)] + \
              [(x + r * 0.8, y + r * 0.9), (x + r * 0.82, y - r * 0.2), (x + r * 0.45, y - r * 0.9), (x, y - r * 1.05), (x - r * 0.45, y - r * 0.9), (x - r * 0.82, y - r * 0.2)]
        poly(img, cam, [U.smooth(pts, 4)], (0.97, 0.97, 1.0), op)
        for dx in (-0.25, 0.25): poly(img, cam, [U.ellipse(x + dx * r, y - r * 0.3, r * 0.12, r * 0.18, n=10)], H("2a2a33"), op)

# ---------------------------------------------------------------- what Ted shares
def share_view(img, cam, S, r, op):
    x, y, w, h = r; k = w / 160.0
    U.CLIP.push(cam, x, y, w, h)
    rrect(img, cam, x, y, w, h, 0, H("1d1e22"), op)
    kind = S.share_kind
    if kind == "slides":     # a blank slide: no slides, no point
        rrect(img, cam, x + 8 * k, y + 8 * k, w - 16 * k, h - 22 * k, 1.5 * k, (1, 1, 1), op)
        if S.share_sub > 0.0:
            rrect(img, cam, x + 18 * k, y + 16 * k, w - 36 * k, 16 * k, 1 * k, None, op * 0.9, H("b9bcc7"), 0.6 * k)
            text(img, cam, "Click to add title", x + w / 2, y + 24 * k, 6.5 * k, H("a3a7b3"), "m", op * 0.9, "cm")
        if S.share_sub > 1.0:
            rrect(img, cam, x + 18 * k, y + 38 * k, w - 36 * k, 36 * k, 1 * k, None, op * 0.9, H("b9bcc7"), 0.6 * k)
            text(img, cam, "•  Click to add text", x + 24 * k, y + 46 * k, 4.6 * k, H("a3a7b3"), "m", op * 0.9, "lm")
        text(img, cam, "Slide 1 of 1", x + w - 10 * k, y + h - 7 * k, 4.2 * k, H("9a9ca6"), "m", op, "rm")
    elif kind in ("dad", "dad2", "young", "violin"):
        photo(img, cam, (x + 6 * k, y + 6 * k, w - 12 * k, h - 18 * k), kind, S.t, op)
        name = {"dad": "dad_fishing_1987.jpg", "dad2": "dad_and_grandpa.jpg", "young": "me_age_7.jpg", "violin": "me_age_8_recital.jpg"}[kind]
        text(img, cam, name, x + w / 2, y + h - 6 * k, 4.4 * k, H("c9cad2"), "m", op, "cm")
    # his small video in the corner
    st = S.st.get(S.speaker)
    sw, sh = w * 0.22, w * 0.22 * 9 / 16
    rr = (x + w - sw - 5 * k, y + h - sh - 14 * k, sw, sh)
    U.CLIP.push(cam, *rr)
    A.room(img, cam, rr, S.bg.get(S.speaker, S.speaker), S.t); A.draw(img, cam, rr, S.speaker, st or A.St(), S.t)
    U.CLIP.pop()
    rrect(img, cam, *rr, 2 * k, None, op, (1, 1, 1), 0.6 * k, 0.8)
    U.CLIP.pop()
    lbl = "Ted is sharing his screen"
    tw = U.text_w(lbl, 11, 1.0, "s") + 24
    rrect(img, cam, x + w / 2 - tw / 2, y + 6, tw, 22, 11, GREEN, op)
    text(img, cam, lbl, x + w / 2, y + 17, 11, (1, 1, 1), "s", op, "cm")

def photo(img, cam, r, kind, t, op):
    """an old photo, warm and faded, drawn in a few flat shapes"""
    x, y, w, h = r; k = w / 160.0
    sep = lambda c: mix(H(c), H("c9a77a"), 0.45)
    U.gradient_rect(img, cam, x, y, w, h, sep("f3e3c3"), sep("d8c09a"), op)
    def Pp(P): return [(x + px * k, y + py * k * (h / w * 160 / 90)) for px, py in P]
    if kind in ("dad", "dad2"):
        poly(img, cam, [Pp([(0, 52), (160, 48), (160, 90), (0, 90)])], sep("8fa6b0"), op)            # the lake
        poly(img, cam, [Pp([(0, 50), (30, 40), (60, 46), (95, 36), (130, 44), (160, 40), (160, 50), (0, 54)])], sep("7a8a6a"), op)
        poly(img, cam, [Pp([(48, 62), (112, 62), (104, 72), (56, 72)])], sep("6b4a32"), op)          # the boat
        cx = 80
        poly(img, cam, [Pp(U.ellipse(cx, 44, 5, 6, n=16))], sep("c99a7a"), op)
        poly(img, cam, [Pp([(cx - 9, 50), (cx + 9, 50), (cx + 10, 63), (cx - 10, 63)])], sep("5a6a4a"), op)
        poly(img, cam, [Pp([(cx - 7, 41), (cx + 7, 41), (cx + 9, 39.5), (cx, 36.5), (cx - 9, 39.5)])], sep("6a5a3a"), op)  # the hat
        stroke(img, cam, Pp([(cx + 8, 54), (cx + 40, 30)]), 0.9 * k, sep("3a2a1a"), op)
        stroke(img, cam, Pp([(cx + 40, 30), (cx + 44, 62)]), 0.3 * k, sep("3a2a1a"), op)
        if kind == "dad2":   # he's holding up a photo of his own father
            poly(img, cam, [Pp([(cx - 32, 34), (cx - 10, 34), (cx - 10, 54), (cx - 32, 54)])], sep("f5ead2"), op)
            poly(img, cam, [Pp([(cx - 29, 37), (cx - 13, 37), (cx - 13, 51), (cx - 29, 51)])], sep("b8a07a"), op)
            poly(img, cam, [Pp(U.ellipse(cx - 21, 42, 2.6, 3, n=12))], sep("8a6a4a"), op)
            poly(img, cam, [Pp([(cx - 25, 46), (cx - 17, 46), (cx - 16, 51), (cx - 26, 51)])], sep("6a5a4a"), op)
    else:
        poly(img, cam, [Pp([(0, 66), (160, 66), (160, 90), (0, 90)])], sep("7a7a7a"), op)              # the street
        stroke(img, cam, Pp([(122, 66), (122, 14)]), 1.4 * k, sep("3a3a3a"), op)                  # lamppost
        poly(img, cam, [Pp([(116, 14), (128, 14), (125, 19), (119, 19)])], sep("3a3a3a"), op)
        U.glow(img, cam, x + 122 * k, y + 20 * k * (h / w * 160 / 90), 16 * k, (0.35, 0.28, 0.12), op * 0.8)
        cx = 70
        poly(img, cam, [Pp(U.ellipse(cx, 40, 4, 4.6, n=16))], sep("e2b896"), op)
        poly(img, cam, [Pp(U.ellipse(cx, 37.2, 4.4, 2.6, n=16))], sep("4a3a2a"), op)
        poly(img, cam, [Pp([(cx - 6, 45), (cx + 6, 45), (cx + 6.5, 56), (cx - 6.5, 56)])], sep("8a3a3a"), op)
        poly(img, cam, [Pp([(cx - 4.5, 56), (cx - 0.5, 56), (cx - 1, 66), (cx - 4, 66)]), Pp([(cx + 0.5, 56), (cx + 4.5, 56), (cx + 4, 66), (cx + 1, 66)])], sep("3a3a4a"), op)
        if kind == "young":
            poly(img, cam, [Pp([(cx + 8, 56), (cx + 20, 56), (cx + 20, 66), (cx + 8, 66)])], sep("6b4a32"), op)          # suitcase
        else:
            poly(img, cam, [Pp(U.ellipse(cx - 7, 50, 3.8, 6, 0.6, n=14))], sep("8a4a1a"), op)                            # violin
            stroke(img, cam, Pp([(cx + 4, 46), (cx - 14, 58)]), 0.5 * k, sep("3a2a1a"), op)
        for j in range(26):     # rain
            rx = (j * 37 + t * 70) % 160; ry = (j * 53 + t * 210) % 90
            stroke(img, cam, Pp([(rx, ry), (rx - 1.5, ry + 6)]), 0.35 * k, (1, 1, 1), op * 0.6)
    # the photo's white border
    rrect(img, cam, x, y, w, h, 0, None, op, H("f7f2e6"), 3.0 * k)

# ---------------------------------------------------------------- the side panel
def side_panel(img, cam, S, r, op):
    x, y, w, h = r
    rrect(img, cam, x, y, w, h, 8, th(S, "panel"), op, th(S, "border"), 0.8, 0.8)
    tabs = ["Chat", "People", "Q&A"]
    for i, tb in enumerate(tabs):
        tx = x + 14 + i * 70
        lab = S.qa_label if tb == "Q&A" else tb
        active = S.panel == tb.lower() or (tb == "Q&A" and S.panel == "qa")
        text(img, cam, lab, tx, y + 18, 12.5, th(S, "ink") if active else th(S, "ink2"), "s" if active else "m", op, "lm")
        if active: rrect(img, cam, tx, y + 30, U.text_w(lab, 12.5, 1.0, "s"), 2.4, 1.2, ACCENT, op)
    stroke(img, cam, [(x, y + 34), (x + w, y + 34)], 0.8, th(S, "border"), op)
    U.CLIP.push(cam, x, y + 35, w, h - 35)
    if S.panel == "chat": chat(img, cam, S, (x, y + 35, w, h - 35), op)
    elif S.panel == "people": people(img, cam, S, (x, y + 35, w, h - 35), op)
    elif S.panel == "qa": qa(img, cam, S, (x, y + 35, w, h - 35), op)
    U.CLIP.pop()

def chat(img, cam, S, r, op):
    x, y, w, h = r
    inp_h = 44
    # messages from the bottom up
    yy = y + h - inp_h - 10
    for m in reversed(S.messages):
        who, body, k_ = m["who"], m["text"], m["k"]
        mine = who == "Me"
        fs = 13.0; maxw = w - 70
        lines = U.text_lines(body, fs, maxw, "m")
        if m.get("clip") and len(lines) > m["clip"]: lines = lines[:m["clip"]]; lines[-1] = lines[-1] + "… Read more"
        lh = fs * 1.38; bh = len(lines) * lh + 14
        bw = max(U.text_w(l, fs, 1.0, "m") for l in lines) + 22
        name_h = 18
        yy -= bh + name_h + 8
        if yy + bh + name_h < y: break
        a = op * k_
        bx = x + w - 12 - bw if mine else x + 40
        if not mine:
            circle(img, cam, x + 22, yy + name_h + 12, 11, INITIAL_COL.get(who, ACCENT), a)
            text(img, cam, who[0], x + 22, yy + name_h + 12, 10.5, (1, 1, 1), "s", a, "cm")
        text(img, cam, ("You" if mine else who) + "  " + m.get("time", ""), bx + (bw if mine else 0), yy + 8, 10.5, th(S, "ink2"), "m", a, "rm" if mine else "lm")
        col = ACCENT if mine else th(S, "bubble")
        if m.get("hl", 0) > 0: col = mix(col, AMBER, m["hl"] * 0.6)
        rrect(img, cam, bx, yy + name_h, bw, bh, 12, col, a)
        for i, l in enumerate(lines):
            text(img, cam, l, bx + 11, yy + name_h + 7 + lh * (i + 0.5), fs, (1, 1, 1) if mine else th(S, "ink"), "m", a, "lm")
        if m.get("react"):
            sticker(img, cam, m["react"], bx + bw - 4 if not mine else bx + 4, yy + name_h + bh, 9, a)
        if m.get("status"):
            st_ = m["status"]
            col_ = RED if "Not" in st_ else th(S, "ink2")
            text(img, cam, st_, bx + bw, yy + name_h + bh + 10, 10.5, col_, "s", a, "rm")
    # the input box
    iy = y + h - inp_h - 6
    rrect(img, cam, x + 10, iy, w - 20, inp_h - 6, 10, th(S, "win2"), op, th(S, "border"), 0.8, 0.8)
    if S.typing:
        text(img, cam, S.typing, x + 22, iy + (inp_h - 6) / 2, 13, th(S, "ink"), "m", op, "lm", maxw=w - 80)
        if (S.t * 2) % 1 < 0.5:
            tw = min(U.text_w(S.typing, 13, 1.0, "m"), w - 80)
            rrect(img, cam, x + 23 + tw, iy + 10, 1.4, inp_h - 26, 0, ACCENT, op)
    else:
        text(img, cam, S.placeholder, x + 22, iy + (inp_h - 6) / 2, 13, th(S, "ink2"), "m", op * 0.8, "lm")
    icon(img, cam, "send", x + w - 30, iy + (inp_h - 6) / 2, 16, ACCENT if S.typing else th(S, "ink2"), op)

def people(img, cam, S, r, op):
    x, y, w, h = r
    text(img, cam, "In this meeting (%d)" % S.n_listed, x + 14, y + 18, 11.5, th(S, "ink2"), "s", op, "lm")
    for i, p in enumerate(PEOPLE_ORDER):
        ry = y + 36 + i * 46
        a = op * S.list_k.get(p, 1.0)
        if a <= 0.01: continue
        gone = S.gone.get(p, 0.0)
        if S.ghost > 0 and p == "Dana":
            sticker(img, cam, "ghost", x + 26, ry + 16, 15, a * (0.4 + 0.6 * S.ghost))
        else:
            circle(img, cam, x + 26, ry + 16, 14, mix(INITIAL_COL[p], H("8a8a8a"), gone), a)
            text(img, cam, p[0], x + 26, ry + 16, 12, (1, 1, 1), "s", a, "cm")
        nm = DISPLAY.get(p, p)
        text(img, cam, nm, x + 48, ry + 10, 13, mix(th(S, "ink"), th(S, "ink2"), gone), "s", a, "lm")
        sub = S.sub.get(p, "")
        tt = S.talk.get(p); tk = S.talk_k if tt is not None else 0.0
        if sub and tk < 0.99: text(img, cam, sub, x + 48, ry + 27, 11, RED if S.sub_red.get(p) else th(S, "ink2"), "m", a * (1 - tk), "lm")
        if tk > 0:
            full = w - 48 - 70
            rrect(img, cam, x + 48, ry + 24, full, 6, 3, th(S, "chip"), a * tk)
            bw = full * min(1.0, tt / 6.0) * tk
            if bw > 1: rrect(img, cam, x + 48, ry + 24, max(6, bw), 6, 3, RED if p == "Ted" else GREEN, a * tk)
            text(img, cam, "%d min" % tt, x + w - 14, ry + 27, 12, RED if p == "Ted" else th(S, "ink2"), "s", a * tk, "rm")
        icon(img, cam, "mic_off" if S.muted.get(p, True) else "mic", x + w - 24, ry + 11, 14, RED if S.muted.get(p, True) else th(S, "ink"), a * (1 - gone) * (1 - tk))

def qa(img, cam, S, r, op):
    x, y, w, h = r
    for i, (lab, val) in enumerate(S.qa_counts):
        cy = y + 40 + i * 64
        rrect(img, cam, x + 14, cy - 24, w - 28, 52, 10, th(S, "win2"), op * S.qa_row_k[i])
        text(img, cam, lab, x + 28, cy + 2, 14, th(S, "ink"), "s", op * S.qa_row_k[i], "lm")
        text(img, cam, val, x + w - 28, cy + 2, 22, RED if val == "0" else th(S, "ink"), "b", op * S.qa_row_k[i], "rm")
    if S.qa_note:
        rrect(img, cam, x + 14, y + 176, w - 28, 64, 10, mix(th(S, "win2"), RED, 0.30), op * S.qa_note_k, RED, 1.0, 0.6)
        icon(img, cam, "lock", x + 34, y + 208, 15, RED, op * S.qa_note_k)
        for j, ln in enumerate(U.text_lines(S.qa_note, 12, w - 80, "s")[:2]):
            text(img, cam, ln, x + 50, y + 198 + j * 18, 12, th(S, "ink"), "s", op * S.qa_note_k, "lm")
    # the question box
    iy = y + h - 50
    rrect(img, cam, x + 10, iy, w - 20, 38, 10, th(S, "win2"), op, th(S, "border"), 0.8, 0.8)
    text(img, cam, S.qa_typing or "Ask a question…", x + 22, iy + 19, 13, th(S, "ink") if S.qa_typing else th(S, "ink2"), "m", op, "lm", maxw=w - 70)

# ---------------------------------------------------------------- Notes: a tally and buzzword bingo
def notes(img, cam, S):
    if S.notes_op <= 0.01: return
    x, y, w, h = S.notes_r; op = S.notes_op
    window(img, cam, S, x, y, w, h, "standup notes", op)
    rrect(img, cam, x + 1, y + 30, w - 2, h - 31, 10, mix(H("fff8dc"), H("3a3626"), S.dark), op)
    ink = mix(H("2b2a24"), H("f3eed8"), S.dark)
    yy = y + 52
    for lab, n in S.tally:
        text(img, cam, lab, x + 18, yy, 16, ink, "s", op, "lm")
        tally(img, cam, x + 98, yy, n, ink, op)
        yy += 34
    if S.bingo_k > 0.01:
        bx, by = x + 18, y + 128; cw, ch = (w - 36) / 3, 46
        words = ["SYNERGY", "JOURNEY", "NORTH STAR", "DEEP DIVE", "UNLOCK", "PIVOT", "MOONSHOT", "STORY", "LEVERAGE"]
        text(img, cam, "BUZZWORD BINGO", x + w / 2, by - 12, 12.5, ink, "b", op * S.bingo_k, "cm", track=0.12)
        for i, wd in enumerate(words):
            r_, c_ = divmod(i, 3)
            cx, cy = bx + c_ * cw, by + r_ * ch
            rrect(img, cam, cx + 2, cy + 2, cw - 4, ch - 4, 6, mix(H("ffffff"), H("4a4535"), S.dark), op * S.bingo_k, mix(H("d8cfa8"), H("6a6450"), S.dark), 0.8)
            text(img, cam, wd, cx + cw / 2, cy + ch / 2, 11.5, ink, "b", op * S.bingo_k, "cm", maxw=cw - 8)
            k_ = S.marks.get(wd, 0.0)
            if k_ > 0:
                rr = 15 + 6 * (1 - min(1, k_ * 3))
                U.ring(img, cam, cx + cw / 2, cy + ch / 2, rr, 3.2, CLIP_RED, op * min(1, k_ * 3) * 0.9)
        if S.bingo_stamp > 0:
            s = S.bingo_stamp; sz = 46 * (1.6 - 0.6 * min(1, s * 3))
            cx, cy = bx + 1.5 * cw, by + 1.5 * ch
            rrect(img, cam, cx - 120, cy - 32, 240, 64, 10, None, op * min(1, s * 3), CLIP_RED, 5)
            text(img, cam, "BINGO!", cx, cy, sz, CLIP_RED, "k", op * min(1, s * 3), "cm")

def tally(img, cam, x, y, n, col, op):
    for i in range(n):
        g, j = divmod(i, 5)
        gx = x + g * 44
        if j < 4: stroke(img, cam, [(gx + j * 8, y - 11), (gx + j * 8 + 1, y + 11)], 2.6, col, op)
        else: stroke(img, cam, [(gx - 4, y + 8), (gx + 30, y - 8)], 2.6, col, op)

# ---------------------------------------------------------------- Calendar
def calendar(img, cam, S):
    if S.cal_op <= 0.01: return
    x, y, w, h = S.cal_r; op = S.cal_op
    window(img, cam, S, x, y, w, h, "Calendar", op)
    ink, ink2 = th(S, "ink"), th(S, "ink2")
    text(img, cam, S.cal_head, x + 18, y + 50, 17, ink, "b", op, "lm")
    t0, t1 = 9.0, 13.0
    gy0, gy1 = y + 72, y + h - 14
    def Y(hh): return gy0 + (hh - t0) / (t1 - t0) * (gy1 - gy0)
    for hh in range(9, 14):
        yy = Y(hh)
        stroke(img, cam, [(x + 64, yy), (x + w - 12, yy)], 0.8, th(S, "border"), op)
        lab = ("%d AM" % hh) if hh < 12 else ("12 PM" if hh == 12 else "%d PM" % (hh - 12))
        text(img, cam, lab, x + 56, yy, 11, ink2, "m", op, "rm")
    U.CLIP.push(cam, x + 64, gy0 - 2, w - 70, gy1 - gy0 + 4)
    for ev in S.cal_events:
        a, b = ev["s"], ev["e"]; col = ev["c"]
        y0, y1 = Y(a), Y(b)
        if y1 - y0 < 3: continue
        ex = x + 70 + ev.get("dx", 0); ew = w - 88 - ev.get("dx", 0)
        rrect(img, cam, ex, y0 + 1, ew, y1 - y0 - 2, 6, mix(col, th(S, "win"), 0.72), op * ev.get("op", 1))
        rrect(img, cam, ex, y0 + 1, 4, y1 - y0 - 2, 2, col, op * ev.get("op", 1))
        text(img, cam, ev["t"], ex + 12, y0 + 13, 12.5, mix(col, ink, 0.55), "s", op * ev.get("op", 1), "lm", maxw=ew - 20)
        if y1 - y0 > 34 and ev.get("sub"):
            text(img, cam, ev["sub"], ex + 12, y0 + 30, 11, mix(col, ink2, 0.5), "m", op * ev.get("op", 1), "lm", maxw=ew - 20)
    if S.cal_now is not None:
        yy = Y(S.cal_now); circle(img, cam, x + 68, yy, 4.5, RED, op); stroke(img, cam, [(x + 68, yy), (x + w - 12, yy)], 1.6, RED, op)
    U.CLIP.pop()

# ---------------------------------------------------------------- notifications, dialogs, popovers
def notifications(img, cam, S):
    for nt in S.notes_list:
        k = nt["k"]
        if k <= 0.01: continue
        w, h = 330, 74
        x = U.DW - 14 - w + (1 - k) * (w + 30); y = nt["y"]
        U.shadow(img, cam, x, y, w, h, 14, 0.25 * k, 14, 6)
        rrect(img, cam, x, y, w, h, 14, mix(th(S, "win"), th(S, "chip"), 0.25), 0.97, th(S, "border"), 0.8, 0.8)
        rrect(img, cam, x + 12, y + 14, 34, 34, 9, nt["col"])
        if nt.get("glyph") == "cal": text(img, cam, nt.get("g", "21"), x + 29, y + 33, 14, (1, 1, 1), "b", 1, "cm")
        elif nt.get("glyph") == "chat": icon(img, cam, "chat", x + 29, y + 31, 20, (1, 1, 1))
        else: icon(img, cam, nt.get("glyph", "bell"), x + 29, y + 31, 18, (1, 1, 1))
        text(img, cam, nt["app"].upper(), x + 56, y + 16, 9.5, th(S, "ink2"), "s", 1, "lm", track=0.06)
        text(img, cam, nt.get("time", "now"), x + w - 14, y + 16, 10, th(S, "ink2"), "m", 1, "rm")
        text(img, cam, nt["title"], x + 56, y + 35, 13.5, th(S, "ink"), "s", 1, "lm", maxw=w - 70)
        text(img, cam, nt["body"], x + 56, y + 54, 12.5, th(S, "ink2"), "m", 1, "lm", maxw=w - 70)
        if nt.get("button"):
            bx = x + w - 84
            rrect(img, cam, bx, y + 26, 70, 26, 8, ACCENT if nt.get("btn_hl", 0) < 0.5 else mix(ACCENT, (0, 0, 0), 0.25))
            text(img, cam, nt["button"], bx + 35, y + 39, 12.5, (1, 1, 1), "s", 1, "cm")

def dialog(img, cam, S, d):
    k = d["k"]
    if k <= 0.01: return
    w, h = d.get("w", 340), d.get("h", 168)
    cx, cy = d["cx"], d["cy"]; s = 0.92 + 0.08 * k
    x, y = cx - w * s / 2, cy - h * s / 2; w, h = w * s, h * s
    U.shadow(img, cam, x, y, w, h, 14, 0.35 * k, 22, 12)
    rrect(img, cam, x, y, w, h, 14, th(S, "win"), k, th(S, "border"), 0.8, 0.8)
    if d.get("icon"):
        rrect(img, cam, x + w / 2 - 22, y + 16, 44, 44, 11, d.get("icon_col", H("ffffff")), k, th(S, "border"), 0.6)
        if d["icon"] == "cal":
            rrect(img, cam, x + w / 2 - 22, y + 16, 44, 13, 11, H("ef4444"), k); rrect(img, cam, x + w / 2 - 22, y + 23, 44, 6, 0, H("ef4444"), k)
            text(img, cam, d.get("g", "21"), x + w / 2, y + 44, 17, H("1d1d1f"), "b", k, "cm")
        else: icon(img, cam, d["icon"], x + w / 2, y + 38, 24, d.get("glyph_col", RED), k)
    ty = y + (76 if d.get("icon") else 30)
    text(img, cam, d["title"], x + w / 2, ty, 15, th(S, "ink"), "b", k, "cm", maxw=w - 30)
    for j, ln in enumerate(U.text_lines(d.get("body", ""), 12.5, w - 50, "m")[:3]):
        text(img, cam, ln, x + w / 2, ty + 24 + j * 18, 12.5, th(S, "ink2"), "m", k, "cm")
    bts = d.get("buttons", [])
    bw = (w - 30 - 10 * (len(bts) - 1)) / max(1, len(bts))
    for i, (lab, primary, dis) in enumerate(bts):
        bx = x + 15 + i * (bw + 10); by = y + h - 46
        col = ACCENT if primary else th(S, "chip")
        if dis: col = th(S, "chip")
        rrect(img, cam, bx, by, bw, 32, 8, col, k * (0.5 if dis else 1))
        text(img, cam, lab, bx + bw / 2, by + 16, 12.5, (1, 1, 1) if (primary and not dis) else th(S, "ink2") if dis else th(S, "ink"), "s", k, "cm")

def menu(img, cam, S, m):
    """a little popup menu (e.g. above the Leave button)"""
    k = m["k"]
    if k <= 0.01: return
    x, y, w = m["x"], m["y"], m.get("w", 250); rows = m["rows"]; h = 16 + len(rows) * 40
    U.shadow(img, cam, x, y - h, w, h, 10, 0.3 * k, 16, 8)
    rrect(img, cam, x, y - h, w, h, 10, th(S, "win"), k, th(S, "border"), 0.8, 0.8)
    for i, (lab, sub, dis, hl) in enumerate(rows):
        ry = y - h + 8 + i * 40
        if hl: rrect(img, cam, x + 6, ry, w - 12, 38, 7, mix(th(S, "chip"), ACCENT, 0.12), k)
        text(img, cam, lab, x + 16, ry + (13 if sub else 19), 13, th(S, "ink2") if dis else (RED if "End" in lab else th(S, "ink")), "s", k, "lm")
        if sub: text(img, cam, sub, x + 16, ry + 29, 10.5, RED if dis else th(S, "ink2"), "m", k, "lm")

def tooltip(img, cam, S, x, y, s, k):
    if k <= 0.01: return
    w = U.text_w(s, 12, 1.0, "s") + 22
    rrect(img, cam, x - w / 2, y - 30, w, 26, 7, H("2a2b30"), 0.96 * k)
    text(img, cam, s, x, y - 17, 12, (1, 1, 1), "s", k, "cm")

def dm_window(img, cam, S):
    """Chatter: her direct messages to Ted at the very end"""
    if S.dm_op <= 0.01: return
    x, y, w, h = S.dm_r; op = S.dm_op
    window(img, cam, S, x, y, w, h, "Chatter", op)
    circle(img, cam, x + 34, y + 58, 16, INITIAL_COL["Ted"], op)
    text(img, cam, "T", x + 34, y + 58, 14, (1, 1, 1), "s", op, "cm")
    circle(img, cam, x + 46, y + 70, 5.5, th(S, "win"), op); circle(img, cam, x + 46, y + 70, 4, mix(GREEN, H("9a9aa2"), S.ted_offline), op)
    text(img, cam, "Ted", x + 58, y + 51, 15, th(S, "ink"), "b", op, "lm")
    text(img, cam, S.ted_status, x + 58, y + 68, 11.5, RED if S.ted_offline > 0.5 else th(S, "ink2"), "m", op, "lm")
    stroke(img, cam, [(x, y + 86), (x + w, y + 86)], 0.8, th(S, "border"), op)
    U.CLIP.push(cam, x, y + 87, w, h - 87)
    chat(img, cam, S.dm, (x, y + 87, w, h - 87), op)
    U.CLIP.pop()
