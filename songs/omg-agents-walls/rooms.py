"""The house: every CCTV camera's room, built from boxes/rects/ellipsoids in metres.
Each room() returns (prims, cams, lights, writable) where cams = {"16x9": Cam, "9x16": Cam}.
x = right, y = up, z = away from the camera wall. Floor y = 0."""
import math
import numpy as np
from engine import Rect, Poly, Ell, Cyl, box, Cam, noise, samp

def N(): return noise()

# ------------------------------------------------------------------ IR materials (albedo in near-infrared)
def plaster(base=0.60, amp=0.06):
    def f(u, v, P):
        n = N(); return base + amp * (samp(n["fbm"], u, v, 90) - 0.5) + 0.05 * (samp(n["low"], u, v, 25) - 0.5)
    return f
def wallpaper(base=0.56):
    def f(u, v, P):
        n = N(); s = 0.5 + 0.5 * np.cos(u * 2 * math.pi / 0.16)
        return base + 0.05 * s + 0.04 * (samp(n["fbm"], u, v, 80) - 0.5) + 0.04 * (samp(n["low"], u, v, 20) - 0.5)
    return f
def wood(base=0.42, plank=0.16, axis=0):
    def f(u, v, P):
        n = N(); a = P[..., 0] if axis == 0 else P[..., 2]; b = P[..., 2] if axis == 0 else P[..., 0]
        k = np.floor(a / plank); r = (np.sin(k * 12.9898) * 43758.5453) % 1.0
        seam = np.abs(((a / plank) % 1.0) - 0.5) > 0.47
        off = (np.sin(k * 7.13) * 91.7) % 1.0 * 1.3; seam2 = (((b + off) / 1.3) % 1.0) < 0.012
        grain = samp(n["fine"], a * 0.2, b * 3.0, 200) - 0.5
        return base + 0.10 * (r - 0.5) + 0.05 * grain - 0.16 * seam - 0.12 * seam2
    return f
def carpet(base=0.48, amp=0.10):
    def f(u, v, P):
        n = N(); return base + amp * (samp(n["fine"], u, v, 400) - 0.5) + 0.04 * (samp(n["fbm"], u, v, 40) - 0.5)
    return f
def fabric(base=0.50):
    def f(u, v, P):
        n = N(); return base + 0.07 * (samp(n["fine"], u, v, 300) - 0.5) + 0.05 * (samp(n["fbm"], u, v, 30) - 0.5)
    return f
def concrete(base=0.40):
    def f(u, v, P):
        n = N(); st = samp(n["low"], u, v, 8)
        return base + 0.10 * (samp(n["fbm"], u, v, 50) - 0.5) - 0.10 * np.clip(st - 0.6, 0, 1) * 3 + 0.04 * (samp(n["fine"], u, v, 500) - 0.5)
    return f
def blocks(base=0.46):
    def f(u, v, P):
        n = N(); row = np.floor(v / 0.2); uu = u + (row % 2) * 0.2
        mort = ((uu % 0.4) < 0.012) | ((v % 0.2) < 0.012)
        k = np.floor(uu / 0.4) + row * 17; r = (np.sin(k * 12.9898) * 43758.5453) % 1.0
        return base + 0.06 * (r - 0.5) + 0.08 * (samp(n["fbm"], u, v, 60) - 0.5) - 0.13 * mort
    return f
def panel_door(base=0.62, W=0.9, H=2.05):
    def f(u, v, P):
        inset = np.zeros_like(u)
        for (a, b, c, d) in ((0.12, 1.15, W - 0.12, H - 0.15), (0.12, 0.15, W - 0.12, 1.0)):
            e = 0.025
            edge = ((np.abs(u - a) < e) | (np.abs(u - c) < e)) & (v > b) & (v < d) | ((np.abs(v - b) < e) | (np.abs(v - d) < e)) & (u > a) & (u < c)
            inset = np.maximum(inset, edge.astype(np.float32))
        n = N(); return base - 0.18 * inset + 0.03 * (samp(n["fbm"], u, v, 60) - 0.5)
    return f
def framed(seed, base=0.25):
    def f(u, v, P):
        n = N(); U = u.max() + 1e-6 if u.size else 1; V = v.max() + 1e-6 if v.size else 1
        border = (u < 0.035) | (v < 0.035) | (u > U - 0.035) | (v > V - 0.035)
        img = 0.35 + 0.45 * samp(n["low"], u + seed, v, 7) + 0.1 * (samp(n["fbm"], u + seed, v, 30) - 0.5)
        return np.where(border, 0.18, img)
    return f
def blinds_emit(level=1.1, slat=0.075):
    def f(u, v, P):
        gap = ((v % slat) / slat) > 0.62
        n = N(); return level * (0.25 + 0.75 * gap) * (0.85 + 0.3 * samp(n["low"], u, v, 3))
    return f
def const(x): return x

def heat_const(h): return h

# ------------------------------------------------------------------ helpers
def room_shell(RW, RH, RD, wall_mat, floor_mat, ceil=0.68, write=None, ppm=200, skip=()):
    """Inside of a box room. write: dict wall -> True to make it writable (atlas assigned later)."""
    w = write or {}
    P = []
    if "back" not in skip: P.append(Rect((0, 0, RD), (RW, 0, 0), (0, RH, 0), wall_mat, 0.22, name="back"))
    if "left" not in skip: P.append(Rect((0, 0, 0), (0, 0, RD), (0, RH, 0), wall_mat, 0.22, name="left"))
    if "right" not in skip: P.append(Rect((RW, 0, RD), (0, 0, -RD), (0, RH, 0), wall_mat, 0.22, name="right"))
    if "front" not in skip: P.append(Rect((RW, 0, 0), (-RW, 0, 0), (0, RH, 0), wall_mat, 0.22, name="front"))
    P.append(Rect((0, 0, 0), (RW, 0, 0), (0, 0, RD), floor_mat, 0.26, name="floor"))
    P.append(Rect((0, RH, RD), (RW, 0, 0), (0, 0, -RD), ceil, 0.24, name="ceil"))
    for p in P:
        p.ppm = ppm
        if w.get(p.name): p.write = True
    return P

