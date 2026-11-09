"""Short F ("I have a subscription") at 9:16: frames 2400-2999 (song 80.00-100.00), In the Walls then the swarm.

  80.00-84.33  s4_walls (CAM 01 PTZ on the TV; "Everything." -> the DVR multiview). Its 9:16 cameras already exist; the
               Short moves the OSD's right-hand items (REC, PTZ/ZOOM) inside the safe column and re-lays the DVR grid
               for a phone: three small cameras per row, two rows above and two below, and the living room full width
               in the middle (so "Everything." in the wall reads at phone size). Camera labels at 34 px.
  84.33-100.0  s5_swarm. Its 9:16 formations already exist; the Short centres the words (LOOK / WHAT / I CAN / DO!,
               AI / GURU) on the safe column (x 0.44 W, max width 0.80 W) instead of the frame, so nothing spelled
               runs under YouTube's buttons.
Both run on PRIVATE copies of the modules (shorts_dg.private), so the published 16:9 film is untouched.
render_frame(t, W, H): 9:16 only (16:9 falls through to the original modules).
end card: shorts_dg.end_card (Short A's)."""
import os, sys, math
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shorts_dg as SD
from studio import core as C

N0, N1 = 2400, 2999
T_SWARM = 2530 / 30.0

# ------------------------------------------------------------------ s4: In the Walls
W4 = SD.private("shortF_walls", "s4_walls.py")
from studio.core import sprite, blit, shadow, text_w


def osd_v(img, t, W, H, cam_label, room_label, extra=None):
    ts = min(W, H) / 1080; fs = int(56 * ts); x = 58 * ts; y = 46 * ts; R = W * SD.SAFE_R
    for i, s in enumerate([cam_label + "  " + room_label, W4.stamp(t)]):
        sp = sprite(s, W4.VT, fs, 4); yy = y + i * fs * 0.95
        shadow(img, sp, x + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, x, yy, W4.OSD_W, 0.95)
    if int((t - W4.T_Q) * 1.25 + 0.2) % 2 == 0:
        rw = text_w("REC", W4.VT, fs); rx = R - rw - 34 * ts; ry = y + fs * 0.52
        cv2.circle(img, (int(rx), int(ry)), int(13 * ts), W4.REC_RED.tolist(), -1, cv2.LINE_AA)
        sp = sprite("REC", W4.VT, fs, 4); shadow(img, sp, rx + 28 * ts, y + 2 * ts, 0.9); blit(img, sp, rx + 26 * ts, y, W4.OSD_W, 0.95)
    if extra:
        sp = sprite(extra, W4.VT, fs, 4); xx = R - text_w(extra, W4.VT, fs); yy = y + fs * 0.95
        shadow(img, sp, xx + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, xx, yy, W4.OSD_W, 0.95)


def grid_v(t, W, H, fi):
    """DVR multiview for a phone: 3 + 3 small cameras, the living room full width, 3 + 3 below."""
    out = np.zeros((H, W, 3), np.float32); ts = W / 1080
    gap = max(2, int(4 * ts)); cols = 3
    tw = (W - gap * (cols - 1)) // cols; tw -= tw % 2
    th = int(300 * ts); th -= th % 2; ch = int(660 * ts); ch -= ch % 2
    tot = 4 * th + ch + 4 * gap; oy = (H - tot) // 2; ox = (W - (tw * cols + gap * (cols - 1))) // 2
    rows_y = [oy, oy + th + gap, oy + 2 * (th + gap) + ch + gap, oy + 3 * (th + gap) + ch + gap]
    fs = max(16, int(34 * ts))
    for i, (_, _, cid) in enumerate(W4.LAYOUT):
        r_, c_ = divmod(i, cols); x0, y0 = ox + c_ * (tw + gap), rows_y[r_]
        tile = W4.nightvision(W4.feed(cid, t, tw, th), fi + i, tw, th)
        out[y0:y0 + th, x0:x0 + tw] = tile
        lab = f"{W4.CAMS[cid][1]} {W4.CAMS[cid][2]}"
        sp = sprite(lab, W4.VT, fs, 3); shadow(out, sp, x0 + 12 * ts + 2, y0 + 8 * ts + 2, 0.9); blit(out, sp, x0 + 12 * ts, y0 + 8 * ts, W4.OSD_W, 0.9)
    cw = W - 2 * ox; cw -= cw % 2; x0, y0 = ox, oy + 2 * (th + gap)
    tile = W4.nightvision(W4.feed("livptz", t, cw, ch), fi + 20, cw, ch)
    W4.tv_composite(tile, t, "livptz", cw, ch)
    out[y0:y0 + ch, x0:x0 + cw] = tile
    fs2 = int(44 * ts); lab = "CAM 01 LIVING RM"
    sp = sprite(lab, W4.VT, fs2, 3); shadow(out, sp, x0 + 18 * ts + 2, y0 + 12 * ts + 2, 0.9); blit(out, sp, x0 + 18 * ts, y0 + 12 * ts, W4.OSD_W, 0.95)
    if int((t - W4.T_Q) * 1.25 + 0.2) % 2 == 0:
        rx = x0 + cw * SD.SAFE_R - 130 * ts; ry = y0 + 12 * ts + fs2 * 0.52
        cv2.circle(out, (int(rx), int(ry)), int(11 * ts), W4.REC_RED.tolist(), -1, cv2.LINE_AA)
        sp = sprite("REC", W4.VT, fs2, 3); blit(out, sp, rx + 22 * ts, y0 + 12 * ts, W4.OSD_W, 0.95)
    cv2.rectangle(out, (x0, y0), (x0 + cw - 1, y0 + ch - 1), (W4.OSD_W * 0.55).tolist(), max(1, int(2 * ts)))
    return out


