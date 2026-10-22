# Deployed on a Friday

[![Deployed on a Friday: watch on YouTube](thumbnail.jpg)](https://youtu.be/8DQ2izFZiO0)

**▶ [Watch it on YouTube](https://youtu.be/8DQ2izFZiO0)**

> Four fifty-nine, laptop half shut. One little change, what could it cut? No ticket, no test, no second pair of eyes, and a green check lying like it always lies. 🌊 A beach-day folk-pop song about taking prod down on a Friday.

## What you see

A 3D beach town where every building is a service: the town clock reads FRI 4:59, she ships one little change and the Auth lighthouse starts to flicker, the tide floods Main Street every chorus while she floats on a ROLLBACK life ring past a dashboard at -97%, the Payments Bank sign flips to NULL, a seagull VP circles "typing…", dead letters wash up as bottles, low tide shows TODO crabs and a SHORTCUT shipwreck, and she fixes it all from the parking lot on one bar.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 1,004 | Deployed on a Friday — a beach-sunset outage. |
| [`scene_2d.py`](scene_2d.py) | 385 | Deployed on a Friday — a beach-sunset outage. |
| [`scene_3d_v1.py`](scene_3d_v1.py) | 519 | Deployed on a Friday — a beach-sunset outage. |

That's **1,908 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:13 long, 11,606 frames rendered (16:9 and 9:16, 30 fps)
- 54 lyric lines and 324 words synced to the vocals, 96 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/deployed-on-a-friday --stills 3.6 58.0 106.4 154.8
python -m studio.render songs/deployed-on-a-friday --fmt 9x16 --stills 3.6 58.0 106.4 154.8
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

`scene.py` is the video that was published. `scene_2d.py` and `scene_3d_v1.py` are the two earlier versions of the same idea, kept to show how it got there.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
