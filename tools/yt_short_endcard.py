"""YouTube copy of the Shorts that reach the song's end card: the 9:16 end card says "follow @<instagram>" (right for
Reels), so for YouTube the end-card frames are re-rendered with "subscribe @<channel_handle>" and laid over the clip.

usage: python3 tools/yt_short_endcard.py songs/<slug> [label ...] [--list]
Writes "<Short file> (YouTube).mp4" next to the Short; studio.package then records it as the Short's yt_file and
tools/youtube_upload.py uploads that copy. --list only prints which Shorts reach the end card.
"""
import os, sys, json, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from studio import core
from studio.config import load_song
from studio.render import load_scene

def end_window(song_dir):
    rec = {}; oe = core.end_screen
    def end(img, t, W, H, t0, dur, *a, **k): rec.setdefault("end", (t0, dur)); return oe(img, t, W, H, t0, dur, *a, **k)
    core.end_screen = end
    try: load_scene(song_dir).render_frame(30.0, 108, 192, 900)
    finally: core.end_screen = oe
    return rec.get("end")

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; song_dir, labels = args[0], set(args[1:])
    song = load_song(song_dir); b = song["build"]; st = json.load(open(os.path.join(b, "clips.json")))
    w = end_window(song_dir)
    if not w: print("this scene has no end card"); return
    t0, dur = w
    hits = [c for c in st["clips"] if c["kind"] in ("short", "reel") and c.get("file") and c["end"] > t0 + 0.05 and (not labels or c["label"] in labels)]   # Reels go to YouTube as Shorts too
    print(f"end card {t0:.2f}-{t0 + dur:.2f}s; Shorts that reach it:", [c["file"] for c in hits] or "none")
    if "--list" in sys.argv: return
    env = dict(os.environ, STUDIO_PLATFORM="youtube"); fx = os.path.join(b, "ytend"); os.makedirs(fx, exist_ok=True)
    for c in hits:
        s, e = c["start"], c["end"]; a = int(math.floor(max(s, t0 - 0.1) * 30)); z = int(math.ceil(e * 30)) + 1
        part = os.path.join(fx, f"{a:06d}_{z:06d}.mp4")
        if not os.path.exists(part):
            subprocess.run([sys.executable, "-m", "studio.render", song_dir, "--worker", "9x16", str(a), str(z), part], cwd=core.ROOT, env=env, check=True)
        src = os.path.join(song["out_dir"], c["file"]); out = os.path.splitext(src)[0] + " (YouTube).mp4"
        off = a / 30 - s; d = e - s
        fc = (f"[0:v][1:v]overlay=0:0:eof_action=pass:enable='between(t,{off:.4f},{d:.4f})',"
              f"fade=t=out:st={d - 0.6:.2f}:d=0.6[v]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-itsoffset", f"{off:.4f}", "-i", part, "-filter_complex", fc,
                        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast", "-b:v", "4M", "-maxrate", "6M", "-bufsize", "10M",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
        print("wrote", os.path.basename(out), f"(end card frames {a}-{z})")

if __name__ == "__main__":
    main()
