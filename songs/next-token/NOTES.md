# Next Token: how it was made

This video was made on October 10, 2026, in the same chat with Claude Opus 5.5 as [LGTM](../lgtm), before the
shared engine in `studio/` existed. The code here is the code that rendered the published video, recovered from that
chat. The beat file and the fonts were computed or downloaded in the chat, so they are described here rather than
included.

## Files

| File | What it is |
|---|---|
| `nt.py` | The renderer. `python3 nt.py still <t>...` writes stills to `ntstills/`; `python3 nt.py seg <f0> <f1> <out.mp4>` renders a frame range (30 fps). `NT_V=1` renders the 9:16 layout. |
| `nt_beats.py` | `python3 nt_beats.py` reads the song and writes `nt_beats.json` (`tempo`, `beats`, `env`, `low`), which `nt.py` loads at import. Edit the audio path at the top first. |
| `nthumb.py` | The YouTube thumbnail (`out/Next_Token_thumbnail.png`, 1280×720). |
| `sheet9.py`, `vsheet.py` | Contact sheets of stills for review. |

Python: numpy, Pillow; librosa for `nt_beats.py`. ffmpeg on the PATH for `seg`.

## What isn't in the repo

- `nt_beats.json`: run `nt_beats.py` against the song.
- The fonts, in `fonts/` next to the code: `jetbrains-mono-400.ttf`, `jetbrains-mono-700.ttf`,
  `cormorant-garamond-600.ttf`, `cormorant-garamond-500-italic.ttf`; and Inter Medium and Inter Display Black from
  `/usr/share/fonts/opentype/inter/`. They were converted from the `@fontsource` packages the same way as in
  [`../lgtm/NOTES.md`](../lgtm/NOTES.md) (the two videos shared one `fonts/` folder).
- The audio (`Next Token.wav`).

## Render and assemble, as it was run

```sh
python3 nt_beats.py

# stills
mkdir -p ntstills
python3 nt.py still 37 53.4 57.2 70.5 96.8 144.5 146.4 172.5 181.2
NT_V=1 python3 nt.py still 12 24 37 41.5 46.3 50 53.4 55.5 57.6 61.5 70.5 90.5 96.8 101 143.5 146.4 152 160 176.5 181
python3 sheet9.py ntstills/shH.jpg $(ls ntstills/s_*.png | sort)

# 16:9 in two halves (5,735 frames = 191.16 s), then join with the audio
mkdir -p out
python3 nt.py seg 0 2868 out/nta.mp4 &
python3 nt.py seg 2868 5735 out/ntb.mp4
printf "file 'nta.mp4'\nfile 'ntb.mp4'\n" > out/ntlist.txt
ffmpeg -f concat -safe 0 -i out/ntlist.txt -i "Next Token.wav" -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest out/Next_Token_music_video.mp4

# 9:16, same frame ranges
NT_V=1 python3 nt.py seg 0 2868 out/ntva.mp4 &
NT_V=1 python3 nt.py seg 2868 5735 out/ntvb.mp4
printf "file 'ntva.mp4'\nfile 'ntvb.mp4'\n" > out/ntvlist.txt
ffmpeg -f concat -safe 0 -i out/ntvlist.txt -i "Next Token.wav" -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest out/Next_Token_reel_master.mp4

# thumbnail
python3 nthumb.py
```
