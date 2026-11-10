#!/usr/bin/env python3
"""Apply the Earth colourist pass (PALETTE.md, QA gate 7) to a rendered silent master or section range. No re-render.

  .venv/bin/python songs/you-said-you-needed-space/living_earth/le_grade.py <in.mp4> <out.mp4> [--start-frame N] [--crf 12]

<in.mp4> is film-timed from --start-frame (default 0 = a full master; a section range from le_render.sh starts at its first
frame, e.g. 5212 for the final-chorus range). Each palette section gets its own 3D LUT (build/palette/lut/, made by
living_earth/le_palette.py); at every section boundary inside the clip the two LUTs crossfade over XFADE seconds centred on
the boundary (no grade pop). Frame-exact: the output has exactly the input's frame count (checked). BT.709 tags kept.
Same LUTs for 16:9 and 9:16 (the grade is per pixel). ~12 fps at 1440p on the M2.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SONG = os.path.dirname(HERE)
LUTS = os.path.join(SONG, "build", "palette", "lut")
FPS = 30


def slug(n):
    return n.replace("/", "_").replace(" ", "_")


def nframes(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", p], capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--start-frame", type=int, default=0)
    ap.add_argument("--crf", type=int, default=12)
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    import le_palette as P
    if not all(os.path.exists(os.path.join(LUTS, f"earth_{slug(n)}.cube")) for n, _, _ in P.SEC):
        subprocess.run([sys.executable, os.path.join(HERE, "le_palette.py")], check=True)
    n_in = nframes(a.inp); f0 = a.start_frame; f1 = f0 + n_in
    half = int(round(P.BASE["xfade"] * FPS / 2))
    # pieces in film frames: ('lut', a, b, sec) or ('mix', a, b, secA, secB, boundary)
    secs = [(n, int(round(t0 * FPS)), int(round(t1 * FPS))) for n, t0, t1 in P.SEC]
    secs[-1] = (secs[-1][0], secs[-1][1], max(secs[-1][2], f1))
    cuts = []  # boundaries with their window
    for k in range(1, len(secs)):
        b = secs[k][1]; cuts.append((b - half, b + half, secs[k - 1][0], secs[k][0], b))
    pieces = []; cur = f0
    def sec_at(fr):
        for n, s0, s1 in secs:
            if s0 <= fr < s1: return n
        return secs[-1][0]
    for w0, w1, sa, sb, b in cuts:
        if w1 <= cur or w0 >= f1: continue
        if w0 > cur: pieces.append(("lut", cur, w0, sec_at(cur)))
        pieces.append(("mix", max(w0, cur), min(w1, f1), sa, sb, w0, w1)); cur = min(w1, f1)
    if cur < f1: pieces.append(("lut", cur, f1, sec_at(cur)))
    inputs, graph, labels = [], [], []
    pre = "scale=in_color_matrix=bt709:in_range=tv,format=rgb48le"
    post = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
    for i, pc in enumerate(pieces):
        s, e = pc[1] - f0, pc[2] - f0
        inputs += ["-ss", f"{s / FPS:.6f}", "-i", a.inp]
        tr = f"trim=end_frame={e - s},setpts=PTS-STARTPTS,{pre}"
        if pc[0] == "lut":
            graph.append(f"[{i}:v]{tr},lut3d={LUTS}/earth_{slug(pc[3])}.cube:interp=tetrahedral,{post}[p{i}]")
        else:
            _, pa, pb, sa, sb, w0, w1 = pc
            # weight of the incoming section: 0 at w0 -> 1 at w1 (film time), T is piece-local
            t_off = (pa - w0) / FPS; dur = (w1 - w0) / FPS
            wexpr = f"clip((T+{t_off:.6f})/{dur:.6f},0,1)"
            graph.append(f"[{i}:v]{tr},split[a{i}][b{i}];[a{i}]lut3d={LUTS}/earth_{slug(sa)}.cube:interp=tetrahedral[A{i}];"
                         f"[b{i}]lut3d={LUTS}/earth_{slug(sb)}.cube:interp=tetrahedral[B{i}];"
                         f"[A{i}][B{i}]blend=all_expr='A*(1-{wexpr})+B*{wexpr}',{post}[p{i}]")
        labels.append(f"[p{i}]")
    graph.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[v]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-r", str(FPS),
           "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", a.out]
    print(json.dumps({"frames": [f0, f1], "pieces": [[p[0], p[1], p[2]] + list(p[3:5]) for p in pieces]}))
    subprocess.run(cmd, check=True)
    n_out = nframes(a.out)
    if n_out != n_in:
        sys.exit(f"FRAME COUNT MISMATCH: in {n_in}, out {n_out}")
    print(f"graded {a.out}: {n_out} frames, film frames {f0}-{f1}")


if __name__ == "__main__":
    main()