def baseboards(RW, RD, h=0.09, d=0.015, mat=0.70):
    out = []
    out += box(0, 0, RD - d, RW, h, RD, mat, 0.22, faces="F")
    out += box(0, 0, 0, d, h, RD, mat, 0.22, faces="R")
    out += box(RW - d, 0, 0, RW, h, RD, mat, 0.22, faces="L")
    return out

def assign_atlas(prims, max_w=4096):
    """Give every writable rect a slot in the camera's wall atlas (shelf packing). Returns (aw, ah, slots)."""
    x = y = rowh = 0; aw = 0; slots = {}
    for p in prims:
        if p.write is not True and not (isinstance(p.write, tuple)): continue
        w = int(math.ceil(p.U * p.ppm)) + 4; h = int(math.ceil(p.V * p.ppm)) + 4
        if x + w > max_w: x = 0; y += rowh; rowh = 0
        p.write = (x + 2, y + 2); slots[p.name] = (x + 2, y + 2, w - 4, h - 4, p)
        x += w; rowh = max(rowh, h); aw = max(aw, x)
    return aw, y + rowh, slots

# ================================================================== CAM 01 — LIVING ROOM
def living():
    RW, RH, RD = 5.2, 2.6, 6.0
    P = room_shell(RW, RH, RD, wallpaper(0.57), wood(0.40, axis=0), write={"back": True, "left": True, "right": True}, ppm=190)
    P += baseboards(RW, RD)
    # window with blinds (back wall, left of centre) + sill + frame
    P.append(Rect((0.85, 0.95, RD - 0.01), (1.55, 0, 0), (0, 1.15, 0), 0.05, 0.08, emit=blinds_emit(0.95), name="window"))
    P += box(0.78, 0.90, RD - 0.10, 2.47, 0.95, RD, 0.75, 0.2, faces="TF")          # sill
    P += box(0.80, 2.10, RD - 0.03, 2.45, 2.16, RD, 0.7, 0.2, faces="FB")           # head trim
    # TV on a console, right of the window
    P += box(3.05, 0.0, RD - 0.48, 4.95, 0.56, RD, 0.30, 0.3, faces="TFLR", name="console")
    P += box(3.25, 0.62, RD - 0.12, 4.75, 1.48, RD - 0.06, 0.07, 0.35, faces="FLRT", name="tvbody")
    P.append(Rect((3.29, 0.66, RD - 0.121), (1.42, 0, 0), (0, 0.78, 0), 0.05, 0.3, name="tv"))
    P += box(3.9, 0.56, RD - 0.25, 4.1, 0.62, RD - 0.1, 0.2, 0.3, faces="TF")       # stand
    # floor lamp, back-left corner
    P += box(0.40, 0.0, RD - 0.55, 0.44, 1.55, RD - 0.51, 0.25, 0.2, faces="FLR")
    P.append(Ell((0.42, 1.68, RD - 0.53), (0.24, 0.20, 0.24), 0.72, 0.25, name="shade", cut_y=1.52))
    # sofa along the right wall facing left (back against the wall)
    sx0 = RW - 0.95
    P += box(sx0, 0.0, 2.0, RW - 0.05, 0.46, 4.4, fabric(0.52), 0.3, faces="TFLK", name="sofa")
    P += box(RW - 0.30, 0.46, 2.0, RW - 0.05, 0.95, 4.4, fabric(0.50), 0.3, faces="TFLK", name="sofaback")
    P += box(sx0, 0.46, 2.0, RW - 0.30, 0.66, 2.22, fabric(0.54), 0.3, faces="TFLK")
    P += box(sx0, 0.46, 4.18, RW - 0.30, 0.66, 4.4, fabric(0.54), 0.3, faces="TFLK")
    P.append(Ell((RW - 0.55, 0.62, 2.75), (0.18, 0.15, 0.30), fabric(0.62), 0.3))       # cushions
    P.append(Ell((RW - 0.55, 0.62, 3.55), (0.18, 0.15, 0.30), fabric(0.60), 0.3))
    # coffee table + rug
    P += box(2.30, 0.36, 2.85, 3.45, 0.42, 3.85, 0.36, 0.25, faces="TFLR")
    for (lx, lz) in ((2.36, 2.9), (3.36, 2.9), (2.36, 3.76), (3.36, 3.76)):
        P += box(lx, 0, lz, lx + 0.05, 0.36, lz + 0.05, 0.3, 0.25, faces="FLR")
    P.append(Rect((1.55, 0.004, 2.1), (2.6, 0, 0), (0, 0, 2.6), carpet(0.55), 0.27, name="rug"))
    # door on the left wall (closed) + frame
    P.append(Rect((0.006, 0, 4.45), (0, 0, -0.9), (0, 2.05, 0), panel_door(0.6), 0.22, name="door"))
    P += box(0, 2.05, 3.5, 0.03, 2.13, 4.5, 0.75, 0.2, faces="RB")
    # two frames on the left wall
    P.append(Rect((0.008, 1.35, 2.6), (0, 0, -0.55), (0, 0.42, 0), framed(1.3), 0.22, name="frame1"))
    P.append(Rect((0.008, 1.25, 1.75), (0, 0, -0.45), (0, 0.6, 0), framed(4.1), 0.22, name="frame2"))
    # outlet near the TV
    P += box(2.75, 0.30, RD - 0.012, 2.83, 0.42, RD, 0.85, 0.2, faces="F")
    cams = {"16x9": Cam((0.30, 2.42, 0.25), (3.05, 0.95, 4.9), hfov=104, k=0.30),
            "9x16": Cam((1.10, 2.30, 0.45), (3.30, 0.30, 5.6), hfov=72, k=0.22)}
    lights = {"tv": ((4.0, 1.07, RD - 0.3), 1.6), "lamp": ((0.42, 1.6, RD - 0.53), 0.9)}
    return P, cams, lights

