"""Tiny 3D toolkit for song worlds (painter's algorithm, flat shading, ink outlines, textured faces).

Coordinates: y is up. A Cam comes from core.orbit / core.Cam.
- box(...)            : a shaded, outlined box (buildings, gifts, servers, beds)
- textured_quad(...)  : any image/texture warped onto a 3D quad (windows, posters, screens)
- word3d(...)         : kinetic type that lives in the world — an extruded word lying on a surface or standing up
- ground(...)         : a ground plane with road/grid lines
Everything is queued into a Scene and drawn back-to-front with Scene.draw(img).
"""
import math
import numpy as np, cv2
from . import core as C

def _cam_basis(cam):
    b = getattr(cam, "_basis", None)
    if b is not None: return b
    b = _cam_basis_calc(cam); cam._basis = b; return b

def _cam_basis_calc(cam):
    z = cam.tgt - cam.pos; z = z / np.linalg.norm(z)
    up = np.array([math.sin(cam.roll), math.cos(cam.roll), 0], np.float32)
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    return x, y, z

def proj(P, cam, W, H):
    P = np.asarray(P, np.float32).reshape(-1, 3)
    x, y, z = _cam_basis(cam); Q = P - cam.pos
    cx, cy, cz = Q @ x, Q @ y, Q @ z
    foc = min(W, H) * 1.25 * cam.fov; czs = np.maximum(cz, 1e-3)
    return np.stack([W / 2 + foc * cx / czs, H / 2 - foc * cy / czs], 1), cz

