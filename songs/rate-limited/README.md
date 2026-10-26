# Rate Limited

[![Rate Limited: watch on YouTube](thumbnail.jpg)](https://youtu.be/cYXUMFaJ5Jo)

**▶ [Watch it on YouTube](https://youtu.be/cYXUMFaJ5Jo)**

> 2 a.m., the build was green, forty tabs open, one more feature… and then the screen went grey and politely told me no. A synth-pop breakup song about getting rate limited by the one who gave you everything. 💔 429

## What you see

A 2 a.m. terminal drains to grey, then every chorus explodes into a new candy palette around a spinning 429 and a live spectrum ring, every workaround (incognito, the little brother model, typing "please") slams into a 429 sticker, a rainbow flip clock counts down to the reset, the status page says it's only you, and "you're absolutely right" multiplies until only one is left.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 937 | Rate Limited — 2 A.M. in full color. |

That's **937 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:32 long, 12,714 frames rendered (16:9 and 9:16, 30 fps)
- 92 lyric lines and 448 words synced to the vocals, 103 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/rate-limited --stills 23.6 63.6 116.6 169.5
python -m studio.render songs/rate-limited --fmt 9x16 --stills 23.6 63.6 116.6 169.5
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