def tiles(base=0.55, size=0.40, grout=0.012):
    def f(u, v, P):
        n = N(); a = P[..., 0]; b = P[..., 2]
        g = ((a % size) < grout) | ((b % size) < grout)
        k = np.floor(a / size) * 7 + np.floor(b / size) * 13; r = (np.sin(k * 12.9898) * 43758.5453) % 1.0
        return base + 0.05 * (r - 0.5) + 0.04 * (samp(n["fbm"], a, b, 40) - 0.5) - 0.22 * g
    return f
def wall_tiles(base=0.66, size=0.15, grout=0.008):
    def f(u, v, P):
        g = ((u % size) < grout) | ((v % (size * 0.5)) < grout)
        return base - 0.2 * g
    return f
def cabinet(base=0.55, w=0.6):
    def f(u, v, P):
        n = N(); seam = (u % w) < 0.012
        inset = (((u % w) > 0.06) & ((u % w) < w - 0.06) & (((u % w) < 0.075) | ((u % w) > w - 0.075))) | \
                (((v > 0.06) & (v < 0.08)) | ((v > v.max() - 0.08) & (v < v.max() - 0.06)) if v.size else False)
        return base - 0.25 * seam - 0.10 * inset + 0.03 * (samp(n["fbm"], u, v, 60) - 0.5)
    return f
def plywood(base=0.50):
    def f(u, v, P):
        n = N(); a = P[..., 0]; b = P[..., 2]
        seam = ((a % 1.22) < 0.01) | ((b % 2.44) < 0.01)
        return base + 0.10 * (samp(n["fine"], a * 0.3, b * 2.0, 150) - 0.5) + 0.06 * (samp(n["low"], a, b, 6) - 0.5) - 0.18 * seam
    return f
def insul(base=0.62):
    def f(u, v, P):
        n = N(); return base + 0.18 * (samp(n["fbm"], u, v, 30) - 0.5) + 0.1 * (samp(n["fine"], u, v, 200) - 0.5)
    return f
def asphalt(base=0.18):
    def f(u, v, P):
        n = N(); a = P[..., 0]; b = P[..., 2]
        dash = (np.abs(b - 11.5) < 0.07) & ((a % 6.0) < 3.0)
        return base + 0.05 * (samp(n["fine"], a, b, 60) - 0.5) + 0.35 * dash
    return f
def grass(base=0.55):
    def f(u, v, P):
        n = N(); a = P[..., 0]; b = P[..., 2]
        return base + 0.15 * (samp(n["fine"], a, b, 40) - 0.5) + 0.10 * (samp(n["low"], a, b, 2) - 0.5)
    return f
def siding(base=0.52, pitch=0.2):
    def f(u, v, P):
        n = N(); lap = ((v % pitch) / pitch) ** 0.6
        return base * (0.8 + 0.2 * lap) + 0.03 * (samp(n["fbm"], u, v, 20) - 0.5)
    return f
def shingles(base=0.30):
    def f(u, v, P):
        n = N(); row = np.floor(v / 0.25); uu = u + (row % 2) * 0.2
        g = ((uu % 0.4) < 0.02) | ((v % 0.25) < 0.03)
        return base + 0.08 * (samp(n["fbm"], u, v, 15) - 0.5) - 0.10 * g
    return f

def door_frame(x, z0, z1, side, RW=0, h=2.05, d=0.02, w=0.07, mat=0.74):
    """Casing around a door on a side wall (x = 0 left wall faces +x; side='L' or 'R')."""
    out = []
    if side == "L":
        out += box(0, 0, z0 - w, d, h + w, z0, mat, 0.2, faces="R")
        out += box(0, 0, z1, d, h + w, z1 + w, mat, 0.2, faces="R")
        out += box(0, h, z0, d, h + w, z1, mat, 0.2, faces="R")
    else:
        out += box(RW - d, 0, z0 - w, RW, h + w, z0, mat, 0.2, faces="L")
        out += box(RW - d, 0, z1, RW, h + w, z1 + w, mat, 0.2, faces="L")
        out += box(RW - d, h, z0, RW, h + w, z1, mat, 0.2, faces="L")
    return out

