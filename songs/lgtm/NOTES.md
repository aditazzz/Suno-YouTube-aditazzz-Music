# LGTM: how it was made

This video was made on October 10, 2026, in one chat with Claude Opus 5.5, before the shared engine in `studio/`
existed. The code here is the code that rendered the published video, recovered from that chat. The beat file and
the fonts were downloaded or computed in the chat, so they are described here rather than included.

## Files

| File | What it is |
|---|---|
| `lgtm.py` | The renderer. `python3 lgtm.py still <t>...` writes stills to `stills/`; `python3 lgtm.py seg <f0> <f1> <out.mp4>` renders a frame range (30 fps). `LGTM_V=1` renders the 9:16 layout. |
| `doc.py` | Generates the pull-request diff (`lgtm.py` imports it). |
| `thumb.py` | The YouTube thumbnail (`out/LGTM_thumbnail.png`, 1280×720) from the video's own layers. |
| `sheet.py`, `vsheet.py` | Contact sheets of 16:9 / 9:16 stills for review. |

Python: numpy, Pillow, scipy. ffmpeg on the PATH for `seg`.

## What isn't in the repo

- `beats.json`, loaded at import: `{"beats": [...], "env": [...], "onset": [...]}`, beat times in seconds plus an
  energy envelope and an onset strength track sampled at 30 fps, made from the song with librosa
  (`librosa.beat.beat_track`, an RMS envelope and `onset_strength`, each resampled to 30 fps and scaled 0–1).
  `../next-token/nt_beats.py` is the same idea for the other song and shows the shape.
- The fonts, in `fonts/` next to the code: `jetbrains-mono-400.ttf`, `jetbrains-mono-700.ttf`, `cinzel-700.ttf`,
  `cinzel-900.ttf`, `cormorant-garamond-600.ttf`, `cormorant-garamond-500-italic.ttf`; and Inter Medium and SemiBold
  from `/usr/share/fonts/opentype/inter/`. The TTFs were made from the `@fontsource` packages:

  ```sh
  mkdir -p fonts && cd fonts
  npm i --silent @fontsource/cinzel @fontsource/cormorant-garamond @fontsource/jetbrains-mono
  pip install fonttools brotli
  python3 - <<'EOF'
  from fontTools.ttLib import TTFont
  want = {"cinzel": ["700", "900"], "cormorant-garamond": ["600", "500-italic"], "jetbrains-mono": ["400", "700"]}
  for fam, ws in want.items():
      for w in ws:
          parts = w.split("-"); style = "italic" if len(parts) > 1 else "normal"
          f = TTFont(f"node_modules/@fontsource/{fam}/files/{fam}-latin-{parts[0]}-{style}.woff2"); f.flavor = None; f.save(f"{fam}-{w}.ttf")
  EOF
  ```

- The audio (`LGTM.wav`), which is only needed to mux the final file.

## Render and assemble, as it was run

```sh
# stills
mkdir -p stills
python3 lgtm.py still 1.5 8 12.6 13.1 20 24 31.1 36 38.5 42 46 49.5
LGTM_V=1 python3 lgtm.py still 8 12.9 13.2 24 31.2 42 46 49.6 62 69 80 91.8 93.5 97 102.4 106.5 117.6 124.5 129.5 147 158 169 176.3 178.9

# 16:9 in two halves (5,398 frames = 179.92 s), then join with the audio
mkdir -p out
python3 lgtm.py seg 0 2700 out/a.mp4 &
python3 lgtm.py seg 2700 5398 out/b.mp4
printf "file 'a.mp4'\nfile 'b.mp4'\n" > out/list.txt
ffmpeg -f concat -safe 0 -i out/list.txt -i LGTM.wav -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest out/LGTM_music_video.mp4

# 9:16, same frame ranges, and the 23 s hook cut
LGTM_V=1 python3 lgtm.py seg 0 2700 out/va.mp4 &
LGTM_V=1 python3 lgtm.py seg 2700 5398 out/vb.mp4
printf "file 'va.mp4'\nfile 'vb.mp4'\n" > out/vlist.txt
ffmpeg -f concat -safe 0 -i out/vlist.txt -i LGTM.wav -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest out/LGTM_reel_master.mp4
ffmpeg -ss 48.3 -t 22.9 -i out/LGTM_reel_master.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -af "afade=t=in:d=0.15,afade=t=out:st=22.3:d=0.6" -c:a aac -b:a 256k -movflags +faststart out/LGTM_reel_hook_23s.mp4

# thumbnail
python3 thumb.py
```
