#!/usr/bin/env python3
"""Quick preview render of a time range with the song's audio (parallel workers).
usage: python3 tools/preview.py songs/<slug> START END out.mp4 [--fmt 16x9|9x16] [--jobs 2] [--scale 1.0]"""
import os, sys, argparse, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from studio.config import load_song
from studio import core

def worker(song_dir, W, H, f0, f1, out):
    from studio.render import load_scene
    sc = load_scene(song_dir)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1): p.stdin.write(sc.render_frame(fi / 30, W, H, fi).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("song"); ap.add_argument("a", type=float); ap.add_argument("b", type=float); ap.add_argument("out")
    ap.add_argument("--fmt", default="16x9"); ap.add_argument("--jobs", type=int, default=2); ap.add_argument("--worker", nargs=3, type=int)
    a = ap.parse_args(); W, H = (1920, 1080) if a.fmt == "16x9" else (1080, 1920)
    if a.worker: worker(a.song, W, H, a.worker[0], a.worker[1], a.out); sys.exit()
    song = load_song(a.song); f0, f1 = int(round(a.a * 30)), int(round(a.b * 30)); n = f1 - f0
    cuts = [f0 + n * i // a.jobs for i in range(a.jobs + 1)]; parts = []; procs = []; st = time.time()
    for i in range(a.jobs):
        pp = a.out + f".p{i}.mp4"; parts.append(pp)
        procs.append(subprocess.Popen([sys.executable, __file__, a.song, str(a.a), str(a.b), pp, "--fmt", a.fmt, "--worker", str(cuts[i]), str(cuts[i + 1]), "0"]))
    for p in procs: p.wait()
    lst = a.out + ".txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-ss", f"{a.a:.3f}", "-t", f"{n / 30:.3f}", "-i", song["audio"],
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out], check=True)
    for p in parts + [lst]: os.remove(p)
    print(f"preview {a.out} ({n} frames in {time.time() - st:.0f}s)")
