# Vacation to My Bed

[![Vacation to My Bed: watch on YouTube](thumbnail.jpg)](https://youtu.be/0G3WPkeBMAs)

**▶ [Watch it on YouTube](https://youtu.be/0G3WPkeBMAs)**

> Two weeks of fires and a twelve-tab brain, so I booked a trip. First class, no fee, one-way ticket down the hall. Packed my PJs and a bag of chips. Travel time: 4 seconds. 🛏️✈️

## What you see

Two weeks of fires and a twelve-tab brain, so she books a trip: a one-way ticket down the hall. In 16:9 each of five illustrations becomes a tilted postcard on warm risograph paper, with big synced lyrics in coral and teal, a boarding pass (FROM: DESK, TO: BED, FLIGHT TIME: 4 SEC) and passport stamps that slam on every chorus. In 9:16 the illustration fills the frame, with the lyric on a paper label.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 249 | Vacation (To My Bed) — the risograph postcard, with a boarding pass. |

That's **249 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:05 long, 11,334 frames rendered (16:9 and 9:16, 30 fps)
- 44 lyric lines and 213 words synced to the vocals, 103 BPM
- 6 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/vacation-to-my-bed --stills 46.2 55.5 101.7 147.9
python -m studio.render songs/vacation-to-my-bed --fmt 9x16 --stills 46.2 55.5 101.7 147.9
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

This scene also needs the five illustrations the postcards show (`img/0.png` to `img/4.png`). Those aren't in this repo, so it won't render as is; the code is here to read.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
