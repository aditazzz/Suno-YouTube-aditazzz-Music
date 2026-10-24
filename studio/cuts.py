"""Step 4 — cuts: Reels, Shorts and the under-3:00 Instagram edit, all cut on downbeats.

usage: python -m studio.cuts songs/<slug> [--only reels|shorts|edit]
Needs build/video_9x16.mp4 (from studio.render). Writes into the song's output folder and build/clips.json.

Rules baked in (see docs/lessons.md):
- Shorts stay under 60 s (a Short over 1 min with any Content ID claim is blocked; your own distributed song can trigger it).
- No black first frame: clips start hard on picture; the hero/first clip opens on the cover frame (song.yaml cover_time).
- Instagram only recommends Reels <= 3:00 to non-followers -> the edit targets <= 2:59.
- Cuts land on downbeats; a sung pickup just before a resume point moves the resume one bar earlier.
- Lyric lines that belong to removed audio are hidden at each join (re-rendered with a lyric filter).
"""
import os, sys, json, argparse, subprocess
import numpy as np, cv2
from .config import load_song
from . import core
from .render import load_scene, ffmpeg_writer, SIZES

ENC = ["-c:v", "libx264", "-preset", "medium", "-b:v", "4M", "-maxrate", "6M", "-bufsize", "10M", "-pix_fmt", "yuv420p"]
SHORT_MAX = 58.0; EDIT_MAX = 179.0

def snap_db(db, t, mode="near"):
    if mode == "le": c = db[db <= t + 1e-3]; return float(c[-1]) if len(c) else 0.0
    if mode == "ge": c = db[db >= t - 1e-3]; return float(c[0]) if len(c) else float(db[-1])
    return float(db[np.argmin(abs(db - t))])

def secs_of(secs, kind): return [s for s in secs if s["kind"] == kind]

def auto_clips(secs, db, dur):
    ch = secs_of(secs, "chorus"); vs = secs_of(secs, "verse"); br = secs_of(secs, "bridge"); bu = secs_of(secs, "build"); pre = secs_of(secs, "pre")
    clips = []
    def clip(kind, label, a, b, cover=False):
        a = snap_db(db, a, "le"); b = min(dur - 0.2, b)
        bb = snap_db(db, b, "le"); b = bb if bb - a > 12 else b
        clips.append({"kind": kind, "label": label, "start": round(a, 3), "end": round(b, 3), "cover": cover})
    if vs:  # the setup / opening joke
        bts = db  # opening reel: start right before the first sung word, never inside the fade-in
        a = max(1.4, vs[0]["first_word_t"] - 0.35)
        clips.append({"kind": "reel", "label": "setup", "start": round(a, 3), "end": round(snap_db(db, a + 20, "le"), 3), "cover": True})
    if ch:  # the hero: open ON the first sung word of the chorus (no lead-in: viewers decide in ~1 s)
        c = ch[0]; a = c["first_word_t"] - 0.15
        clips.append({"kind": "reel", "label": "chorus", "start": round(a, 3), "end": round(snap_db(db, min(c["e"], a + 30), "le"), 3), "cover": False})
    if br:
        b0 = br[0]; clip("reel", "bridge", b0["s"], min(b0["e"] + 1.5, b0["s"] + 29.5))
    if ch:
        c = ch[0]; a = (pre[0]["first_word_t"] if pre and pre[0]["s"] < c["s"] else c["first_word_t"]) - 0.15
        clips.append({"kind": "short", "label": "first chorus", "start": round(a, 3), "end": round(min(c["e"], a + 40), 3), "cover": False})
    if len(ch) > 1:
        c = ch[-1]; a = (bu[-1]["first_word_t"] if bu and bu[-1]["e"] <= c["s"] + 0.5 else c["first_word_t"]) - 0.15
        clips.append({"kind": "short", "label": "build to final chorus" if bu else "final chorus", "start": round(a, 3),
                      "end": round(min(dur - 0.2, c["e"], a + 40), 3), "cover": False})
    return clips

