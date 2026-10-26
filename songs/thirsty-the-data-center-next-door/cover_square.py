"""The square album cover (3000x3000), rendered natively from the video's world: dusk, her profile at the river
railing (the video's final close-up), her face against the lit wall of the windowless facility across the water,
its steam rising into the last light. Text, when on, is exactly the release title and the artist name.
  python3 cover_square.py [size] [--notext] [--out file.jpg]
"""
import os, sys, argparse, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import scene as SC
import ys_eng as E, ys_world as WD, ys_type as TY, ys_her as HER
from ys_eng import hexc, F32, sample, fbm_tex

TITLE, SUBTITLE, ARTIST = "THIRSTY", "(The Data Center Next Door)", "aditazzz"   # release: "Thirsty (The Data Center Next Door)"

ap = argparse.ArgumentParser()
ap.add_argument("size", nargs="?", type=int, default=900)
ap.add_argument("--notext", action="store_true"); ap.add_argument("--both", action="store_true"); ap.add_argument("--out", default=None)
ap.add_argument("--dusk", type=float, default=0.25); ap.add_argument("--water", type=float, default=-2.9)
ap.add_argument("--bold", type=float, default=1.7); ap.add_argument("--cloud", type=float, default=0.25); ap.add_argument("--backlit", type=float, default=0.06); ap.add_argument("--rim", type=float, default=0.7)
ap.add_argument("--eye", default="-360,4.0,-58"); ap.add_argument("--tgt", default="-700,22,215"); ap.add_argument("--fov", type=float, default=40)
ap.add_argument("--her", default="0.27,0.355,0.245")     # crown x, y (frame fractions), head height (fraction of H)
ap.add_argument("--rail", default="0.20")                 # railing slope (down to the right)
ap.add_argument("--drip", type=float, default=0.62)
a = ap.parse_args()
N = a.size; W = H = N; t = 93.0
f3 = lambda s: tuple(float(v) for v in s.split(","))

# ---------------------------------------------------------------- the world
cam = E.Cam(f3(a.eye), f3(a.tgt), fov=a.fov, W=W, H=H, t=t)
S = SC.dusk_state(t, dusk=a.dusk, sun_az=-0.85, tree_clear=40, glow=1.0)
S['cloud'] = a.cloud
S.update(mono_lights=1.0, plumes=1.0, town_lights=0.9, water=a.water, dry=0.55, breath=0.75, fac_trees=0.25)
img = np.maximum(SC.valley(cam, S, t), 0)
img = cv2.GaussianBlur(img, (0, 0), 1.6 * E.pxs(W, H))          # a touch of depth of field behind her

# ---------------------------------------------------------------- her at the railing, in profile (the video's final close-up),
# her face against the facility's lit wall; rim-lit from the right by it
hx, hy, hh = f3(a.her); cx, cy, h = hx * W, hy * H, hh * H
HER.draw(img, 'profile', cx, cy, h, light_dir=(1.0, -0.40), rim=hexc('cfe2ee') * 0.85 + hexc('ffd2a0') * 0.30, backlit=a.backlit, rim_amt=a.rim, fine=(int(2.2 * h) if h > 300 else 0),
         t=t, seed=21, wind=0.25)

# the railing: a concrete parapet across her chest, sloping down to the right; top lit by the sky and the facility
slope = float(a.rail)
y_at = lambda x: cy + 1.95 * h + (x - (cx + 0.6 * h)) * slope
yy, xx = np.mgrid[0:H, 0:W].astype(F32)
top = y_at(xx); thick = 0.016 * H
cap = E.ss_arr(top - 1.5, top + 1.5, yy) * (1 - E.ss_arr(top + thick - 1.5, top + thick + 1.5, yy))
face = E.ss_arr(top + thick - 1.5, top + thick + 1.5, yy)
grain = sample(fbm_tex(256, 1.3, 77), xx * 0.35, yy * 0.35, 1.0)
lit_x = np.clip(xx / W, 0, 1)
cap_col =hexc('c99a8c')[None, None] * (0.020 + 0.010 * (1 - lit_x))[..., None] + hexc('cfe2ee')[None, None] * (0.010 + 0.028 * lit_x)[..., None]
cap_col = cap_col * (0.75 + 0.5 * grain)[..., None]
face_col = hexc('1d2230') * (0.010 + 0.006 * grain)[..., None] * (1.0 - 0.5 * np.clip((yy - top) / (0.25 * H), 0, 1))[..., None]
img = img * (1 - cap[..., None]) + cap_col * cap[..., None]
img = img * (1 - face[..., None]) + face_col * face[..., None]

base_img = img
def finish(with_text):
    img = base_img.copy()
    # ------------------------------------------------------------ title (linear, so it takes the grade and the grain)
    if with_text:
        probe, _, _ = TY.title_mask(W, H, 300, 1.0, a.bold)
        ts = (0.86 * W) / probe.shape[1]
        TITLE_Y = 0.040
        TY.title(img, t, 0.5, TITLE_Y, size=300, op=1.0, drip=a.drip, ts=ts, center=True, bold=a.bold, drip_w=300 * ts / 180)
    out = np.clip(E.develop(img, 0), 0, 1)
    if not with_text: return out
    # ------------------------------------------------------------ subtitle + artist (display space)
    tm, _, (xS, base) = TY.title_mask(W, H, 300, ts, a.bold)
    X0 = 0.5 * W - tm.shape[1] / 2
    # right-aligned under the title, slid so the S drip falls through a gap between two words, not across a letter
    fs = int(0.050 * H); m, ox, oy = TY.glyphs(SUBTITLE, TY.F_GHOST, fs)
    ink = m.max(0) > 0.08; runs, r0 = [], None
    for i, v in enumerate(ink):
        if not v and r0 is None: r0 = i
        if v and r0 is not None:
            if i - r0 > fs * 0.12: runs.append((r0 + i) / 2)
            r0 = None
    cols = np.nonzero(ink)[0]
    Xs = X0 + tm.shape[1] - 0.02 * W - cols[-1]                  # mask x so its ink ends under the title's right edge
    drip_x = X0 + xS
    g = min(runs, key=lambda gx: abs(Xs + gx - drip_x)); Xs += drip_x - (Xs + g)
    ys = TITLE_Y * H + base + 0.022 * H - oy
    sh = cv2.GaussianBlur(m, (0, 0), max(1.5, fs / 14))
    TY.blit(out, sh, Xs + fs * 0.04, ys + fs * 0.06, np.zeros(3, F32), 0.7)
    TY.blit(out, m, Xs, ys, TY.IVORY_D * 0.96, 1.0)
    fa = int(0.034 * H); m, ox, oy = TY.glyphs(ARTIST, TY.F_MONO, fa)
    sh = cv2.GaussianBlur(m, (0, 0), max(1.5, fa / 14))
    TY.blit(out, sh, 0.055 * W - ox + fa * 0.04, 0.915 * H - oy + fa * 0.06, np.zeros(3, F32), 0.5)
    TY.blit(out, m, 0.055 * W - ox, 0.915 * H - oy, TY.PINK_D, 1.0)
    return out

def save(out, dst):
    cv2.imwrite(dst, cv2.cvtColor((out * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print("wrote", dst, out.shape, flush=True)

dst = a.out or os.path.join(HERE, "build", "dev", "cover.jpg")
if a.both:
    save(finish(True), dst); save(finish(False), dst.replace(".jpg", " (no text).jpg"))
else:
    save(finish(not a.notext), dst)
