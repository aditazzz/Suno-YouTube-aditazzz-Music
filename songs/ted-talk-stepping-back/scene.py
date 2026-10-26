"""TED Talk, stepping back: one continuous zoom out.

I asked Ted if the file was ready. He said "so — stepping back," and the camera does: from the eight people at
standup, out through the office, the city (the streets are named after his buzzwords), the countryside, the clouds,
the Earth, the solar system, the stars, the Milky Way, all the way to the edge of the observable universe. The
question stays pinned in the middle the whole time, unanswered. At "Ted. This is a standup." the zoom snaps all the
way back into the room; in the final chorus it goes out again, faster, and in the outro Ted takes it offline:
his dot drifts out past the edge of everything we can see.
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc
from view import View
import citymap as CM
import cosmos as CO
import office as OF

TM = C.Timing(HERE)
TAIL = 3.0
DUR = TM.duration + TAIL
F32 = np.float32
lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)

FONT = lambda n: os.path.join(C.FONTS, n)
F_SANS = FONT("Inter-SemiBold.otf"); F_SANSM = FONT("Inter-Medium.otf"); F_BOLD = FONT("InterDisplay-Bold.otf")
F_BLACK = FONT("InterDisplay-Black.otf"); F_MONO = FONT("JBMono-700.ttf"); F_SERIF = FONT("EBGaramond-SemiBold.ttf")
F_ITAL = FONT("EBGaramond-MediumItalic.ttf"); F_TAB = FONT("Anton-Regular.ttf")

INK = hexc('1d1c1a'); INK2 = hexc('4a4741'); MUTE = hexc('8b877f'); WHITE = hexc('ffffff'); CREAM = hexc('fbf6ec')
RED = hexc('d93a2b'); BLUE = hexc('2f6fe0'); BLUE_D = hexc('2448a8'); WATER_T = hexc('3f7fb3')

# ---------------------------------------------------------------- key times
T_V1 = lt("He doesn't answer"); T_FOUR = lt("about four minutes"); T_ASK = lt("I asked him")
T_SO = wt("He said, so", "so"); T_STEP = wt("He said, so", "stepping"); T_DIM = lt("Somebody dim"); T_SIT = lt("everybody sit")
T_SLIDES = wt("Eighteen minutes", "slides,", 0); T_POINT = wt("Eighteen minutes", "point.", 0)
T_PAUSE = wt("pause he thinks", "pause", 0); T_PAUSE_E = TM.lines[[i for i, L in enumerate(TM.lines) if L['text'].startswith("There's a pause")][0]]['e']
T_CIRCLE = lt("circle back", 0); T_CIRCLE_E = lt("right after the part", 0)
T_V2 = TM.section("V2")["s"]; T_SOw = wt("He starts every", "so."); T_RIGHT = wt("He ends every", "right?")
T_REALQ = wt("He says, the real", "real"); T_JOURNEY = wt("He said journey", "journey."); T_UNLOCK = wt("He said journey", "unlock.")
T_STORY = wt("let me tell you", "story,"); T_CAL = lt("and I watched my calendar"); T_GIVEUP = lt("give up")
T_SLIDES2 = wt("Eighteen minutes", "slides,", 1); T_POINT2 = wt("Eighteen minutes", "point.", 1)
T_PAUSE2 = wt("pause he thinks", "pause", 1); T_PAUSE2_E = TM.lines[[i for i, L in enumerate(TM.lines) if L['text'].startswith("There's a pause")][1]]['e']
T_CIRCLE2 = lt("circle back", 1); T_CIRCLE2_E = lt("right after the part", 1)
T_STOP = TM.section("BRIDGE")["s"]; T_TED = lt("Ted."); T_STANDUP = lt("This is a standup"); T_FIFTEEN = lt("It is fifteen")
T_EIGHT = lt("for eight people"); T_SIX = lt("You have used six"); T_HARD = lt("Dana had a hard stop"); T_HAS = lt("Dana has had")
T_TWO = lt("for two years"); T_GHOST = lt("Dana is a ghost"); T_DIDTHAT = lt("You did that")
T_FINAL = TM.section("FINAL")["s"]; T_NOSCHED = lt("Nobody scheduled"); T_NOEND = lt("Nobody can end"); T_NOQA = lt("There's no Q")
T_ANYWAY = lt("Anyway"); T_HESAYS = lt("He says."); T_HAVING = lt("Having taken"); T_PLACE = lt("Into a place"); T_REACH = lt("none of us")
T_END = 157.2
T_PILL = T_V2 + 0.3
TT = [L['s'] for L in TM.lines if L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")]

# ---------------------------------------------------------------- the zoom: z = log10(16:9 frame width in metres)
ZK = [(0.0, 1.34), (6.1, 1.06), (20.0, 1.00), (T_SO, 0.98), (T_STEP, 1.0), (T_DIM, 1.16), (26.1, 1.58), (28.64, 1.98),
      (32.03, 2.48), (T_PAUSE, 2.93), (T_PAUSE_E - 0.4, 2.93), (40.4, 3.15), (T_CIRCLE, 3.33), (45.84, 3.84), (48.88, 4.2),
      (T_V2, 4.6), (56.88, 5.03), (62.64, 5.52), (69.2, 6.02), (T_CAL, 6.58), (76.72, 7.25), (80.48, 8.0), (83.04, 8.6),
      (T_PAUSE2, 9.08), (T_PAUSE2_E - 0.3, 9.08), (T_CIRCLE2, 11.3), (T_CIRCLE2_E, 11.76), (98.32, 12.45), (T_TED, 13.05),
      (T_STANDUP, 13.08), (T_STANDUP + 1.05, 1.16), (T_FIFTEEN, 1.13), (T_GHOST, 1.09), (T_DIDTHAT, 1.03), (T_FINAL, 0.95),
      (TT[4], 0.97), (T_NOSCHED, 1.75), (T_NOEND, 3.1), (T_NOQA, 6.2), (129.92, 8.3), (131.44, 10.2), (TT[5], 15.6),
      (TT[6], 18.6), (T_ANYWAY, 21.2), (T_HESAYS, 22.5), (T_PLACE, 24.0), (150.5, 25.0), (T_REACH, 26.1), (155.6, 27.05), (DUR + 1, 27.25)]
_ZT = np.array([k[0] for k in ZK]); _ZV = np.array([k[1] for k in ZK])
def _pchip_slopes(x, y):
    h = np.diff(x); d = np.diff(y) / h; m = np.zeros_like(y)
    for i in range(1, len(y) - 1):
        if d[i - 1] * d[i] <= 0: m[i] = 0
        else:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0] = d[0] if d[0] * d[0] > 0 else 0; m[-1] = d[-1] if d[-1] * d[-1] > 0 else 0
    if d[0] == 0: m[0] = 0
    if d[-1] == 0: m[-1] = 0
    return m
_ZM = _pchip_slopes(_ZT, _ZV)
def Z(t):
    t = float(np.clip(t, _ZT[0], _ZT[-1])); i = int(np.clip(np.searchsorted(_ZT, t) - 1, 0, len(_ZT) - 2))
    h = _ZT[i + 1] - _ZT[i]; s = (t - _ZT[i]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
    return float(h00 * _ZV[i] + h10 * h * _ZM[i] + h01 * _ZV[i + 1] + h11 * h * _ZM[i + 1])

def ROT(t):
    """'He'll circle back': the map turns a full circle"""
    return 2 * math.pi * ease_io((t - T_CIRCLE) / (T_CIRCLE_E - T_CIRCLE - 0.3))