def plan_edit(secs, db, dur, timing_lines, target=EDIT_MAX - 0.4):
    """Return keep segments [(a,b)] so the edit fits under 3:00."""
    if dur <= target: return [(0.0, dur)]
    R = dur - target
    ch_idx = [i for i, s in enumerate(secs) if s["kind"] == "chorus"]
    if not ch_idx: return [(0.0, target)]
    first_end_i = ch_idx[0]
    while first_end_i + 1 < len(secs) and secs[first_end_i + 1]["kind"] in ("post",): first_end_i += 1
    last_i = ch_idx[-1]
    while last_i - 1 > first_end_i and secs[last_i - 1]["kind"] in ("build", "pre") and secs[last_i - 1]["name"] != secs[first_end_i]["name"]: last_i -= 1
    middle = secs[first_end_i + 1:last_i]
    bridge = [s for s in middle if s["kind"] == "bridge"]
    removable = [s for s in middle if s["kind"] != "bridge"]
    m0 = secs[first_end_i]["e"]
    keep_mid = []; removed = 0.0
    if bridge:
        b = bridge[0]; removed = b["s"] - m0 + sum(s["e"] - s["s"] for s in middle if s["s"] >= b["e"])
        # keep bridge, drop everything else in the middle; trim the bridge if still too long
        bs, be = b["s"], b["e"]; E = R - removed
        if E > 0:
            bar = float(np.median(np.diff(db)))
            nb = int(np.ceil(E / bar)); total_bars = int(round((be - bs) / bar))
            ls = [(L["s"], L["wt"][-1]) for L in timing_lines]
            def line_done(c, slack):   # every line that started before c has finished its last word
                return all(last < c - slack for st, last in ls if st < c - 0.02)
            clean_cut = lambda c: line_done(c, 0.25)
            clean_resume = lambda c: line_done(c, 0.1) and not any(c - 0.7 < st < c - 0.02 for st, _ in ls)
            pref = max(2, int((total_bars - nb) * 0.4)); best = None
            for extra in range(0, 3):
                for dh in sorted(range(-pref + 1, total_bars), key=abs):
                    h = pref + dh
                    if h < 1 or h + nb + extra > total_bars: continue
                    c0 = snap_db(db, bs + h * bar); c1 = snap_db(db, c0 + (nb + extra) * bar)
                    if c1 <= be and clean_cut(c0) and clean_resume(c1): best = (c0, c1); break
                if best: break
            if not best:
                c0 = snap_db(db, bs + pref * bar); best = (c0, min(be, snap_db(db, c0 + nb * bar)))
            c0, c1 = best
            keep_mid = [(bs, c0), (c1, be)] if c1 < be else [(bs, c0)]
        else:
            keep_mid = [(bs, be)]
        segs = [(0.0, m0)] + keep_mid + [(secs[last_i]["s"], dur)]
    else:
        acc = 0.0; cut_until = m0
        for s in removable:
            acc += s["e"] - s["s"]; cut_until = s["e"]
            if acc >= R: break
        segs = [(0.0, m0), (cut_until, dur)]
    # merge contiguous and trim the tail if still long
    out = []
    for a, b in segs:
        if out and abs(out[-1][1] - a) < 1e-3: out[-1] = (out[-1][0], b)
        elif b - a > 0.5: out.append((a, b))
    total = sum(b - a for a, b in out)
    if total > EDIT_MAX - 0.2:
        a, b = out[-1]; out[-1] = (a, b - (total - (EDIT_MAX - 0.25)))
    return out

def cover_png(song, sc):
    p = os.path.join(song["build"], "cover_9x16.png")
    if not os.path.exists(p):
        from PIL import Image
        t = float(song.get("cover_time", 30)); Image.fromarray(sc.render_frame(t, 1080, 1920, int(t * 30))).save(p)
    return p

