#!/usr/bin/env python3
"""Asking for a Friend: the 16:9 MASTER, assembled from final frames. Resumable: only changed EDL rows are re-encoded.

  python3 songs/asking-for-a-friend/finish/master/assemble_master.py \
      [--res 1080|1440] [--name master_v1] [--no-encode] [--deliver]

Per EDL row (finish/edl_routeB.csv), the row's frames come from, in order:
  1. renders/routeB/<shot>/fNNNNN.png when the row is COMPLETE (every frame present),
  2. else the previous final in renders/routeB/_old_<shot>/ when complete (a re-render in progress),
  3. else, when the 2D kit covers the whole row (finish/kit2d/items.json -> renders/routeB/kit2d/<K>/<K>.mp4), the kit clip
     (this is what the approved first cut showed, e.g. the more-car beats until their 3D finals land),
  4. else per frame: 3D png / kit frame / a grey "PENDING" slate.
A row is never a mix of a half-rendered 3D shot and something else (a 3D folder being written is ignored until complete).

Each row is encoded once to a lossless RGB segment (FFV1, gbrp) under <film>/master/segs_<res>/<shot>.mkv; a segment is
rebuilt only when its source signature (paths + sizes + mtimes, resolution, slate text) changes. The master is one
encode of all segments (concat demuxer, decoded, never stream-copied) with BT.709 stamped in the filter chain, muxed
with the song WAV from t=0. Writes finish/master/coverage_<name>.md and the mp4.

Delivery (CLAUDE.md "A release, end to end"): route-B 3D frames are 1920x1080; the kit clips are native 2560x1440.
  --res 1440 --deliver   builds the muted 2560x1440 picture (3D frames lanczos-upscaled, kit clips native) and links it as
                         songs/asking-for-a-friend/build/video_16x9_1440.mp4, ready for
                         `python3 -m studio.render songs/asking-for-a-friend --fmt 16x9_1440 --finals-only`.
Reads frames only; renders nothing; never touches the GPU queue.
"""
import csv, datetime, hashlib, json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

SONG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOME = os.path.expanduser("~")
FILM = f"{HOME}/Documents/Original Music/Asking for a Friend 2"
REN = f"{FILM}/renders/routeB"
KIT = f"{REN}/kit2d"
WAV = f"{HOME}/Documents/Original Music/Asking for a Friend 2 (clean).wav"
FPS = 24
OUT = os.path.join(SONG, "finish", "master")
FONT = "/System/Library/Fonts/Helvetica.ttc"


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


RES = int(arg("--res", "1080"))
W, H = {1080: (1920, 1080), 1440: (2560, 1440)}[RES]
NAME = arg("--name", "master_v1")
SEGS = f"{FILM}/master/segs_{RES}"


def sh(*a):
    return subprocess.run(a, check=True, capture_output=True, text=True)


def rng(s):
    a, b = s.split("-")
    return int(a), int(b)


def load_edl():
    rows = []
    for r in csv.DictReader(open(os.path.join(SONG, "finish", "edl_routeB.csv"))):
        if r["new_frames"].strip() and int(r["n"] or 0) > 0:
            a, b = rng(r["new_frames"].strip())
            rows.append(dict(shot=r["shot"], a=a, b=b, world=r["world"], set=r["set"]))
    rows.sort(key=lambda r: r["a"])
    prev = -1
    for r in rows:   # the EDL must tile the film exactly
        assert r["a"] == prev + 1, f"EDL gap/overlap before {r['shot']} ({r['a']}, previous end {prev})"
        prev = r["b"]
    return rows


def kit_map():
    """film frame -> (kit id, index into that kit's mp4)"""
    m = {}
    for it in json.load(open(os.path.join(SONG, "finish", "kit2d", "items.json"))):
        if not re.match(r"^\d", it["frames"]):
            continue
        idx = 0
        for seg in re.split(r"[+,]", it["frames"]):
            a, b = rng(seg.strip())
            for f in range(a, b + 1):
                m[f] = (it["id"], idx)
                idx += 1
    return m


_kitn = {}