# ================================================================== CAM 02 — HALLWAY
def hallway():
    RW, RH, RD = 1.4, 2.5, 8.0
    P = room_shell(RW, RH, RD, plaster(0.62), wood(0.42, plank=0.14, axis=0), write={"back": True, "left": True, "right": True}, ppm=170)
    P += box(0, 0, 0, 0.015, 0.09, RD, 0.72, 0.2, faces="R") + box(RW - 0.015, 0, 0, RW, 0.09, RD, 0.72, 0.2, faces="L")
    P.append(Rect((0.38, 0.004, 0.5), (0.64, 0, 0), (0, 0, 7.0), carpet(0.50, 0.12), 0.27, name="runner"))
    # doors: left wall z 2.0-2.9 and 5.2-6.1; right wall z 3.4-4.3 (this one opens later)
    P.append(Rect((0.006, 0, 2.9), (0, 0, -0.9), (0, 2.05, 0), panel_door(0.60), 0.22, name="door_l1"))
    P.append(Rect((0.006, 0, 6.1), (0, 0, -0.9), (0, 2.05, 0), panel_door(0.60), 0.22, name="door_l2"))
    P.append(Rect((RW - 0.006, 0, 3.4), (0, 0, 0.9), (0, 2.05, 0), panel_door(0.60), 0.22, name="door_r1"))
    P += door_frame(0, 2.0, 2.9, "L") + door_frame(0, 5.2, 6.1, "L") + door_frame(0, 3.4, 4.3, "R", RW=RW)
    for z in (2.85, 6.05): P.append(Ell((0.05, 0.98, z - 0.06), (0.03, 0.03, 0.03), 0.8, 0.2))
    P.append(Ell((RW - 0.05, 0.98, 3.46), (0.03, 0.03, 0.03), 0.8, 0.2))
    # end window with blinds
    P.append(Rect((0.35, 0.95, RD - 0.01), (0.7, 0, 0), (0, 1.15, 0), 0.05, 0.08, emit=blinds_emit(0.85), name="window"))
    P += box(0.30, 0.90, RD - 0.08, 1.10, 0.95, RD, 0.75, 0.2, faces="TF")
    # frames on the right wall, a switch plate, a ceiling light, the dome camera at the far end
    P.append(Rect((RW - 0.008, 1.30, 1.0), (0, 0, 0.5), (0, 0.38, 0), framed(2.2), 0.22, name="frame1"))
    P.append(Rect((RW - 0.008, 1.25, 5.4), (0, 0, 0.6), (0, 0.45, 0), framed(5.5), 0.22, name="frame2"))
    P += box(RW - 0.012, 1.15, 0.55, RW, 1.27, 0.63, 0.85, 0.2, faces="L")
    P.append(Ell((0.70, RH, 3.9), (0.20, 0.06, 0.20), 0.85, 0.2, cut_y=RH - 0.07))
    P.append(Ell((0.70, RH, 7.55), (0.11, 0.09, 0.11), 0.22, 0.45, name="dome", cut_y=RH - 0.10))
    P += box(0.55, RH - 0.02, 7.40, 0.85, RH, 7.70, 0.5, 0.3, faces="B")
    cams = {"16x9": Cam((0.70, 2.34, 0.15), (0.70, 1.05, 8.0), hfov=100, k=0.30),
            "9x16": Cam((0.70, 2.34, 0.15), (0.70, 0.95, 8.0), hfov=66, k=0.22)}
    lights = {"window": ((0.7, 1.5, RD - 0.2), 0.8)}
    return P, cams, lights

# ================================================================== CAM 03 — KITCHEN
def kitchen():
    RW, RH, RD = 4.2, 2.6, 4.4
    P = room_shell(RW, RH, RD, plaster(0.64), tiles(0.52), write={"back": True, "left": True, "right": True}, ppm=180)
    # base cabinets + counter along the back wall
    P += box(0.15, 0.0, RD - 0.62, 3.15, 0.86, RD, cabinet(0.55), 0.24, faces="TFLR", name="base")
    P += box(0.12, 0.86, RD - 0.65, 3.18, 0.91, RD, 0.70, 0.24, faces="TFLR", name="counter")
    P.append(Rect((0.15, 0.91, RD - 0.004), (3.0, 0, 0), (0, 0.5, 0), wall_tiles(0.66), 0.22, name="splash"))
    # window over the sink, upper cabinets left of it
    P.append(Rect((1.90, 1.20, RD - 0.01), (0.95, 0, 0), (0, 0.85, 0), 0.05, 0.08, emit=blinds_emit(0.75, 0.11), name="window"))
    P += box(0.15, 1.45, RD - 0.36, 1.75, 2.25, RD, cabinet(0.56, 0.4), 0.22, faces="FBLR", name="upper")
    P += box(3.0, 1.45, RD - 0.36, 3.15, 2.25, RD, cabinet(0.56, 0.4), 0.22, faces="FBL")
    # microwave on the counter
    P += box(0.40, 0.91, RD - 0.48, 0.95, 1.22, RD - 0.12, 0.45, 0.35, faces="TFLR", name="microwave")
    P.append(Rect((0.43, 1.16, RD - 0.481), (0.36, 0, 0), (0, -0.22, 0), 0.08, 0.35, name="mwdoor"))
    # fridge (front face is writable: notes)
    P += box(3.30, 0.0, RD - 0.78, 4.15, 1.86, RD - 0.05, 0.78, 0.4, faces="TLR", name="fridge_side")
    fr = Rect((3.30, 0.0, RD - 0.78), (0.85, 0, 0), (0, 1.86, 0), cabinet(0.80, 0.85), 0.4, name="fridge")
    fr.write = True; fr.ppm = 900; P.append(fr)
    P += box(3.38, 1.05, RD - 0.80, 3.41, 1.55, RD - 0.78, 0.9, 0.3, faces="FLR")      # handle
    # table + 2 chairs
    P += box(1.30, 0.72, 1.35, 2.45, 0.77, 2.25, 0.40, 0.25, faces="TFLR", name="table")
    for (lx, lz) in ((1.35, 1.4), (2.35, 1.4), (1.35, 2.15), (2.35, 2.15)):
        P += box(lx, 0, lz, lx + 0.05, 0.72, lz + 0.05, 0.35, 0.25, faces="FLR")
    for cz in (1.1, 2.5):
        P += box(1.65, 0.0, cz - 0.2, 2.1, 0.46, cz + 0.2, 0.42, 0.25, faces="TFLR")
    P += box(1.65, 0.46, 0.85, 2.1, 0.95, 0.9, 0.42, 0.25, faces="FKLR")
    P += box(1.65, 0.46, 2.65, 2.1, 0.95, 2.7, 0.42, 0.25, faces="FKLR")
    # pendant light over the table
    P.append(Ell((1.88, RH, 1.8), (0.22, 0.07, 0.22), 0.80, 0.25, cut_y=RH - 0.08))
    cams = {"16x9": Cam((0.25, 2.42, 0.25), (2.55, 0.95, 4.1), hfov=102, k=0.30),
            "9x16": Cam((1.20, 2.40, 0.30), (2.55, 0.55, 4.2), hfov=70, k=0.22)}
    lights = {"window": ((2.4, 1.6, RD - 0.3), 0.7), "fridge": ((3.7, 1.0, RD - 1.0), 0.4)}
    return P, cams, lights