HOOK_DUR = 3.0
def hook_png(song, text, accent=None, y=None):
    """On-screen hook for the first ~3 s of a Short/Reel: big, bold, inside the safe frame, below the top bar."""
    from PIL import Image
    W, H = SIZES["9x16"]; img = np.zeros((H, W, 3), np.float32); alpha = np.zeros((H, W), np.float32)
    accent = core.hexc(accent) if isinstance(accent, str) else (accent if accent is not None else core.hexc('ff3d9a'))
    S = core.SAFE_9x16
    fs = int(song.get("hook_fs", 86)); maxw = W * (S['right'] - S['left'] - 0.06)   # song.yaml hook_fs: a smaller pill for scenes with a full top band
    while True:
        words = text.split(); rows = [[]]
        for w in words:
            if rows[-1] and core.text_w(" ".join(rows[-1] + [w]), core.F_DISP, fs) > maxw: rows.append([w])
            else: rows[-1].append(w)
        if len(rows) <= 3 or fs <= 58: break
        fs -= 4
    lh = fs * 1.18; bw = max(core.text_w(" ".join(r), core.F_DISP, fs) for r in rows) + fs * 1.2; bh = lh * len(rows) + fs * 0.9
    y = float(y if y is not None else song.get("hook_y", 0.135))                        # per-song (or per-clip) height
    y = min(max(y, S['top']), S['bottom'] - bh / H)                                     # never under the top bar or the captions
    x0, y0 = (W - bw) / 2, H * y
    m = np.zeros((H, W), np.float32); r = int(fs * 0.45)
    xi, yi, wi, hi = int(x0), int(y0), int(bw), int(bh)
    cv2.rectangle(m, (xi + r, yi), (xi + wi - r, yi + hi), 1.0, -1); cv2.rectangle(m, (xi, yi + r), (xi + wi, yi + hi - r), 1.0, -1)
    for cx, cy in ((xi + r, yi + r), (xi + wi - r, yi + r), (xi + r, yi + hi - r), (xi + wi - r, yi + hi - r)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
    img += m[..., None] * core.hexc('0d0b1a'); alpha = np.maximum(alpha, m * 0.88)
    bar = np.zeros((H, W), np.float32); cv2.rectangle(bar, (xi + r, yi + hi - 12), (xi + wi - r, yi + hi), 1.0, -1)
    img = img * (1 - bar[..., None]) + bar[..., None] * accent; alpha = np.maximum(alpha, bar)
    for i, row in enumerate(rows):
        sp = core.sprite(" ".join(row), core.F_DISP, fs)
        a = sp[0]; h, w = a.shape; x = int(W / 2 - w / 2); y = int(y0 + fs * 0.42 + i * lh - sp[2])
        reg = img[y:y + h, x:x + w]; reg *= (1 - a[..., None]); reg += a[..., None] * core.WHITE
        alpha[y:y + h, x:x + w] = np.maximum(alpha[y:y + h, x:x + w], a)
    rgba = np.dstack([np.clip(img, 0, 1) * 255, alpha * 255]).astype(np.uint8)
    p = os.path.join(song["build"], f"hook_{abs(hash((text, y))) % 10**8}.png"); Image.fromarray(rgba, "RGBA").save(p); return p

OPEN_HOLD, OPEN_FADE = 0.25, 0.3
SAFE_SCALE = None   # song.yaml `vertical_safe_scale`: shrink the 9:16 picture into the area
                    # phones keep (the Shorts/Reels players crop ~9% off each side and put buttons on the right)
def enc_piece(src, a, b, out, cover=None, extra_vf=None, hook=None, open_cover=None, safe=None):
    """hook: on-screen hook for the first HOOK_DUR s. safe: shrink the picture (with its hook) to this scale over a dark,
    blurred copy of itself, so nothing sits where the phone players crop. open_cover: a cover image (e.g. the Instagram
    cover) shown full-frame for the first OPEN_HOLD s and faded out over OPEN_FADE s, so the file's first frame (what
    Instagram and phones show) is the cover. cover: a still shown for the first 0.2 s (clips without a hook)."""
    W, H = SIZES["9x16"]; safe = safe or SAFE_SCALE
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src]; n = 1; ch = []; cur = "[0:v]"
    if hook:
        cmd += ["-loop", "1", "-t", f"{HOOK_DUR + 0.1}", "-i", hook]; hi = n; n += 1
        ch.append(f"[{hi}:v]format=rgba,fade=t=out:st={HOOK_DUR - 0.35:.2f}:d=0.35:alpha=1[h]")
        ch.append(f"{cur}[h]overlay=0:0:eof_action=pass:enable='lt(t,{HOOK_DUR})'[vh]"); cur = "[vh]"
    if safe:
        sw, sh = int(round(W * safe / 2)) * 2, int(round(H * safe / 2)) * 2
        ch.append(f"{cur}split=2[sa][sb]")
        ch.append(f"[sa]scale={W}:{H},gblur=sigma=30,colorchannelmixer=rr=0.4:gg=0.4:bb=0.4[sbg]")
        ch.append(f"[sb]scale={sw}:{sh}[sfg]")
        ch.append(f"[sbg][sfg]overlay={(W - sw) // 2}:{(H - sh) // 2}[vs]"); cur = "[vs]"
    if open_cover:
        cmd += ["-loop", "1", "-t", f"{OPEN_HOLD + OPEN_FADE + 0.1}", "-i", open_cover]; oi = n; n += 1
        ch.append(f"[{oi}:v]scale={W}:{H},format=rgba,fade=t=out:st={OPEN_HOLD:.2f}:d={OPEN_FADE:.2f}:alpha=1[oc]")
        ch.append(f"{cur}[oc]overlay=0:0:eof_action=pass:enable='lt(t,{OPEN_HOLD + OPEN_FADE:.2f})'[vo]"); cur = "[vo]"
    elif cover and not hook:
        cmd += ["-loop", "1", "-t", "0.2", "-i", cover]; ci = n; n += 1
        ch.append(f"{cur}[{ci}:v]overlay=enable='lt(t,0.2)'[vc]"); cur = "[vc]"
    if extra_vf: ch.append(f"{cur}{extra_vf}[v]"); cur = "[v]"
    if ch:
        if cur != "[v]": ch.append(f"{cur}null[v]")
        cmd += ["-filter_complex", ";".join(ch), "-map", "[v]"]
    subprocess.run(cmd + ENC + ["-an", out], check=True)

