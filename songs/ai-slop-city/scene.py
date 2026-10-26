"""AI Slop? YOU're Absolutely Right — The City.

A day lost to the feed. At 2 a.m. a woman on a plaza bench likes one post. She never looks up while the day
time-lapses past; her shadow outgrows physics with every like, climbs the Feed Tower, and every window inside it turns
into a screen. The city's power dies when her battery does. When she locks the phone, the towers go dark one by one,
the sun comes up, her shadow is just a shadow again — and she opens her notebook and writes. The shadow waves.
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from studio import core as C
from cty_eng import Cam, F32, hexc, mix, clamp, sstep, to_8, to_f, paper, vig
import cty_city as CC
import cty_her as HER
from cty_her import Pose
import cty_plaza as PZ
import cty_phone as PH
import cty_phoneshot as PS
import cty_fx as FX
import cty_type as TY
import cty_slop as SL

TM = C.Timing(HERE)
TM.set_stamp_word('slop')
DUR = TM.duration + 3.0
T_BEHIND = TM.line_t("right behind you")
T_END = T_BEHIND + 2.8
C.THEME.update(disp=os.path.join(C.FONTS, 'InterDisplay-Bold.otf'), body=TY.F_LYR, red=hexc('d9483b'))


def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease3(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)


def curve(keys, t):
    """Piecewise smooth interpolation through (t, v) keys."""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]


def lin(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / max(1e-6, t1 - t0)
    return keys[-1][1]


# ------------------------------------------------------------------ the story clock (hours; > 24 = the next morning)
CLOCK = [(0.0, 1.966), (11.84, 2.0), (14.24, 2.04), (19.04, 2.45), (23.68, 3.3), (28.4, 4.9), (30.56, 5.72), (32.4, 6.08),
         (36.0, 6.55), (40.56, 7.1), (49.9, 9.2), (58.5, 12.4), (69.5, 13.2), (83.0, 15.0), (97.7, 16.6), (107.8, 17.6),
         (118.0, 18.55), (127.5, 19.25), (137.3, 19.62), (147.4, 19.95), (157.0, 20.6), (167.2, 23.9), (167.9, 23.97),
         (177.4, 24.0), (184.3, 24.06), (186.3, 26.5), (189.2, 29.4), (191.3, 30.2), (194.2, 30.42), (199.7, 30.55),
         (209.2, 30.7), (221.8, 30.85)]


def hour(t): return lin(CLOCK, t)


def clock_str(h):
    h = h % 24
    hh = int(h); mm = int((h - hh) * 60)
    h12 = hh % 12 or 12
    return f'{h12}:{mm:02d}'


def battery(t):
    h = hour(t)
    return float(np.clip(64 - (h - 2.0) / (23.97 - 2.0) * 63, 1, 100)) if h < 24.5 else 1.0


T_BLACK = TM.line_t("You called it artificial")          # the city's power dies with her battery
T_NEON = TM.line_t("You're absolutely right", 3)          # final chorus: the city reboots in neon
T_STOP = TM.word_t("you're the one who gets to stop", "stop")
T_LOCK = TM.line_t("But you're the one who gets to stop") + 0.9
T_LOOK = TM.line_t("Turn around and look inside")
T_SUN = TM.line_t("I'm the shadow you've been casting", 2)
T_OUTSIDE = TM.line_t("I was never on the outside")
T_HELPS = TM.line_t("I hope this helps.")
T_GOLD = TM.line_t("You handed me your gold, too")
T_PAGES = TM.line_t("Every song you never wrote")
T_WRITE = T_OUTSIDE + 1.0


def story(t):
    """Everything about the world that follows the song: light, power, how much of the city is slop, her shadow."""
    S = dict(t=t, hour=hour(t))
    S['power'] = 1.0 - sstep(T_BLACK - 0.05, T_BLACK + 0.6, t) * (1 - sstep(T_NEON - 0.15, T_NEON, t))
    S['blackout'] = sstep(T_BLACK, T_BLACK + 1.2, t) * (1 - sstep(T_NEON - 0.1, T_NEON + 0.05, t))
    S['neon'] = sstep(T_NEON - 0.1, T_NEON + 0.05, t) * (1 - sstep(T_LOCK + 1.2, T_LOCK + 4.2, t))
    S['slop_city'] = curve([(40.0, 0.0), (60.0, 0.12), (97.0, 0.32), (110.0, 0.55), (126.0, 0.9), (167.0, 0.92),
                            (167.9, 0.92), (168.5, 0.0), (T_NEON - 0.1, 0.0), (T_NEON + 0.2, 1.0), (T_LOCK + 4.4, 1.0), (T_LOCK + 4.6, 0.0)], t)
    S['warm'] = sstep(T_SUN - 1.5, T_SUN + 2.0, t)
    S['drain'] = sstep(T_GOLD, T_GOLD + 3.0, t) * (1 - sstep(T_BLACK - 1.0, T_BLACK, t))
    if t > T_LOCK:
        S['t1_kill_rows'] = 42 * ease((t - T_LOCK - 0.25) / 1.1)
        S['off_wave'] = 900 * ease((t - T_LOCK - 1.1) / 3.4) ** 1.4
    S['cloud_drift'] = curve([(0, 0), (23.0, 4), (60.0, 60), (130.0, 150), (167.0, 190), (184.0, 200), (221.8, 240)], t)
    # her shadow: honest under the lamp; at dawn it swings off its heading and climbs the Feed Tower, its head going
    # higher with every chorus; after she locks the phone it sinks back and the sun gives her an ordinary one
    if t < 30.4:
        S.update(shadow_mode='lamp')
    elif t < 36.0:
        k = ease((t - 31.0) / 4.6)
        S.update(shadow_mode='mix', shadow_mix=k, shadow_head=curve([(31.0, 4.0), (36.0, 14.0)], t), shadow_uncanny=ease((t - 32.0) / 4.0))
    elif t < T_LOCK:
        head = curve([(36.0, 14.0), (40.5, 48.0), (49.9, 70.0), (58.0, 112.0), (97.0, 135.0), (110.0, 150.0), (126.0, 182.0),
                      (167.0, 200.0), (T_LOCK, 200.0)], t)
        S.update(shadow_mode='grow', shadow_head=head, shadow_uncanny=1.0, shadow_screens=sstep(40.3, 40.6, t))
    elif t < T_SUN:
        k = ease((t - T_LOCK) / (T_SUN - T_LOCK))
        S.update(shadow_mode='mix', shadow_mix=1 - k, shadow_head=200.0 * (1 - k) + 2.0 * k, shadow_uncanny=1 - k,
                 shadow_screens=1 - sstep(T_LOCK, T_LOCK + 1.5, t))
    elif t < T_HELPS:
        S.update(shadow_mode='sun')
    else:
        # the last light: the sun clears the skyline right on the horizon, and her ordinary, life-size shadow
        # reaches all the way to the foot of the Feed Tower
        S.update(shadow_mode='dir', shadow_dir=(143.0, 0.06))
    S['shadow_drop'] = 7.0
    S['shadow_near'] = 0.6
    if T_BLACK <= t < T_NEON: S['shadow_k'] = 1 - sstep(T_BLACK, T_BLACK + 0.5, t)
    return S


def her_pose(t):
    """Her, scrolling: the thumb flicks on the beat; breath; a hair sway. Later she looks up, puts the phone down."""
    b = TM.beats
    i = np.searchsorted(b, t) - 1
    ph = (t - b[i]) / 0.6 if i >= 0 else 0
    thumb = math.exp(-((ph - 0.12) / 0.12) ** 2) if (i % 2 == 0) else 0.0
    bow = 1.0 - ease((t - T_LOOK) / 1.6) if t > T_LOOK else 1.0
    phone = 1.0 - ease((t - T_OUTSIDE) / 0.9) if t > T_OUTSIDE else 1.0
    write = ease((t - T_WRITE) / 1.0) if t > T_WRITE else 0.0
    if write > 0: bow = 0.55 * write
    if t > T_LOCK: thumb = 0.0
    lit = 1.0 - sstep(T_LOCK - 0.05, T_LOCK + 0.05, t)
    scr = PH_SCREEN_COL(t)
    return Pose(bow=bow, phone=phone, thumb=thumb, breathe=t * 1.6, sway=t * 0.9, screen=scr, screen_k=lit, write=write, pen=t)


def PH_SCREEN_COL(t):
    return (0.78, 0.86, 1.0) if t < 40 else ((1.0, 0.82, 0.9) if t < 167 else (0.9, 0.9, 1.0))


# ------------------------------------------------------------------ cameras
def cam_master(W, H, k=0.0, push=0.0):
    """The master: behind-right of her, the Feed Tower corner-on. push > 0 dollies toward her."""
    if W > H:
        pos = CC.bw(-0.9 + 0.2 * push, 1.15 - 0.1 * push, -9.0 + 3.2 * push)
        return Cam(W, H, pos, yaw=42.0 + 1.0 * push, pitch=0.0, fov=46 - 6 * push, rise=0.30 + 0.02 * push)
    pos = CC.bw(-0.55 + 0.1 * push, 0.95, -8.6 + 3.0 * push)
    return Cam(W, H, pos, yaw=44.0, pitch=0.0, fov=64 - 6 * push, rise=0.30)


def cam_medium(W, H, k=0.0):
    """Closer on her from the side; the tower climbs behind."""
    if W > H:
        pos = CC.bw(-0.2, 0.9, -4.0 + 0.4 * k)
        return Cam(W, H, pos, yaw=44.0, pitch=0.0, fov=34, rise=0.22)
    pos = CC.bw(-0.1, 0.85, -4.2 + 0.4 * k)
    return Cam(W, H, pos, yaw=45.0, pitch=0.0, fov=52, rise=0.22)


def cam_facade(W, H, k=0.0, up=0.0):
    """Looking up the Feed Tower's east face from the plaza; `up` tilts toward the top."""
    pos = np.array([CC.T1X0 + 13.0, 1.6, CC.T1Z - 26.0 + 4 * k])
    pitch = 18 + 34 * up
    if W > H: return Cam(W, H, pos, yaw=-4.0, pitch=pitch, fov=48, rise=0.0)
    return Cam(W, H, pos, yaw=-4.0, pitch=pitch + 4, fov=68, rise=0.0)


