"""Assemble v3 "The Comic Book": every section's chunk in order -> flat picture -> the comic-page pass -> + the song.
  python3 assemble_v3.py <out.mp4> [--no-comic] [--allow-missing]
Sections are exact frame ranges at 30 fps (see v3_BRIEF.md). A missing section is a hard error unless --allow-missing,
which fills it with a dark card naming the section (for previews)."""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build"); V3 = os.path.join(B, "v3")
AUD = "/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do (clean).wav"
SEG = [("P1a", os.path.join(B, "seg_part1.mp4"), 0, 1244, 0),        # (id, file, first frame, last frame, offset of the file's frame 0)
       ("P1b", os.path.join(V3, "P1_tail.mp4"), 1245, 1287, 1245),
       ("S1", os.path.join(V3, "S1.mp4"), 1288, 1712, 1288), ("S2", os.path.join(V3, "S2.mp4"), 1713, 1962, 1713),
       ("S3", os.path.join(V3, "S3.mp4"), 1963, 2399, 1963), ("S4", os.path.join(V3, "S4.mp4"), 2400, 2529, 2400),
       ("S5", os.path.join(V3, "S5.mp4"), 2530, 2999, 2530), ("S6", os.path.join(V3, "S6.mp4"), 3000, 3687, 3000),
       ("S7", os.path.join(V3, "S7.mp4"), 3688, 4095, 3688), ("S8", os.path.join(V3, "S8.mp4"), 4096, 4552, 4096),
       ("BD", os.path.join(B, "seg_bd.mp4"), 4553, 4748, 4553), ("S9", os.path.join(V3, "S9.mp4"), 4749, 5151, 4749),
       ("S10", os.path.join(V3, "S10.mp4"), 5152, 5447, 5152), ("END", os.path.join(B, "chunks_2d_tail", "endcard.mp4"), 5448, 5951, 5448)]


def nframes(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", p], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def main():
    out = sys.argv[1]; allow = "--allow-missing" in sys.argv; comic = "--no-comic" not in sys.argv
    parts = []; os.makedirs(os.path.join(V3, "parts"), exist_ok=True)
    for sid, f, a, b, off in SEG:
        part = os.path.join(V3, "parts", f"{a:05d}_{sid}.mp4"); n = b - a + 1
        if os.path.exists(f):
            s0 = a - off
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", f"trim=start_frame={s0}:end_frame={s0 + n},setpts=PTS-STARTPTS,fps=30,format=yuv420p",
                            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", part], check=True)
        elif allow:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x101012:s=1920x1080:r=30:d={n / 30:.4f}", "-vf",
                            f"drawtext=fontfile=/home/claude/aditazzz/suno-youtube-aditazzz-music/assets/fonts/JBMono-700.ttf:text='{sid} rendering':fontcolor=0x888888:fontsize=48:x=(w-tw)/2:y=(h-th)/2",
                            "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", part], check=True)
        else:
            sys.exit(f"missing section {sid}: {f}")
        got = nframes(part)
        if got != n: sys.exit(f"{sid}: {got} frames, expected {n}")
        parts.append(part); print(sid, n, "ok", flush=True)
    lst = os.path.join(V3, "parts.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    flat = os.path.join(V3, "flat.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", flat], check=True)
    pic = flat
    if comic:
        pic = os.path.join(V3, "comic.mp4"); subprocess.run([sys.executable, os.path.join(HERE, "comic.py"), flat, pic], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", AUD, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", os.environ.get("PRESET", "medium"),
                    "-b:v", "12M", "-maxrate", "16M", "-bufsize", "24M", "-c:a", "aac", "-b:a", "320k", "-af", "apad=pad_dur=12", "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out, nframes(out), "frames")


if __name__ == "__main__":
    main()
