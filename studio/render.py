"""Step 3 — render: songs/<slug>/scene.py -> full 16:9 and 9:16 videos.

usage:
  python -m studio.render songs/<slug> --stills 10 60 120      # contact sheet for review (build/stills_<fmt>.jpg)
  python -m studio.render songs/<slug> --fmt 16x9 --jobs 4     # full video (parallel chunks, resumable)
  python -m studio.render songs/<slug> --fmt 9x16 --jobs 4     # needs a passing `python -m studio.safezone songs/<slug>`
Outputs build/video_<fmt>.mp4 (no audio) then the final files in the song's output folder.
"""
import os, sys, time, json, argparse, subprocess, importlib.util
import numpy as np
from .config import load_song
from . import core

SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}

def load_scene(song_dir):
    path = os.path.join(song_dir, "scene.py")
    sys.path.insert(0, os.path.abspath(song_dir))
    spec = importlib.util.spec_from_file_location("scene_" + os.path.basename(os.path.abspath(song_dir)).replace("-", "_"), path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def ffmpeg_writer(out, W, H, crf=16):
    preset = os.environ.get("STUDIO_CHUNK_PRESET", "medium")   # e.g. "veryfast" in a time-limited shell (bigger chunks, same crf)
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(core.FPS),
                             "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)

def worker(song_dir, fmt, f0, f1, out):
    W, H = SIZES[fmt]; sc = load_scene(song_dir)
    p = ffmpeg_writer(out + ".part.mp4", W, H); st = time.time()
    for fi in range(f0, f1):
        p.stdin.write(sc.render_frame(fi / core.FPS, W, H, fi).tobytes())
        if (fi - f0) % 150 == 0: print(f"[{os.path.basename(out)}] {fi - f0}/{f1 - f0} {time.time() - st:.0f}s", flush=True)
    p.stdin.close(); rc = p.wait()
    if rc != 0: raise SystemExit(f"ffmpeg exited {rc} for {out}: chunk left as .part")   # never publish a truncated chunk
    os.replace(out + ".part.mp4", out)

def stills(song_dir, fmt, times, clean=False):
    from PIL import Image
    W, H = SIZES[fmt]; sc = load_scene(song_dir); core.STATE["clean"] = clean
    ims = [Image.fromarray(sc.render_frame(t, W, H, int(t * core.FPS))) for t in times]
    tw = 480 if fmt == "16x9" else 270; th = int(tw * H / W); cols = 4 if fmt == "16x9" else 6
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows))
    for i, im in enumerate(ims): sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    out = os.path.join(song_dir, "build", f"stills_{fmt}{'_clean' if clean else ''}.jpg"); sheet.save(out, quality=85)
    for t, im in zip(times, ims): im.save(os.path.join(song_dir, "build", f"still_{fmt}_{t:07.2f}{'_clean' if clean else ''}.png"))
    print(out)