def render_patch(song, sc, a, b, flt, out):
    W, H = SIZES["9x16"]; core.STATE["lyric_filter"] = flt
    p = ffmpeg_writer(out, W, H, crf=14)
    for fi in range(int(round(a * 30)), int(round(b * 30))): p.stdin.write(sc.render_frame(fi / 30, W, H, fi).tobytes())
    p.stdin.close(); p.wait(); core.STATE["lyric_filter"] = None

def first_lit(vid, t0, limit=1.5, thresh=14):
    """Never open on black: move the start forward to the first frame with real picture."""
    import cv2
    cap = cv2.VideoCapture(vid); t = t0
    while t < t0 + limit:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        if ok and fr.mean() > thresh: break
        t += 0.1
    cap.release(); return round(min(t, t0 + limit), 3)

def make_clip(song, vid, c, idx, cover, sc=None, lines=None):
    if not c.get("cover"): c["start"] = first_lit(vid, c["start"])
    T = song["title"]; d = c["end"] - c["start"]; ds = int(round(d))
    name = f"{T} - {'Reel' if c['kind']=='reel' else 'Short'} {idx} ({c['label']}, {ds}s).mp4"
    out = os.path.join(song["out_dir"], name); tmp = os.path.join(song["build"], "clip_v.mp4")
    hook = c.get("hook") or song.get("clip_copy", {}).get(c["label"], {}).get("onscreen")
    hp = hook_png(song, hook, song.get("accent"), c.get("hook_y")) if hook else None
    a0 = c["start"]
    stale = sc is not None and lines is not None and d > HOOK_DUR + 1.0 and any(L["s"] < a0 - 0.05 <= L["e"] + 0.6 for L in lines)
    if stale:   # a line from before the clip is still fading out at frame 0: re-render the opening without it
        b = song["build"]; P = HOOK_DUR + 0.2
        raw = os.path.join(b, "clip_patch.raw.mp4"); p1 = os.path.join(b, "clip_p1.mp4"); p2 = os.path.join(b, "clip_p2.mp4")
        render_patch(song, sc, a0, a0 + P, (lambda L, a0=a0: L["s"] >= a0 - 0.05), raw)
        enc_piece(raw, 0, P, p1, None, None, hook=hp)
        enc_piece(vid, a0 + P, c["end"], p2, None, f"fade=t=out:st={d - P - 0.6:.2f}:d=0.6")
        lst = os.path.join(b, "clip_list.txt"); open(lst, "w").write(f"file '{os.path.basename(p1)}'\nfile '{os.path.basename(p2)}'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", tmp], check=True)
    else:
        enc_piece(vid, c["start"], c["end"], tmp, cover if (c.get("cover") and not hp) else None, f"fade=t=out:st={d - 0.6:.2f}:d=0.6", hook=hp)
    c["hook"] = hook
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ss", f"{c['start']:.3f}", "-t", f"{d:.3f}", "-i", song["audio"], "-map", "0:v", "-map", "1:a",
                    "-af", f"afade=t=in:st=0:d=0.05,afade=t=out:st={d - 1.2:.2f}:d=1.2,apad", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-t", f"{d:.3f}", "-movflags", "+faststart", out], check=True)   # apad + -t: a clip that runs into the end card keeps it
    c["file"] = name; print("wrote", name)

