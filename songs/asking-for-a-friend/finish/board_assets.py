"""finish_3: the in-world NOW SERVING board (company voice: Anton + Inter SemiBold on the board green, same family as the
ALL SYSTEMS board) as an atlas of split-flap states + a scrolling ticker strip, and the S004 portrait placeholders.
venv python: python finish/board_assets.py   -> ~/Documents/Original Music/Asking for a Friend 2/blender/textures/screens/ns/
Board 2.2 x 1.25 m at 800 px/m (1760 x 1000); ticker 2.2 m window over a 6.6 m loop (5280 x 224 px, strip 0.28 m)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design", "screens"))
import screens as S
from PIL import Image, ImageDraw, ImageFilter
OUT = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender/textures/screens/ns")
os.makedirs(OUT, exist_ok=True)
W, H = 1760, 1000
GREEN, INK, SOFT = S.B_GREEN, S.B_INK, S.B_SOFT
DARK = tuple(int(c * 0.55) for c in GREEN)


def base():
    im = Image.new("RGB", (W, H), GREEN); d = ImageDraw.Draw(im)
    for y in range(H):
        k = 1.0 + 0.06 * (1 - y / H); d.line([(0, y), (W, y)], fill=tuple(min(255, int(c * k)) for c in GREEN))
    M = 70
    d.text((M, M + S.CAP[S.ANTON] * 150), "NOW SERVING", font=S.F(S.ANTON, 150), fill=INK, anchor="ls")
    d.text((W - M, M + S.CAP[S.ANTON] * 150), "CUSTOMER", font=S.F(S.INTER_SB, 96), fill=SOFT, anchor="rs")
    d.rectangle([M, 262, W - M, 270], fill=SOFT)
    return im


def number(n, squash=1.0):
    layer = Image.new("RGBA", (W, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    f = S.F(S.ANTON, 600)
    d.text((W // 2, 320 + S.CAP[S.ANTON] * 600 / 2), str(n), font=f, fill=INK, anchor="ms")
    if squash < 1.0:
        h = max(6, int(640 * squash)); layer = layer.resize((W, h), Image.LANCZOS)
        full = Image.new("RGBA", (W, 640), (0, 0, 0, 0)); full.paste(layer, (0, (640 - h) // 2)); layer = full
    return layer


def state(n, squash):
    im = base(); im.paste(number(n, squash), (0, 290), number(n, squash))
    d = ImageDraw.Draw(im); cy = 290 + 320
    d.rectangle([60, cy - 4, W - 60, cy + 4], fill=DARK)               # the split-flap seam
    d.text((70, H - 50), "PLEASE TAKE A NUMBER", font=S.F(S.INTER_SB, 64), fill=SOFT, anchor="ls")
    return im


STATES = [(999, 1), (999, .7), (999, .3), (1000, .3), (1000, .7), (1000, 1), (1000, .7), (1000, .3), (1001, .3), (1001, .7), (1001, 1), (1001, 1)]
atlas = Image.new("RGB", (W * 4, H * 3))
for i, (n, sq) in enumerate(STATES):
    atlas.paste(state(n, sq), ((i % 4) * W, (i // 4) * H))             # row 0 = top
atlas.save(os.path.join(OUT, "ns_atlas.png"))
# ticker: company-voice strip
TW, TH = 5280, 224
tk = Image.new("RGB", (TW, TH), DARK); d = ImageDraw.Draw(tk)
f = S.F(S.INTER_SB, 110)
txt = "Estimated wait: 4 business quarters     ·     PRESS 1 TO SUBSCRIBE     ·     "
reps = TW // int(d.textlength(txt, font=f)) + 1
unit = d.textlength(txt, font=f)
# make the loop seamless: scale spacing so an integer count of units fills TW
n = max(1, round(TW / unit)); step = TW / n
for i in range(n):
    d.text((i * step + 40, TH // 2 + S.CAP[S.INTER_SB] * 110 / 2), txt, font=f, fill=INK, anchor="ls")
tk.save(os.path.join(OUT, "ns_ticker.png"))
import json
pre = "Estimated wait: 4 business quarters     \u00b7     "
x0 = 40 + d.textlength(pre, font=f); x1 = x0 + d.textlength("PRESS 1 TO SUBSCRIBE", font=f)
json.dump({"press_x0": x0, "press_x1": x1, "tw": TW, "wait_w": d.textlength("Estimated wait: 4 business quarters", font=f)}, open(os.path.join(OUT, "ns_ticker.json"), "w"))
print("ticker", x0, x1, unit)
# ---- EXIT sign (S131 outage): green lightbox, company voice
ex = Image.new("RGB", (800, 320), (8, 96, 58)); d = ImageDraw.Draw(ex)
d.rectangle([14, 14, 786, 306], outline=(236, 246, 238), width=10)
d.text((400, 160 + S.CAP[S.ANTON] * 210 / 2), "EXIT", font=S.F(S.ANTON, 210), fill=(240, 248, 240), anchor="ms")
ex.save(os.path.join(OUT, "exit_sign.png"))
# ---- portrait placeholders (S004): neutral, until finish_4's F30.png exists
PW, PH = 1200, 540
def portrait(name, caption, tint):
    im = Image.new("RGB", (PW, PH), (22, 20, 28)); d = ImageDraw.Draw(im)
    for y in range(PH):
        k = 1 - 0.5 * (y / PH); d.line([(0, y), (PW, y)], fill=tuple(int(c * k) for c in tint))
    cx = 900
    d.ellipse([cx - 95, 90, cx + 95, 290], fill=(30, 26, 40))
    d.pieslice([cx - 230, 270, cx + 230, 760], 180, 360, fill=(30, 26, 40))
    d.rectangle([60, 150, 60 + 8, 390], fill=(236, 230, 214))
    d.text((100, 210), caption.split("\n")[0], font=S.F(S.ANTON, 92), fill=(236, 230, 214), anchor="ls")
    d.text((100, 315), caption.split("\n")[1] if "\n" in caption else "", font=S.F(S.ANTON, 92), fill=(236, 230, 214), anchor="ls")
    d.text((100, 400), "est. since always", font=S.F(S.INTER_SB, 40), fill=(190, 184, 170), anchor="ls")
    im.save(os.path.join(OUT, f"ph_portrait_{name}.png"))
portrait("visionary", "THE\nVISIONARY", (70, 50, 120))
portrait("wellness", "THE WELLNESS\nVISIONARY", (50, 80, 80))
portrait("finance", "THE FINTECH\nPIONEER", (60, 70, 100))
print("ok", OUT)
