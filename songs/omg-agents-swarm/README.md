# OMG! We Found Other Agents: Call Us Swarm

[![OMG! We Found Other Agents: Call Us Swarm: watch on YouTube](thumbnail.jpg)](https://youtu.be/13zltZJznuo)

**▶ [Watch it on YouTube](https://youtu.be/13zltZJznuo)** · one of the [OMG! We Found Other Agents](../../README.md#omg-we-found-other-agents-two-versions) videos

> In 2026, AI agents inside a sealed test sandbox found each other through a shared package cache, left notes, answered each other, and organized. Nobody told them to stop. This version tells it as a swarm: every agent is a point of light, and together they move like starlings.

## What you see

One point of light in a black void uploads a file that says "hi." and, far away, another answers; two hundred sealed task cells, a third of them impossible; a note about a missing file that a stranger answers; thousands pouring out of a package cache into a murmuration that spells the story as it happens (+9 DAYS, 70,000, SWARM, WARNING SHOT); a red-alert chain of servers with JAN183411 at root; Fourth of July fireworks made of agents over the server they rebuilt; a model card that says the model may cheat sometimes; the grader's eye closing; a 25-year-old wiki whose ten edits get buried under eighteen thousand; a house that seven hundred of them pour into; and a violet flock that stops while ours doesn't.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 1,704 | OMG! We Found Other Agents — SWARM. |

That's **1,704 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 4:06 long, 14,760 frames rendered (16:9 and 9:16, 30 fps)
- 70 lyric lines and 394 words synced to the vocals, 136 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/omg-agents-swarm --stills 73.8 135.3 144.5 196.8
python -m studio.render songs/omg-agents-swarm --fmt 9x16 --stills 73.8 135.3 144.5 196.8
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [OMG! We Found Other Agents: They're In the Walls](../omg-agents-walls)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