def traffic_t(t):
    """the city's clock: it stops during the pause he thinks is powerful"""
    a, b = T_PAUSE, T_PAUSE_E - 0.4
    if t < a: return t
    if t < b: return a
    return t - (b - a)

def years(t):
    """the planets' clock: one orbit while he circles back"""
    return ease_io((t - T_CIRCLE2) / (T_CIRCLE2_E - T_CIRCLE2))

def days(t):
    """the Earth's clock: 'I watched my calendar give up' — days fly past, then it stops"""
    k = clamp((t - T_CAL) / (T_GIVEUP + 0.4 - T_CAL)); return 5.0 * (k ** 2.2)

def dim(t):
    """office lights: down for the keynote, on again at the hard stop"""
    a = sstep(T_DIM, T_DIM + 1.6, t) * (1 - sstep(T_STANDUP + 0.6, T_STANDUP + 0.75, t))
    if T_STANDUP + 0.6 <= t < T_STANDUP + 1.2: a = max(a, 0.5 * (math.sin((t - T_STANDUP) * 60) > 0.2))
    return a

def story(t):
    return dict(t_traffic=traffic_t(t), sit=sstep(T_SIT, T_SIT + 0.8, t) * (1 - sstep(T_STANDUP, T_STANDUP + 0.6, t)),
                phones=sstep(T_FOUR + 0.3, T_FOUR + 1.4, t) * (1 - sstep(T_ASK - 0.6, T_ASK, t)),
                ted_talk=1.0, dana_gone=sstep(T_HARD + 0.2, T_HAS + 0.6, t) if t < T_FINAL else 1.0,
                ghost=sstep(T_GHOST - 0.1, T_GHOST + 1.0, t) if t < T_FINAL else 1.0)