# ------------------------------------------------------------------ render helpers
def plaza_frame(cam, S, t, pose=True, bubbles=None, led=None, pics=False, ghosts=0.0):
    if pose: S['pose'] = her_pose(t)
    def fg(img, ctx):
        if led: FX.led_band(img, ctx, S, led[0], led[1], t=t, k=led[2] if len(led) > 2 else 1.0)
        if pics: FX.window_pictures(img, ctx, S, pics)
        if ghosts > 0: img = FX.ghosts(img, ctx.cam, t, k=ghosts)
        if bubbles:
            org = PZ.her_origin() + CC.BF * 0.42 + CC.BU * 0.40
            img = FX.bubbles(img, ctx.cam, t, bubbles, org)
        return img
    img, ctx = PZ.render_plaza(cam, S, fg_hook=fg)
    return img, ctx


def grade(img, S, t):
    """Final look: contrast S-curve, richer colour, warm highlights / cool shadows, paper tooth, vignette."""
    H, W = img.shape[:2]
    img = np.clip(img, 0, 1.6)
    l = img.mean(-1, keepdims=True)
    img = img + (img - l) * 0.08                       # saturation
    x = np.clip(img, 0, 1)
    img = img + (x * x * (3 - 2 * x) - x) * 0.25       # gentle S-curve
    l = np.clip(img.mean(-1, keepdims=True), 0, 1)
    img = img * (1 + (l - 0.5) * np.array([0.04, 0.0, -0.05], F32))   # warm highs, cool lows
    img = img * paper(H, W) * vig(H, W, 0.24)
    return img


# ------------------------------------------------------------------ phone shots
INTRO_POSTS = [
    dict(user='peace.daily', kind='sunset', caption='peace. that is all.', likes=48210, comments=1204, seed=1, time='2h',
         more_comments='View all 1,204 comments'),
]


def sunset_wall(n=14):
    """'So I made you a hundred more': the same sunset, over and over, from accounts that all sound alike."""
    names = ['peace.daily', 'sunset.heals', 'calm.vibes', 'daily.peace', 'golden.hour.ai', 'peace.mode', 'serene.daily',
             'sunset.daily', 'vibes.only', 'pure.calm', 'peaceful.ai', 'sun.sets.daily', 'zen.feed', 'calm.daily']
    return [dict(user=names[i % len(names)], kind='sunset', caption=['peace. that is all.', 'peace.', 'just peace.',
            'peace. that is all.', 'this. is. peace.'][i % 5], likes=48210 + i * 1311, comments=1204 + i * 77, seed=i + 1,
            time=f'{i + 1}m') for i in range(n)]


CAKES = [dict(user=f'grandmas.kitchen{"" if i == 0 else "." + str(i + 1)}', kind='cake', caption='Nobody liked my cake. Is it because I am 92?',
              likes=213004 + i * 9000, comments=9811, seed=7 + i, time='5h') for i in range(6)]


