"""v3 YouTube master: the assembled comic cut (build/v3/comic.mp4) -> 2560x1440 with two QA fixes, + the clean song.
  * the newspaper (frames 3000-3687) toned from mean ~0.84 to ~0.71 with a soft vignette (no pixel above the glow line)
  * the keynote's white slide flashes (3688-4095) held to a mean of 0.42
  python3 master_v3.py <out.mp4>"""
import os, sys, subprocess, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "build", "v3", "comic.mp4")
AUD = "/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do (clean).wav"
W, H, OW, OH = 1920, 1080, 2560, 1440
yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.10 * np.clip(r - 0.35, 0, None) ** 1.6).astype(np.float32)[..., None]
def ramp(n, a, b, k=11): return min(1.0, max(0.0, min((n - a) / k, (b - n) / k)))
out = sys.argv[1]
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", "30", "-i", "-", "-i", AUD,
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-profile:v", "high",
                        "-c:a", "aac", "-b:a", "320k", "-af", "apad=pad_dur=12", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
n = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
    if 3000 <= n <= 3687:
        k = ramp(n, 3000, 3687); g = 1 - 0.16 * k
        f = f * (g * (VIG * k + (1 - k)))
    elif 3688 <= n <= 4095:
        m = f.mean() / 255
        if m > 0.42: f = f * (0.42 / m)
    f = np.clip(f, 0, 255).astype(np.uint8)
    enc.stdin.write(cv2.resize(f, (OW, OH), interpolation=cv2.INTER_LANCZOS4).tobytes()); n += 1
enc.stdin.close(); enc.wait(); print("frames", n)