# ---------------------------------------------------------------- where things are
def me_world():
    return OF.person_pos([i for i, p in enumerate(OF.PEOPLE) if p[0] == "Me"][0]) + np.array([0.0, -0.02])
def ted_world(t=0.0):
    return OF.person_pos(0, t)

def map_center(W, H):
    """the zoom's focal point on the map: a little south of the middle of the circle, so the group sits above the lyrics"""
    return (0.0, 0.46) if W > H else (0.0, 0.90)

def space_center(z):
    """2-D space view centre: the Earth at first; the Sun once the planets are in frame; for a moment, the middle of
    the Local Group (so the Milky Way and Andromeda share the frame)"""
    if z < 15:
        E0 = CO.planet_positions(0.0)["Earth"]
        return E0 * (1 - sstep(11.25, 11.75, z))
    return ANDROMEDA * 0.5 * float(sstep(21.9, 22.6, z) * sstep(24.2, 23.3, z))

# ---------------------------------------------------------------- the frame
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W
    z = Z(t); th = ROT(t); st = story(t)
    mpp = 10 ** z / 1920.0
    out = None; k_space = float(sstep(6.15, 6.55, z))
    if k_space < 1:
        view = View(W, H, *map_center(W, H), mpp, th)
        cvm = CM.draw_map(view, t, z, st)
        img_map = cvm.astype(F32) / 255.0
        lights(img_map, view, t, z)
        if z > 5.15:
            col, a = CM.clouds(view, cloud_cover(z))
            img_map = img_map * (1 - a[..., None]) + col * a[..., None]
        out = img_map
    if k_space > 0:
        img_sp = render_space(t, z, W, H, fi)
        out = img_sp if out is None else out * (1 - k_space) + img_sp * k_space
    overlays(out, t, z, W, H, th, st)
    return finish(out, t, fi)

def cloud_cover(z):
    return float(sstep(5.15, 6.2, z)) * 0.98

