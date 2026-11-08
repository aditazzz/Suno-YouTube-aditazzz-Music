#!/usr/bin/env python3
"""Master v2: master v1's assembly (finish/master/assemble_master.py) with the swaps in finish/v2/SWAPS.yaml laid over it.

  python3 songs/asking-for-a-friend/finish/v2/assemble_v2.py \
      [--res 1080|1440] [--name master_v2] [--deliver] [--no-look]

Per EDL row: the base frames are assemble_master's (routeB/<shot> -> _old_<shot> -> 2D kit -> slate); every SWAPS.yaml overlay
then replaces exactly the frames it carries. Each row is a lossless FFV1 segment in <film>/master/segs_v2_<res>/ with
assemble_master's source signature: rows identical to master v1's segment are hard-linked from segs_<res>/ (no re-encode),
only changed rows encode. The master encode applies the film's ONE look (AFF_look_v1.cube from
finish/lookdev/tools/make_lut.py + vignette) to every frame (RERENDER section A: the v2 chains render WITHOUT the LUT; --no-look skips it),
BT.709 stamped, the song WAV muxed from t=0, cut to the EDL length. Writes finish/v2/coverage_<name>.md and
finish/v2/<name>_build.json (master path, swapped ranges, splices) for gate_v2.py and the page step.
"""
import datetime, json, os, subprocess, sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SONG = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SONG, "finish", "master"))
_argv = sys.argv
sys.argv = [sys.argv[0]] + [a for i, a in enumerate(_argv[1:], 1) if a in ("--res",) or (i > 1 and _argv[i - 1] == "--res")]
import assemble_master as am   # noqa: E402  (reads --res at import)
sys.argv = _argv

NAME = am.arg("--name", "master_v2")
am.NAME = NAME
SEGS = f"{am.FILM}/master/segs_v2_{am.RES}"
V1SEGS = f"{am.FILM}/master/segs_{am.RES}"
LOOK = "--no-look" not in sys.argv


def per_frame(runs):
    out = []
    for kind, path, s, c in runs:
        for k in range(c):
            out.append((kind, path, s + k if kind != "slate" else 0))
    return out


def merge(per):
    runs = []
    for kind, path, i in per:
        if runs and runs[-1][0] == kind and runs[-1][1] == path and (kind == "slate" or runs[-1][2] + runs[-1][3] == i):
            runs[-1] = (kind, path, runs[-1][2], runs[-1][3] + 1)
        else:
            runs.append((kind, path, i, 1))
    return runs


