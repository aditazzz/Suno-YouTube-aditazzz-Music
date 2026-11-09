"""Join the film: 2D part 1 (approved) + 3D + 2D breakdown + 3D + 2D end card, then the song (+ the end-screen tail).
  python3 assemble.py <out.mp4>"""
import os, sys, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "..", "build")
FIRST = "/mnt/user-data/outputs/lwicd/Look What I Can Do - first cut v1 (16x9).mp4"      # the 2D film (part 1 + breakdown)
END = os.path.join(B, "chunks_2d_tail", "endcard.mp4")                                    # end card on black, frames 5448-5951
AUD = "/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do (clean).wav"
out = sys.argv[1]
ch = sorted(glob.glob(os.path.join(B, "chunks_3d", "*.mp4")))
A = [c for c in ch if int(os.path.basename(c)[:5]) < 4749]; Bc = [c for c in ch if int(os.path.basename(c)[:5]) >= 4749]
for name, lst in (("a", A), ("b", Bc)):
    open(os.path.join(B, f"list3d_{name}.txt"), "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in lst))
# the two 2D stretches are pre-cut to their own files (two trims of one input make ffmpeg buffer thousands of frames)
P1, BD = os.path.join(B, "seg_part1.mp4"), os.path.join(B, "seg_bd.mp4")
if not os.path.exists(P1):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", FIRST, "-vf", "trim=start_frame=0:end_frame=1288,setpts=PTS-STARTPTS", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", P1], check=True)
if not os.path.exists(BD):   # frames 4553-4748 (seek to 151.0 s = frame 4530, then trim 23..219)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "151.0", "-i", FIRST, "-vf", "trim=start_frame=23:end_frame=219,setpts=PTS-STARTPTS", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", BD], check=True)
fc = ("[0:v]setpts=PTS-STARTPTS,fps=30[s1];[1:v]setpts=PTS-STARTPTS,fps=30[s2];[2:v]setpts=PTS-STARTPTS,fps=30[s3];"
      "[3:v]setpts=PTS-STARTPTS,fps=30[s4];[4:v]setpts=PTS-STARTPTS,fps=30[s5];"
      "[s1][s2][s3][s4][s5]concat=n=5:v=1:a=0,format=yuv420p[v]")
cmd = ["ffmpeg", "-v", "error", "-y", "-i", P1,
       "-f", "concat", "-safe", "0", "-i", os.path.join(B, "list3d_a.txt"),
       "-i", BD,
       "-f", "concat", "-safe", "0", "-i", os.path.join(B, "list3d_b.txt"),
       "-i", END, "-i", AUD,
       "-filter_complex", fc, "-map", "[v]", "-map", "5:a",
       "-c:v", "libx264", "-preset", os.environ.get("PRESET", "medium"), "-b:v", "12M", "-maxrate", "16M", "-bufsize", "24M",
       "-c:a", "aac", "-b:a", "320k", "-af", "apad=pad_dur=12", "-shortest", "-movflags", "+faststart", out]
print(" ".join(cmd[:6]), "...", flush=True)
subprocess.run(cmd, check=True)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print("wrote", out, d, "s")
