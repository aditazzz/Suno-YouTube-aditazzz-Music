"""Short B "Net worth" (9:16): verse 3 in the Daily Standup, frames 3005-3659 (100.15-121.97 s), rendered natively at
1080x1920 from sections/s6_paper_v.py, + a 1.5 s end card in the film's terminal look. Writes build/shorts/B.mp4,
B_cover.jpg (its first frame) and B_sheet.jpg (4x3 contact sheet), and checks the brightness of every frame.
  cd <repo> && python3 songs/look-what-i-can-do/build_short_B.py"""
import os, sys, math, subprocess
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "sections")]
import s6_paper_v as V
from studio import core as C
from studio.core import sstep, ease_out, hexc

W, H, FPS = 1080, 1920, 30
N0, N1 = 3005, 3659; NSEC = N1 - N0 + 1; NEND = 45
AUD = "/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do (clean).wav"
OUT = os.path.join(HERE, "build", "shorts"); os.makedirs(OUT, exist_ok=True)
BG = hexc("0c0c0b"); INK = hexc("ece6d8"); MUTE = hexc("8d887d"); GREEN = hexc("74e36a"); LINE = hexc("2e2d33")
CX = 507   # centre of the safe column (x 64..950)

def txt(img, s, x, y, font, px, col, op=1.0, anchor='c'):
    spr = C.sprite(s, font, px)
    w = spr[0].shape[1]
    X = x - w / 2 if anchor == 'c' else x
    C.blit(img, spr, X, y, col, op)
    return w

def end_card(i):
    """i = frame index inside the card (0..44). The three Shorts share one end card (Short A's, sections/short_a.py)."""
    import short_a
    return short_a.end_card(i / FPS, W, H, N1 + 1 + i)   # uint8 from C.finish

def end_card_old(i):
    """(the first draft's own card, kept for reference; unused)"""
    t = i / FPS
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    # a terminal prompt types the command, then the card answers
    cmd = "❯ watch --full"
    n = min(len(cmd), int(t / 0.016) + 4)
    w = txt(img, cmd[:n], 96, 560, C.F_MONOB, 46, GREEN, 1.0, 'l')
    if (t * 2.4) % 1 < 0.6 or n < len(cmd): C.blit(img, (np.ones((50, 22), np.float32), None, 0), 96 + w + 8, 566, GREEN, 0.9)
    k1 = ease_out((t - 0.12) / 0.25)
    txt(img, "Full video", CX, 700 + 20 * (1 - k1), C.F_MONOB, 80, INK, k1)
    txt(img, "on my channel", CX, 800 + 20 * (1 - k1), C.F_MONOB, 80, INK, k1)
    k2 = ease_out((t - 0.30) / 0.25)
    if k2 > 0:
        fs = 58; lw = C.text_w("SUBSCRIBE", C.F_DISP, fs); bh = int(fs * 1.9); bw = int(lw + bh * 1.55)
        pop = 1 + 0.08 * math.exp(-max(0, t - 0.55) * 8) * (t > 0.55)
        x = CX - bw / 2; y = 960
        C._pill(img, x, y, bw, bh, C.SUB_RED, k2)
        C._bell(img, x + bh * 0.62, y + bh / 2, bh * 0.62, C.WHITE, k2, ring=math.sin(t * 16) * math.exp(-max(0, t - 0.6) * 1.5) if t > 0.6 else 0)
        C.blit(img, C.sprite("SUBSCRIBE", C.F_DISP, int(fs * pop)), x + bh * 1.12, y + bh / 2 - fs * pop * 0.62, C.WHITE, k2)
    k3 = ease_out((t - 0.45) / 0.25)
    txt(img, "@adita_zzz", CX, 1150, C.F_MONOB, 60, GREEN, k3)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

def frames():
    for n in range(N0, N1 + 1): yield V.render_frame(n / FPS, W, H)
    for i in range(NEND): yield end_card(i)

if __name__ == "__main__":
    dur = NSEC / FPS; tot = (NSEC + NEND) / FPS
    af = f"atrim=start={N0 / FPS:.4f}:duration={dur:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={dur - 0.25:.4f}:d=0.25,apad=whole_dur={tot:.4f}"
    out = os.path.join(OUT, "B.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", AUD, "-filter_complex", f"[1:a]{af}[a]", "-map", "0:v", "-map", "[a]",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(FPS),
                            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-t", f"{tot:.4f}", "-movflags", "+faststart", out + ".part.mp4"],
                           stdin=subprocess.PIPE)
    lum = np.array([0.2126, 0.7152, 0.0722], np.float32); stats = []; keep = {}
    pick = set(np.linspace(0, NSEC + NEND - 1, 12).round().astype(int))
    for i, f in enumerate(frames()):
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
        y = (f[:int(H * 0.86)].astype(np.float32) / 255) @ lum
        stats.append((y.mean(), (y > 0.92).mean(), y.max()))
        if i == 0: cv2.imwrite(os.path.join(OUT, "B_cover.jpg"), f[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
        if i in pick: keep[i] = cv2.resize(f[..., ::-1], (360, 640), interpolation=cv2.INTER_AREA)
        if i % 60 == 0: print("frame", i, flush=True)
    enc.stdin.close(); enc.wait(); os.replace(out + ".part.mp4", out)
    ims = [keep[k] for k in sorted(keep)]
    cv2.imwrite(os.path.join(OUT, "B_sheet.jpg"), np.vstack([np.hstack(ims[r * 4:r * 4 + 4]) for r in range(3)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    s = np.array(stats)
    print(f"frames {len(s)}  mean luma max {s[:, 0].max():.3f} (frame {s[:, 0].argmax()})  avg {s[:, 0].mean():.3f}  "
          f">0.92 max {100 * s[:, 1].max():.2f}%  peak {s[:, 2].max():.3f}  frames mean>=0.62: {(s[:, 0] >= 0.62).sum()}")
