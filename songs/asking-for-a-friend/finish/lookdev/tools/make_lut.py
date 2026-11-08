"""AFF look v1: ONE display-referred look for every shot, 3D and 2D (LOOK_BIBLE.md section 2).
Writes finish/lookdev/AFF_look_v1.cube (33^3, Rec.709/sRGB in -> out). Apply with
  ffmpeg -i IN -vf "lut3d=file=AFF_look_v1.cube:interp=tetrahedral,vignette=angle=0.30" OUT, then short/tools/finish_still.py (grain)
(the master and the 9:16 reframe apply it in their ffmpeg chain). Pure function of the input pixel, so it is identical on every frame.

What it does, in order (display sRGB in [0,1]):
 1. Murk out: low-value olive/brown/green (hue 40-170 deg, V < ~0.55) loses 60% saturation and leans 45% to cool slate-teal.
    Bright saturated greens (the board, NOW SERVING, status greens = "the system holding") are protected by a V/S weight.
 2. Orange (Claude, 12-38 deg) +6% saturation: the only warm hero colour stays the most saturated thing in frame.
 3. Ultraviolet (255-300 deg, the founder) a touch deeper (V -4%), so his world reads violet, not lavender pastel.
 4. Split tone: shadows toward cool slate, highlights toward warm practical (small: +-1.5%).
 5. Tone: black point 0 -> 0.010 (no crushed detail: her Nov 5 note), mid lift (gamma 0.93) + mid-contrast S about 0.30 (+9% separation),
    shoulder from 0.78 so 1.0 -> 0.935 (highlight control: clipped whites and paper-white 2D cards stop reading as
    blank paper; the robot keeps a visible top value).
 6. Global saturation 0.97.
"""
import numpy as np, colorsys, os, sys

def look(rgb):
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hd = h * 360.0

    def band(x, a, b_, soft=12.0):
        # smooth 0..1 membership of hue x in [a, b_]
        lo = np.clip((x - (a - soft)) / soft, 0, 1)
        hi = np.clip(((b_ + soft) - x) / soft, 0, 1)
        return float(min(lo, hi))

    # 1. murk out (olive/brown/green, darker and mid-sat only)
    w_murk = band(hd, 40, 170, 15) * float(np.clip((0.62 - v) / 0.30, 0, 1)) * float(np.clip(1.15 - s, 0, 1))
    if w_murk > 0:
        s *= 1 - 0.60 * w_murk
        # lean hue toward teal-slate 190 deg
        hd = hd + (195 - hd) * 0.45 * w_murk
    # 2. Claude orange
    w_or = band(hd, 12, 38, 8)
    s = min(1.0, s * (1 + 0.06 * w_or))
    # 3. ultraviolet
    w_uv = band(hd, 255, 300, 15)
    v *= 1 - 0.04 * w_uv
    r, g, b = colorsys.hsv_to_rgb((hd % 360) / 360.0, s, v)

    # 4. split tone by luma
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sh = float(np.clip((0.30 - y) / 0.30, 0, 1)); hi = float(np.clip((y - 0.55) / 0.45, 0, 1))
    r += -0.012 * sh + 0.012 * hi
    g += 0.000 * sh + 0.004 * hi
    b += 0.016 * sh - 0.015 * hi

    # 5. tone curve per channel (keeps hue roughly; small moves)
    def tone(x):
        x = min(max(x, 0.0), 1.0)
        # mid-contrast S around pivot p
        p, k = 0.30, 0.09
        x = x ** 0.93                      # mid lift: keeps the median where it was after the S and the vignette
        x = x + k * (x - p) * (1 - abs(x - p) / max(p, 1 - p)) * 1.0
        # black point lift
        x = 0.010 + x * (1 - 0.010)
        # shoulder: above t compress so 1.0 -> top
        t, top = 0.78, 0.935
        if x > t:
            u = (x - t) / (1.0 - t)
            x = t + (top - t) * (1 - (1 - u) ** 1.6)
        return x
    r, g, b = tone(r), tone(g), tone(b)

    # 6. global saturation
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    r, g, b = [y + 0.97 * (c - y) for c in (r, g, b)]
    return [min(max(c, 0.0), 1.0) for c in (r, g, b)]

def main(out):
    N = 33
    lines = ["TITLE \"AFF_look_v1\"", "# Asking for a Friend, one look for 3D and 2D. finish/lookdev/tools/make_lut.py",
             f"LUT_3D_SIZE {N}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    for bi in range(N):
        for gi in range(N):
            for ri in range(N):
                o = look([ri / (N - 1), gi / (N - 1), bi / (N - 1)])
                lines.append("%.6f %.6f %.6f" % tuple(o))
    # .cube order: red fastest
    open(out, "w").write("\n".join(lines) + "\n")
    print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "AFF_look_v1.cube"))
