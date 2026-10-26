"""Step 2b — safe-zone check for the 9:16 master: does every lyric line land where phones can show it?

usage: python -m studio.safezone songs/<slug> [--every N] [--times 12.5 40]

For each lyric line it renders the 9:16 frame twice, once normally and once with the overlays switched off
(core.STATE['clean']), and takes the pixels the overlay made brighter as the line's text. The text's bounding box is
checked against core.SAFE_9x16 (the top bar, the caption block, the phone crop on both sides, the like/share column).

Writes build/safe_zone_9x16.json (one entry per line + "ok") and build/safe_zone_9x16.jpg (the frames, worst first, with
the unsafe areas shaded and each line's box drawn green or red). studio.render will not start a 9:16 render until this
file says ok and is newer than the song's code. --times adds frames to the sheet for a visual check of in-scene text
(signs, HUD words) that the clean switch doesn't hide.
"""
import os, sys, glob, json, time, argparse
import numpy as np, cv2
from .config import load_song
from . import core
from .render import load_scene

W, H = 1080, 1920


def sample_time(L, nxt):
    """A moment when the whole line is on screen at full opacity: just after its last word, before the swap."""
    last = L['wt'][-1] if L.get('wt') else L['s'] + 0.5
    t = min(last + 0.15, L['e'] + 0.02, nxt - 0.22)
    return max(t, L['s'] + 0.06)


def text_bands(a, b):
    """Rows of overlay text, each with its own box: separate rows (a headline up top, a title further down) are checked
    on their own, so a wide headline above the like/share column doesn't count as being in it."""
    la = a.astype(np.float32).mean(2); lb = b.astype(np.float32).mean(2)
    m = cv2.morphologyEx(((la - lb) > 10).astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    rows = np.where(m.sum(1) > 0)[0]
    if not len(rows): return []
    bands = []; start = prev = rows[0]
    for r in rows[1:]:
        if r - prev > 14: bands.append((start, prev)); start = r
        prev = r
    bands.append((start, prev)); out = []
    for y0, y1 in bands:
        cols = np.where(m[y0:y1 + 1].sum(0) > 0)[0]
        if len(cols) and (y1 - y0) >= 6: out.append((int(cols[0]), int(y0), int(cols[-1]) + 1, int(y1) + 1))
    return out


def violations_of(a, c):
    v = []
    for bb in text_bands(a, c):
        for x in core.safe_violations(bb, W, H):
            if x not in v: v.append(x)
    return v


def text_box(a, b):
    """Pixels the overlay brightened (text is light on a darkened band) -> bounding box, or None."""
    la = a.astype(np.float32).mean(2); lb = b.astype(np.float32).mean(2)
    m = ((la - lb) > 10).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 30]
    if not keep: return None
    xs0 = min(st[i, 0] for i in keep); ys0 = min(st[i, 1] for i in keep)
    xs1 = max(st[i, 0] + st[i, 2] for i in keep); ys1 = max(st[i, 1] + st[i, 3] for i in keep)
    return int(xs0), int(ys0), int(xs1), int(ys1)


