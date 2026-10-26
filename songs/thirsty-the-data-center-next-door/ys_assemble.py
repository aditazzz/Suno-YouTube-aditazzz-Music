"""Join this song's chunks (rendered on two machines) into the final file, with the hum-cleaned audio.
  python3 songs/thirsty-the-data-center-next-door/ys_assemble.py --fmt 16x9_1440 --extra <dir with the other machine's chunks> --out <file.mp4>
Every chunk is checked (frame count, size) before anything is encoded. Video: H.264 at the format's YouTube bitrate
(VB below); audio: song.yaml's audio as AAC 320k, padded by the song's tail."""
import os, sys, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio.config import load_song
from studio.render import SIZES
sys.path.insert(0, os.path.join(ROOT, "tools"))
try: from mac_post import VB
except ImportError:   # the YouTube bitrates per format (H.264)
    VB = {"16x9": ["-b:v", "12M", "-maxrate", "16M", "-bufsize", "24M"], "9x16": ["-b:v", "4M", "-maxrate", "6M", "-bufsize", "10M"],
          "16x9_1440": ["-b:v", "24M", "-maxrate", "30M", "-bufsize", "48M"], "16x9_4k": ["-b:v", "45M", "-maxrate", "60M", "-bufsize", "90M"]}

ap = argparse.ArgumentParser(); ap.add_argument("--fmt", default="16x9_1440"); ap.add_argument("--extra", default=None)
ap.add_argument("--out", required=True); ap.add_argument("--preset", default="fast"); ap.add_argument("--check-only", action="store_true")
a = ap.parse_args()
song = load_song(HERE); b = song["build"]; ch = os.path.join(b, f"chunks_{a.fmt}")
dur = json.load(open(os.path.join(b, "beats.json")))["duration"] + float(song.get("tail", 0)); N = int(dur * 30)
W, H = SIZES[a.fmt]
files, bad = [], []
for s in range(0, N, 30):
    n_exp = min(N, s + 30) - s
    cands = [os.path.join(ch, f"{s:06d}.mp4")] + ([os.path.join(a.extra, f"{s:06d}.mp4")] if a.extra else [])
    f = next((c for c in cands if os.path.exists(c) and os.path.getsize(c) > 1000), None)
    if f is None: bad.append((s, "missing")); continue
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets,width,height", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    w, h, n = r.split(",")
    if (int(w), int(h), int(n)) != (W, H, n_exp): bad.append((s, r))
    files.append(f)
print(f"{len(files)} chunks for {N} frames at {W}x{H}; problems: {bad if bad else 'none'}", flush=True)
if bad or a.check_only: sys.exit(1 if bad else 0)
lst = a.out + ".txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
tail = float(song.get("tail", 0)); af = ["-af", f"apad=pad_dur={tail}"] if tail else []
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", song["audio"], "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-preset", a.preset, *VB[a.fmt], "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", *af, "-shortest",
       "-movflags", "+faststart", a.out]
print(" ".join(cmd[:12]), "...", flush=True)
subprocess.run(cmd, check=True)
print("wrote", a.out, os.path.getsize(a.out) // 2 ** 20, "MB", flush=True)