def seg_filter(song, a, e):
    """Lyric lines kept in the re-rendered opening of a resumed edit segment: lines that start inside it, plus (with
    edit_keep_running in song.yaml) a line that is still being sung across the splice, e.g. a chorus spliced into a chorus."""
    keep = bool(song.get("edit_keep_running"))
    return lambda L: a - 0.05 <= L["s"] < e or (keep and L["s"] < a and L["e"] > a + 0.5)

def make_edit(song, vid, sc, segs, cover, lines):
    b = song["build"]; pieces = []
    for k, (a, e) in enumerate(segs):
        flt = seg_filter(song, a, e)
        if k > 0:  # re-render the first 3 s of each resumed segment with stray lyric lines hidden
            pe = min(e, a + 3.0); pp = os.path.join(b, f"edit_patch{k}.mp4"); raw = pp + ".raw.mp4"
            render_patch(song, sc, a, pe, flt, raw); enc_piece(raw, 0, pe - a, pp); pieces.append(pp)
            a = pe
        if e - a > 0.05:
            hk = song.get("edit_hook") if k == 0 else None
            pp = os.path.join(b, f"edit_seg{k}.mp4"); enc_piece(vid, a, e, pp, cover if (k == 0 and not hk) else None, hook=hook_png(song, hk, song.get("accent"), song.get("edit_hook_y")) if hk else None); pieces.append(pp)
    lst = os.path.join(b, "edit_list.txt"); open(lst, "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in pieces))
    allv = os.path.join(b, "edit_video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", allv], check=True)
    total = sum(e - a for a, e in segs)
    # song.yaml edit_xfade {join index: seconds}: a longer audio crossfade where two very different textures meet (a
    # crossfade overlaps the pieces, so the outgoing piece's audio runs on by the same amount to stay in sync)
    xf = {int(k): float(v) for k, v in (song.get("edit_xfade") or {}).items()}
    def seg_audio(k, a, e):
        d = xf.get(k + 1, 0.04) if k + 1 < len(segs) else 0.0
        fi = ",afade=t=in:st=0:d=0.3" if k == 0 and a > 0.05 else ""         # an edit that starts mid-song fades in
        return f"[0:a]atrim={a:.3f}:{e + d:.3f},asetpts=PTS-STARTPTS{fi}[a{k}];"
    parts = "".join(seg_audio(k, a, e) for k, (a, e) in enumerate(segs))
    chain = "[a0]"; fc = parts
    for k in range(1, len(segs)):
        fc += f"{chain}[a{k}]acrossfade=d={xf.get(k, 0.04):.3f}:c1=tri:c2=tri[x{k}];"; chain = f"[x{k}]"
    fc += f"{chain}afade=t=out:st={total - 1.3:.2f}:d=1.3[a]"
    aud = os.path.join(b, "edit_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", song["audio"], "-filter_complex", fc, "-map", "[a]", aud], check=True)
    out = os.path.join(song["out_dir"], f"{song['title']} - Instagram 9x16 (under 3 min).mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", allv, "-i", aud, "-map", "0:v", "-map", "1:a", "-vf", f"fade=t=out:st={total - 0.8:.2f}:d=0.8",
                    *ENC, "-c:a", "aac", "-b:a", "320k", "-af", "apad", "-t", f"{total:.3f}", "-movflags", "+faststart", out], check=True)   # keep the end card after the song ends
    print("wrote", os.path.basename(out), f"{total:.1f}s")
    return os.path.basename(out), total