# ================================================================== CAM 04 — BEDROOM
def bedroom():
    RW, RH, RD = 4.2, 2.6, 4.8
    P = room_shell(RW, RH, RD, plaster(0.60), carpet(0.46, 0.08), write={"back": True, "left": True, "right": True}, ppm=180)
    P += baseboards(RW, RD)
    bx0, bx1 = 1.30, 2.90
    P += box(1.20, 0.0, RD - 0.09, 3.00, 1.20, RD, wood(0.40, 0.3), 0.25, faces="TFLR", name="headboard")
    P += box(bx0, 0.0, RD - 2.15, bx1, 0.46, RD - 0.09, 0.38, 0.25, faces="TFLR", name="frame")
    P += box(bx0 + 0.02, 0.46, RD - 2.12, bx1 - 0.02, 0.62, RD - 0.09, fabric(0.62), 0.3, faces="FLR", name="mattress")
    P += box(bx0 - 0.04, 0.58, RD - 2.16, bx1 + 0.04, 0.66, RD - 0.55, fabric(0.66), 0.35, faces="TFLR", name="duvet")
    for x in (1.72, 2.48):
        P.append(Ell((x, 0.70, RD - 0.33), (0.33, 0.10, 0.19), fabric(0.80), 0.35, name="pillow"))
    P.append(Ell((1.74, 0.66, RD - 1.30), (0.30, 0.17, 0.82), fabric(0.64), 0.95, name="sleeper1", cut_y=0.62))
    P.append(Ell((2.46, 0.66, RD - 1.25), (0.29, 0.15, 0.78), fabric(0.64), 0.95, name="sleeper2", cut_y=0.62))
    P.append(Ell((1.78, 0.79, RD - 0.47), (0.11, 0.10, 0.12), 0.40, 1.0, name="head1"))
    P.append(Ell((2.44, 0.78, RD - 0.45), (0.11, 0.10, 0.12), 0.36, 1.0, name="head2"))
    P += box(0.70, 0.0, RD - 0.50, 1.18, 0.58, RD - 0.05, wood(0.38, 0.5), 0.25, faces="TFLR", name="ns_l")
    P += box(3.02, 0.0, RD - 0.50, 3.50, 0.58, RD - 0.05, wood(0.38, 0.5), 0.25, faces="TFLR", name="ns_r")
    P.append(Cyl((3.26, 0, RD - 0.27), 0.06, 0.58, 0.76, 0.30, 0.45, name="speaker"))
    P += box(0.86, 0.58, RD - 0.32, 0.98, 0.592, RD - 0.12, 0.10, 0.4, faces="T", name="phone")
    P.append(Ell((0.94, 0.70, RD - 0.27), (0.10, 0.11, 0.10), 0.72, 0.3, cut_y=0.62))         # lamp
    # window on the right wall with curtains
    P.append(Rect((RW - 0.01, 0.95, 1.9), (0, 0, 1.25), (0, 1.15, 0), 0.05, 0.08, emit=blinds_emit(0.70, 0.09), name="window"))
    P += box(RW - 0.16, 0.3, 1.62, RW - 0.04, 2.3, 1.95, fabric(0.48), 0.24, faces="LFK")
    P += box(RW - 0.16, 0.3, 3.10, RW - 0.04, 2.3, 3.43, fabric(0.48), 0.24, faces="LFK")
    # dresser on the left wall
    P += box(0.0, 0.0, 1.0, 0.52, 0.95, 2.3, cabinet(0.48, 0.65), 0.24, faces="TRFK", name="dresser")
    cams = {"16x9": Cam((0.25, 2.42, 0.25), (2.25, 0.62, 3.9), hfov=100, k=0.30),
            "9x16": Cam((2.10, 2.38, 1.05), (2.10, 0.45, 4.3), hfov=76, k=0.22)}
    lights = {"window": ((RW - 0.3, 1.5, 2.55), 0.9), "phone": ((0.92, 0.62, RD - 0.22), 0.25)}
    return P, cams, lights

