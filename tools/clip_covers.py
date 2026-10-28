"""Covers for a song's Reels/Shorts and the under-3-min edit, straight from the scene (no lyrics, no hook pill).

usage: python3 tools/clip_covers.py songs/<slug> [--reuse-picks]
For every clip in build/clips.json: score 8 clean low-res frames from after the hook (t > 3.3 s), render the best one at
1080x1920, slide it down by `cover_shift_y` (song.yaml, fraction of the height) so the scene's centerpiece sits between
the hook text (song.yaml `cover_lines`, else `thumb_lines`, plus `thumb_sub`; a clip can set its own
`cover_lines`) and the title pill, and write <out>/Covers/<clip> - cover.jpg with tools/reel_covers.cover.
"""
import os, sys, json, tempfile
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from studio.config import load_song, public_name
from studio.render import load_scene
from studio import core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel_covers as RC

def edit_to_song(t, segs):
    acc = 0.0
    for a, e in segs:
        if t < acc + (e - a): return a + (t - acc)
        acc += e - a
    return segs[-1][1] - 0.1

def shift_down(a, sy):
    if sy <= 0: return a
    H, W = a.shape[:2]; M = np.float32([[1, 0, 0], [0, 1, H * sy]])
    sh = cv2.warpAffine(a.astype(np.float32), M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    m = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    m = cv2.GaussianBlur(m, (0, 0), W * 0.02)[..., None]
    fill = cv2.GaussianBlur(a.astype(np.float32), (0, 0), W * 0.05) * 0.45
    return np.clip(sh * m + fill * (1 - m), 0, 255).astype(np.uint8)

def place(a, sy, scale=1.0):
    """Slide the frame down by sy (fraction of the height) and, with scale < 1, shrink it about its center first, so a
    tall centerpiece fits between the hook text and the title pill. The uncovered margin is a soft, darker blur of the
    same frame with a wide feather, so the shrunken picture doesn't read as a box."""
    if scale >= 0.999: return shift_down(a, sy)
    H, W = a.shape[:2]
    M = np.float32([[scale, 0, W * (1 - scale) / 2], [0, scale, H * sy + H * (1 - scale) / 2]])
    sh = cv2.warpAffine(a.astype(np.float32), M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    m = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    r = max(3, int(W * 0.035)); m = cv2.erode(m, np.ones((2 * r + 1, 2 * r + 1), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), W * 0.03)[..., None]
    bg = cv2.GaussianBlur(shift_down(a, sy).astype(np.float32), (0, 0), W * 0.035) * 0.62
    return np.clip(sh * m + bg * (1 - m), 0, 255).astype(np.uint8)

def main(song_dir):
    song = load_song(song_dir); sc = load_scene(song_dir); b = song["build"]
    st = json.load(open(os.path.join(b, "clips.json")))
    hook, acc = RC.SONGS.get(song["title"], ("ANIMATED THIS", "#" + str(song.get("accent", "d7ff3a")).lstrip("#")))
    if song.get("cover_color"): acc = "#" + str(song["cover_color"]).lstrip("#")   # song.yaml override (badge, hook line, title pill)
    od = os.path.join(song["out_dir"], "Covers"); os.makedirs(od, exist_ok=True)
    cl = {c["label"]: c for c in song.get("clips", [])}
    # per cover (a clip in song.yaml, or song.yaml `edit_cover` for the under-3-min edit): cover_lines, and optionally
    # cover_t (song time of the frame, instead of the automatic pick), cover_shift_y, cover_scale and cover_tone
    items = [(c["file"], c["start"], c["end"] - c["start"], None, cl.get(c.get("label"), c)) for c in st["clips"] if c.get("file")]
    if st.get("edit"): items.append((st["edit"]["file"], 0.0, st["edit"]["duration"], [tuple(s) for s in st["edit"]["segments"]], song.get("edit_cover") or {}))
    lines0 = song.get("cover_lines") or song.get("thumb_lines"); sub = song.get("cover_sub", song.get("thumb_sub"))
    sy = float(song.get("cover_shift_y", 0)); tmp = tempfile.mkdtemp(); core.STATE["clean"] = True; picks = {}
    if lines0: sy = float(song.get("cover_shift_y_ctx", sy + 0.06))   # the hook block is taller than CLAUDE / ANIMATED THIS
    pj = os.path.join(od, "picks.json"); old = json.load(open(pj)) if (REUSE and os.path.exists(pj)) else {}
    for name, start, d, segs, cfg in items:
        ts = [3.3 + (d - 4.3) * (k + 0.5) / 8 for k in range(8)]
        song_ts = [edit_to_song(t, segs) if segs else start + t for t in ts]
        best, bs = (float(cfg["cover_t"]) if cfg.get("cover_t") is not None else old.get(name)), -1e9
        for k, t in enumerate([] if best is not None else song_ts):
            p = os.path.join(tmp, f"s{k}.jpg"); Image.fromarray(sc.render_frame(t, 270, 480, int(t * 30))).save(p, quality=90)
            s = RC.score(p)
            if s > bs: best, bs = t, s
        fr = place(sc.render_frame(best, 1080, 1920, int(best * 30)), float(cfg.get("cover_shift_y", sy)), float(cfg.get("cover_scale", 1.0)))
        out = os.path.join(od, os.path.splitext(name)[0].replace("Instagram 9x16", "Instagram") + " - cover.jpg")
        tone = bool(cfg.get("cover_tone", song.get("cover_tone", True)))   # false: keep the frame's own colours (no duotone for pale UI frames)
        RC.cover(Image.fromarray(fr), public_name(song), hook, acc, tone=tone, lines=cfg.get("cover_lines") or lines0, sub=sub).save(out, quality=92); picks[name] = round(best, 2)
        print("cover", os.path.basename(out), "from t =", round(best, 2), flush=True)
    core.STATE["clean"] = False
    json.dump(picks, open(os.path.join(od, "picks.json"), "w"), indent=1)

REUSE = "--reuse-picks" in sys.argv   # keep the frames picked last time (only redraw the text)

if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")][0])