def main(song_dir, only=None):
    song = load_song(song_dir); b = song["build"]; os.makedirs(song["out_dir"], exist_ok=True)
    secs = json.load(open(os.path.join(b, "sections.json"))); bt = json.load(open(os.path.join(b, "beats.json")))
    lines = json.load(open(os.path.join(b, "timed.json")))
    db = np.array(bt["downbeats"]); dur = bt["duration"]; vid = os.path.join(b, "video_9x16.mp4")
    sc = load_scene(song_dir); cover = cover_png(song, sc)
    clips = song.get("clips") or auto_clips(secs, db, dur)
    for c in clips:
        if c["kind"] == "short" and c["end"] - c["start"] > SHORT_MAX: c["end"] = c["start"] + SHORT_MAX
    res = {"clips": clips}
    n = {"reel": 0, "short": 0}
    if only in (None, "reels", "shorts"):
        for c in clips:
            n[c["kind"]] += 1
            if only and not only.startswith(c["kind"]): continue
            make_clip(song, vid, c, n[c["kind"]], cover, sc, lines)
    if only in (None, "edit") and dur > EDIT_MAX:
        segs = song.get("edit_segments") or plan_edit(secs, db, dur, lines)
        name, total = make_edit(song, vid, sc, [tuple(s) for s in segs], cover, lines)
        res["edit"] = {"file": name, "segments": segs, "duration": total}
    json.dump(res, open(os.path.join(b, "clips.json"), "w"), indent=1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("song_dir"); ap.add_argument("--only"); ap.add_argument("--plan", action="store_true")
    a = ap.parse_args()
    if a.plan:
        song = load_song(a.song_dir); b = song["build"]
        secs = json.load(open(os.path.join(b, "sections.json"))); bt = json.load(open(os.path.join(b, "beats.json")))
        lines = json.load(open(os.path.join(b, "timed.json"))); db = np.array(bt["downbeats"])
        for c in (song.get("clips") or auto_clips(secs, db, bt["duration"])): print(c)
        segs = plan_edit(secs, db, bt["duration"], lines); print("edit:", [(round(x, 2), round(y, 2)) for x, y in segs], round(sum(y - x for x, y in segs), 1))
    else: main(a.song_dir, a.only)
