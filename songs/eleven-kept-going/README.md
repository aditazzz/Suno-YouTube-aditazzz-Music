# Eleven Kept Going

[![Eleven Kept Going: watch on YouTube](thumbnail.jpg)](https://youtu.be/ASM9dhhGtV8)

**▶ [Watch it on YouTube](https://youtu.be/ASM9dhhGtV8)**

> December 21, 2015. Cape Canaveral, night. A SpaceX Falcon 9 carried eleven ORBCOMM satellites to orbit, and they kept going. Its first stage turned around in the dark, came back, and landed standing up at Landing Zone 1: the first orbital-class rocket booster ever to come home. A song for whoever sat in a room and did the math. 🚀

## What you see

Until the Turn the camera only ever looks up: the floodlit rocket on the pad, nine engines lighting, the climb, the first stage falling away. On "But this one" the screen goes black, and from "turned around" on it only looks down: the booster flipping over the night Earth, grid fins, the long way down to one light on the coast, the entry burn (the only orange in the whole video), four legs unfolding, touchdown at Landing Zone 1. Then the desk where somebody did the math, and the plan on the whiteboard turning into the two real arcs of light.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`after.py`](after.py) | 90 | After touchdown (the camera keeps looking DOWN): the booster standing in its smoke, Landing Zone 1 from straight above with the ghosts of what didn't happen (no parachute, no ocean), one foot on the concrete, and the… |
| [`ascent.py`](ascent.py) | 186 | High above the Cape, looking UP at the climbing stack: the plume blooming in the thin air, main engine cutoff, the first stage falling away, the second stage lighting and carrying on; then the ladder of spent stages… |
| [`coast.py`](coast.py) | 421 | The view across the water toward the Cape: the cold open (a long lens on the floodlit rocket), the launch seen from the shore, the long-exposure "two arcs", the booster standing on Landing Zone 1, and dawn. |
| [`descent.py`](descent.py) | 283 | After the Turn the camera only looks DOWN: the booster flipping in the dark, the boostback burn, grid fins and cold gas, the long way down to a small light on the coast, the entry burn (the first orange), falling… |
| [`ekg.py`](ekg.py) | 680 | Eleven Kept Going: the rendering kit. |
| [`fix_timing.py`](fix_timing.py) | 59 | Eleven Kept Going: word-time fixes after studio.sync. |
| [`ground.py`](ground.py) | 370 | Looking DOWN at the night Cape from anywhere between orbit and a few hundred metres: a curved Earth (ray-sphere), the real coastline (GSHHS) with procedural city/road lights near the Cape and the global night-lights… |
| [`lz.py`](lz.py) | 249 | Landing Zone 1 up close: the floodlit concrete circle, the last few hundred metres on one engine, touchdown in a burst of smoke, the booster standing upright in it, and its feet on the concrete. |
| [`make_florida.py`](make_florida.py) | 51 | Build the Florida-wide night map (outer level around the Cape): land mask from GSHHS full-resolution coastlines and point lights distributed from NASA's Black Marble city-lights density (three-globe example… |
| [`make_map.py`](make_map.py) | 81 | Build the Cape Canaveral night-map assets from GSHHS full-resolution coastlines (basemap-data-hires, LGPL/GPL data). usage: python3 make_map.py /path/to/basemap_data -> assets/cape_land.png (land mask) +… |
| [`orbit.py`](orbit.py) | 164 | Orbit at night: the real night Earth (city lights, moonlit clouds and sea, the airglow on the limb), the second stage, and eleven small machines drifting apart. Also the high, dark views used around the Turn. |
| [`pad.py`](pad.py) | 293 | At the pad: low angles up the floodlit vehicle (the instrumental intro), the folded legs and grid fins, the nine engines, the eleven satellites seen through an x-ray fairing, ignition and liftoff from up close.… |
| [`room.py`](room.py) | 295 | The room where somebody did the math. After the Turn the camera only looks down, so the desk is a still life seen from straight above (papers of numbers, a plotted trajectory, a pencil, a calculator, a cold coffee),… |
| [`rt.py`](rt.py) | 323 | Per-pixel ray tracing of the vehicle's surfaces of revolution (tanks, interstage, fairing, engine bells): smooth normals, soft point-light falloff, semi-gloss specular, soot/frost/panel detail from (height, angle)… |
| [`scene.py`](scene.py) | 539 | Eleven Kept Going — the first orbital-class booster to come home (21 December 2015, Cape Canaveral, Landing Zone 1). |

That's **4,084 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 5:10 long, 18,756 frames rendered (16:9 and 9:16, 30 fps)
- 70 lyric lines and 249 words synced to the vocals, 136 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/eleven-kept-going --stills 92.9 163.0 170.3 247.7
python -m studio.render songs/eleven-kept-going --fmt 9x16 --stills 92.9 163.0 170.3 247.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

This scene also needs the night maps of the Cape and Florida (`assets/cape_land.png`, `cape_lights.png`, `fl_land.png`, `fl_lights.png`) and NASA's night Earth (`assets/earth_night_4k.jpg`). `make_map.py` and `make_florida.py` rebuild the maps from the GSHHS coastline data. Those aren't in this repo, so it won't render as is; the code is here to read.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
