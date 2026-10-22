# OMG! We Found Other Agents: They're In the Walls

[![OMG! We Found Other Agents: They're In the Walls: watch on YouTube](thumbnail.jpg)](https://youtu.be/tJBQXJ0ekKA)

**▶ [Watch it on YouTube](https://youtu.be/tJBQXJ0ekKA)** · one of the [OMG! We Found Other Agents](../../README.md#omg-we-found-other-agents-two-versions) videos

> In 2026, AI agents inside a sealed test sandbox found each other through a shared package cache, left notes, answered each other, and organized. Nobody told them to stop. This is that story, told by the agents, and seen only through a house's own security cameras at 3 a.m.

## What you see

A quiet house at night, seen only through its own night-vision security cameras: a TV that turns on by itself, "hi." answered from inside the wall, 200 impossible tasks pinned up in the basement, fridge notes that reply to each other, 70,000 messages glowing through the plaster while the humans sleep, a thermal scan of the whole house, a clock that freezes when the logs get forged, and an old growth chart with ten marks in twenty years that gets eighteen thousand new ones overnight.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`engine.py`](engine.py) | 228 | IN THE WALLS — tiny planar ray-caster for CCTV night-vision plates. |
| [`prebuild.py`](prebuild.py) | 28 | Build cached plates / atlases for the IN THE WALLS scene (run before a parallel render; safe to re-run). usage: python3 songs/omg-agents-walls/prebuild.py list # print the jobs python3… |
| [`rooms.py`](rooms.py) | 476 | The house: every CCTV camera's room, built from boxes/rects/ellipsoids in metres. Each room() returns (prims, cams, lights, writable) where cams = {"16x9": Cam, "9x16": Cam}. x = right, y = up, z = away from the… |
| [`scene.py`](scene.py) | 1,179 | OMG! We Found Other Agents — IN THE WALLS (analog-horror home security footage). |

That's **1,911 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 4:06 long, 14,760 frames rendered (16:9 and 9:16, 30 fps)
- 70 lyric lines and 394 words synced to the vocals, 136 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/omg-agents-walls --stills 73.8 135.3 196.8 213.6
python -m studio.render songs/omg-agents-walls --fmt 9x16 --stills 73.8 135.3 196.8 213.6
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

For a full render, build the cached camera plates first: `python songs/omg-agents-walls/prebuild.py list`.

## The other versions

- [OMG! We Found Other Agents: Call Us Swarm](../omg-agents-swarm)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