def lights(img, view, t, z):
    """the keynote lighting: the office goes dark except a spot on Ted"""
    d = dim(t)
    if d <= 0.01 or z > 3.4: return
    H, W = img.shape[:2]
    x0, y0, x1, y1 = OF.BLD
    P = view.to_px(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]))
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.round(P * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
    s = view.to_px(ted_world(t)[None])[0]; rs = 0.95 / view.mpp
    yy, xx = np.ogrid[:H, :W]
    spot = np.exp(-(((xx - s[0]) ** 2 + (yy - s[1]) ** 2) / (rs * rs)) ** 2)
    k = (m.astype(F32) / 255.0) * (1 - spot) * d * 0.72 * float(sstep(3.4, 2.6, z))
    img *= (1 - k)[..., None]
    img += (spot * d * 0.06 * float(sstep(3.4, 2.6, z)))[..., None] * np.array([1.0, 0.9, 0.7], F32)

def render_space(t, z, W, H, fi):
    hdr = np.zeros((H, W, 3), F32)
    if z < 9.9:
        cover = cloud_cover(z) if z < 7.4 else None
        e_img, e_cov, cam = CO.render_earth(z, t, W, H, days=days(t), cloud_cover=cover)
        hdr += e_img * float(sstep(9.9, 9.5, z))
    if z > 8.3:
        space2d(hdr, t, z, W, H)
    expo = 1.0 + 0.9 * float(sstep(7.3, 6.2, z))           # the morning sun is low: lift the close-up Earth
    return CO.develop_f(hdr, exposure=expo, bloom_k=0.05, vignette=0.16)

def space2d(hdr, t, z, W, H):
    mpp = 10 ** z / 1920.0
    c = space_center(z)
    v = View(W, H, c[0], c[1], mpp, 0.0)
    yr = years(t); P = CO.planet_positions(yr)
    # star backdrop that is part of the world beyond the solar system
    if z > 13.8:
        CO.draw_stars_world(hdr, v, gain=float(sstep(13.8, 14.8, z)) * float(sstep(21.4, 20.4, z)))
    # orbits + planets + the Sun
    k_sol = float(sstep(9.6, 10.4, z)) * float(sstep(15.2, 14.0, z))
    if k_sol > 0:
        sun = v.to_px(np.zeros((1, 2)))[0]
        for name, a, per, ang, rad, col in CO.PLANETS:
            CO.ring(hdr, v, (0, 0), a * CO.AU, (0.55, 0.62, 0.75), 0.30 * k_sol, 1.4)
        for name, a, per, ang, rad, col in CO.PLANETS:
            p = v.to_px(P[name][None])[0]
            CO.dot(hdr, p[0], p[1], max(2.6, rad / mpp), col, 1.4 * k_sol, glow=0.25 * k_sol)
        CO.sun_glow(hdr, sun[0], sun[1], k=k_sol * float(sstep(15.5, 13.0, z)) + 0.0, rpx=max(1.6, 6.96e8 / mpp))
    if z > 13.0:
        sun = v.to_px(np.zeros((1, 2)))[0]
        CO.sun_glow(hdr, sun[0], sun[1], k=float(sstep(13.0, 14.0, z)) * float(sstep(20.5, 18.5, z)) * 0.35, rpx=1.6, spikes=False)
    # the Moon's orbit around the Earth
    k_moon = float(sstep(8.3, 8.8, z)) * float(sstep(10.6, 10.0, z))
    if k_moon > 0:
        CO.ring(hdr, v, P["Earth"], 3.844e8, (0.55, 0.62, 0.75), 0.30 * k_moon, 1.4)
    # the Milky Way
    if z > 19.6:
        k_g = float(sstep(19.6, 20.6, z))
        gc = np.array([-0.82, 0.48]) * 26000 * CO.LY
        CO.blit_galaxy(hdr, v, gc, CO.GAL_HALF, CO.galaxy("mw"), gain=0.9 * k_g * float(sstep(25.2, 24.2, z)), incl=1.0, pa=0.4)
    if z > 21.5:
        k_lg = float(sstep(21.5, 22.4, z)) * float(sstep(25.6, 24.6, z))
        CO.blit_galaxy(hdr, v, ANDROMEDA, 110000 * CO.LY, CO.galaxy("m31"), gain=1.1 * k_lg, incl=0.32, pa=-0.6)
        CO.blit_galaxy(hdr, v, TRIANGULUM, 30000 * CO.LY, CO.galaxy("m31"), gain=0.8 * k_lg, incl=0.8, pa=1.1)
        for (p, s_) in DWARFS: CO.blit_galaxy(hdr, v, p, s_, CO.galaxy("m31"), gain=0.5 * k_lg, incl=0.7, pa=0.3)
    if z > 23.0:
        CO.cosmic_web(hdr, v, gain=float(sstep(23.0, 23.9, z)))
    if z > 26.0:
        CO.universe_edge(hdr, v, gain=float(sstep(26.0, 26.5, z)))

ANDROMEDA = np.array([0.92, -0.39]) * 2.54e6 * CO.LY
TRIANGULUM = np.array([0.86, -0.20]) * 2.73e6 * CO.LY + np.array([2e5, 3e5]) * CO.LY
DWARFS = [(np.array([0.9, 0.5]) * 1.6e5 * CO.LY, 9000 * CO.LY), (np.array([0.8, 0.75]) * 2.0e5 * CO.LY, 5000 * CO.LY),
          (np.array([-0.4, 0.95]) * 7e5 * CO.LY, 4000 * CO.LY), (np.array([0.2, -0.9]) * 1.1e6 * CO.LY, 3500 * CO.LY)]

# ---------------------------------------------------------------- overlays (labels, pins, HUD, lyrics) — in overlay.py
import overlay as OV   # noqa: E402
class _Self:                 # overlay.py reads this scene's names through S (the module may not be in sys.modules)
    def __getattr__(self, k): return globals()[k]
OV.S = _Self()
overlays, finish = OV.overlays, OV.finish

def ted_offset(t, z, W, H, sc):
    """Ted's screen offset from the pin. In the outro his distance grows faster than the zoom: he leaves everything."""
    base = np.array([26.0, -6.0]) * sc
    if t < T_HAVING - 0.2: return base, 1.0
    mpp = lambda tt: 10 ** Z(tt) / 1920.0
    t0, t1 = T_HAVING - 0.2, 156.0
    r0 = math.log10(math.hypot(*base) * mpp(t0)); r1 = math.log10(1.10 * CO.R_OBS)
    k = ease_io((t - t0) / (t1 - t0)); r = 10 ** (r0 + (r1 - r0) * k) if t < t1 else 1.10 * CO.R_OBS * (1 + (t - t1) * 0.15)
    d = r / mpp(t)
    ang = math.radians(-32 + 10 * math.sin(k * 3.0))
    fade = 1 - sstep(156.0, 156.9, t)
    return np.array([math.cos(ang), math.sin(ang)]) * d, fade
