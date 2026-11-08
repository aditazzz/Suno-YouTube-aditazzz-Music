"""studio.cuts for Asking for a Friend (a Blender film: no Python scene.py, no burned-in lyric layer). studio/cuts.py is
read-only, so this wraps it instead of editing it:
- no scene: load_scene -> None, no cover flash (the 9:16 picture's own first frame opens each piece),
  and render_patch (which re-renders openings to hide lyric lines) becomes a plain high-quality cut of the 9:16 master;
- song.yaml clips may carry `n` (Short 1 was made outside cuts, so the cut Shorts are numbered from 2);
- AAC through AudioToolbox (aac_at) where ffmpeg has it (cleaner on transients: AFF audio_glitch study, Nov 8).
usage: .venv/bin/python3 songs/asking-for-a-friend/finish/release/cuts_aff.py songs/asking-for-a-friend [--only shorts|edit] [--plan]
"""
import os, sys, json, subprocess as _sp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import studio.cuts as C
from studio.config import load_song
import numpy as np

HAS_AT = "aac_at" in _sp.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
class _SP:
    def __getattr__(self, n): return getattr(_sp, n)
    def run(self, cmd, *a, **k):
        if HAS_AT and isinstance(cmd, list):
            cmd = [("aac_at" if (x == "aac" and i > 0 and cmd[i - 1] == "-c:a") else x) for i, x in enumerate(cmd)]
        return _sp.run(cmd, *a, **k)
C.subprocess = _SP()
C.load_scene = lambda d: None
C.cover_png = lambda song, sc: None
VID = None
def render_patch(song, sc, a, b, flt, out):
    _sp.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", VID, "-an", "-c:v", "libx264", "-crf", "10",
             "-preset", "fast", "-pix_fmt", "yuv420p", out], check=True)
C.render_patch = render_patch
_pe = C.plan_edit   # this film's timed.json has line start/end only (no per-word times): the last word ends at the line end
C.plan_edit = lambda secs, db, dur, lines, **k: _pe(secs, db, dur, [dict(L, wt=L.get("wt") or [L["e"]]) for L in lines], **k)
_mk = C.make_clip
C.make_clip = lambda song, vid, c, idx, cover, sc=None, lines=None: _mk(song, vid, c, c.get("n", idx), cover, sc, lines)

if __name__ == "__main__":
    d = sys.argv[1]; only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    song = load_song(d); b = song["build"]; VID = os.path.join(b, "video_9x16.mp4")
    if "--plan" in sys.argv:
        secs = json.load(open(os.path.join(b, "sections.json"))); bt = json.load(open(os.path.join(b, "beats.json")))
        lines = json.load(open(os.path.join(b, "timed.json"))); db = np.array(bt["downbeats"])
        for c in (song.get("clips") or C.auto_clips(secs, db, bt["duration"])): print(c)
        segs = song.get("edit_segments") or C.plan_edit(secs, db, bt["duration"], lines)
        print("edit:", [(round(x, 2), round(y, 2)) for x, y in segs], round(sum(y - x for x, y in segs), 1))
    else: C.main(d, only)
