"""Render one v3 section (a module in this folder exporting render_frame(t, W, H) -> HxWx3 uint8 RGB).
  cd <repo> && python3 songs/look-what-i-can-do/sections/run.py <module> range <n0> <n1> <out.mp4> [W H]   # frames n0..n1 inclusive, 30 fps
  cd <repo> && python3 songs/look-what-i-can-do/sections/run.py <module> stills <out_dir> <t1> <t2> ... [--wh W H]
Frames are song time t = n / 30. Output: silent H.264 (CRF 16) for the assembler."""
import os, sys, subprocess, importlib, time
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [ROOT, HERE]
mod = importlib.import_module(sys.argv[1]); mode = sys.argv[2]
def as_u8(a):
    a = np.asarray(a)
    if a.dtype != np.uint8: a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8) if a.max() <= 1.0001 else np.clip(a, 0, 255).astype(np.uint8)
    return a[..., :3]
if mode == "range":
    n0, n1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    W, H = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (1920, 1080)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out + ".part.mp4"], stdin=subprocess.PIPE)
    t0 = time.time()
    for n in range(n0, n1 + 1):
        p.stdin.write(as_u8(mod.render_frame(n / 30.0, W, H)).tobytes())
        if (n - n0) % 30 == 0: print(f"[{sys.argv[1]}] frame {n} ({(n - n0 + 1) / (time.time() - t0):.2f} fps)", flush=True)
    p.stdin.close(); p.wait(); os.replace(out + ".part.mp4", out); print("wrote", out)
else:
    out = sys.argv[3]; args = sys.argv[4:]; W, H = 1920, 1080
    if "--wh" in args: i = args.index("--wh"); W, H = int(args[i + 1]), int(args[i + 2]); args = args[:i]
    os.makedirs(out, exist_ok=True)
    for ts in args:
        t0 = time.time(); Image.fromarray(as_u8(mod.render_frame(float(ts), W, H))).save(os.path.join(out, f"s_{float(ts):.2f}.jpg"), quality=92)
        print("still", ts, f"{time.time() - t0:.2f}s", flush=True)
