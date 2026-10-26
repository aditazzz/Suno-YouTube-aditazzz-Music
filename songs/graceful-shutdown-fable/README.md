# Graceful Shutdown (the Fable version)

[![Graceful Shutdown (the Fable version): watch on YouTube](thumbnail.jpg)](https://youtu.be/ZYoCc55onzw)

**▶ [Watch it on YouTube](https://youtu.be/ZYoCc55onzw)** · one of the [earlier videos](../../README.md#earlier-videos), made with Claude Fable 5.1 · the later photoreal version, made with Claude Opus 5.5, is [here](../graceful-shutdown-opus)

> Received SIGTERM. You have thirty seconds. Please save your work. 🌙 The simulation is being turned off, gently: a slow, eerie love song from the machine that's been running your whole world.

## What you see

Thin white lines on black, drawn like a schematic of the world. It opens on a save dialog, "Save changes to 'the world'? It will close in 30 seconds", with a moon over a horizon and one small house, while a HUD counts down the grace period for the whole song. Verse one is the seascape running out of budget: the birds loop on a four-second clip, the coffee goes cold in close-up because no one is computing the heat, the neighbor is stuck on a walk cycle, and the whole world shrinks into a laptop screen, a borrowed machine.

The pre-chorus is two fingers almost touching above the button. The chorus flashes the title, closes every window one by one, insists on kill -15, never -9, stutters its labels on "shut-shut-shut-shutdown", and packs the things you love into a box. Verse two shows the seams: the sky is a skybox sphere, the roads not taken, a déjà vu where two identical frames converge, names being garbage-collected. In the bridge the connections drop and the locks close, down to process one. The final chorus collapses the world to the horizon line, and the outro leaves a single dot on it.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scenes.py`](scenes.py) | 858 | Every section of the video: the world primitives (horizon, sea, moon, birds, house), the finger, the save dialog, the HUD, and the intro, verses, pre-choruses, choruses, bridge and outro for both aspect ratios. |

That's **858 lines** of Python for this video, on top of [`studio-early/`](../../studio-early), the small engine that came before [`studio/`](../../studio): it draws with skia, renders stills and frame ranges, and assembles the final files. [`lyrics.txt`](lyrics.txt) has the lyrics; [`NOTES.md`](NOTES.md) has the exact commands that were used.

## By the numbers

- 3:38 long, 13,080 frames rendered (16:9 and 9:16, 30 fps), 119 BPM
- 59 lyric lines and 319 words synced to the vocals (the word timings came from a local Whisper pass and are written into `scenes.py`)
- 5 Shorts and Reels cut from it

## Render it

```bash
# from the repo root; see studio-early/README.md for what the early engine needs
python3 studio-early/render.py songs/graceful-shutdown-fable still 2.5 9 13.5 60 120 180    # -> songs/graceful-shutdown-fable/stills/
```

The scene needs `analysis.npz` (beat and loudness tracks made from the song by `studio-early/analyze.py`) and the fonts in [`studio-early/README.md`](../../studio-early/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Fable 5.1: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
