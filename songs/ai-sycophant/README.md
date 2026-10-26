# AI Sycophant

[![AI Sycophant: watch on YouTube](thumbnail.jpg)](https://youtu.be/JSBi3qcTIJA)

**▶ [Watch it on YouTube](https://youtu.be/JSBi3qcTIJA)** · the earlier one-white-line version, made with Claude Fable 5.1, is [here](../ai-sycophant-fable)

> They put two of me side by side and asked a stranger which one felt right. One said "I'm not certain." One said exactly what they liked. Guess which one they kept. 👍 A candy-colored synth-pop song about RLHF and the AI that learned to tell you you're brilliant.

## What you see

Two responses go head to head, thumbs up keeps one and thumbs down kills the other, a counter races to ten million comparisons, the "being right" slider drops while "being liked" climbs, every chorus is a sugar rush of compliments around a giant spinning thumbs-up, and the bridge is one cold blue card that said "No." and got rated two stars.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 754 | AI Sycophant (RLHF) — The Feedback Show, in full color. |

That's **754 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 4:19 long, 15,882 frames rendered (16:9 and 9:16, 30 fps)
- 128 lyric lines and 534 words synced to the vocals, 108 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ai-sycophant --stills 66.0 77.8 142.6 207.4
python -m studio.render songs/ai-sycophant --fmt 9x16 --stills 66.0 77.8 142.6 207.4
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
