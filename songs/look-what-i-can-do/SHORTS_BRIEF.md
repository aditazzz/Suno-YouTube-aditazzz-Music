# Look What I Can Do: three YouTube Shorts (9:16) — brief for the workers

The full video is public: https://youtu.be/SpaSjbRM8nQ (16:9, 1920x1080 cut at build/v3/comic.mp4, 30 fps; the
v3 architecture is in v3_BRIEF.md and README.md). Adita approved making three Shorts (Nov 8, 18:54: "All 3").

| Short | Song time (s) | Frames @30 | What's in it | Section code |
|---|---|---|---|---|
| A "Too late!" | 34.41 to 56.38 | 1032-1691 | "Can I direct?... Can I win an Oscar? Too late!" in the terminal (temperature jiggle), the dive into the city, the meeting doubling to 256 rooms that spell LOOK WHAT I CAN DO | `scene.py` (2D, part 1) then `web/s1.html` + `web/js/s1/` (3D) |
| B "Net worth" | 100.15 to 121.97 | 3005-3659 | Verse 3 in the TED Charts newspaper, ending on "$0 × 3 = $0" | `sections/s6_paper.py`, `s6_ink.py` (2D) |
| C "I knew it" | 151.05 to 186.40 | 4532-5592 | "Do you think I'm talented?" "You are extraordinarily–" "I KNEW IT!", the Please Hold tower drop, the bench: "Can we make one more?" "You've reached your usage limit." "Hey ChatGPT?" | `scene.py` (2D breakdown) then `web/s9.html` + `web/js/s9/` (3D drop + outro) |

## How to make each one
- Render NATIVELY at 1080x1920 (9:16) from the section code, never by cropping the 16:9 film. `scene.py` already handles
  vertical (`vert = H > W`); the 2D section modules take `render_frame(t, W, H)`; the 3D pages take W H in `render.mjs`
  (`PAGE=s1.html node render.mjs range 1080 1920 out.mp4 t0 t1`; the end time for frames n0..n1 is (n1+1)/30).
  Where a layout was designed for 16:9, ADAPT it for 9:16 (stack, reframe, re-place cameras) in your OWN copy or behind
  an `H > W` branch — never break the 16:9 output (the film is published; re-render a 16:9 frame or two to prove it).
- No comic-page transitions inside a Short (it's one or two worlds); cut hard or keep the section's own move.
- First frame must be a real, readable picture (never black). It doubles as the cover.
- Her rules: text inside the 9:16 safe zone (keep the bottom ~22% and right ~12% clear of anything that must be read:
  YouTube's buttons and caption sit there), type >= 34 px (cap >= 25) and lyric-sized lines >= 58 px; no text spilling
  out of its box; no blown-out white frames (mean luma < 0.62, < 12% of pixels above 0.92 on the top 86% of the frame);
  no standard subtitle-style lyric line; no kids; the GT3 RS keeps Ultraviolet paint + yellow calipers; the Claude
  robot stays recognizable; nothing inflammatory; no subscribe ask except the end card.
- End card: the last 1.5 s (added after the song section, so the Short is section length + 1.5 s): dark, clean, in the
  film's terminal look: "Full video on my channel" + a red SUBSCRIBE pill + "@adita_zzz". Keep it inside the safe zone.
- Audio: the clean song, "/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do (clean).wav",
  cut at your section's start/end with a 30 ms fade in and a 250 ms fade out before the end card; the end card is silent
  or holds the tail at low level.
- Keep the Short under 60 s.
- Output: `build/shorts/<A|B|C>.mp4` (1080x1920, 30 fps, H.264 CRF 16, AAC 320k) and `build/shorts/<A|B|C>_cover.jpg`
  (its first frame). Make a 4x3 contact sheet `build/shorts/<A|B|C>_sheet.jpg` and LOOK at it and at full-size frames
  wherever text appears before you report. Run the brightness check over every frame.
- The box has 2 cores shared by 3 workers: render each piece once, carefully; render stills first to check layouts.
- Don't touch `build/v3/*`, other workers' files, or anything outside songs/look-what-i-can-do/. Don't commit or push.

Report back: the file paths, frame count/duration, what you changed for 9:16 (files), anything you're unsure of, and the
cover frame.
