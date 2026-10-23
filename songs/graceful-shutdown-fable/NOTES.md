# Graceful Shutdown (the Fable version): how it was made

This video was made on October 12, 2026, in one chat with Claude Fable 5.1, with the small engine that came before
`studio/`: [`studio-early/`](../../studio-early). The code here is the code that rendered the published video,
recovered from that chat. The only change is that the absolute paths the chat used (`/home/claude/common`,
`/home/claude/syco`, `/home/claude/fonts`) are now relative to the repo; each one is marked with a comment.

## Files

| File | What it is |
|---|---|
| `scenes.py` | Every section of the video, drawn with skia through `studio-early/kit.py` (which brings in the line helpers from [`../ai-sycophant-fable/lib.py`](../ai-sycophant-fable/lib.py)). `SECTIONS`, `BPM` and `PHASE` (the beat grid) are at the top; the word timings are inside each section. |

The renderer, the chunked render driver, the thumbnail and the assembly script are in `studio-early/`.

## What isn't in the repo

- `analysis.npz`: beat and loudness tracks made from the song with `studio-early/analyze.py`.
- The word timings came from a local Whisper pass (`studio-early/asr/asrw.mjs`) and were then written into `scenes.py`,
  so the transcript itself isn't needed.
- The fonts (see [`studio-early/README.md`](../../studio-early/README.md)) and the audio (`Graceful Shutdown.wav`).

## Render and assemble, as it was run

```sh
# from the repo root
S=songs/graceful-shutdown-fable
python3 studio-early/analyze.py "Graceful Shutdown.wav" $S/analysis.npz
ffmpeg -i "Graceful Shutdown.wav" -ac 1 -ar 16000 -f f32le $S/full.f32 && (cd studio-early/asr && node asrw.mjs ../../$S/full.f32 ../../$S/asr_w.json)

python3 studio-early/render.py $S still 2.5 9.0 13.5 60 120 180      # stills -> $S/stills/s_<t>.png

# 16:9 then 9:16, in 300-frame chunks, two workers (END 218.0 s -> 6,540 frames)
for k in 0 1; do studio-early/drive.sh $S $k 2 6540 & done; wait

# concat the chunks, mux the audio, cut the Shorts and Reels
python3 studio-early/assemble.py $S "Graceful Shutdown.wav" 218.0 "Graceful Shutdown" \
  '[["Short 1 (chorus, 39s)", 49.3, 88.5], ["Short 2 (countdown to final chorus, 50s)", 147.5, 198.0], ["Reel 1 (chorus, 30s)", 57.3, 87.6], ["Reel 2 (the world glitches, 20s)", 16.9, 36.8], ["Reel 3 (countdown, 20s)", 147.5, 167.3]]'

python3 studio-early/thumbs.py gs         # the thumbnail: out/thumb_text.png and out/thumb_clean.png
```
