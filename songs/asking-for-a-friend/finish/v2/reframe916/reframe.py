#!/usr/bin/env python3
"""9:16 reframe pass over a 16:9 master (reframe916, Sun Nov 8). Re-runnable on any master assemble_v2 builds.

  PY=python3
  $PY finish/v2/reframe916/reframe.py analyse [--name master_v2] [--res 1080|1440] [--only S001,S002] [--reset]
  $PY finish/v2/reframe916/reframe.py render  [--name master_v2] [--res ...] [--only ...] [--jobs 3] [--draft-out <mp4>]
  $PY finish/v2/reframe916/reframe.py sheet   [--name master_v2] [--every 8] [--extra S056,S138]

Source: the master's own UNGRADED lossless row segments <film>/master/segs_v2_<res>/<shot>.mkv (rows from
finish/v2/<name>_build.json). --res defaults to 1440 when segs_v2_1440 holds every row (after a DELIVER=1 run), else 1080.
The film look (AFF_look_v1.cube from finish/lookdev/tools/make_lut.py + vignette) is applied once on the 9:16 frame.

crops.yaml (hand-editable; an entry with `auto: false` is never overwritten by analyse):
  S012: {mode: crop, keys: [[0, 0.52, 1.0, 0.5], [14, 0.60, 1.0, 0.5]]}   # [frame offset in shot, x-centre 0..1 of the 16:9
        width, zoom (1 = full height; >1 in; 0.7..1 = zoom-out with a soft reflected fill top/bottom, no letterbox), y-centre 0..1];
        smoothstep-eased between keys (`ease: linear` on the entry for a constant rate), held outside them; never crosses a cut
  S050: {mode: fit}                      # whole 16:9 picture, width 1080, over a dark blurred fill (nothing cropped)
  S049: {mode: native, dir: finish/v2/car_uv/S049/916}   # native 1080x1920 frames f%05d.png (film frame numbers)
render: one H.264 segment per shot in <film>/master/segs916_<name>_<res>/ (signature-cached: only changed shots re-encode),
then a frame-exact concat -> the muted draft + a copy muxed with the song WAV.
"""
import argparse, concurrent.futures as cf, csv, glob, hashlib, json, os, subprocess, sys

import cv2
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
SONG = os.path.abspath(os.path.join(V2, "..", ".."))
FILM = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2")
WAV = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2 (clean).wav")
FPS = 24
OW, OH = 1080, 1920
CROPS = os.path.join(HERE, "crops.yaml")
ANALYSIS = os.path.join(HERE, "analysis.json")
VERSION = "rf3"
TEXT_MIN_PX = 58            # 9:16 lyric/text minimum (CLAUDE.md)
NATIVE = {"S049": "finish/v2/car_uv/S049/916", "S103b": "finish/v2/car_uv/S103b/916",
          "S118b": "finish/v2/car_uv/S118b/916", "S141b": "finish/v2/car_uv/S141b/916"}
NATIVE_FALLBACK = os.path.join(FILM, "renders", "routeB_916")
SCREEN_SOURCES = ("port2d", "kit")


def sh(*a, **k):
    return subprocess.run(a, check=True, capture_output=True, text=True, **k)


def load_rows(name):
    b = json.load(open(os.path.join(V2, f"{name}_build.json")))
    return b, b["rows"]


def pick_res(rows, want):
    if want:
        return int(want)
    d = f"{FILM}/master/segs_v2_1440"
    return 1440 if all(os.path.exists(f"{d}/{r['shot']}.mkv") for r in rows) else 1080


def seg_path(res, shot):
    return f"{FILM}/master/segs_v2_{res}/{shot}.mkv"


def edl_world():
    return {r["shot"]: r for r in csv.DictReader(open(os.path.join(SONG, "finish", "edl_routeB.csv")))}


def is_screen(row, edl):
    e = edl.get(row["shot"], {})
    return e.get("world") == "2D" or any(s in row["source"] for s in SCREEN_SOURCES)


