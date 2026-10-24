# Deployed on a Friday (the Fable version): The Drive

[![Deployed on a Friday (the Fable version): watch on YouTube](thumbnail.jpg)](https://youtu.be/FRhtSqMPmFY)

**▶ [Watch it on YouTube](https://youtu.be/FRhtSqMPmFY)** · made with Claude Fable 5.1 · the Claude Opus 5.5 version of the same song, a 3D beach town, is [here](../deployed-on-a-friday)

> Four fifty-nine, laptop half shut. One little change, what could it cut? 🚗 The whole song is the drive home after shipping at 4:59 on a Friday, and every lyric is a road sign.

## What you see

The whole video is seen from the driver's seat of a car on a coast highway. The dashboard carries the clock, the gauges and a phone in its mount: at 4:59 the phone shows PR #459 and a green SHIP IT button, the office gate lifts, and the drive starts. The first verse is road signs: NO TICKET, NO TEST, NO SECOND PAIR OF EYES, MERGE → MAIN, a green light that lies. The pager buzzes in the pre-chorus, and every chorus the tide comes in over the road: the car floats, water rises inside it, the gauges go sunset red, a PROD warning light blinks and a ROLLBACK life ring comes through the windshield on a rope.

Verse two is night on a pier of neon Slack channels: the bank sign flips from $ $ $ to NULL, a queue of RETRY cars backs up, dead letters stack up on the shoulder, and a billboard says VP is typing… then stops. The bridge parks the car at an overlook at low tide, where the seabed shows every shortcut (TODO, hardcoded, skip tests) and the phone has one bar of signal. Verse three is a U-turn and the fix: the pipeline crawls along the road's center line and then whooshes, the road dips and climbs back for "graph dips down, graph comes back", and the lights go green on green. The final chorus is dawn, the tide going out and the PROD lighthouse still standing, past a MONDAY: POSTMORTEM billboard. The outro is the office gate at 4:59 again, SHIP IT on the phone: a loop.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 318 | The story: speed and distance along the road, the clock, the time of day, the tides, the phone's screens, every sign and when it appears. |
| [`dof_world.py`](dof_world.py) | 384 | The pseudo-3D road: a curving, dipping track, sky and sea by time of day, the flood over the road, sprites placed by distance, fog and glow. |
| [`dof_sprites.py`](dof_sprites.py) | 350 | Every roadside thing, drawn once and cached: highway signs, billboards, neon channel names, palms, streetlights, the RETRY cars, the lighthouse, the gate, the life ring. |
| [`dof_dash.py`](dof_dash.py) | 323 | Inside the car: dashboard, gauges and clock, the phone and its screens, coffee, laptop, wheel and hands, mirror, water inside the car. |
| [`dof_type.py`](dof_type.py) | 93 | The lyrics, kept inside the phone-safe area in 9:16. |
| [`v1_paper_boat/scene.py`](v1_paper_boat/scene.py) | 1,280 | The first version (the PR folds into a paper boat), kept to show how it got here. |

That's **1,468 lines** of Python for The Drive (2,748 with the first version), on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:18 long, 11,906 frames rendered (16:9 and 9:16, 30 fps)
- 54 lyric lines and 324 words synced to the vocals, 96 BPM
- 5 Shorts cut from it

## Render it

```bash
python -m studio.render songs/deployed-on-a-friday-fable --stills 8.6 25 53 81.5 123.5 157.6
python -m studio.safezone songs/deployed-on-a-friday-fable
python -m studio.render songs/deployed-on-a-friday-fable --fmt 9x16 --stills 8.6 25 53 81.5 123.5 157.6
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Fable 5.1: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