def kit_frames(k):
    """frame count of a kit mp4 (0 if missing)"""
    if k not in _kitn:
        mp4 = f"{KIT}/{k}/{k}.mp4"
        _kitn[k] = int(sh("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", mp4).stdout.strip()) if os.path.exists(mp4) else 0
    return _kitn[k]


def slate(shot, sset):
    os.makedirs(f"{OUT}/slates", exist_ok=True)
    p = f"{OUT}/slates/{shot}_{RES}.png"
    if not os.path.exists(p):
        im = Image.new("RGB", (W, H), (46, 48, 52))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(FONT, int(48 * H / 1080))
        t = f"{shot} {sset}: PENDING"
        d.text(((W - d.textlength(t, font=f)) / 2, H / 2 - 28 * H / 1080), t, font=f, fill=(200, 202, 206))
        im.save(p)
    return p


def plan_row(r, km):
    """-> (runs, source label). runs: list of (kind, path, start, count); kind png = image sequence starting at frame
    `start`, kit = mp4 from index `start`, slate = still image."""
    n = r["b"] - r["a"] + 1
    pngs = [f"{REN}/{r['shot']}/f{f:05d}.png" for f in range(r["a"], r["b"] + 1)]
    have = [os.path.exists(p) for p in pngs]
    if all(have):
        return [("png", f"{REN}/{r['shot']}/f%05d.png", r["a"], n)], "3D"
    for old in (f"_old_{r['shot'].lower()}", f"_old_{r['shot']}"):   # a re-render in progress: keep the previous final
        od = f"{REN}/{old}"
        if all(os.path.exists(f"{od}/f{f:05d}.png") for f in range(r["a"], r["b"] + 1)):
            return [("png", f"{od}/f%05d.png", r["a"], n)], f"previous final ({old}; re-render in progress {sum(have)}/{n})"
    per = []   # per frame (kind, path, idx)
    for f, ok in zip(range(r["a"], r["b"] + 1), have):
        if f in km and kit_frames(km[f][0]) > km[f][1]:
            k, i = km[f]
            per.append(("kit", f"{KIT}/{k}/{k}.mp4", i))
        else:
            per.append(("slate", slate(r["shot"], r["set"]), 0))
    kinds = {p[0] for p in per}
    label = ("kit fallback" if kinds == {"kit"} else "PENDING slate" if kinds == {"slate"} else "MIXED kit+slate")
    if any(have):
        label += f" (3D {sum(have)}/{n} in progress, ignored)"
    runs = []
    for kind, path, i in per:   # merge consecutive frames of the same source
        if runs and runs[-1][0] == kind and runs[-1][1] == path and (kind == "slate" or runs[-1][2] + runs[-1][3] == i):
            runs[-1] = (kind, path, runs[-1][2], runs[-1][3] + 1)
        else:
            runs.append((kind, path, i, 1))
    return runs, label


def signature(runs):
    h = hashlib.sha1(f"{W}x{H}|v2".encode())
    for kind, path, s, c in runs:
        h.update(f"{kind}|{path}|{s}|{c}".encode())
        files = [path % f for f in range(s, s + c)] if kind == "png" else [path]
        for p in files:
            st = os.stat(p)
            h.update(f"{p}|{st.st_size}|{st.st_mtime_ns}".encode())
    return h.hexdigest()


def encode_row(r, runs, out):
    args, chains = [], []
    for j, (kind, path, s, c) in enumerate(runs):
        if kind == "png":
            args += ["-framerate", str(FPS), "-start_number", str(s), "-i", path]
            chains.append(f"[{j}:v]trim=end_frame={c},setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,format=gbrp,setsar=1[v{j}]")
        elif kind == "kit":
            args += ["-i", path]
            chains.append(f"[{j}:v]trim=start_frame={s}:end_frame={s + c},setpts=PTS-STARTPTS,"
                          f"scale={W}:{H}:flags=lanczos:in_color_matrix=bt709:in_range=tv,format=gbrp,setsar=1[v{j}]")
        else:
            args += ["-loop", "1", "-framerate", str(FPS), "-i", path]
            chains.append(f"[{j}:v]trim=end_frame={c},setpts=PTS-STARTPTS,scale={W}:{H},format=gbrp,setsar=1[v{j}]")
    fc = ";".join(chains) + ";" + "".join(f"[v{j}]" for j in range(len(runs))) + f"concat=n={len(runs)}:v=1:a=0,fps={FPS}[out]"
    tmp = out + ".tmp.mkv"
    sh("ffmpeg", "-y", "-v", "error", *args, "-filter_complex", fc, "-map", "[out]", "-c:v", "ffv1", "-level", "3",
       "-pix_fmt", "gbrp", "-r", str(FPS), tmp)
    n = int(sh("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets",
               "-of", "csv=p=0", tmp).stdout.strip())
    want = r["b"] - r["a"] + 1
    if n != want:
        raise SystemExit(f"{r['shot']}: segment has {n} frames, EDL wants {want}")
    os.replace(tmp, out)