def walls_v(t, W, H):
    fi = int(round(t * 30))
    if t < W4.T_EV - 0.01:
        img, extra = W4.ptz_shot(t, W, H, fi)
        osd_v(img, t, W, H, "CAM 01", "LIVING RM", extra)
        cut = W4.T_TO - 0.02
    else:
        img = grid_v(t, W, H, fi); cut = W4.T_EV - 0.01
    since = t - cut
    gl = 0.38 * (1 - since / 0.10) if 0 <= since < 0.10 else 0.0
    if 0 <= since < 0.067: img = W4.static_burst(img, W, H, fi, 0.20)
    fl = 0.0
    if 0 <= t - W4.T_FLOOD < 0.5: fl = 0.35 * math.exp(-(t - W4.T_FLOOD) * 8)
    return C.finish(img, t, fi, 1e9, flash=fl, flash_col=np.array([0.92, 1.0, 0.92], np.float32), glitch_amt=gl, ca=0.0012)


# ------------------------------------------------------------------ s5: the swarm
S5 = SD.private("shortF_swarm", "s5_swarm.py")
S5.SRC_HASH = S5.SRC_HASH + "_shortF2"            # its own formation plans in build/s5_cache (never the film's)
_tt0 = S5.text_targets
def _tt(lines, W, H, n, cy_frac, size_px, font=S5.DISP, maxw=0.86, lh=1.02, seed=1, cx_frac=0.5, edge=0.42):
    if H > W and abs(cx_frac - 0.5) < 1e-6: cx_frac, maxw = 0.44, min(maxw, 0.80)
    return _tt0(lines, W, H, n, cy_frac, size_px, font=font, maxw=maxw, lh=lh, seed=seed, cx_frac=cx_frac, edge=edge)
S5.text_targets = _tt
_gg0 = S5.guru_geo
def _gg(W, H):
    cx, cy, rx, ry = _gg0(W, H)
    return (W * 0.44, cy, rx, ry) if H > W else (cx, cy, rx, ry)
S5.guru_geo = _gg
_lay0 = S5.LAY
def _lay(W, H):
    L = _lay0(W, H)
    if H > W and not L.get("_shortF"):
        x, y, rx, ry = L["stage"]; L["stage"] = (W * 0.45, y, rx, ry); L["_shortF"] = True
    return L
S5.LAY = _lay
_pg0 = S5.page_geo
def _pg(W, H):
    """The résumé: a little smaller and left of centre, so the stack of 14 sheets stays inside 0.88 W and the page
    counter sits under it, clear of the bottom 22%."""
    if W >= H: return _pg0(W, H)
    w = W * 0.56; h = w / 0.74; cx, cy = W * 0.40, H * 0.37
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
S5.page_geo = _pg


def _page_marks(E, img, t, W, H):
    """s5's page_marks with the counter laid out for 9:16: 'page' and 14/14 stacked under the sheet (not over it)."""
    if W >= H: return _pm0(E, img, t, W, H)
    o = S5.form_k("resume", t)
    if o <= 0.02: return
    ts = S5.LAY(W, H)["ts"]; x0, y0, x1, y1 = S5.page_geo(W, H); w, h = x1 - x0, y1 - y0
    p = S5.page_at(t); dx, dy = 16 * ts, -13 * ts
    for k in range(p - 1, 0, -1):
        i = k - 1; u = t - S5.FLIPS[i]; s_in = S5.eo(S5.clamp(u / 0.10))
        S5.glass(img, x0 + dx * k * s_in, y0 + dy * k * s_in, w, h, o, border=S5.AGENT * 0.95, fill=S5.col(0.018, 0.03, 0.06),
                 r=int(10 * ts), edge=0.75 + 0.5 * math.exp(-u * 8), alpha=0.94)
    S5.glass(img, x0, y0, w, h, o, border=S5.AGENT * 0.0, fill=S5.col(0.012, 0.022, 0.05), r=int(10 * ts), edge=0.0, alpha=0.96)
    fs = int(46 * ts); fb = int(150 * ts); cx = (x0 + x1) / 2 + dx * 3
    S5.label(img, "page", cx, y1 + 52 * ts, fs, S5.DIM * 1.8, o, path=S5.MONOB, anchor="ct", glow=0.0)
    done = p >= S5.N_PAGES
    flash = math.exp(-max(0.0, t - S5.FLIPS[-1]) * 6) if done else 0.0
    S5.label(img, f"{p}/{S5.N_PAGES}", cx, y1 + 52 * ts + fs * 1.3, fb, S5.WHITE, o, path=S5.DISP, anchor="ct", glow=0.35 + 0.6 * flash)
_pm0 = S5.page_marks
S5.page_marks = _page_marks


def render_frame(t, W, H):
    if W >= H:
        import s4_walls, s5_swarm
        return (s4_walls if t < T_SWARM else s5_swarm).render_frame(t, W, H)
    return walls_v(t, W, H) if t < T_SWARM else S5.render_frame(t, W, H)
