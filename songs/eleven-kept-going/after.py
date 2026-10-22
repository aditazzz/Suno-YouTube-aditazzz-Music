"""After touchdown (the camera keeps looking DOWN): the booster standing in its smoke, Landing Zone 1 from straight
above with the ghosts of what didn't happen (no parachute, no ocean), one foot on the concrete, and the booster alone
on its lit circle with the coast, the moonlit sea and the stars on the horizon."""
import math
import numpy as np, cv2
import ekg as K
import rt, lz as Z, ground as G
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out

B_STAND = np.array([0.0, 4.32, 0.0], F32)          # base of the tank when standing on its legs
T_TOUCH = 196.56

def standing(t, W, H, u, st):
    """'It stood there in the smoke / Upright': a slow drone orbit from above, the booster bright under the floods,
    its smoke drifting off downwind across the scrub."""
    ang = math.radians(st.get("ang0", 35.0) + st.get("orbit", 14.0) * u)
    dist = st.get("dist", 150.0) - 20 * u; h = st.get("h", 58.0) - 6 * u
    eye = (math.sin(ang) * dist, h, math.cos(ang) * dist)
    return Z.render(t, W, H, dict(eye=eye, target=(0, st.get("ty", 17.0), 0), fov=st.get("fov", 38), B=tuple(B_STAND), legs=1.0, fins=1.0,
                                  soot=0.75, ts=t - T_TOUCH, scorch=1, smoke_dens=st.get("smoke", 0.8)))

def ghost_parachute(img, cam, k, top):
    """a white line drawing of a parachute over the booster (the way boosters used to come down), dissolving."""
    if k <= 0: return
    pts_all = []
    R = 26.0; hgt = 22.0; c = top + np.array([0, 34.0, 0], F32)
    n = 16
    rim = [c + np.array([math.cos(a) * R, -hgt * 0.35, math.sin(a) * R], F32) for a in np.linspace(0, 2 * math.pi, 97)]
    pts_all.append([cam.p1(p)[:2] for p in rim])
    for i in range(n):
        a = i * 2 * math.pi / n
        gore = [c + np.array([math.cos(a) * R * math.sin(v * math.pi / 2), hgt * 0.35 - hgt * 0.7 * (1 - math.cos(v * math.pi / 2)) - 0 * v,
                              math.sin(a) * R * math.sin(v * math.pi / 2)], F32) for v in np.linspace(0, 1, 24)]
        pts_all.append([cam.p1(p)[:2] for p in gore])
        pts_all.append([cam.p1(rim[int(i * 96 / n)])[:2], cam.p1(top)[:2]])        # suspension lines
    S = min(img.shape[:2]) / 1080
    for pts in pts_all:
        K.polyline_glow(img, pts, np.array([0.85, 0.9, 1.0], F32), width=1.6 * S, glow=3.0 * S, gain=0.55 * k, glow_gain=0.35)

def ghost_ocean(img, cam, k, t):
    """the sea that isn't there: rings of swell drawn in white line around the booster, spreading and fading."""
    if k <= 0: return
    S = min(img.shape[:2]) / 1080
    for j in range(7):
        rr = 10.0 + j * 9.0 + (t * 6.0) % 9.0
        a_ = k * math.exp(-j * 0.25) * (1 - ((t * 6.0) % 9.0) / 9.0 * (j == 6))
        pts = []
        for a in np.linspace(0, 2 * math.pi, 140):
            wob = 1.2 * math.sin(a * 7 + j + t * 0.8)
            pts.append(cam.p1((math.cos(a) * (rr + wob), 0.3, math.sin(a) * (rr + wob)))[:2])
        K.polyline_glow(img, pts, np.array([0.80, 0.88, 1.0], F32), width=1.4 * S, glow=3.0 * S, gain=0.45 * a_, glow_gain=0.3)

def topdown(t, W, H, u, st):
    """'Landing Zone One / No parachute / No ocean': straight down from above the booster, rising slowly; the ghosts
    of a parachute and of the sea appear on their words and dissolve."""
    h = lerp(st.get("h0", 120.0), st.get("h1", 150.0), ease_io(u))
    ang = math.radians(lerp(130.0, 145.0, u))
    eye = (math.sin(ang) * h * 0.62, h, math.cos(ang) * h * 0.62)
    img, cam = Z.render(t, W, H, dict(eye=eye, target=(0, 22, 0), fov=st.get("fov", 46), roll=st.get("roll", 0.0),
                                      B=tuple(B_STAND), legs=1.0, fins=1.0, soot=0.75, ts=t - T_TOUCH, scorch=1, smoke_dens=0.55))
    top = B_STAND + np.array([0, K.L_S1 + K.L_INT, 0], F32)
    gp = st.get("para", 0.0); go = st.get("ocean", 0.0)
    ghost_parachute(img, cam, gp, top)
    ghost_ocean(img, cam, go, t)
    return img, cam

def foot(t, W, H, u, st):
    """'Just concrete / Under its feet': one foot pad resting on the scorched concrete, looking down at it."""
    tipdir = np.array([1.0, 0, 0], F32)                     # leg 0 points east (+x)
    foot_p = tipdir * (K.R_BODY + 0.18 + 9.85 * math.sin(math.radians(118))) + np.array([0, 0.2, 0], F32)
    side = np.array([-tipdir[2], 0, tipdir[0]], F32)
    eye = foot_p + tipdir * lerp(6.0, 4.8, u) + side * lerp(-2.0, 1.2, u) + np.array([0, lerp(5.2, 4.2, u), 0], F32)
    tgt = foot_p - tipdir * 1.6 + np.array([0, 0.6, 0], F32)
    img, cam = Z.render(t, W, H, dict(eye=tuple(eye), target=tuple(tgt), fov=st.get("fov", 48), B=tuple(B_STAND), legs=1.0, fins=1.0,
                                      soot=0.8, ts=t - T_TOUCH, scorch=1, smoke_dens=0.35))
    return img, cam

def alone(t, W, H, u, st):
    """'Like it had somewhere to be tomorrow': far and high, the lit circle, the booster a white needle on it, the coast,
    the moonlit sea, stars on the horizon. Looking down."""
    ang = math.radians(lerp(338.0, 346.0, u))                 # north-north-west of the pad, looking south over it to the towns
    dist = lerp(430.0, 400.0, u); h = lerp(125.0, 115.0, u)
    eye = np.array([math.sin(ang) * dist, h, math.cos(ang) * dist], F32)
    tgt = np.array([0, 10.0, 0], F32) + np.array([math.sin(ang), 0, math.cos(ang)], F32) * -260.0
    cam = K.Cam(eye, tgt, W, H, fov=st.get("fov", 40), up=(0, 1, 0))
    img, hit = G.view(cam, W, H, t, dict(moon=1.0, lights=1.0, clouds=0.15, cloud_alt=2200, stars=0.5, lz=1.0, scorch=1, haze=0.8))
    L = Z.pad_lights(1.0, 0.0, (0, 0, 0), at=tuple(B_STAND + np.array([0, 20.0, 0], F32)))
    rt.draw_vehicle(img, cam, B_STAND, None, L, stage="booster", legs=1.0, fins=1.0, soot=0.75, ss=3)
    Z.touchdown_smoke(img, cam, t, t - T_TOUCH, 1.0, 0.0, dens=0.5)
    return img, cam