def native_dir(shot):
    for d in ([os.path.join(SONG, NATIVE[shot])] if shot in NATIVE else []) + [os.path.join(NATIVE_FALLBACK, shot)]:
        if os.path.isdir(d) and glob.glob(f"{d}/f*.png"):
            return d
    return None


def decode(path, w, h, n=None):
    """all frames of a segment as uint8 RGB arrays (h, w, 3)"""
    vf = [] if (w, h) == probe_wh(path) else ["-vf", f"scale={w}:{h}:flags=area"]
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       check=True, capture_output=True).stdout
    a = np.frombuffer(p, np.uint8).reshape(-1, h, w, 3)
    return a


def probe_wh(path):
    o = sh("ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", path).stdout
    w, h = o.strip().split(",")[:2]
    return int(w), int(h)


# ---------------------------------------------------------------- analysis
def saliency(img):
    """cheap subject map on a small RGB frame: centre-surround contrast + edges + brightness + colour, mild centre prior"""
    f = img.astype(np.float32) / 255
    g = f.mean(2)
    cs = np.abs(g - cv2.GaussianBlur(g, (0, 0), 18))
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    col = np.linalg.norm(lab[..., 1:] - cv2.GaussianBlur(lab[..., 1:], (0, 0), 24), axis=2) / 40
    ed = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    br = cv2.GaussianBlur(g, (0, 0), 6)

    def nz(x):
        return x / (np.percentile(x, 99.5) + 1e-6)
    s = nz(cv2.GaussianBlur(cs, (0, 0), 3)) + 0.6 * nz(cv2.GaussianBlur(ed, (0, 0), 4)) + 0.5 * nz(br) ** 2 + 0.6 * nz(col)
    h, w = g.shape
    xs = (np.arange(w) - w / 2) / w
    s *= np.exp(-xs ** 2 / (2 * 0.38 ** 2))[None, :]
    return s


_FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") if hasattr(cv2, "CascadeClassifier") else None


def best_x(img, cwn):
    """-> (x-centre 0..1, captured fraction) for a window cwn (fraction of width) on frame img"""
    s = saliency(img)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    for (x, y, w, h) in (_FACE.detectMultiScale(g, 1.1, 5, minSize=(16, 16)) if _FACE is not None else []):
        s[y:y + h, x:x + w] += 3 * s.max()
    p = s.sum(0)
    w = len(p)
    cw = max(1, int(round(cwn * w)))
    cs = np.concatenate([[0], np.cumsum(p)])
    win = cs[cw:] - cs[:-cw]
    centre = np.arange(len(win)) + cw / 2
    win = win * (1 - 0.15 * np.abs(centre / w - 0.5))      # tie-break toward the middle
    i = int(np.argmax(win))
    return (i + cw / 2) / w, float((cs[i + cw] - cs[i]) / (cs[-1] + 1e-9))


