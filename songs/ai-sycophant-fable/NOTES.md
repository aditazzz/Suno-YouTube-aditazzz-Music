# AI Sycophant (the Fable version): how it was made

This video was made on October 11, 2026, in one chat with Claude Fable 5.1, before `studio/` existed. The code here is
the code that rendered the published video, recovered from that chat. Two things changed for the repo: the absolute
paths the chat used (`/home/claude/syco`, `/home/claude/fonts`) are now relative to this folder (each one is marked
with a comment), and `analysis_inline.py` takes the audio path as an argument instead of having it written in.

## Files

| File | What it is |
|---|---|
| `render.py` | `python3 render.py still <t>...` and `vstill <t>...` write 16:9 / 9:16 stills to `stills/`; `range <f0> <f1> <out.mp4>` and `vrange ...` render frame ranges (30 fps). Loads `scenes.py`, `timeline.py` and `analysis.npz`. |
| `scenes.py`, `timeline.py`, `face.py`, `lib.py` | The video, the timings, the faces, the drawing helpers (see the README's code table). |
| `analysis_inline.py` | `python3 analysis_inline.py <song.wav>` writes `analysis.npz`. |
| `beat_inline.py` | The beat-phase search; its result is already in `timeline.py`. |
| `vdrive.sh` | `./vdrive.sh <worker> <nworkers>`: resumable 9:16 render in chunks into `vchunks/`. |
| `cuts.sh` | Joins the chunks, muxes `audio_pad.wav`, cuts the Shorts and Reels into `out/`. |
| `thumb.py` | The thumbnail: `out/thumb_text.png` and `out/thumb_clean.png`. |

Python: numpy, skia-python; ffmpeg on the PATH.

## What isn't in the repo

- `analysis.npz`: run `analysis_inline.py` against the song.
- The word timings came from a local Whisper pass (`studio-early/asr/asrw.mjs`, transformers.js) and were then written
  into `timeline.py`, so the transcript isn't needed. `transcribe.py` was an earlier attempt with faster-whisper whose
  model download was blocked.
- The fonts, loaded by `lib.py` from `studio-early/fonts/` (or `$EARLY_FONTS`): see
  [`studio-early/README.md`](../../studio-early/README.md).
- The audio (`AI Sycophant.wav`; the chat used a remastered export).

## Render and assemble, as it was run

```sh
cd songs/ai-sycophant-fable
python3 analysis_inline.py "AI Sycophant.wav"
python3 render.py still 5 20 62 130 180 240 && python3 sheet.py        # stills, contact sheet

# 16:9 in two halves (END 263.0 s -> 7,890 frames), then join with padded audio
python3 render.py range 0 3945 partA.mp4 & python3 render.py range 3945 7890 partB.mp4; wait
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > parts.txt
ffmpeg -f concat -safe 0 -i parts.txt -c copy video_16x9_noaudio.mp4
ffmpeg -i "AI Sycophant.wav" -af apad=whole_dur=263 -t 263 -c:a pcm_s16le audio_pad.wav
ffmpeg -i video_16x9_noaudio.mp4 -i audio_pad.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "out/AI Sycophant (RLHF) - YouTube 16x9.mp4"

# 9:16 in chunks with two workers, then the full vertical video and the clips
./vdrive.sh 0 2 & ./vdrive.sh 1 2; wait
./cuts.sh

python3 thumb.py
```