def main():
    os.makedirs(SEGS, exist_ok=True)
    edl = load_edl()
    km = kit_map()
    stats, rebuilt = [], 0
    for r in edl:
        runs, label = plan_row(r, km)
        sig = signature(runs)
        seg = f"{SEGS}/{r['shot']}.mkv"
        sigf = seg + ".sig"
        if not (os.path.exists(seg) and os.path.exists(sigf) and open(sigf).read() == sig):
            if "--no-encode" not in sys.argv:
                encode_row(r, runs, seg)
                open(sigf, "w").write(sig)
                rebuilt += 1
                print(f"  seg {r['shot']:6s} {r['a']}-{r['b']} {label}", flush=True)
        stats.append((r, label))
    total = edl[-1]["b"] + 1
    n3 = sum(r["b"] - r["a"] + 1 for r, l in stats if l == "3D")
    L = [f"# Master coverage: {NAME} {RES}p ({datetime.datetime.now():%a %b %d %H:%M})", "",
         f"Film {total} frames = {total / FPS:.2f} s, {len(edl)} EDL rows; final 3D frames {n3}; segments rebuilt this run {rebuilt}.", "",
         "Rows not on final 3D frames (2D rows on the approved kit are expected):", "",
         "| shot | world | set | frames | source |", "|---|---|---|---|---|"]
    for r, l in stats:
        if l != "3D":
            L.append(f"| {r['shot']} | {r['world']} | {r['set']} | {r['a']}-{r['b']} ({r['b'] - r['a'] + 1}) | {l} |")
    open(f"{OUT}/coverage_{NAME}.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:3]))
    if "--no-encode" in sys.argv:
        return
    lst = f"{SEGS}/_list_{NAME}.txt"
    open(lst, "w").write("".join(f"file '{SEGS}/{r['shot']}.mkv'\n" for r in edl))
    cs = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
    # setpts renumbers frames by decode order: the mkv segments carry ms timestamps (34 f = 1.417 s), and the concat
    # demuxer summing those slipped one duplicate frame into master_v1's first build (~f2900, every later cut 1 f late).
    vf = f"setpts=N/({FPS}*TB),scale={W}:{H}:out_color_matrix=bt709:out_range=tv,{cs}"
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    os.makedirs(f"{FILM}/master", exist_ok=True)
    if "--deliver" in sys.argv:   # muted picture for studio.render --finals-only (it muxes the WAV itself)
        out = f"{FILM}/master/AFF {NAME} picture ({RES}p, muted).mp4"
        sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", vf, "-c:v", "libx264",
           "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", *tags, "-an", "-movflags", "+faststart", out)
        if RES == 1440:
            link = os.path.join(SONG, "build", "video_16x9_1440.mp4")
            if os.path.islink(link) or os.path.exists(link):
                os.remove(link)
            os.symlink(out, link)
    else:
        out = f"{FILM}/master/AFF {NAME} ({RES}p, {datetime.datetime.now():%Y-%m-%d %H%M}).mp4"
        sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", WAV, "-map", "0:v", "-map", "1:a",
           "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", *tags,
           "-c:a", "aac", "-b:a", "256k", "-t", f"{total / FPS:.4f}", "-movflags", "+faststart", out)
    n = int(sh("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets",
               "-of", "csv=p=0", out).stdout.strip())
    if n != total:
        raise SystemExit(f"master has {n} frames, EDL wants {total}")
    print(out)


if __name__ == "__main__":   # importable by finish/v2/assemble_v2.py
    main()