def ocr_lines(img):
    """tesseract line boxes [(x0, y0, x1, y1, text)] on a full-res RGB frame"""
    tmp = os.path.join(HERE, "_ocr.png")
    cv2.imwrite(tmp, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    out = []
    for psm in ("11", "3"):
        try:
            t = sh("tesseract", tmp, "-", "--psm", psm, "tsv").stdout
        except subprocess.CalledProcessError:
            continue
        lines = {}
        for ln in t.splitlines()[1:]:
            c = ln.split("\t")
            if len(c) < 12 or not c[11].strip():
                continue
            conf, txt = float(c[10]), c[11].strip()
            if conf < 65 or sum(ch.isalnum() for ch in txt) < 2:
                continue
            k = (c[2], c[3], c[4])
            x, y, w, h = map(int, c[6:10])
            if h < 8 or h > img.shape[0] * 0.3:
                continue
            L = lines.setdefault(k, [x, y, x + w, y + h, []])
            L[0], L[1], L[2], L[3] = min(L[0], x), min(L[1], y), max(L[2], x + w), max(L[3], y + h)
            L[4].append((txt, h))
        for L in lines.values():
            hs = sorted(h for _, h in L[4])
            out.append((L[0], L[1], L[2], L[3], " ".join(t for t, _ in L[4]), hs[len(hs) // 2]))
        if out:
            break
    os.remove(tmp)
    return out


def analyse(a):
    build, rows = load_rows(a.name)
    res = pick_res(rows, a.res)
    edl = edl_world()
    only = set(a.only.split(",")) if a.only else None
    crops = yaml.safe_load(open(CROPS)) if os.path.exists(CROPS) and not a.reset else {}
    crops = crops or {}
    ana = json.load(open(ANALYSIS)) if os.path.exists(ANALYSIS) else {}
    W, H = {1080: (1920, 1080), 1440: (2560, 1440)}[res]
    cwn = (H * 9 / 16) / W                       # window width as fraction of 16:9 width at zoom 1
    scale = OH / H                               # source px -> 9:16 px at zoom 1
    for r in rows:
        sh_, n = r["shot"], r["b"] - r["a"] + 1
        if only and sh_ not in only:
            continue
        if sh_ in crops and crops[sh_].get("auto") is False:
            continue
        nd = native_dir(sh_)
        if nd:
            have = sum(os.path.exists(f"{nd}/f{f:05d}.png") for f in range(r["a"], r["b"] + 1))
            crops[sh_] = {"mode": "native", "dir": os.path.relpath(nd, SONG) if nd.startswith(SONG) else nd, "auto": True}
            ana[sh_] = {"native_frames": f"{have}/{n}"}
            if have == n:
                continue
            crops[sh_]["note"] = f"only {have}/{n} native frames; missing ones fall back to the crop keys"
        small = decode(seg_path(res, sh_), 480, 270)
        offs = sorted({min(n - 1, max(0, int(round(n * q)))) for q in (0.12, 0.5, 0.88)})
        picks = [best_x(small[o], cwn) for o in offs]
        xs = [p[0] for p in picks]
        cap = float(np.mean([p[1] for p in picks]))
        entry = {"mode": "crop", "auto": True}
        mono = (xs[0] <= xs[len(xs) // 2] <= xs[-1]) or (xs[0] >= xs[len(xs) // 2] >= xs[-1])
        d = abs(xs[-1] - xs[0])
        speed = d / max(1, offs[-1] - offs[0]) * FPS     # fraction of width per second
        if len(xs) > 1 and mono and 0.06 <= d and speed <= 0.25:
            entry["keys"] = [[offs[0], round(xs[0], 3), 1.0, 0.5], [offs[-1], round(xs[-1], 3), 1.0, 0.5]]
        else:
            entry["keys"] = [[0, round(float(np.median(xs)), 3), 1.0, 0.5]]
        info = {"cap": round(cap, 2), "xs": [round(x, 3) for x in xs], "screen": is_screen(r, edl)}
        if info["screen"]:
            full = decode(seg_path(res, sh_), W, H)
            lines = []
            for o in sorted({int(n * 0.55), n - 3 if n > 4 else n - 1}):
                lines += ocr_lines(full[o])
            del full
            info["lines"] = [[x0, y0, x1, y1, t[:40], h] for x0, y0, x1, y1, t, h in lines]
            pad = 12 * H / 1080
            cw = H * 9 / 16
            if lines:
                u0, u1 = min(l[0] for l in lines), max(l[2] for l in lines)
                minh = min(l[5] for l in lines)
                info["text_span_px"] = int(u1 - u0)
                info["min_line_px_916"] = int(minh * scale)
                fits = (u1 - u0) <= cw - 2 * pad
                big = minh * scale >= TEXT_MIN_PX
                info["crop_ok"] = bool(fits and big)
                info["why"] = ("" if fits else f"text spans {int(u1 - u0)} px > window {int(cw - 2 * pad)} px; ") + \
                              ("" if big else f"smallest line ~{int(minh * scale)} px < {TEXT_MIN_PX} px in 9:16")
                if fits:
                    entry["keys"] = [[0, round(((u0 + u1) / 2) / W, 3), 1.0, 0.5]]
                if not info["crop_ok"]:
                    entry = {"mode": "fit", "auto": True, "note": "screen text would be cut/too small -> native 9:16 layout"}
            else:
                info["crop_ok"] = None
                info["why"] = "no text found by OCR (check by eye)"
        crops[sh_] = entry
        ana[sh_] = info
        print(f"{sh_:6s} {entry['mode']:6s} {entry.get('keys', '')} cap={info.get('cap')} {info.get('why', '')}", flush=True)
    yaml.safe_dump({k: crops[k] for k in sorted(crops, key=lambda s: next((i for i, r in enumerate(rows) if r['shot'] == s), 999))},
                   open(CROPS, "w"), default_flow_style=None, sort_keys=False, width=160)
    json.dump(ana, open(ANALYSIS, "w"), indent=1)
    print(f"res {res}: wrote {CROPS}")


# ---------------------------------------------------------------- render
def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


ZOOM_MIN = 0.7              # zoom < 1 = zoom-out past full height; the extra rows get a soft reflected fill (no letterbox)


def key_at(keys, o, linear=False):
    keys = sorted([list(k) + [1.0, 0.5][len(k) - 2:] if len(k) < 4 else list(k) for k in keys])
    if o <= keys[0][0]:
        k = keys[0]
    elif o >= keys[-1][0]:
        k = keys[-1]
    else:
        for k0, k1 in zip(keys, keys[1:]):
            if k0[0] <= o <= k1[0]:
                t = (o - k0[0]) / max(1e-9, k1[0] - k0[0])
                t = t if linear else ease(t)
                k = [o] + [k0[i] + (k1[i] - k0[i]) * t for i in range(1, 4)]
                break
    return float(k[1]), max(ZOOM_MIN, float(k[2])), float(k[3])


def crop_frame(img, cx, zoom, cy):
    H, W = img.shape[:2]
    ch = H / zoom
    cw = ch * OW / OH
    x0 = min(max(cx * W - cw / 2, 0), W - cw)
    y0 = min(max(cy * H - ch / 2, 0), H - ch) if ch <= H else cy * H - ch / 2
    s = OH / ch
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    if ch <= H:
        return cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    # zoom-out (Nov 8, short2_screen_fit): window taller than the source. Rows outside the picture are the frame mirrored
    # at its edge (continuous at the seam), then blurred and darkened more the further they are from it: reads as soft
    # out-of-focus ceiling/floor, never a hard letterbox bar. The bands stay inside the 9:16 top/bottom UI zones.
    out = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT_101)
    top, bot = -y0 * s, (H - y0) * s                 # output rows where the real picture starts / ends
    blur = cv2.GaussianBlur(out, (0, 0), 22)
    yy = np.arange(OH, dtype=np.float32)
    d = np.maximum(top - yy, yy - bot)               # >0 inside a band: distance from the seam in output px
    band = max(1.0, top, OH - bot)
    a = np.clip(d / 36.0, 0, 1)[:, None, None]       # blur ramps in over 36 px from the seam
    dark = (1 - 0.45 * np.clip(d / band, 0, 1) ** 1.2)[:, None, None]
    f = out.astype(np.float32) * (1 - a) + blur.astype(np.float32) * a
    f = np.where(d[:, None, None] > 0, f * dark, out.astype(np.float32))
    return np.clip(f + 0.5, 0, 255).astype(np.uint8)


def fit_frame(img):
    H, W = img.shape[:2]
    bg = crop_frame(img, 0.5, 1.0, 0.5)
    bg = cv2.resize(cv2.GaussianBlur(cv2.resize(bg, (OW // 8, OH // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (OW, OH),
                    interpolation=cv2.INTER_LINEAR)
    out = (bg.astype(np.float32) * 0.30).astype(np.uint8)
    fh = int(round(OW * H / W / 2)) * 2
    fg = cv2.resize(img, (OW, fh), interpolation=cv2.INTER_AREA)
    y0 = (OH - fh) // 2
    out[y0:y0 + fh] = fg
    return out


def look_vf():
    lut = os.path.join(SONG, "finish/lookdev/AFF_look_v1.cube")   # written by finish/lookdev/tools/make_lut.py
    return f"lut3d=file='{lut}':interp=tetrahedral,vignette=angle=0.30"


def shot_sig(res, r, entry):
    h = hashlib.sha1()
    sp = seg_path(res, r["shot"])
    sig = sp + ".sig"
    h.update((open(sig).read() if os.path.exists(sig) else str(os.path.getmtime(sp))).encode())
    h.update(json.dumps([VERSION, res, r["a"], r["b"], entry, look_vf()], sort_keys=True).encode())
    if entry.get("mode") == "native":
        d = entry["dir"] if os.path.isabs(entry["dir"]) else os.path.join(SONG, entry["dir"])
        for f in sorted(glob.glob(f"{d}/f*.png")):
            h.update(f"{os.path.basename(f)}{os.path.getmtime(f)}".encode())
    return h.hexdigest()


def render_shot(args):
    res, r, entry, outdir, vf = args
    sh_, n = r["shot"], r["b"] - r["a"] + 1
    out = f"{outdir}/{sh_}.mp4"
    sig = shot_sig(res, r, entry)
    if os.path.exists(out) and os.path.exists(out + ".sig") and open(out + ".sig").read() == sig:
        return sh_, "reused"
    W, H = {1080: (1920, 1080), 1440: (2560, 1440)}[res]
    src = decode(seg_path(res, sh_), W, H)
    if len(src) != n:
        raise RuntimeError(f"{sh_}: segment has {len(src)} frames, row says {n}")
    nd = None
    if entry.get("mode") == "native":
        nd = entry["dir"] if os.path.isabs(entry["dir"]) else os.path.join(SONG, entry["dir"])
    keys = entry.get("keys") or [[0, 0.5, 1.0, 0.5]]
    tmp = out + ".part.mp4"
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                            "-i", "-", "-vf", f"{vf},scale=out_color_matrix=bt709:out_range=tv,"
                            "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-g", "48", *tags,
                            "-an", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    fell = 0
    for o in range(n):
        f = r["a"] + o
        img = None
        if nd:
            p = f"{nd}/f{f:05d}.png"
            if os.path.exists(p):
                img = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
                if img.shape[:2] != (OH, OW):
                    img = cv2.resize(img, (OW, OH), interpolation=cv2.INTER_AREA)
            else:
                fell += 1
        if img is None:
            img = fit_frame(src[o]) if entry.get("mode") == "fit" else crop_frame(src[o], *key_at(keys, o, entry.get("ease") == "linear"))
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"{sh_}: encode failed")
    os.replace(tmp, out)
    open(out + ".sig", "w").write(sig)
    return sh_, "encoded" + (f" ({fell} native frames missing -> crop)" if fell else "")


def render(a):
    import time
    t0 = time.time()
    build, rows = load_rows(a.name)
    res = pick_res(rows, a.res)
    crops = yaml.safe_load(open(CROPS)) or {}
    outdir = f"{FILM}/master/segs916_{a.name}_{res}"
    os.makedirs(outdir, exist_ok=True)
    vf = look_vf()
    only = set(a.only.split(",")) if a.only else None
    jobs = [(res, r, crops.get(r["shot"], {"mode": "crop", "keys": [[0, 0.5, 1.0, 0.5]]}), outdir, vf)
            for r in rows if not only or r["shot"] in only]
    with cf.ProcessPoolExecutor(a.jobs) as ex:
        for shot, how in ex.map(render_shot, jobs):
            print(f"{shot}: {how}", flush=True)
    if only:
        print(f"--only: segments done in {time.time() - t0:.0f} s (no concat)")
        return
    total = sum(r["b"] - r["a"] + 1 for r in rows)
    lst = f"{outdir}/_list.txt"
    open(lst, "w").write("".join(f"file '{outdir}/{r['shot']}.mp4'\n" for r in rows))
    out = a.draft_out or os.path.join(SONG, "build", "video_9x16_v2_draft.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out)
    n = int(sh("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets",
               "-of", "csv=p=0", out).stdout.strip())
    song = out[:-4] + "_song.mp4"
    sh("ffmpeg", "-y", "-v", "error", "-i", out, "-i", WAV, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
       "-b:a", "256k", "-t", f"{total / FPS:.4f}", "-movflags", "+faststart", song)
    msg = f"res {res}: {out} ({n}/{total} frames{' OK' if n == total else ' MISMATCH'}), {song}, {time.time() - t0:.0f} s"
    print(msg)
    json.dump({"name": a.name, "res": res, "draft": out, "draft_song": song, "frames": n, "expected": total,
               "secs": round(time.time() - t0)}, open(os.path.join(HERE, f"render_{a.name}.json"), "w"), indent=1)


# ---------------------------------------------------------------- sheet
def safe_overlay(img):
    h, w = img.shape[:2]
    ov = img.copy()
    red = (200, 40, 40)
    cv2.rectangle(ov, (0, 0), (w, int(0.13 * h)), red, -1)
    cv2.rectangle(ov, (0, int(0.70 * h)), (w, h), red, -1)
    cv2.rectangle(ov, (0, 0), (int(0.09 * w), h), red, -1)
    cv2.rectangle(ov, (int(0.91 * w), 0), (w, h), red, -1)
    cv2.rectangle(ov, (int(0.80 * w), h // 2), (w, h), red, -1)
    return cv2.addWeighted(ov, 0.28, img, 0.72, 0)


def sheet(a):
    build, rows = load_rows(a.name)
    res = pick_res(rows, a.res)
    outdir = f"{FILM}/master/segs916_{a.name}_{res}"
    crops = yaml.safe_load(open(CROPS)) or {}
    pick = rows[::a.every]
    extra = set((a.extra or "").split(","))
    pick += [r for r in rows if (crops.get(r["shot"], {}).get("mode") == "native" or r["shot"] in extra) and r not in pick]
    pick.sort(key=lambda r: r["a"])
    cols = 10
    tw = 1600 // cols
    th = int(tw * OH / OW)
    lab = 22
    nrow = -(-len(pick) // cols)
    canvas = np.full((nrow * (th + lab), cols * tw, 3), 20, np.uint8)
    for i, r in enumerate(pick):
        n = r["b"] - r["a"] + 1
        o = n // 2
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{outdir}/{r['shot']}.mp4", "-vf", f"select=eq(n\\,{o}),scale={tw}:{th}",
                            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        img = safe_overlay(np.frombuffer(p, np.uint8).reshape(th, tw, 3).copy())
        y, x = (i // cols) * (th + lab), (i % cols) * tw
        canvas[y:y + th, x:x + tw] = img
        m = crops.get(r["shot"], {}).get("mode", "crop")[0].upper()
        cv2.putText(canvas, f"{r['shot']} f{r['a'] + o} {m}", (x + 3, y + th + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1,
                    cv2.LINE_AA)
    out = os.path.join(HERE, "sheet_916.jpg")
    cv2.imwrite(out, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(out, canvas.shape[1], "x", canvas.shape[0], len(pick), "frames")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["analyse", "render", "sheet"])
    ap.add_argument("--name", default="master_v2")
    ap.add_argument("--res", default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--every", type=int, default=8)
    ap.add_argument("--draft-out", default=None)
    ap.add_argument("--extra", default=None, help="sheet: also show these shots")
    a = ap.parse_args()
    {"analyse": analyse, "render": render, "sheet": sheet}[a.cmd](a)


if __name__ == "__main__":
    main()