# ================================================================== CAM 05 — BASEMENT (the network)
SHELF_DX = 0.45
def basement():
    RW, RH, RD = 3.8, 2.25, 4.2
    P = room_shell(RW, RH, RD, blocks(0.46), concrete(0.40), ceil=0.30, write={"back": True, "left": True, "right": True}, ppm=170)
    P[0].ppm = 400
    for x in np.arange(0.2, RW, 0.41):                      # open joists
        P += box(x, RH - 0.24, 0, x + 0.05, RH, RD, wood(0.48, 0.3), 0.22, faces="BLR")
    # metal shelf with the network gear (right of the task board)
    DX = SHELF_DX
    sx0, sx1, sz0 = 1.15 + DX, 2.45 + DX, RD - 0.45
    for x in (sx0, sx1 - 0.03):
        P += box(x, 0, sz0, x + 0.03, 1.85, sz0 + 0.03, 0.62, 0.22, faces="FLR")
    for y in (0.15, 0.62, 1.10, 1.58):
        P += box(sx0, y, sz0, sx1, y + 0.025, RD - 0.02, 0.58, 0.22, faces="TFB")
    P += box(1.30 + DX, 1.125, RD - 0.38, 1.75 + DX, 1.24, RD - 0.12, 0.30, 0.55, faces="TFLR", name="router")
    for ax in (1.35, 1.70):
        P += box(ax + DX, 1.24, RD - 0.16, ax + DX + 0.012, 1.42, RD - 0.15, 0.25, 0.4, faces="FLR")
    P += box(1.85 + DX, 1.125, RD - 0.36, 2.30 + DX, 1.18, RD - 0.12, 0.35, 0.5, faces="TFLR", name="switch")
    P += box(1.40 + DX, 0.645, RD - 0.40, 1.80 + DX, 0.98, RD - 0.12, 0.28, 0.6, faces="TFLR", name="nas")
    P += box(1.95 + DX, 0.645, RD - 0.33, 2.25 + DX, 0.82, RD - 0.12, 0.40, 0.5, faces="TFLR", name="modem")
    P += box(1.30 + DX, 0.175, RD - 0.40, 2.30 + DX, 0.45, RD - 0.10, 0.36, 0.25, faces="TFLR", name="boxes")
    P += box(1.52 + DX, 1.24, RD - 0.03, 1.55 + DX, RH - 0.25, RD - 0.005, 0.2, 0.3, faces="FLR", name="cable")
    # water heater, pipes, stairs, high window
    P.append(Cyl((3.42, 0, RD - 0.42), 0.28, 0.0, 1.50, 0.70, 0.55, name="heater"))
    P += box(3.40, 1.50, RD - 0.44, 3.44, RH - 0.25, RD - 0.40, 0.6, 0.4, faces="FLR")
    P += box(0.0, RH - 0.33, 0.0, RW, RH - 0.29, 0.04, 0.6, 0.3, faces="B")
    P += box(0.6, RH - 0.40, 0.3, 0.64, RH - 0.36, RD, 0.62, 0.3, faces="BLR")
    for k in range(8):
        z = 0.5 + k * 0.26; y = 0.20 * (k + 1)
        P += box(0.05, y - 0.03, z, 0.92, y, z + 0.28, wood(0.45, 0.3), 0.25, faces="TF")
    P.append(Rect((0.01, 1.70, 2.9), (0, 0, -0.7), (0, 0.35, 0), 0.05, 0.08, emit=blinds_emit(0.55, 0.35), name="window"))
    cams = {"16x9": Cam((3.40, 1.80, 0.25), (1.45, 0.75, 4.2), hfov=100, k=0.30),
            "9x16": Cam((2.20, 1.80, 0.35), (1.45, 0.75, 4.2), hfov=72, k=0.22)}
    lights = {"router": ((1.55 + DX, 1.2, RD - 0.3), 0.35)}
    return P, cams, lights

# ================================================================== CAM 06 — FRONT DOOR / ENTRY
def entry():
    RW, RH, RD = 2.8, 2.6, 3.4
    P = room_shell(RW, RH, RD, wallpaper(0.55), tiles(0.50, 0.30), write={"back": True, "left": True, "right": True}, ppm=200)
    P += baseboards(RW, RD)
    P.append(Rect((0.95, 0, RD - 0.006), (0.92, 0, 0), (0, 2.08, 0), panel_door(0.60, 0.92, 2.08), 0.2, name="frontdoor"))
    P += box(0.88, 0, RD - 0.02, 0.95, 2.15, RD, 0.75, 0.2, faces="F") + box(1.87, 0, RD - 0.02, 1.94, 2.15, RD, 0.75, 0.2, faces="F")
    P += box(0.88, 2.08, RD - 0.02, 1.94, 2.15, RD, 0.75, 0.2, faces="F")
    P.append(Rect((2.02, 0.35, RD - 0.008), (0.26, 0, 0), (0, 1.6, 0), 0.05, 0.08, emit=blinds_emit(0.55, 0.12), name="sidelight"))
    P.append(Ell((1.03, 1.0, RD - 0.04), (0.035, 0.035, 0.035), 0.85, 0.2, name="knob"))
    P += box(0.99, 1.10, RD - 0.035, 1.07, 1.28, RD - 0.006, 0.25, 0.4, faces="FLRT", name="keypad")
    P.append(Rect((1.05, 0.004, RD - 0.95), (0.75, 0, 0), (0, 0, 0.6), carpet(0.40, 0.1), 0.25, name="mat"))
    # key rack right of the sidelight, growth-chart ruler left of the door (both on the back wall)
    P += box(2.36, 1.40, RD - 0.03, 2.72, 1.50, RD, wood(0.52, 0.36), 0.22, faces="F", name="keyrack")
    rul = Rect((0.32, 0.25, RD - 0.012), (0.24, 0, 0), (0, 1.85, 0), wood(0.70, 0.24), 0.22, name="ruler")
    rul.write = True; rul.ppm = 1000; P.append(rul)
    P += box(0.30, 0.23, RD - 0.02, 0.58, 0.25, RD, 0.5, 0.2, faces="FT") + box(0.30, 2.10, RD - 0.02, 0.58, 2.12, RD, 0.5, 0.2, faces="FB")
    # console table + mirror on the left wall, coats on the right wall
    P += box(0.0, 0.78, 1.2, 0.36, 0.82, 2.2, wood(0.42, 0.4), 0.24, faces="TRFK")
    for z in (1.24, 2.12): P += box(0.30, 0.0, z, 0.34, 0.78, z + 0.04, 0.35, 0.24, faces="RFK")
    P.append(Ell((0.18, 0.86, 1.7), (0.13, 0.05, 0.13), 0.62, 0.24, cut_y=0.82))
    P.append(Rect((0.008, 1.15, 2.05), (0, 0, -0.7), (0, 0.6, 0), framed(3.3), 0.22, name="mirror"))
    for z in (1.6, 1.95, 2.3):
        P.append(Ell((RW - 0.12, 1.45, z), (0.10, 0.38, 0.12), fabric(0.38), 0.25, name="coat"))
    cams = {"16x9": Cam((2.55, 2.42, 0.22), (1.25, 0.95, 3.2), hfov=100, k=0.30),
            "9x16": Cam((1.85, 2.40, 0.25), (1.30, 0.80, 3.3), hfov=70, k=0.22)}
    lights = {"sidelight": ((2.15, 1.2, RD - 0.2), 0.6)}
    return P, cams, lights