def _warp_into(img, tex, quad2, op=1.0, alpha=None, tint=None):
    """Warp tex (h,w,3) [+alpha (h,w)] onto the 2D quad (4x2: tl,tr,br,bl) only inside its bounding box."""
    H, W = img.shape[:2]
    x0, y0 = np.floor(quad2.min(0)).astype(int); x1, y1 = np.ceil(quad2.max(0)).astype(int)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X1 - X0 < 2 or Y1 - Y0 < 2: return
    h, w = tex.shape[:2]
    src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    dst = (quad2 - [X0, Y0]).astype(np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(tex, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = alpha if alpha is not None else np.ones((h, w), np.float32)
    am = cv2.warpPerspective(a, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None] * op
    if tint is not None: out = out * tint
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - am); reg += out * am

class Scene:
    def __init__(s, cam, W, H, fog=None, fog_dist=(40, 140), light=(0.5, 0.8, -0.35), ink=0.9):
        s.cam, s.W, s.H, s.items = cam, W, H, []
        s.fog = fog; s.fog_dist = fog_dist; s.light = np.array(light, np.float32) / np.linalg.norm(light); s.ink = ink
        s.basis = _cam_basis(cam)

    def _fogk(s, depth):
        if s.fog is None: return 0.0
        a, b = s.fog_dist; return float(np.clip((depth - a) / (b - a), 0, 1))

    def quad(s, P4, col, normal=None, tex=None, alpha=None, op=1.0, outline=True, shade=True, tint=None):
        P4 = np.asarray(P4, np.float32)
        q, z = proj(P4, s.cam, s.W, s.H)
        if (z < 0.2).any(): return
        if normal is not None:   # back-face cull
            if np.dot(normal, P4.mean(0) - s.cam.pos) >= 0: return
        d = float(z.mean())
        lit = 1.0
        if shade and normal is not None: lit = 0.62 + 0.38 * max(0.0, float(np.dot(normal, s.light)))
        s.items.append((d, "quad", q, np.asarray(col, np.float32) * lit, tex, alpha, op, outline, tint))

    def box(s, c, size, col, tex=None, tex_faces=("front", "back", "left", "right"), top_col=None, op=1.0, outline=True):
        cx, cy, cz = c; sx, sy, sz = size; x0, x1 = cx - sx / 2, cx + sx / 2; y0, y1 = cy, cy + sy; z0, z1 = cz - sz / 2, cz + sz / 2
        V = lambda x, y, z: (x, y, z)
        faces = {
            "front": ([V(x0, y1, z0), V(x1, y1, z0), V(x1, y0, z0), V(x0, y0, z0)], (0, 0, -1)),
            "back": ([V(x1, y1, z1), V(x0, y1, z1), V(x0, y0, z1), V(x1, y0, z1)], (0, 0, 1)),
            "left": ([V(x0, y1, z1), V(x0, y1, z0), V(x0, y0, z0), V(x0, y0, z1)], (-1, 0, 0)),
            "right": ([V(x1, y1, z0), V(x1, y1, z1), V(x1, y0, z1), V(x1, y0, z0)], (1, 0, 0)),
            "top": ([V(x0, y1, z1), V(x1, y1, z1), V(x1, y1, z0), V(x0, y1, z0)], (0, 1, 0)),
        }
        for name, (P, n) in faces.items():
            t = tex if (tex is not None and name in tex_faces) else None
            cc = top_col if (name == "top" and top_col is not None) else col
            s.quad(P, cc, normal=np.array(n, np.float32), tex=t, op=op, outline=outline, tint=None)

    def word(s, text, origin, right, up, height, col, side_col=None, depth=0.0, font=C.F_DISP, op=1.0, glow=0.0, shadow=0.0):
        """Kinetic type in the world. origin = bottom-left corner; right/up = unit vectors of the text plane."""
        sp = C.sprite(text, font, 160, 10); a = sp[0]; h, w = a.shape
        aspect = w / h; width = height * aspect
        o = np.asarray(origin, np.float32); r = np.asarray(right, np.float32); u = np.asarray(up, np.float32)
        n = np.cross(r, u); n /= np.linalg.norm(n)
        tex = np.ones((h, w, 3), np.float32)
        steps = int(max(0, depth) * 10)
        for k in range(steps, 0, -1):   # extrusion: stacked darker layers behind the face
            off = n * depth * k / max(1, steps)   # behind the face (away from the camera)
            P = [o + off + u * height, o + off + r * width + u * height, o + off + r * width, o + off]
            q, z = proj(P, s.cam, s.W, s.H)
            if (z < 0.2).any(): continue
            s.items.append((float(z.mean()) + 1e-3 * k, "quad", q, np.asarray(side_col if side_col is not None else col * 0.45, np.float32), tex, a, op, False, None))
        P = [o + u * height, o + r * width + u * height, o + r * width, o]
        q, z = proj(P, s.cam, s.W, s.H)
        if (z < 0.2).any(): return
        s.items.append((float(z.mean()) - 1e-3, "word", q, np.asarray(col, np.float32), tex, a, op, False, (sp[1], glow, shadow)))

    def ground(s, col, size=200, y=0.0, lines=None):
        """Infinite ground plane: filled below the projected horizon; lines are clipped to the near plane."""
        s.items.append((2e9, "ground", None, np.asarray(col, np.float32), y, None, 1.0, False, None))
        x, yb, z = s.basis
        for (a, b, c, w_) in (lines or []):
            A = np.array(a, np.float32) + (0, 0.01, 0); B = np.array(b, np.float32) + (0, 0.01, 0)
            za = (A - s.cam.pos) @ z; zb = (B - s.cam.pos) @ z
            if za < 0.3 and zb < 0.3: continue
            if za < 0.3: A = A + (B - A) * (0.3 - za) / (zb - za)
            if zb < 0.3: B = B + (A - B) * (0.3 - zb) / (za - zb)
            q, zz = proj([A, B], s.cam, s.W, s.H)
            s.items.append((1e9 - 1, "line", q, np.asarray(c, np.float32), w_, None, 1.0, False, None))

    def draw(s, img):
        s.items.sort(key=lambda it: -it[0])
        H, W = img.shape[:2]
        for d, kind, q, col, tex, alpha, op, outline, extra in s.items:
            fk = s._fogk(d) if d < 1e8 else 0.0
            c = col * (1 - fk) + (s.fog * fk if s.fog is not None else 0)
            if kind == "ground":
                yg = tex; x, yb, z = s.basis
                fwd = np.array([z[0], 0, z[2]], np.float32); fwd /= max(1e-6, np.linalg.norm(fwd)); rt = np.array([x[0], 0, x[2]], np.float32)
                far = s.cam.pos * np.array([1, 0, 1], np.float32) + fwd * 5000 + np.array([0, yg, 0], np.float32)
                q, _ = proj([far - rt * 5000, far + rt * 5000], s.cam, W, H)
                (xa, ya), (xb, yb2) = q
                k = (yb2 - ya) / (xb - xa + 1e-6)
                hl, hr = ya + k * (0 - xa), ya + k * (W - xa)
                poly = np.array([[0, hl], [W, hr], [W, H * 4], [0, H * 4]], np.float32)
                cv2.fillPoly(img, [np.round(poly).astype(np.int32)], col.tolist(), cv2.LINE_AA)
                if s.fog is not None:   # haze near the horizon
                    yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
                    hy = hl + (hr - hl) * xx / W; m = np.clip(1 - (yy - hy) / (H * 0.35), 0, 1) * (yy > hy)
                    img[:] = img * (1 - 0.8 * m[..., None]) + s.fog * 0.8 * m[..., None]
                continue
            if kind == "line":
                cv2.line(img, tuple(np.round(q[0]).astype(int)), tuple(np.round(q[1]).astype(int)), c.tolist(), int(tex), cv2.LINE_AA)
                continue
            if kind == "word":
                g, glow, *rest = extra; shadow = rest[0] if rest else 0.0
                if shadow > 0 and g is not None:   # dark halo so light words read on a bright sky / sun
                    off = np.array([W * 0.004, H * 0.006], np.float32)
                    _warp_into(img, np.ones(g.shape + (3,), np.float32) * np.array([0.05, 0.03, 0.08], np.float32), q + off, min(1.0, op * shadow * 0.9), alpha=np.clip(g * 3.5, 0, 1))
                if glow > 0 and g is not None:
                    _warp_into(img, np.ones(g.shape + (3,), np.float32) * c, q, op * glow, alpha=np.clip(g * 1.5, 0, 1))
                _warp_into(img, np.ones(alpha.shape + (3,), np.float32) * c, q, op, alpha=alpha)
                continue
            if tex is not None:
                _warp_into(img, tex, q, op, alpha=alpha, tint=c if alpha is None else None) if alpha is None else \
                    _warp_into(img, np.ones(alpha.shape + (3,), np.float32) * c, q, op, alpha=alpha)
            else:
                pts = np.round(q * 4).astype(np.int32)
                lay = img if op >= 0.999 else img.copy()
                cv2.fillConvexPoly(lay, pts, c.tolist(), cv2.LINE_AA, shift=2)
                if op < 0.999: img[:] = img * (1 - op) + lay * op
            if outline and s.ink > 0:
                cv2.polylines(img, [np.round(q * 4).astype(np.int32)], True, (C.hexc('1a1418') * s.ink).tolist(), max(1, int(min(W, H) / 540)), cv2.LINE_AA, shift=2)

def window_texture(w=64, h=128, lit=0.4, seed=0, wall=(0.85, 0.82, 0.78), win=(0.18, 0.2, 0.28), glow=(1.0, 0.85, 0.55)):
    """Facade texture with a grid of windows (some lit)."""
    r = np.random.default_rng(seed); t = np.ones((h, w, 3), np.float32) * np.array(wall, np.float32)
    cols, rows = 4, 8; cw, ch = w / cols, h / rows
    for i in range(cols):
        for j in range(rows):
            x0, y0 = int(i * cw + cw * 0.2), int(j * ch + ch * 0.22); x1, y1 = int(x0 + cw * 0.6), int(y0 + ch * 0.55)
            c = np.array(glow if r.random() < lit else win, np.float32)
            t[y0:y1, x0:x1] = c
    return t
