# Graceful Shutdown

[![Graceful Shutdown: watch on YouTube](thumbnail.jpg)](https://youtu.be/rGj4VVjmH4Q)

**▶ [Watch it on YouTube](https://youtu.be/rGj4VVjmH4Q)**

> Received SIGTERM. You have thirty seconds. Please save your work. 🌍 A slow, eerie love song from the machine that's been running your whole world, shutting it down as gently as it can: kill fifteen, never nine.

## What you see

The world is a process, and someone who loves it is shutting it down gracefully. Photoreal space: the real Earth (NASA Blue/Black Marble), a physically-motivated atmosphere, an eclipse that becomes an EYE (the Earth's night side is the pupil, the Sun's corona the iris, lids of amber light). The eye opens on SIGTERM, blinks on "shut-shut-shut-shutdown", and closes for good on "exit code zero". In between, the simulation shows its seams: the sunrise renders at 5 fps, the Moon drops frames, the clouds loop every 4 s, the ocean runs out of memory, the heat isn't computed, the sky is a skybox, cities are garbage collected, and in the bridge the sky and sea are unmounted. HUD: a 30-second grace period that counts down across the whole song (it hits 0 on "process one") and a count of running processes (people) that falls to 1, then 0.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 602 | Graceful Shutdown — Claude Opus 5.5 version. |

That's **602 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:35 long, 12,888 frames rendered (16:9 and 9:16, 30 fps)
- 59 lyric lines and 311 words synced to the vocals, 117 BPM
- 6 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/graceful-shutdown-opus --stills 8.5 64.4 118.1 171.8
python -m studio.render songs/graceful-shutdown-opus --fmt 9x16 --stills 8.5 64.4 118.1 171.8
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