# ================================================================== CAM 07 — ATTIC ("root")
def attic():
    RW, RD, RH = 5.0, 6.0, 2.3
    P = [Rect((0, 0, 0), (RW, 0, 0), (0, 0, RD), plywood(0.48), 0.24, name="floor")]
    lw = Poly([(0, 0.25, 0), (0, 0.25, RD), (RW / 2, RH, RD), (RW / 2, RH, 0)], mat=insul(0.58), heat=0.2, name="roofL")
    rw = Poly([(RW / 2, RH, RD), (RW / 2, RH, 0), (RW, 0.25, 0), (RW, 0.25, RD)], mat=insul(0.58), heat=0.2, name="roofR")
    P += [lw, rw]
    gable = Poly([(0, 0, RD), (RW, 0, RD), (RW, 0.25, RD), (RW / 2, RH, RD), (0, 0.25, RD)], mat=plywood(0.52), heat=0.2, name="back")
    gable.write = True; gable.ppm = 160; P.append(gable)
    P.append(Rect((RW / 2 - 0.3, 1.0, RD - 0.01), (0.6, 0, 0), (0, 0.45, 0), 0.05, 0.08, emit=blinds_emit(0.6, 0.05), name="vent"))
    # rafters (strips on both roof planes)
    import numpy as _np
    for z in _np.arange(0.2, RD, 0.6):
        for side in (0, 1):
            if side == 0: q = [(0.02, 0.27, z), (0.02, 0.27, z + 0.05), (RW / 2, RH - 0.02, z + 0.05), (RW / 2, RH - 0.02, z)]
            else: q = [(RW / 2, RH - 0.02, z), (RW / 2, RH - 0.02, z + 0.05), (RW - 0.02, 0.27, z + 0.05), (RW - 0.02, 0.27, z)]
            P.append(Poly(q, mat=wood(0.62, 0.05), heat=0.2, name="rafter"))
    P += box(RW / 2 - 0.04, RH - 0.12, 0, RW / 2 + 0.04, RH, RD, wood(0.6, 0.1), 0.2, faces="BLR")
    rf = Rect((1.2, 0.95, 3.2), (0, 0, 0.12), (1.0, 0.76, 0), wood(0.66, 0.12), 0.2, name="beam")
    # storage boxes
    for (x, z, w, h, d) in ((0.7, 2.0, 0.6, 0.45, 0.5), (0.9, 2.6, 0.5, 0.35, 0.45), (3.6, 1.6, 0.7, 0.5, 0.6), (3.8, 3.4, 0.55, 0.4, 0.5)):
        P += box(x, 0, z, x + w, h, z + d, 0.55, 0.22, faces="TFLRK")
    P.append(Ell((RW / 2, 1.85, 2.6), (0.05, 0.07, 0.05), 0.9, 0.3, name="bulb"))
    P += box(RW / 2 - 0.006, 1.92, 2.594, RW / 2 + 0.006, RH - 0.1, 2.606, 0.3, 0.2, faces="FLR")
    lw.write = True; lw.ppm = 150
    cams = {"16x9": Cam((2.5, 1.95, 0.25), (2.5, 0.85, 5.5), hfov=100, k=0.30),
            "9x16": Cam((2.5, 1.95, 0.25), (2.5, 0.75, 5.5), hfov=70, k=0.22)}
    lights = {"bulb": ((RW / 2, 1.8, 2.6), 1.2)}
    return P, cams, lights

# ================================================================== CAM 08 — STREET (porch camera)
HOUSES = [(-14.0, 20.0, 9.0, 6.0), (-2.5, 19.0, 9.5, 6.5), (9.5, 20.0, 9.0, 6.0), (21.0, 21.0, 9.0, 5.5)]  # x0, z0(front), width, wall h
def house(x0, z0, w, h, depth=9.0, seed=0, mat=None):
    out = []
    mat = mat or siding(0.48)
    out.append(Rect((x0, 0, z0), (w, 0, 0), (0, h, 0), mat, 0.25, name="facade"))
    out.append(Rect((x0, 0, z0 + depth), (0, 0, -depth), (0, h, 0), mat, 0.25, name="side"))
    out.append(Rect((x0 + w, 0, z0), (0, 0, depth), (0, h, 0), mat, 0.25, name="side"))
    rh = h + 2.6
    out.append(Poly([(x0, h, z0), (x0 + w, h, z0), (x0 + w / 2, rh, z0)], mat=mat, heat=0.25, name="gable"))
    out.append(Poly([(x0 - 0.3, h - 0.1, z0 - 0.3), (x0 + w / 2, rh, z0 - 0.3), (x0 + w / 2, rh, z0 + depth), (x0 - 0.3, h - 0.1, z0 + depth)], mat=shingles(0.26), heat=0.2, name="roof"))
    out.append(Poly([(x0 + w / 2, rh, z0 - 0.3), (x0 + w + 0.3, h - 0.1, z0 - 0.3), (x0 + w + 0.3, h - 0.1, z0 + depth), (x0 + w / 2, rh, z0 + depth)], mat=shingles(0.26), heat=0.2, name="roof"))
    out.append(Rect((x0 + w * 0.42, 0, z0 - 0.01), (1.0, 0, 0), (0, 2.1, 0), 0.30, 0.25, name="hdoor"))
    out += box(x0 + w * 0.38, 0, z0 - 1.4, x0 + w * 0.42 + 1.4, 0.35, z0, 0.42, 0.22, faces="TF")
    return out