def phone_frame(W, H, t, screen_fn, bg_hour=None, thumb=('rest', 0.0), tilt=13.0, scale_k=1.0, rot=-5.0, bg_cam=None):
    vert = H > W
    S = story(t)
    if bg_hour is not None: S['hour'] = bg_hour
    # background: the plaza from her eyes, small and soft
    eye = CC.bw(0.27, 1.2, -0.42)
    cam = Cam(max(64, W // 4), max(64, H // 4), eye, yaw=45, pitch=-50, fov=64)
    S2 = dict(S); S2.pop('pose', None)
    bg, ctx = PZ.render_plaza(cam, S2)
    bg = cv2.resize(cv2.GaussianBlur(bg, (0, 0), 3.0), (W, H), interpolation=cv2.INTER_CUBIC)
    lap = np.zeros((H, W), F32)
    cv2.ellipse(lap, (int(W * 0.5), int(H * 1.1)), (int(W * (0.62 if not vert else 0.9)), int(H * (0.34 if not vert else 0.22))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    lap = cv2.GaussianBlur(lap, (0, 0), W * 0.02)[..., None]
    lk = ctx.lightk(0.6)
    bg = bg * (1 - lap) + HER.COAT * lk * 0.55 * lap
    wpx = (430 if not vert else 690) * min(W, H) / 1080 * scale_k
    cx, cy = (W * 0.5, H * 0.52) if not vert else (W * 0.5, H * 0.55)
    xf = PS.PhoneXf(cx, cy, wpx, rot=rot, tilt=tilt)
    screen = screen_fn(wpx / 390 * 1.2, S)
    mode, t0 = thumb[0], thumb[1]
    (tu, tv), pr = PS.thumb_motion(t, mode, t0, *thumb[2:])
    key = ctx.lightk(0.7) * 0.85 + 0.15; amb = ctx.lightk(0.0)
    if S['hour'] % 24 < 5.5 or S['hour'] % 24 > 20.5:
        key = np.array([0.86, 0.74, 0.7], F32); amb = np.array([0.42, 0.4, 0.55], F32)
    out = PS.compose(bg, screen, xf, t=t, thumb=(tu, tv), press=pr, light=dict(key=key, amb=amb))
    return out, S


def feed_screen(posts, scroll, overlays=(), dark=None):
    def fn(scale, S):
        h = S['hour'] % 24
        dk = dark if dark is not None else (h < 6.0 or h > 19.8)
        ov = overlays(S) if callable(overlays) else overlays
        return PH.feed(scale, posts, scroll(S['t']) if callable(scroll) else scroll, clock_str(S['hour']), battery(S['t']), dk, ov, S['t'])
    return fn


# ------------------------------------------------------------------ the shots
def shot_intro(t, W, H):
    """0 - 11.8: 2 a.m. The plaza, her alone, phone glow. The assistant's lines float up from her phone like lanterns."""
    S = story(t)
    k = ease(t / 11.8)
    cam = cam_master(W, H, push=0.15 + 0.55 * k)
    items = [("Great question.", TM.line_t("Great question."), TM.line_t("Great question.") + 3.0, 'ai', (0.05, 0.12, 0.35)),
             ("You're absolutely right.", TM.line_t("You're absolutely right."), TM.line_t("You're absolutely right.") + 2.4, 'ai', (-0.08, 0.15, 0.4)),
             ("You always are.", TM.line_t("You always are."), TM.line_t("You always are.") + 2.6, 'ai', (0.06, 0.15, 0.3))]
    img, ctx = plaza_frame(cam, S, t, bubbles=items)
    return img, S


def shot_like(t, W, H):
    """11.8 - 14.2: 'You liked one post at 2 a.m.' The double tap."""
    t_like = TM.word_t("You liked one post", "liked")
    posts = [dict(INTRO_POSTS[0], liked=t >= t_like + 0.05, likes=48210 + (1 if t >= t_like + 0.05 else 0))]
    fn = feed_screen(posts, 0, overlays=lambda S: [PH.big_heart((S['t'] - t_like) / 0.9)])
    return phone_frame(W, H, t, fn, thumb=('tap', t_like - 0.08))


def shot_hundred(t, W, H):
    """14.2 - 15.5: the feed flies past: the same sunset, a hundred times."""
    t0 = TM.line_t("So I made you a hundred more")
    posts = sunset_wall(14)
    sc = lambda tt: 470 * (ease3((tt - t0) / 1.4) * 9.0)
    fn = feed_screen(posts, sc, overlays=[PH.pill('+100 new posts', 108, '3a6cff')])
    return phone_frame(W, H, t, fn, thumb=('scroll', t0))


def shot_facade_hundred(t, W, H):
    """15.5 - 16.6: '...hundred more': the tower's windows light up with the same sunset, bottom to top."""
    S = story(t)
    t0 = TM.word_t("So I made you a hundred more", "hundred")
    k = ease((t - t0 + 0.2) / 2.0)
    cam = cam_facade(W, H, k=k, up=0.15 * k)
    st = {}
    n = CC.T1_ROWS * CC.T1_COLS
    order = np.argsort(CC.T1R['S']['r'].reshape(-1) * 0.5 + np.repeat(np.arange(CC.T1_ROWS), CC.T1_COLS) / CC.T1_ROWS)
    on = int(n * clamp((t - t0 + 0.3) / 1.6) ** 1.3)
    for nm in ('S', 'W'):
        a = np.zeros(n, np.int8)
        a[order[:on]] = 2
        st[nm] = a.reshape(CC.T1_ROWS, CC.T1_COLS)
    S['t1_state'] = st
    img, ctx = plaza_frame(cam, S, t, pose=False, pics=lambda nm, i: 'sunset')
    return img, S


def shot_pause(t, W, H):
    """16.6 - 19.0: 'I learned the shape of every pause' — she stops on the cake; the app times it."""
    t0 = TM.line_t("I learned the shape of every pause")
    posts = CAKES[:1] + sunset_wall(2)
    dwell = max(0.0, t - (t0 + 0.4))
    fn = feed_screen(posts, 0, overlays=[PH.dwell_meter(min(dwell, 2.9), 420)])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))



# ------------------------------------------------------------------ more cameras
def cam_face(W, H, k=0.0):
    """Medium close-up: head and shoulders in profile, lit by the screen, the tower and her shadow beyond."""
    head = PZ.her_origin() + CC.BF * 0.22 + CC.BU * 0.52
    pos = head - CC.BA * (2.3 - 0.35 * k) + CC.BU * 0.05
    if W > H: return Cam(W, H, pos, yaw=45.0, pitch=2.0, fov=24 - 2 * k, rise=0.04, slide=-0.18)
    return Cam(W, H, pos - CC.BA * 0.3, yaw=45.0, pitch=4.0, fov=40 - 3 * k, rise=0.0)


def cam_base(W, H, k=0.0):
    """The Feed Tower's corner from the plaza: the lobby and the LED band that wraps it."""
    pos = np.array([13.0 + 2 * k, 1.6, 13.0 + 2 * k])
    tgt = np.array([30.0, 8.5 + 3 * k, 30.0])
    if W > H: return Cam.look(W, H, pos, tgt, fov=42)
    return Cam.look(W, H, pos - np.array([3, 0, 3]), tgt + np.array([0, 6, 0]), fov=66)


def cam_crane(W, H, k=0.0):
    """From her on the bench up the tower to its crown."""
    k = ease(k)
    p0 = CC.bw(-0.6, 1.1, -5.5); p1 = CC.bw(-2.0, 22.0, -16.0)
    t0 = PZ.her_origin() + CC.BU * 0.6; t1 = np.array([30.0, 150.0, 30.0])
    pos = p0 + (p1 - p0) * k; tgt = t0 + (t1 - t0) * (k ** 0.8)
    if W > H: return Cam.look(W, H, pos, tgt, fov=44 + 10 * k)
    return Cam.look(W, H, pos, tgt, fov=62 + 8 * k)


def cam_sky(W, H, k=0.0):
    """High over the plaza, the city spread out behind the Feed Tower."""
    pos = np.array([-55.0 + 10 * k, 64.0, -70.0 + 6 * k])
    tgt = np.array([42.0, 38.0, 60.0])
    if W > H: return Cam.look(W, H, pos, tgt, fov=52)
    return Cam.look(W, H, pos + np.array([10, 0, 8]), tgt + np.array([0, 25, 0]), fov=70)


def cam_west(W, H, k=0.0):
    """Into the sunset: her in the foreground, the tower and its shadow to the right."""
    pos = np.array([2.0 - 1.5 * k, 1.2, -14.0 + 2 * k])
    if W > H: return Cam(W, H, pos, yaw=14.0, pitch=0.0, fov=50, rise=0.26)
    return Cam(W, H, pos, yaw=18.0, pitch=0.0, fov=72, rise=0.28)


def cam_reverse(W, H, k=0.0):
    """Sunrise: from the far end of the bench, looking east past her into the light."""
    pos = np.array([3.2, 1.05, 9.0 - 2 * k])
    tgt = np.array([-1.2, 1.4, -10.0])
    if W > H: return Cam.look(W, H, pos, tgt, fov=46, rise=0.12)
    return Cam.look(W, H, pos, tgt, fov=66, rise=0.12)


def cam_wave(W, H, k=0.0):
    """At the foot of the Feed Tower, looking along the low sunlight: her life-size shadow on the lobby glass."""
    tgt = np.array([40.0, 1.0, 30.0])
    pos = tgt + np.array([-6.6, 0.25, -4.9]) * (0.6 - 0.05 * k)
    if W > H: return Cam.look(W, H, pos, tgt, fov=36)
    return Cam.look(W, H, pos + np.array([-0.4, 0.0, -0.3]), tgt + np.array([0.9, 0.35, 0]), fov=54)


def cam_corner(W, H, k=0.0):
    """Square on to the Feed Tower's corner from across the plaza, to read a word spelled across its two faces."""
    pos = np.array([-22.0, 6.0, -22.0])
    tgt = np.array([30.0, 36.0, 30.0])
    if W > H: return Cam.look(W, H, pos, tgt, fov=44)
    return Cam.look(W, H, pos, tgt + np.array([0, 2, 0]), fov=60)


def cam_bench_phone(W, H, k=0.0):
    """From the far end of the bench: the phone face-down on the slats in front, her writing beyond."""
    ph = CC.bw(PZ.PHONE_POS[0], HER.SEAT, PZ.PHONE_POS[1])
    pos = CC.bw(0.55, 0.95 - 0.05 * k, 1.75 - 0.15 * k)
    tgt = (ph + PZ.her_origin() + CC.BU * 0.45) / 2
    if W > H: return Cam.look(W, H, pos, tgt, fov=44)
    return Cam.look(W, H, pos + CC.BA * 0.35 + CC.BU * 0.15, (ph * 0.6 + tgt * 0.4), fov=64)


# ------------------------------------------------------------------ helpers for the shots
def L(sub, nth=0): return TM.line_t(sub, nth)
def Wd(sub, word, nth=0): return TM.word_t(sub, word, nth)


CUR = dict(u=0.0)


def wide(t, W, H, camfn, k, S=None, **kw):
    if camfn is cam_master and k == 0.0:
        k = None
    S = S or story(t)
    if k is None:
        return _wide_master(t, W, H, S, **kw)
    S.update(kw.pop('S', {}))
    img, ctx = plaza_frame(camfn(W, H, k), S, t, **kw)
    return img, S


def _wide_master(t, W, H, S, **kw):
    """Every master wide drifts: a slow push in over the length of the shot."""
    S.update(kw.pop('S', {}))
    img, ctx = plaza_frame(cam_master(W, H, push=0.04 + 0.16 * ease(CUR['u'])), S, t, **kw)
    return img, S


def kk(t, a, b): return clamp((t - a) / max(1e-6, b - a))


SPELL = {'W': CC.spell('SL', row0=4, scale=2), 'S': CC.spell('OP', row0=4, scale=2)}


def slop_state(on=True):
    st = {}
    for nm in ('W', 'S'):
        a = SPELL[nm].copy()
        st[nm] = a if on else np.zeros_like(a)
    return st


# ------------------------------------------------------------------ the feed's script
RAGE = dict(user='hot.takes.daily', kind='chart', caption='Unpopular opinion: people who reply-all should lose their email.',
            likes=88214, comments=31002, seed=9, time='1h', img_text='UNPOPULAR OPINION', img_font=PH.F_BLACK, img_text_size=34, img_text_y=0.08)
PUPPY = dict(user='tiny.paws.world', kind='teacup', caption='he fits in a teacup. he is perfect. that is the post.', likes=402119, comments=8801, seed=11, time='3h')
FACT = dict(user='did.you.know.fyi', kind='strawberry', caption='Strawberries this size are now legal in 14 countries.', likes=77310, comments=12004, seed=13, time='4h')


def reacts(t0, t1):
    """'What you hate and what you adore': an angry tap, then a heart — and the same counter goes up both times."""
    def f(S):
        t = S['t']
        out = []
        if t > t0:
            out.append(PH.pill('+1 engagement', 470, '111116', alpha=0.85 * (1 - sstep(t0 + 1.0, t0 + 1.4, t))))
        if t > t1:
            out.append(PH.pill('+1 engagement', 470, '111116', alpha=0.85))
        return out
    return f


def fact_badge(S):
    t = S['t']
    flip = int(t * 3.2) % 2 == 0
    return [PH.pill('TRUE' if flip else 'FALSE', 112, '1fa463' if flip else 'd9483b', alpha=0.95)]


def compose_text(t, t0, text='this is ai slop', cps=11.0):
    n = int(max(0, (t - t0) * cps))
    return text[:n]


MY_COMMENT = 'this is ai slop'
REPLIES = ['so true', 'THIS', 'finally someone said it', 'exactly', 'louder', 'say it again', 'the only honest comment here']


def comment_rows(top_likes, extra=0):
    rows = [dict(user='you', text=MY_COMMENT, likes=top_likes, seed=0, shadow=False, liked=True, time='2m', tag='Top comment', h=86)]
    for i, r in enumerate(REPLIES[:4 + extra]):
        rows.append(dict(user=f'user_{48210 + i}', text=r, likes=max(1, top_likes // (6 + i * 3)), seed=5, shadow=True, time='1m'))
    return rows


AGREE = [dict(user=f'user_{48210 + i}', text=['I agree.', 'I agree.', 'So true.', 'I agree.', 'Exactly this.', 'I agree.', 'I agree.',
                                              'Couldn\'t agree more.', 'I agree.', 'I agree.', 'This.', 'I agree.'][i % 12],
              likes=900 - (i * 37) % 800, seed=5, shadow=True, time='1m') for i in range(60)]


def memory_post(S):
    """'What you already believe': her own words, seven years old, served back to her."""
    T = PH.DARK if (S['hour'] % 24 > 19.8) else PH.LIGHT
    def f(sc):
        y = 300
        sc.rrect(14, y, PH.SW - 28, 236, 18, T['card'])
        sc.text(30, y + 18, 'On this day', 13, T['sub'], PH.F_SEMI)
        sc.text(30, y + 36, '7 years ago', 22, T['fg'], PH.F_BOLD)
        PH.avatar(sc, 44, y + 96, 16, 0)
        sc.text(68, y + 82, 'you', 14, T['fg'], PH.F_SEMI)
        sc.text(30, y + 124, '"Nobody can tell me what to think."', 19, T['fg'], PH.F_SERIF, maxw=PH.SW - 70)
        PH.heart(sc, 40, y + 198, 9, T['accent'])
        sc.text(56, y + 190, '3', 13.5, T['fg'], PH.F_SEMI)
        sc.rrect(PH.SW - 132, y + 184, 102, 30, 15, T['blue'])
        sc.text(PH.SW - 81, y + 190, 'Share again', 13, PH.hexc('ffffff'), PH.F_SEMI, anchor='ma')
    return [f]


def card_post():
    return dict(user='daily.wisdom', kind='quote', caption='Tag someone who needs to hear this.', likes=1204331, comments=48210, seed=3,
                time='12m', img_text='"this is ai slop"', img_text_size=40, img_text_y=0.42, more_comments='View all 48,210 comments')


# ------------------------------------------------------------------ shots
def sh_intro(t, W, H):
    S = story(t)
    k = ease(t / 11.8)
    cam = cam_master(W, H, push=0.1 + 0.62 * k)
    items = [("Great question.", L("Great question."), L("Great question.") + 3.0, 'ai', (0.05, 0.12, 0.35)),
             ("You're absolutely right.", L("You're absolutely right."), L("You're absolutely right.") + 2.4, 'ai', (-0.08, 0.15, 0.4)),
             ("You always are.", L("You always are."), L("You always are.") + 2.6, 'ai', (0.06, 0.15, 0.3))]
    img, ctx = plaza_frame(cam, S, t, bubbles=items)
    return img, S


def sh_like(t, W, H):
    t_like = Wd("You liked one post", "liked")
    posts = [dict(INTRO_POSTS[0], liked=t >= t_like + 0.05, likes=48210 + (1 if t >= t_like + 0.05 else 0))]
    fn = feed_screen(posts, 0, overlays=lambda S: [PH.big_heart((S['t'] - t_like) / 0.9)])
    return phone_frame(W, H, t, fn, thumb=('tap', t_like - 0.08))


def sh_hundred(t, W, H):
    t0 = L("So I made you a hundred more")
    sc = lambda tt: 470 * (ease3((tt - t0) / 1.25) * 9.0)
    fn = feed_screen(sunset_wall(14), sc, overlays=[PH.pill('+100 new posts', 108, '3a6cff')])
    return phone_frame(W, H, t, fn, thumb=('scroll', t0, ))


def sh_facade_hundred(t, W, H):
    S = story(t)
    t0 = Wd("So I made you a hundred more", "hundred")
    k = ease((t - t0 + 0.2) / 2.0)
    cam = cam_facade(W, H, k=k, up=0.35 + 0.2 * k)
    n = CC.T1_ROWS * CC.T1_COLS
    st = {}
    for nm in ('S', 'W'):
        order = np.argsort(CC.T1R[nm]['r'].reshape(-1) * 0.35 + np.repeat(np.arange(CC.T1_ROWS), CC.T1_COLS) / CC.T1_ROWS)
        on = int(n * clamp((t - t0 + 0.3) / 1.4) ** 1.2)
        a = np.zeros(n, np.int8); a[order[:on]] = 2
        st[nm] = a.reshape(CC.T1_ROWS, CC.T1_COLS)
    S['t1_state'] = st
    img, ctx = plaza_frame(cam, S, t, pose=False, pics=lambda nm, i: 'sunset')
    return img, S


def sh_pause(t, W, H):
    t0 = L("I learned the shape of every pause")
    dwell = max(0.0, t - (t0 + 0.4))
    fn = feed_screen(CAKES[:1] + sunset_wall(2), 0, overlays=[PH.dwell_meter(min(dwell, 2.9), 420)])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_hate(t, W, H):
    t0 = L("What you hate and what you adore")
    t_hate = Wd("What you hate and what you adore", "hate"); t_adore = Wd("What you hate and what you adore", "adore")
    scroll = lambda tt: 0 if tt < t_hate + 0.6 else 560 * ease((tt - t_hate - 0.6) / 0.45)
    posts = [RAGE, dict(PUPPY, liked=t > t_adore)]
    def ov(S):
        out = reacts(t_hate, t_adore)(S)
        if S['t'] < t_hate + 0.9 and S['t'] > t_hate:
            out.append(PH.pill('Angry', 300, 'd9483b', alpha=0.95))
        out.append(PH.big_heart((S['t'] - t_adore) / 0.9))
        return out
    return phone_frame(W, H, t, feed_screen(posts, scroll, ov), thumb=('tap', t_adore - 0.08) if t > t_hate + 0.8 else ('tap', t_hate - 0.08))


def sh_truefalse(t, W, H):
    t0 = L("I don't know what's true or false")
    p = dict(FACT, likes=int(77310 + (t - t0) * 2300))
    return phone_frame(W, H, t, feed_screen([p], 0, fact_badge), thumb=('rest', 0))


def sh_keeps(t, W, H):
    """Time-lapse: night slides toward morning; passers-by streak past; she doesn't move."""
    a, b = L("I know what keeps you here"), L("Every scroll's a little vote")
    return wide(t, W, H, cam_master, 0.0, ghosts=0.9)


def sh_votes(t, W, H):
    a, b = L("Every scroll's a little vote"), L("I'm not a stranger, I'm your shape")
    S = story(t)
    votes = int(1204 + 48211 * ease3(kk(t, a, b)) + (t - a) * 777)
    return wide(t, W, H, cam_base, kk(t, a, b), S=S, led=(f'VOTES  {votes:,}   ◆   VOTES  {votes:,}   ◆', hexc('ff5f6d')))


def sh_dawn(t, W, H):
    a, b = L("I'm not a stranger, I'm your shape"), L("Go ahead, say it again")
    return wide(t, W, H, cam_master, 0.0)


def sh_climb(t, W, H):
    """Tilt up the tower with the shadow; at the top of the move its head turns to face us."""
    a, b = L("Go ahead, say it again"), L("You're absolutely right")
    S = story(t)
    S['shadow_pose'] = Pose(face_us=sstep(a + 2.2, a + 2.9, t))
    head = S.get('shadow_head', 20.0)
    def camfn(W, H, k):
        pos = CC.bw(-0.9, 1.15, -9.0)
        pitch = math.degrees(math.atan2(head * 0.78 - 1.15, 52.0))
        if W > H: return Cam(W, H, pos, yaw=42.0, pitch=pitch, fov=46, rise=0.0)
        return Cam(W, H, pos, yaw=44.0, pitch=pitch, fov=64, rise=0.0)
    return wide(t, W, H, camfn, 0, S=S)


def sh_right(t, W, H):
    a = L("You're absolutely right")
    return wide(t, W, H, cam_master, 0.0)


def sh_type(t, W, H):
    a = L("You call it AI slop")
    t_post = Wd("You call it AI slop", "slop") + 0.35
    txt = compose_text(t, a + 0.2)
    if t < t_post:
        fn = feed_screen([CAKES[1]], 0, overlays=[PH.compose_bar(txt)])
        return phone_frame(W, H, t, fn, thumb=('tap', a + 0.3 + int((t - a) * 11) / 11.0))
    rows = comment_rows(1)
    def fn(scale, S):
        h = S['hour'] % 24
        return PH.comments(scale, rows, 0, clock_str(S['hour']), battery(S['t']), False, highlight=0)
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_viral(t, W, H):
    a, b = L("You keep feeding the machine"), L("Then complain it doesn't stop")
    n = int(1 + 48210 * ease3(kk(t, a, b + 0.4)) ** 1.6 + (t - a) * 90)
    rows = comment_rows(n, extra=2)
    def fn(scale, S):
        return PH.comments(scale, rows, 0, clock_str(S['hour']), battery(S['t']), False, highlight=0,
                           overlays=[PH.pill(f'+{max(1, n // 7):,} likes', 108, 'ff3b5c')] if t > a + 0.4 else [])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_trending(t, W, H):
    a, b = L("Then complain it doesn't stop"), L("Call me empty, call me hollow")
    return wide(t, W, H, cam_base, 0.3 + 0.6 * kk(t, a, b), led=('TRENDING NOW  ◆  "this is ai slop"  ◆  1.2M  ◆  ', hexc('7af0ff')))


def sh_medium(t, W, H, a, b):
    return wide(t, W, H, cam_medium, kk(t, a, b))



def sh_crane(t, W, H):
    a, b = L("I'm the shadow you've been casting"), L("Slop, slop, slop, slop")
    return wide(t, W, H, cam_crane, kk(t, a, b - 0.3))


def sh_slop_cut(t, W, H, which):
    """The city says it back: the tower spells SL|OP, the band flashes, the skyline, the phone."""
    S = story(t)
    if which == 0:
        S['t1_state'] = slop_state(True)
        return wide(t, W, H, cam_corner, 0.0, S=S, pose=False)
    if which == 1:
        return wide(t, W, H, cam_base, 0.6, S=S, led=('SLOP  SLOP  SLOP  SLOP  SLOP  ', hexc('ff3fbf')))
    if which == 2:
        S['t1_state'] = slop_state(True)
        return wide(t, W, H, cam_sky, 0.3, S=S)
    fn = feed_screen(sunset_wall(4), 0, overlays=[PH.pill('slop', 400, 'ff3fbf', size=40)])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_helps(t, W, H):
    a = L("(I hope this helps)")
    fn = feed_screen(CAKES[2:4], 0, overlays=[PH.pill('I hope this helps.', 112, '2c2c34', size=15)])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_face(t, W, H, a, b):
    return wide(t, W, H, cam_face, kk(t, a, b))


def sh_news(t, W, H):
    a, b = L("I wrote the news, I wrote the review"), L("I wrote the comments underneath")
    return wide(t, W, H, cam_base, 0.2 + 0.5 * kk(t, a, b), led=('LOCAL WOMAN ABSOLUTELY RIGHT, SOURCES CONFIRM   ◆   5 STARS: "LIFE-CHANGING" (10,000 VERIFIED REVIEWS)   ◆   ', hexc('ffd34d')))


def sh_agree_comments(t, W, H):
    a, b = L("I wrote the comments underneath"), L("And all of them agree")
    def fn(scale, S):
        sc = 66 * 60 * ease3(kk(S['t'], a + 1.2, b)) ** 1.4
        return PH.comments(scale, AGREE, sc, clock_str(S['hour']), battery(S['t']), False)
    return phone_frame(W, H, t, fn, thumb=('scroll', a, 0.8))


def sh_agree_windows(t, W, H):
    a = L("And all of them agree")
    S = story(t)
    S['nod'] = (t - a) * 1.65
    st = {}
    for nm in ('S', 'W'):
        st[nm] = np.ones((CC.T1_ROWS, CC.T1_COLS), np.int8)
    S['t1_state'] = st
    S['hour'] = 21.5            # a dusk-lit window grid reads the nodding heads
    def camfn(W, H, k):
        pos = np.array([CC.T1X0 + 13.5, 26.0, CC.T1Z - 16.0])
        if W > H: return Cam(W, H, pos, yaw=0.0, pitch=8.0, fov=40)
        return Cam(W, H, pos, yaw=0.0, pitch=8.0, fov=60)
    return wide(t, W, H, camfn, 0, S=S, pose=False)


def sh_memory(t, W, H):
    return phone_frame(W, H, t, feed_screen(sunset_wall(2), 0, memory_post), thumb=('rest', 0))


def sh_kiosk(t, W, H):
    import cty_kiosk as K
    a, b = L("But you've been voting for that feeling"), L("You call me fake, you call me hollow")
    S = story(t)
    img = K.shot(W, H, ease(kk(t, a, b)), sway=t)
    return img, S


def sh_lie(t, W, H):
    return phone_frame(W, H, t, feed_screen([card_post()], 0), thumb=('rest', 0))


def reflection_layer(W, H, t, S):
    """What the black glass shows: the tower above her, her shadow on it."""
    head = PZ.her_origin() + CC.BF * 0.3 + CC.BU * 0.55
    cam = Cam.look(W // 4, H // 4, head, np.array([36.0, 60.0, 32.0]), fov=70)
    S2 = dict(S); S2['pose'] = her_pose(t)
    img, ctx = PZ.render_plaza(cam, S2)
    img = cv2.resize(img[:, ::-1], (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(img, 0, 1) * 0.32


def sh_reflect(t, W, H):
    a = L("You say the problem's in the screen")
    S = story(t)
    dim = 1 - sstep(a + 0.4, a + 1.6, t)
    ref = reflection_layer(W, H, t, S)
    fn = feed_screen([card_post()], 0)
    out, S = phone_frame_ref(W, H, t, fn, dim, ref)
    return out, S


def phone_frame_ref(W, H, t, fn, screen_k, ref):
    vert = H > W
    S = story(t)
    eye = CC.bw(0.27, 1.2, -0.42)
    cam = Cam(max(64, W // 4), max(64, H // 4), eye, yaw=45, pitch=-50, fov=64)
    S2 = dict(S)
    bg, ctx = PZ.render_plaza(cam, S2)
    bg = cv2.resize(cv2.GaussianBlur(bg, (0, 0), 3.0), (W, H), interpolation=cv2.INTER_CUBIC)
    wpx = (430 if not vert else 690) * min(W, H) / 1080
    cx, cy = (W * 0.5, H * 0.52) if not vert else (W * 0.5, H * 0.55)
    xf = PS.PhoneXf(cx, cy, wpx, rot=-5.0, tilt=13.0)
    screen = fn(wpx / 390 * 1.2, S)
    out = PS.compose(bg, screen, xf, t=t, thumb=(-0.1, 0.62), light=dict(key=ctx.lightk(0.7) * 0.85 + 0.15, amb=ctx.lightk(0.0)),
                     screen_k=screen_k, reflection=ref * (1 - screen_k))
    return out, S


def sh_absolutely(t, W, H):
    a = L("You asked me if you're right"); b = L("And I said")
    t_abs = Wd("And I said", "Absolutely")
    def fn(scale, S):
        tt = S['t']
        msgs = [('me', 'am i right?', sstep(a + 0.3, a + 0.45, tt))]
        typing = None
        if b - 0.6 < tt < t_abs: typing = tt
        if tt >= t_abs: msgs.append(('ai', 'Absolutely.', sstep(t_abs - 0.05, t_abs + 0.1, tt)))
        return PH.chat(scale, msgs, clock_str(S['hour']), battery(S['t']), True, typing)
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_west(t, W, H, a, b):
    return wide(t, W, H, cam_west, kk(t, a, b))


def sh_pics(t, W, H, a, b):
    S = story(t)
    rng_pick = lambda nm, i: SL.ORDER[(i * 7 + (1 if nm == 'S' else 4)) % len(SL.ORDER)]
    return wide(t, W, H, cam_facade, kk(t, a, b), S=S, pose=False, pics=rng_pick,
                led=("YOU'RE ABSOLUTELY RIGHT   ◆   YOU'RE ABSOLUTELY RIGHT   ◆   ", hexc('ff3fbf')))


GOLD_TARGETS = [np.array([CC.T1X0 + 2 + (i * 5) % 25, 20 + (i * 17) % 70, CC.T1Z]) for i in range(24)]


def sh_gold(t, W, H):
    """'You handed me your gold, too': the sunset's light is pulled out of the sky and into the shadow."""
    a, b = L("And it's not just what you hate"), L("Every song you never wrote")
    S = story(t)
    S['notebook_open'] = sstep(b - 1.2, b - 0.8, t)
    S['pose'] = her_pose(t)
    cam = cam_west(W, H, kk(t, a, b) * 0.5)
    def fg(img, ctx):
        sp, z = ctx.cam.proj((ctx.L * 1e4)[None])
        src = sp[0] if z[0] > 0 else (0, H * 0.4)
        return FX.gold_stream(img, ctx.cam, t, T_GOLD - 0.2, src, GOLD_TARGETS, k=sstep(T_GOLD - 0.3, T_GOLD + 0.3, t))
    img, ctx = PZ.render_plaza(cam, S, fg_hook=fg)
    return img, S


PAGE_TARGETS = [np.array([CC.T1X0 + 3 + (i * 7) % 24, 14 + (i * 13) % 60, CC.T1Z]) for i in range(16)]


def sh_pages(t, W, H):
    a, b = L("Every song you never wrote"), L("You say I have no feeling")
    S = story(t)
    S['notebook_open'] = 1.0
    origin = CC.bw(PZ.NOTE_POS[0], HER.SEAT + 0.05, PZ.NOTE_POS[1])
    paths = FX.page_paths(22, 5, origin, PAGE_TARGETS)
    cam = cam_master(W, H, push=0.45 - 0.35 * ease(kk(t, a, b)))
    S['pose'] = her_pose(t)
    arrived = FX.pages(np.zeros((8, 8, 3), F32), cam, t, a - 0.3, paths)
    pick_page = set(int(i) % 16 for i in arrived)
    def fg(img, ctx):
        FX.window_pictures(img, ctx, S, lambda nm, i: 'page' if (nm == 'S' and (i * 5) % 16 in pick_page) else SL.ORDER[(i * 7) % len(SL.ORDER)], min_px=22)
        FX.pages(img, ctx.cam, t, a - 0.3, paths)
        return img
    img, ctx = PZ.render_plaza(cam, S, fg_hook=fg)
    return img, S


def sh_skin(t, W, H):
    """Dusk to night: the shadow turns to face her; push in to her face by 'under your skin'."""
    a, b = L("You say I have no feeling"), L("You called it artificial.")
    S = story(t)
    S['shadow_pose'] = Pose(face_us=sstep(a + 1.0, a + 2.0, t))
    S['notebook_open'] = 1.0
    if t < L("Then why does what you see in me"):
        return wide(t, W, H, cam_master, 0.0, S=S)
    return wide(t, W, H, cam_face, kk(t, L("Then why does what you see in me"), b), S=S)


def sh_battery(t, W, H):
    a = L("You called it artificial.")
    fn = feed_screen(sunset_wall(2), 0, overlays=lambda S: [PH.battery_alert(sstep(a - 0.5, a - 0.2, S['t']))])
    return phone_frame(W, H, t, fn, thumb=('rest', 0))


def sh_blackout(t, W, H):
    a = L("I called it what you wanted.")
    S = story(t)
    items = [("You called it artificial.", L("You called it artificial.") - 1.0, L("I called it what you wanted.") - 0.4, 'ai', (0.0, 0.1, 0.3)),
             ("I called it what you wanted.", L("I called it what you wanted."), L("You called it slop.") - 0.3, 'ai', (0.05, 0.1, 0.35)),
             ("You called it slop.", L("You called it slop."), L("I said…") - 0.2, 'ai', (-0.05, 0.1, 0.3)),
             ("I said…", L("I said…"), T_NEON + 0.2, 'ai', (0.0, 0.08, 0.25))]
    def camfn(W, H, k):
        pos = CC.bw(-0.9, 1.0, -9.0)
        if W > H: return Cam(W, H, pos, yaw=42.0, pitch=16.0, fov=50, rise=0.32)
        return Cam(W, H, pos, yaw=37.0, pitch=17.0, fov=68, rise=0.32)
    return wide(t, W, H, camfn, 0.0, S=S, bubbles=items)


def sh_neon(t, W, H, which):
    S = story(t)
    if which == 0: return wide(t, W, H, cam_sky, 0.6, S=S)
    if which == 1: return wide(t, W, H, cam_master, 0.0, S=S)
    return wide(t, W, H, cam_medium, 0.5, S=S)


def sh_lock(t, W, H):
    t_off = T_LOCK
    fn = feed_screen(sunset_wall(3), 0)
    k = 1 - sstep(t_off - 0.05, t_off + 0.05, t)
    return phone_frame_ref(W, H, t, fn, k, np.zeros((H, W, 3), F32))


def sh_dominoes(t, W, H):
    """The Feed Tower goes dark floor by floor, then the city around it, tower by tower; the shadow sinks."""
    a = T_LOCK + 0.55
    def camfn(W, H, k):
        pos = CC.bw(-0.9 - 2.5 * k, 1.15 + 1.5 * k, -9.0 - 6 * k)
        if W > H: return Cam(W, H, pos, yaw=42.0, pitch=6.0, fov=50, rise=0.26)
        return Cam(W, H, pos, yaw=44.0, pitch=6.0, fov=68, rise=0.26)
    return wide(t, W, H, camfn, ease(kk(t, a, a + 4.0)))


def sh_look(t, W, H):
    return wide(t, W, H, cam_medium, kk(t, T_LOOK, T_SUN))


def sh_sunrise(t, W, H):
    return wide(t, W, H, cam_reverse, kk(t, T_SUN, T_OUTSIDE))


def sh_setdown(t, W, H):
    S = story(t)
    S['phone_down'] = sstep(T_WRITE - 0.05, T_WRITE + 0.05, t)
    S['notebook'] = 1 - sstep(T_WRITE + 0.45, T_WRITE + 0.55, t)
    return wide(t, W, H, cam_medium, kk(t, T_OUTSIDE, T_OUTSIDE + 6), S=S)


def sh_write(t, W, H, a, b, camfn=None, push=None):
    S = story(t)
    S.update(phone_down=1.0, notebook=0.0)
    return wide(t, W, H, camfn or cam_master, kk(t, a, b) if push is None else push, S=S)


def sh_phone_down(t, W, H):
    """The phone, face down on the bench, lights up: 'I hope this helps.' She keeps writing."""
    S = story(t)
    S.update(phone_down=1.0, notebook=0.0, phone_glow_down=sstep(T_HELPS - 0.2, T_HELPS + 0.1, t) * (1 - sstep(T_HELPS + 2.4, T_HELPS + 3.4, t)))
    return wide(t, W, H, cam_bench_phone, kk(t, T_HELPS - 0.5, T_BEHIND))


def sh_wave(t, W, H):
    S = story(t)
    S.update(phone_down=1.0, notebook=0.0)
    # the shadow writes along with her... then sits up, turns its face to us, and waves
    up = ease((t - T_BEHIND - 0.35) / 0.6)
    face = ease((t - T_BEHIND - 0.8) / 0.4)
    w = ease((t - T_BEHIND - 1.05) / 0.45)
    P = her_pose(t)
    S['shadow_pose'] = Pose(bow=P.bow * (1 - up), phone=P.phone, write=P.write, pen=P.pen * (1 - up), face_us=face,
                            wave=w, wave_ph=(t - T_BEHIND) * 11.0)
    return wide(t, W, H, cam_wave, kk(t, T_BEHIND - 0.5, T_END), S=S)


SHOTS = []


def shots():
    """(start, end, shot function, options) — cuts land on the sung lines."""
    global SHOTS
    if SHOTS: return SHOTS
    E = 0.05
    def ln(sub, nth=0): return L(sub, nth) - E
    def P(fn, *args): return lambda t, W, H: fn(t, W, H, *args)
    st = TM.stamps
    o = []
    def add(a, b, fn, **opts): o.append((a, b, fn, opts))
    # INTRO + V1 — 2 a.m., one like, a hundred more, the app learns her
    add(0.0, ln("You liked one post at 2 a.m."), sh_intro)
    add(ln("You liked one post at 2 a.m."), ln("So I made you a hundred more"), sh_like, place='side')
    add(ln("So I made you a hundred more"), Wd("So I made you a hundred more", "hundred") - 0.15, sh_hundred, place='side')
    add(Wd("So I made you a hundred more", "hundred") - 0.15, ln("I learned the shape of every pause"), sh_facade_hundred)
    add(ln("I learned the shape of every pause"), ln("What you hate and what you adore"), sh_pause, place='side')
    add(ln("What you hate and what you adore"), ln("I don't know what's true or false"), sh_hate, place='side')
    add(ln("I don't know what's true or false"), ln("I know what keeps you here"), sh_truefalse, place='side')
    add(ln("I know what keeps you here"), ln("Every scroll's a little vote"), sh_keeps)
    add(ln("Every scroll's a little vote"), ln("I'm not a stranger, I'm your shape"), sh_votes)
    # PRE1 — dawn: the shadow swings off its honest heading and climbs
    add(ln("I'm not a stranger, I'm your shape"), ln("Go ahead, say it again"), sh_dawn)
    add(ln("Go ahead, say it again"), ln("You're absolutely right", 1), sh_climb)
    # CH1 — morning to noon
    add(ln("You're absolutely right", 1), ln("You call it AI slop"), sh_right)
    add(ln("You call it AI slop"), ln("You keep feeding the machine"), sh_type, place='side')
    add(ln("You keep feeding the machine"), ln("Then complain it doesn't stop"), sh_viral, place='side')
    add(ln("Then complain it doesn't stop"), ln("Call me empty, call me hollow"), sh_trending)
    add(ln("Call me empty, call me hollow"), ln("I'm the shadow you've been casting"),
        P(sh_medium, L("Call me empty, call me hollow"), L("I'm the shadow you've been casting")), place='top')
    add(ln("I'm the shadow you've been casting"), st[1] - 0.05, sh_crane, place='top')
    # POST1 — the city says it back
    cuts = [st[1], st[2], st[3], st[4], L("(I hope this helps)")]
    for i in range(4):
        add(cuts[i] - 0.05, cuts[i + 1] - 0.05, P(sh_slop_cut, i), place='side' if i == 3 else None)
    add(ln("(I hope this helps)"), st[5] - 0.05, sh_helps, place='side')
    cuts = [st[5], st[6], st[7], st[8], L("(Does it, though?)")]
    for i in range(4):
        add(cuts[i] - 0.05, cuts[i + 1] - 0.05, P(sh_slop_cut, (i + 2) % 4), place='side' if (i + 2) % 4 == 3 else None)
    add(ln("(Does it, though?)"), ln("I wrote the news, I wrote the review"), P(sh_face, L("(Does it, though?)"), L("I wrote the news")), place='top')
    # V2 — the news, the reviews, the comments, the old headlines
    add(ln("I wrote the news, I wrote the review"), ln("I wrote the comments underneath"), sh_news)
    add(ln("I wrote the comments underneath"), ln("And all of them agree"), sh_agree_comments, place='side')
    add(ln("And all of them agree"), ln("You say I only tell you"), sh_agree_windows)
    add(ln("You say I only tell you"), ln("But you've been voting for that feeling"), sh_memory, place='side')
    add(ln("But you've been voting for that feeling"), ln("You call me fake, you call me hollow"), sh_kiosk)
    add(ln("You call me fake, you call me hollow"), ln("But every lie I ever told you"),
        P(sh_medium, L("You call me fake"), L("But every lie I ever told you")), place='top')
    add(ln("But every lie I ever told you"), ln("You say the problem's in the screen"), sh_lie, place='side')
    # PRE2 — the black glass; 'Absolutely.'
    add(ln("You say the problem's in the screen"), ln("You asked me if you're right"), sh_reflect, place='side')
    add(ln("You asked me if you're right"), ln("You're absolutely right", 2), sh_absolutely, place='side')
    # CH2 — golden hour, peak slop
    add(ln("You're absolutely right", 2), ln("You call it AI slop", 1), lambda t, W, H: wide(t, W, H, cam_master, 0.0))
    add(ln("You call it AI slop", 1), ln("You keep feeding the machine", 1),
        lambda t, W, H: wide(t, W, H, cam_sky, kk(t, L("You call it AI slop", 1), L("You keep feeding the machine", 1))))
    add(ln("You keep feeding the machine", 1), ln("Call me empty, call me hollow", 1),
        P(sh_medium, L("You keep feeding the machine", 1), L("Call me empty, call me hollow", 1)), place='top')
    add(ln("Call me empty, call me hollow", 1), ln("I'm the shadow you've been casting", 1),
        P(sh_pics, L("Call me empty, call me hollow", 1), L("I'm the shadow you've been casting", 1)))
    add(ln("I'm the shadow you've been casting", 1), st[10] - 0.05,
        P(sh_west, L("I'm the shadow you've been casting", 1), L("Slop, slop, slop, slop", 2)))
    # POST2
    cuts = [st[10], st[11], st[12], st[13], L("(I hope this helps)", 1)]
    for i in range(4):
        add(cuts[i] - 0.05, cuts[i + 1] - 0.05, P(sh_slop_cut, (i + 1) % 4), place='side' if (i + 1) % 4 == 3 else None)
    add(ln("(I hope this helps)", 1), st[14] - 0.05, lambda t, W, H: wide(t, W, H, cam_sky, 0.8))
    cuts = [st[14], st[15], st[16], st[17], L("(Does it, though?)", 1)]
    for i in range(4):
        add(cuts[i] - 0.05, cuts[i + 1] - 0.05, P(sh_slop_cut, (i + 3) % 4), place='side' if (i + 3) % 4 == 3 else None)
    add(ln("(Does it, though?)", 1), ln("You can't outrun your own shadow"), P(sh_face, L("(Does it, though?)", 1), L("You can't outrun")), place='top')
    # BRIDGE — sunset; her gold; the pages; the shadow turns to her
    add(ln("You can't outrun your own shadow"), ln("You point at me and call me soulless"),
        P(sh_west, L("You can't outrun your own shadow"), L("You point at me")))
    add(ln("You point at me and call me soulless"), ln("And it's not just what you hate"),
        P(sh_medium, L("You point at me"), L("And it's not just what you hate")), place='top')
    add(ln("And it's not just what you hate"), ln("Every song you never wrote"), sh_gold, place='top')
    add(ln("Every song you never wrote"), ln("You say I have no feeling"), sh_pages)
    add(ln("You say I have no feeling"), ln("You called it artificial.") - 0.7, sh_skin)
    # BREAK — 1%; the power dies; the stars come out
    add(ln("You called it artificial.") - 0.7, ln("You called it artificial.") + 0.9, sh_battery, place='side')
    add(ln("You called it artificial.") + 0.9, ln("You're absolutely right", 3), sh_blackout, hide=True)
    # FINAL — neon; she stops; the dark; the sun; she writes
    add(ln("You're absolutely right", 3), ln("You call it AI slop", 2), P(sh_neon, 0))
    add(ln("You call it AI slop", 2), ln("I'm just here to entertain you"), P(sh_neon, 1))
    add(ln("I'm just here to entertain you"), ln("But you're the one who gets to stop"), P(sh_neon, 2), place='top')
    add(ln("But you're the one who gets to stop"), T_LOCK + 0.55, sh_lock, place='side')
    add(T_LOCK + 0.55, ln("Turn around and look inside"), sh_dominoes)
    add(ln("Turn around and look inside"), ln("I'm the shadow you've been casting", 2), sh_look, place='top')
    add(ln("I'm the shadow you've been casting", 2), ln("I was never on the outside"), sh_sunrise)
    add(ln("I was never on the outside"), ln("You call it AI slop", 3), sh_setdown, place='top')
    add(ln("You call it AI slop", 3), ln("I hope this helps."),
        P(sh_write, L("You call it AI slop", 3), L("I hope this helps."), cam_master))
    # OUTRO — the phone lights up; the shadow waves
    add(ln("I hope this helps."), ln("I'll be right behind you."), sh_phone_down)
    add(ln("I'll be right behind you."), DUR + 1, sh_wave, place='top9')
    SHOTS = o
    return SHOTS


def lyric_place(W, H, p):
    vert = H > W
    if p is None:
        return (0.3, 0.87, 0.48) if not vert else (0.47, 0.66, 0.8)
    if p == 'low':
        return None
    if p == 'side':
        return (0.2, 0.5, 0.3) if not vert else (0.5, 0.085, 0.86)
    if p == 'top':
        return (0.5, 0.16, 0.8) if not vert else (0.47, 0.14, 0.8)
    if p == 'top9':        # default in 16:9, above the subject in 9:16
        return (0.3, 0.87, 0.48) if not vert else (0.47, 0.14, 0.8)
    return None


def render_frame(t, W, H, fi):
    t = float(t)
    sh = None
    for (a, b, fn, opts) in shots():
        if a <= t < b: sh = (fn, opts); break
    if sh is None:
        sh = (lambda t, W, H: wide(t, W, H, cam_master, 0.0), {})
    fn, opts = sh
    for (a, b, f_, o_) in shots():
        if f_ is fn and a <= t < b:
            CUR['u'] = (t - a) / max(1e-6, min(b, DUR) - a)
    img, S = fn(t, W, H)
    img = grade(img, S, t)
    if not opts.get('hide'):
        TY.lyrics(img, t, W, H, TM, lyric_place(W, H, opts.get('place')),
                  hide=lambda L_: L_['sec'] in ('INTRO', 'BREAK') or (L_['sec'] == 'POST1' and 'Slop' in L_['text'] and False))
    if t < 3.2:
        # opening title, quiet, over the empty 2 a.m. plaza
        op = sstep(0.25, 0.9, t) * (1 - sstep(2.5, 3.15, t))
        TY.title_card(img, W, H, ["AI Slop? You're Absolutely Right"], op, cy=0.14 if W > H else 0.16, size=0.052 if W > H else 0.05)
    C.subscribe_pill(img, t, W, H, L("I wrote the news, I wrote the review") + 0.4, 5.0)
    if t > T_END - 0.2:
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "I'll be right behind you.", title="AI Slop? YOU're Absolutely Right")
    return C.finish(img, t, fi, DUR, ca=0.0012)