def main():
    sw = yaml.safe_load(open(os.path.join(HERE, "SWAPS.yaml")))
    overlays = sw.get("overlays") or []
    os.makedirs(SEGS, exist_ok=True)
    edl = am.load_edl()
    km = am.kit_map()
    src_of = {}   # film frame -> overlay label
    for o in overlays:
        for f in range(o["a"], o["b"] + 1):
            src_of[f] = (o["chain"], os.path.join(SONG, o["dir"]) + "/f%05d.png", o["shot"])
    stats, rebuilt, linked = [], 0, 0
    t0 = datetime.datetime.now()
    for r in edl:
        runs, label = am.plan_row(r, km)
        per = per_frame(runs)
        sw_n = 0
        for j, f in enumerate(range(r["a"], r["b"] + 1)):
            if f in src_of:
                chain, pat, _ = src_of[f]
                if not os.path.exists(pat % f):
                    raise SystemExit(f"{r['shot']}: overlay {chain} lacks frame {f} ({pat % f}); re-run swaps.py")
                per[j] = ("png", pat, f)
                sw_n += 1
        if sw_n:
            label = f"SWAP {', '.join(sorted({src_of[f][0] for f in range(r['a'], r['b'] + 1) if f in src_of}))} ({sw_n}/{r['b'] - r['a'] + 1} f) over {label}"
        runs = merge(per)
        sig = am.signature(runs)
        seg, sigf = f"{SEGS}/{r['shot']}.mkv", f"{SEGS}/{r['shot']}.mkv.sig"
        if not (os.path.exists(seg) and os.path.exists(sigf) and open(sigf).read() == sig):
            v1, v1s = f"{V1SEGS}/{r['shot']}.mkv", f"{V1SEGS}/{r['shot']}.mkv.sig"
            for p in (seg, sigf):
                if os.path.exists(p):
                    os.remove(p)
            if os.path.exists(v1) and os.path.exists(v1s) and open(v1s).read() == sig:
                os.link(v1, seg)
                linked += 1
            else:
                am.encode_row(r, runs, seg)
                rebuilt += 1
                print(f"  seg {r['shot']:6s} {r['a']}-{r['b']} {label}", flush=True)
            open(sigf, "w").write(sig)
        stats.append((r, label))
    total = edl[-1]["b"] + 1
    # splices: every frame where the source switches between a swap and anything else
    splices = []
    prev = None
    starts = {r["a"] for r in edl}
    designed = {int(x) for o in overlays for x in (o.get("cuts") or [])}   # camera cuts the swap's design puts off the EDL grid
    for f in range(total):
        cur = src_of.get(f, (None,))[0]
        if f and cur != prev:
            splices.append(dict(f=f, from_=prev or "base", to=cur or "base", at_edl_cut=f in starts, designed_cut=f in designed))
        prev = cur
    t1 = datetime.datetime.now()
    L = [f"# Master coverage: {NAME} {am.RES}p ({t1:%a %b %d %H:%M})", "",
         f"Film {total} frames = {total / am.FPS:.2f} s, {len(edl)} EDL rows; segments encoded {rebuilt}, reused from v1 {linked}; "
         f"look {'ON (AFF_look_v1.cube + vignette)' if LOOK else 'OFF'}.", "",
         "| shot | frames | source | flag |", "|---|---|---|---|"]
    rows = sw.get("rows") or {}
    for r, l in stats:
        fl = (rows.get(r["shot"]) or {}).get("flag") or ""
        if l != "3D" or fl:
            L.append(f"| {r['shot']} | {r['a']}-{r['b']} | {l} | {fl} |")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    open(os.path.join(HERE, f"coverage_{NAME}.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:3]), flush=True)

    import hashlib
    allsig = hashlib.sha1(("|".join(open(f"{SEGS}/{r['shot']}.mkv.sig").read() for r in edl)
                           + f"|look={LOOK}|deliver={'--deliver' in sys.argv}|{am.RES}").encode()).hexdigest()
    bj = os.path.join(HERE, f"{NAME}_build.json") if "--deliver" not in sys.argv else None
    reuse = None
    if bj and os.path.exists(bj) and "--force" not in sys.argv:
        old = json.load(open(bj))
        if old.get("allsig") == allsig and os.path.exists(old["master"]):
            print(f"nothing changed since {os.path.basename(old['master'])}: picture reused (--force re-encodes)")
            reuse = old["master"]
    lst = f"{SEGS}/_list_{NAME}.txt"
    open(lst, "w").write("".join(f"file '{SEGS}/{r['shot']}.mkv'\n" for r in edl))
    cs = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
    # the film look: finish/lookdev/AFF_look_v1.cube (written by finish/lookdev/tools/make_lut.py) + a gentle vignette
    lut = os.path.join(SONG, "finish/lookdev/AFF_look_v1.cube")
    look = f"lut3d=file='{lut}':interp=tetrahedral,vignette=angle=0.30," if LOOK else ""
    # setpts renumbers by decode order (mkv ms timestamps drifted master_v1's first build by 1 f; see assemble_master)
    vf = f"setpts=N/({am.FPS}*TB),{look}scale={am.W}:{am.H}:out_color_matrix=bt709:out_range=tv,{cs}"
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    if reuse:
        out = reuse
    elif "--deliver" in sys.argv:
        out = f"{am.FILM}/master/AFF {NAME} picture ({am.RES}p, muted).mp4"
        am.sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", vf, "-c:v", "libx264",
              "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", *tags, "-an", "-movflags", "+faststart", out)
    else:
        out = f"{am.FILM}/master/AFF {NAME} ({am.RES}p, {datetime.datetime.now():%Y-%m-%d %H%M}).mp4"
        am.sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", am.WAV, "-map", "0:v", "-map", "1:a",
              "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", *tags,
              "-c:a", "aac", "-b:a", "256k", "-t", f"{total / am.FPS:.4f}", "-movflags", "+faststart", out)
    n = int(am.sh("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets",
                  "-of", "csv=p=0", out).stdout.strip())
    if n != total:
        raise SystemExit(f"master has {n} frames, EDL wants {total}")
    t2 = datetime.datetime.now()
    build = dict(name=NAME, res=am.RES, master=out, allsig=allsig, deliver="--deliver" in sys.argv, look=LOOK, frames=total,
                 rows=[dict(shot=r["shot"], a=r["a"], b=r["b"], source=l) for r, l in stats],
                 swapped=[dict(shot=o["shot"], chain=o["chain"], a=o["a"], b=o["b"]) for o in overlays],
                 splices=[{("from" if k == "from_" else k): v for k, v in s.items()} for s in splices],
                 flags=sw.get("flags") or [], segs_encoded=rebuilt, segs_reused=linked,
                 t_segments_s=round((t1 - t0).total_seconds()), t_encode_s=round((t2 - t1).total_seconds()))
    json.dump(build, open(os.path.join(HERE, f"{NAME}_build.json" if "--deliver" not in sys.argv else f"{NAME}_deliver.json"), "w"), indent=1)
    print(out)
    print(f"segments {build['t_segments_s']} s ({rebuilt} encoded, {linked} reused), master encode {build['t_encode_s']} s")


main()