def full(song_dir, fmt, jobs, step=300, budget=None, finalize=True, skip_safe=False):
    if fmt == "9x16" and not skip_safe:   # every lyric line must land inside the phone-safe area (see core.SAFE_9x16)
        from .safezone import require_ok
        ok, why = require_ok(song_dir)
        if not ok:
            raise SystemExit(f"9:16 render blocked: {why}. Run `python -m studio.safezone {song_dir}` and fix what it flags "
                             f"(or pass --skip-safe-check for a song with no on-screen lyrics).")
    song = load_song(song_dir); b = song["build"]; ch = os.path.join(b, f"chunks_{fmt}"); os.makedirs(ch, exist_ok=True)
    dur = json.load(open(os.path.join(b, "beats.json")))["duration"] + float(song.get("tail", 0)); N = int(dur * core.FPS)
    # many small chunks so a crash or sleep only loses one piece; resumable
    parts = [(a, min(N, a + step)) for a in range(0, N, step)]
    todo = [(a, c) for a, c in parts if not os.path.exists(os.path.join(ch, f"{a:06d}.mp4"))]
    print(f"{fmt}: {len(parts)} chunks, {len(todo)} to render with {jobs} jobs")
    procs = []; t_start = time.time()
    while todo or procs:
        if budget and time.time() - t_start > budget: todo = []   # stop launching; let running chunks finish
        while todo and len(procs) < jobs:
            a, c = todo.pop(0)
            procs.append(subprocess.Popen([sys.executable, "-m", "studio.render", song_dir, "--worker", fmt, str(a), str(c),
                                           os.path.join(ch, f"{a:06d}.mp4")], cwd=core.ROOT))
        time.sleep(2)
        for p in procs[:]:
            if p.poll() is not None:
                procs.remove(p)
                if p.returncode != 0: raise SystemExit(f"chunk failed ({p.returncode})")
    missing = [a for a, _ in parts if not os.path.exists(os.path.join(ch, f"{a:06d}.mp4"))]
    if missing:
        print(f"PARTIAL: {len(parts) - len(missing)}/{len(parts)} chunks done — run again to continue"); return
    print("ALL CHUNKS DONE")
    if not finalize: return
    lst = os.path.join(ch, "list.txt")
    open(lst, "w").write("".join(f"file '{a:06d}.mp4'\n" for a, _ in parts))
    vid = os.path.join(b, f"video_{fmt}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    finals(song, fmt)

def concat(song_dir, fmt, step=300):
    song = load_song(song_dir); b = song["build"]; ch = os.path.join(b, f"chunks_{fmt}")
    dur = json.load(open(os.path.join(b, "beats.json")))["duration"] + float(song.get("tail", 0)); N = int(dur * core.FPS)
    parts = [a for a in range(0, N, step)]
    lst = os.path.join(ch, "list.txt"); open(lst, "w").write("".join(f"file '{a:06d}.mp4'\n" for a in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", os.path.join(b, f"video_{fmt}.mp4")], check=True)
    print("concat done")

def finals(song, fmt):
    os.makedirs(song["out_dir"], exist_ok=True); b = song["build"]
    vid = os.path.join(b, f"video_{fmt}.mp4"); T = song["title"]
    if fmt == "16x9":
        out = os.path.join(song["out_dir"], f"{T} - YouTube 16x9.mp4"); vb = ["-b:v", "12M", "-maxrate", "16M", "-bufsize", "24M"]
    else:
        out = os.path.join(song["out_dir"], f"{T} - Instagram 9x16 full.mp4"); vb = ["-b:v", "4M", "-maxrate", "6M", "-bufsize", "10M"]
    tail = float(song.get("tail", 0))   # silent seconds after the song for the end screen
    af = ["-af", f"apad=pad_dur={tail}"] if tail else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", song["audio"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                    "-preset", "fast", *vb, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", *af, "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("song_dir")
    ap.add_argument("--fmt", default="16x9"); ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--stills", nargs="*", type=float); ap.add_argument("--clean", action="store_true")
    ap.add_argument("--worker", nargs=4); ap.add_argument("--finals-only", action="store_true")
    ap.add_argument("--step", type=int, default=300); ap.add_argument("--budget", type=float, help="seconds; stop launching chunks after this (for time-limited shells)")
    ap.add_argument("--no-finalize", action="store_true"); ap.add_argument("--concat-only", action="store_true")
    ap.add_argument("--skip-safe-check", action="store_true", help="9:16 only: render without a passing studio.safezone check")
    a = ap.parse_args()
    if a.worker: worker(a.song_dir, a.worker[0], int(a.worker[1]), int(a.worker[2]), a.worker[3])
    elif a.stills: stills(a.song_dir, a.fmt, a.stills, a.clean)
    elif a.finals_only: finals(load_song(a.song_dir), a.fmt)
    elif a.concat_only: full(a.song_dir, a.fmt, a.jobs, a.step, finalize=False) if False else concat(a.song_dir, a.fmt, a.step)
    else: full(a.song_dir, a.fmt, a.jobs, a.step, a.budget, not a.no_finalize, a.skip_safe_check)