def shade(img):
    """Unsafe areas in translucent red."""
    S = core.SAFE_9x16; o = img.astype(np.float32); red = np.array([235, 40, 50], np.float32); k = 0.32
    def tint(x0, y0, x1, y1):
        o[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = o[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] * (1 - k) + red * k
    tint(0, 0, 1, S['top']); tint(0, S['bottom'], 1, 1)
    tint(0, S['top'], S['left'], S['bottom']); tint(S['right'], S['top'], 1, S['bottom'])
    tint(S['buttons_x'], S['buttons_y'], S['right'], S['bottom'])
    return o.astype(np.uint8)


def check(song_dir, every=1, extra_times=()):
    song = load_song(song_dir); b = song["build"]; sc = load_scene(song_dir)
    lines = json.load(open(os.path.join(b, "timed.json")))
    res = []; frames = []; t0 = time.time()
    for i, L in enumerate(lines):
        if i % every: continue
        nxt = lines[i + 1]['s'] if i + 1 < len(lines) else L['e'] + 2
        t = sample_time(L, nxt); fi = int(round(t * core.FPS))
        core.STATE["clean"] = False; a = sc.render_frame(t, W, H, fi)
        core.STATE["clean"] = True; c = sc.render_frame(t, W, H, fi)
        core.STATE["clean"] = False
        box = text_box(a, c)
        v = violations_of(a, c) if box else []
        res.append(dict(line=L['text'], sec=L.get('sec'), t=round(t, 2), box=box, violations=v,
                        box_frac=[round(box[0] / W, 3), round(box[1] / H, 3), round(box[2] / W, 3), round(box[3] / H, 3)] if box else None))
        frames.append((len(v), t, a, box, v, L['text']))
        print(f"{t:7.2f}  {'OK ' if not v else 'BAD'}  {', '.join(v):24s} {L['text'][:60]}", flush=True)
    # the end card (drawn only when the overlays are on)
    dur = json.load(open(os.path.join(b, "beats.json")))["duration"] + float(song.get("tail", 0) or getattr(sc, "TAIL", 0) or 0)
    if hasattr(sc, "DUR"): dur = float(sc.DUR)
    t = dur - 1.2; fi = int(round(t * core.FPS))
    core.STATE["clean"] = False; a = sc.render_frame(t, W, H, fi); core.STATE["clean"] = True; c = sc.render_frame(t, W, H, fi); core.STATE["clean"] = False
    box = text_box(a, c); v = violations_of(a, c) if box else []
    res.append(dict(line="(end card)", sec="END", t=round(t, 2), box=box, violations=v,
                    box_frac=[round(box[0] / W, 3), round(box[1] / H, 3), round(box[2] / W, 3), round(box[3] / H, 3)] if box else None))
    frames.append((len(v), t, a, box, v, "(end card)"))
    print(f"{t:7.2f}  {'OK ' if not v else 'BAD'}  {', '.join(v):24s} (end card)", flush=True)
    for t in extra_times:
        a = sc.render_frame(t, W, H, int(round(t * core.FPS))); frames.append((0, t, a, None, [], f"(t={t})"))
    bad = [r for r in res if r['violations']]
    out = dict(ok=not bad, checked=len(res), bad=len(bad), safe=core.SAFE_9x16, lines=res,
               code_mtime=code_mtime(song_dir), when=time.strftime("%Y-%m-%d %H:%M:%S"))
    json.dump(out, open(os.path.join(b, "safe_zone_9x16.json"), "w"), indent=1)
    sheet(frames, os.path.join(b, "safe_zone_9x16.jpg"))
    print(f"\n{'ALL LINES SAFE' if not bad else f'{len(bad)} of {len(res)} lines break the safe zone'}  "
          f"({time.time() - t0:.0f}s)  -> {os.path.join(b, 'safe_zone_9x16.jpg')}")
    return out


def sheet(frames, path, cols=6, tw=270):
    from PIL import Image, ImageDraw
    frames = sorted(frames, key=lambda f: (-f[0], f[1]))[:36]
    th = int(tw * H / W); rows = max(1, (len(frames) + cols - 1) // cols)
    S = Image.new("RGB", (tw * cols, (th + 34) * rows), (16, 16, 20)); d = ImageDraw.Draw(S)
    for k, (nv, t, a, box, v, text) in enumerate(frames):
        im = Image.fromarray(shade(a)); dd = ImageDraw.Draw(im)
        if box: dd.rectangle(box, outline=(255, 50, 50) if v else (60, 230, 120), width=6)
        x, y = (k % cols) * tw, (k // cols) * (th + 34)
        S.paste(im.resize((tw, th)), (x, y))
        d.text((x + 6, y + th + 4), f"{t:.1f}s {'BAD: ' + ', '.join(v) if v else 'ok'}", fill=(255, 90, 90) if v else (150, 230, 160))
        d.text((x + 6, y + th + 18), text[:42], fill=(200, 200, 200))
    S.save(path, quality=85)


def code_mtime(song_dir):
    files = glob.glob(os.path.join(song_dir, "*.py")) + [os.path.join(song_dir, "build", "timed.json")]
    files += glob.glob(os.path.join(core.ROOT, "studio", "core.py"))
    return max(os.path.getmtime(f) for f in files if os.path.exists(f))


def require_ok(song_dir):
    """Called by studio.render before a 9:16 render: True if a passing check is newer than the song's code."""
    p = os.path.join(song_dir, "build", "safe_zone_9x16.json")
    if not os.path.exists(p): return False, "no safe-zone check yet"
    r = json.load(open(p))
    if not r.get("ok"): return False, f"the last check found {r.get('bad')} lines outside the safe zone"
    if code_mtime(song_dir) > os.path.getmtime(p) + 1: return False, "the scene changed since the last check"
    return True, "ok"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("song_dir"); ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--times", nargs="*", type=float, default=[])
    a = ap.parse_args(); r = check(a.song_dir, a.every, a.times); sys.exit(0 if r["ok"] else 1)