WINDOWS = []     # (house index, world corners c, ex, ey) filled by street()
def street():
    P = [Rect((-60, 0, 0), (120, 0, 0), (0, 0, 8.0), grass(0.50), 0.3, name="lawn"),
         Rect((-60, 0, 8.0), (120, 0, 0), (0, 0, 1.6), concrete(0.55), 0.3, name="walk"),
         Rect((-60, 0, 9.6), (120, 0, 0), (0, 0, 7.6), asphalt(0.17), 0.3, name="road"),
         Rect((-60, 0, 17.2), (120, 0, 0), (0, 0, 1.6), concrete(0.52), 0.3, name="walk2"),
         Rect((-60, 0, 18.8), (120, 0, 0), (0, 0, 60), grass(0.45), 0.3, name="lawn2"),
         Rect((-200, -5, 160), (400, 0, 0), (0, 120, 0), 0.0, 0.05, emit=lambda u, v, P: 0.035 + 0.05 * np.clip(1 - v / 60, 0, 1), name="sky")]
    WINDOWS.clear()
    for i, (x0, z0, w, h) in enumerate(HOUSES):
        P += house(x0, z0, w, h, seed=i)
        for (fx, fy) in ((0.12, 0.45), (0.65, 0.45), (0.12, 0.08), (0.70, 0.08)):
            wx, wy = x0 + w * fx, h * (0.5 + fy * 0.9) if fy > 0.3 else 0.85
            c = (wx, wy + 1.25, z0 - 0.02); ex = (1.35, 0, 0); ey = (0, -1.25, 0)
            P.append(Rect((wx, wy, z0 - 0.015), (1.35, 0, 0), (0, 1.25, 0), 0.06, 0.1, name="hwin"))
            WINDOWS.append((i, c, ex, ey))
    # streetlight, trees, parked car, mailbox
    P.append(Cyl((5.0, 0, 8.6), 0.07, 0.0, 6.0, 0.4, 0.3, name="pole"))
    P += box(5.0, 5.9, 8.45, 6.5, 6.0, 8.75, 0.35, 0.3, faces="TBFLR")
    P.append(Ell((6.3, 5.85, 8.6), (0.35, 0.10, 0.18), 0.2, 0.6, emit=3.0, name="lamp"))
    for (tx, tz, r) in ((-9.0, 7.0, 2.6), (13.0, 6.5, 2.9), (-20, 26, 3.5), (3.5, 27.5, 3.2)):
        P.append(Cyl((tx, 0, tz), 0.22, 0, 2.6, 0.35, 0.3))
        P.append(Ell((tx, 3.6 + r * 0.5, tz), (r, r * 0.9, r), insul(0.42), 0.3, name="tree"))
    P += box(-7.0, 0.25, 10.4, -2.6, 1.05, 12.2, 0.55, 0.3, faces="TFLRK", name="car")
    P += box(-6.1, 1.05, 10.6, -3.6, 1.55, 12.0, 0.25, 0.3, faces="TFLRK", name="car")
    cams = {"16x9": Cam((0.0, 2.7, 0.3), (1.0, 1.6, 22.0), hfov=96, k=0.28),
            "9x16": Cam((0.0, 2.7, 0.3), (0.5, 1.9, 22.0), hfov=62, k=0.20)}
    lights = {"lamp": ((6.3, 5.6, 8.6), 60.0), "police": ((1.5, 1.7, 13.4), 30.0), "sky": ((0.0, 80.0, 40.0), 9000.0)}
    return P, cams, lights


def net():
    """Second camera in the basement, close on the network shelf."""
    P, cams, lights = basement()
    RD = 4.2
    DX = SHELF_DX
    cams = {"16x9": Cam((2.75 + DX, 1.70, 2.55), (1.75 + DX, 1.00, RD), hfov=84, k=0.26),
            "9x16": Cam((2.30 + DX, 1.72, 2.65), (1.78 + DX, 0.85, RD), hfov=62, k=0.20)}
    return P, cams, lights


def closeup(room_fn, c16, c9):
    """Same room, a tighter camera (a PTZ zoom): c16 / c9 = (pos, look, hfov)."""
    P, cams, lights = room_fn()
    return P, {"16x9": Cam(c16[0], c16[1], hfov=c16[2], k=0.10), "9x16": Cam(c9[0], c9[1], hfov=c9[2], k=0.08)}, lights

def fridge(): return closeup(kitchen, ((2.40, 1.45, 1.40), (3.72, 0.88, 3.62), 50), ((2.95, 1.40, 1.60), (3.72, 0.88, 3.62), 40))
def keys(): return closeup(entry, ((1.95, 1.65, 1.75), (2.50, 1.30, 3.40), 46), ((2.20, 1.60, 1.95), (2.48, 1.20, 3.40), 34))
def ruler(): return closeup(entry, ((0.95, 1.25, 2.15), (0.44, 1.10, 3.40), 40), ((0.70, 1.20, 2.30), (0.44, 1.05, 3.40), 30))
def keypad(): return closeup(entry, ((1.30, 1.38, 2.55), (1.03, 1.19, 3.40), 30), ((1.20, 1.36, 2.65), (1.03, 1.17, 3.40), 22))
def card(): return closeup(entry, ((1.65, 1.15, 2.30), (1.33, 0.02, 3.15), 44), ((1.50, 1.20, 2.35), (1.33, 0.02, 3.15), 32))
def dome(): return closeup(hallway, ((0.70, 1.85, 5.40), (0.70, 2.40, 7.55), 38), ((0.70, 1.80, 5.60), (0.70, 2.35, 7.55), 28))
def board(): return closeup(basement, ((1.10, 1.45, 1.85), (0.80, 1.15, 4.2), 52), ((1.0, 1.40, 2.0), (0.80, 1.10, 4.2), 38))

def calendar_cam(): return closeup(kitchen, ((2.85, 1.55, 2.0), (3.62, 1.46, 3.62), 30), ((3.05, 1.52, 2.05), (3.62, 1.44, 3.62), 24))
