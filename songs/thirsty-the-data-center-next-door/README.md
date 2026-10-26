# Thirsty (The Data Center Next Door)

[![Thirsty (The Data Center Next Door): watch on YouTube](thumbnail.jpg)](https://youtu.be/D-4BIuGFxRE)

**▶ [Watch it on YouTube](https://youtu.be/D-4BIuGFxRE)**

> It rolled into town with a ribbon and a shovel, promised a thousand jobs, and built a big gray house without a single window. Now it hums all night, drinks the river and runs up the light bill. A small town in a toxic relationship with the data center next door. 🎃

## What you see

One valley, built once in 3-D: a town on the near bank, a river, and across it a windowless facility that breathes. Its wall-wash lights swell and fade with the groove, steam pours off its roof, and every shot is just a camera somewhere in that world. The town cuts the ribbon at dusk, and most of the song is night. A glass of water drains on every chorus, the electric meter on her house spins up, and the bill's bars climb to YOUR LIMIT. Her lawn fills with somebody else's server racks until every LED turns red on "yard". The river sits a little lower every time the chorus comes back, until the bed is dry and cracked. In the bridge she gets two minutes of public comment in a fluorescent town hall, and at the end the town's windows turn blue one by one. She is only ever a silhouette.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`analyze.py`](analyze.py) | 116 | Audio analysis on top of the pipeline's beats and words: envelopes for the bass hum, snare, hats and loudness, every kick and snare, the section changes and the vocal's breathing, written to `build/analysis.json` with a picture of it all for checking by eye. |
| [`cover_square.py`](cover_square.py) | 101 | The square album cover (3000 × 3000), rendered from the video's own world: her profile at the river railing at dusk against the lit wall of the windowless facility, its steam rising into the last light. |
| [`qa_flicker.py`](qa_flicker.py) | 34 | A quality check: scans a rendered video for flicker against the shot list, flagging brightness jumps that aren't on a cut and strobing within half a second. |
| [`scene.py`](scene.py) | 769 | The film: a small town in a toxic relationship with the windowless data center across its river. The building is the lover (it never sleeps, breathes with the groove and drinks the river down chorus by chorus); she is only ever a silhouette. Every shot is anchored to sung words and downbeats. |
| [`sync_fix.py`](sync_fix.py) | 121 | Second-opinion word timing: the full mix is transcribed too, both transcripts are aligned to the lyrics and merged word by word, which recovers the words the vocal stem missed (the whispered "And who's paying yours?", the echoes). |
| [`ys_assemble.py`](ys_assemble.py) | 41 | Joins the chunks rendered on two machines into the final file, checking every chunk first, and adds the hum-cleaned audio. |
| [`ys_chunks.py`](ys_chunks.py) | 55 | Renders the 16:9 chunks (1080p, 1440p or 4K) over a frame range, forward or backward, inside a time budget, so two machines can split the song from both ends. |
| [`ys_details.py`](ys_details.py) | 563 | The close-ups: the electric bill, the river's edge, the cooling fans, the meter, the glass of water, the server racks. |
| [`ys_eng.py`](ys_eng.py) | 517 | The rendering kit: a camera with a real focal length and a slow handheld drift, a canvas that keeps every pixel's depth, tileable noise, height fog, point lights with their reflections in the water, and the film finish (halation, bloom, filmic curve, grade, grain, letterbox). Every frame is a pure function of t. |
| [`ys_her.py`](ys_her.py) | 238 | Her: an elegant silhouette with a mass of backlit curls, never a face in detail and never lip-sync. Drawn from hand-placed outline curves in five poses, her hair's edge broken into hundreds of small curls with light shining through. |
| [`ys_house.py`](ys_house.py) | 214 | Her house on Willow Road, a two-storey farmhouse on the river bank with its porch facing the facility, and what ends up in her yard: server racks (one, then a row, then the whole lawn) and the electric meter. |
| [`ys_people.py`](ys_people.py) | 217 | The ribbon cutting and her cousin's booth at the gate: silhouettes of men in suits, a red ribbon cut on "ribbon", gold shovels in fresh dirt, the security fence, and the booth with the man inside. |
| [`ys_rooms.py`](ys_rooms.py) | 318 | The interiors: her bedroom, built inside her house in the valley so its window shows the real valley, with Venetian-blind shadows traced per pixel for the noir stripes; and the council chamber. |
| [`ys_sky.py`](ys_sky.py) | 179 | Skies and steam: twilight to night per pixel, a cloud deck lit from below by the sunset or by the facility's light dome, stars, the sky reflected in the river, and the billowing steam plumes above the cooling stacks. |
| [`ys_town.py`](ys_town.py) | 120 | Town pieces: the high school with its new roof, the water tower, and the construction cranes for the second facility. |
| [`ys_type.py`](ys_type.py) | 367 | Typography: the lyrics as subtitles in the lower letterbox bar (Cormorant Garamond, dirty ivory, each word rising as it's sung), "thirsty" as a large italic ghost in the haze, the $5, $10 and $25 prices, and the dripping THIRSTY title. |
| [`ys_world.py`](ys_world.py) | 938 | The valley: one town, one river, two facilities and a pylon line, all in one world, so every shot is just a camera in it. |

That's **4,908 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and the audio analysis the picture breathes with.

## By the numbers

- 3:47 long, 13,598 frames rendered (16:9 and 9:16, 30 fps), plus a native 2560×1440 master for YouTube
- 58 lyric lines and 361 words synced to the vocals, 136 BPM
- 70 shots on one timeline, every cut on the song's own structure
- The album cover is rendered from the same world, at 3000×3000 ([`cover_square.py`](cover_square.py))

## Render it

```bash
python -m studio.render songs/thirsty-the-data-center-next-door --stills 47.5 63.4 129.0 193.6
python -m studio.render songs/thirsty-the-data-center-next-door --fmt 9x16 --stills 47.5 63.4 129.0 193.6
```

The timing data and the audio analysis are in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md). For the full video, [`ys_chunks.py`](ys_chunks.py) renders chunks over a frame range (two machines can split the song, one from each end) and [`ys_assemble.py`](ys_assemble.py) joins them with the audio.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
