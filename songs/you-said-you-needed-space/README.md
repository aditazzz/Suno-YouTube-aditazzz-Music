# You Said You Needed Space

> Earth gave him rivers, rain, and every spark he had. Then he said he needed space. A breakup song between a living planet and an ambitious satellite, ending with a thread that reaches all the way down to the people on the ground.

[Watch the film](https://youtu.be/_hB6zPA_ujA)

<!-- model: Claude Fable 5.1 + Codex Astra -->
<!-- excerpt: living_earth/ground/render_ground.py pose -->

## The story

The camera moves between planetary scale and the life that makes Earth worth returning to. Cool rivers and violet air belong to Earth; the satellite carries the warm amber accent. The sand becomes a chip, server cases leave the planet, and the child's thread turns a technical connection into something personal.

The ground shots share one set. A wide view introduces the family, the instrumental returns to the child holding the thread, and the final chorus cuts into the plants before returning to orbit. The portrait version has its own framing and ground renders.

## The code

| File | Lines | What it does |
|---|---:|---|
| [`living_earth/ground/render_ground.py`](living_earth/ground/render_ground.py) | 551 | The shared ground set, actors, thread, plant close-ups and camera animation. |
| [`remotion/src/le/film/engine.ts`](remotion/src/le/film/engine.ts) | 63 | Evaluates the film at song time and combines camera, palette, motion and insert layers. |
| [`remotion/src/le/film/sections/chorus2.ts`](remotion/src/le/film/sections/chorus2.ts) | 438 | The satellite chase, server cases, temperature gag and the second chorus’s camera progression. |
| [`remotion/src/le/film/Extra.tsx`](remotion/src/le/film/Extra.tsx) | 416 | The layered mineral-grain hook and other scene effects. |
| [`remotion/src/le/film/Film.tsx`](remotion/src/le/film/Film.tsx) | 48 | Composites the film and native landscape/portrait inserts. |
| [`remotion/src/le/film/timing.gen.ts`](remotion/src/le/film/timing.gen.ts) | 2301 | The resolved song sections, lyric anchors and word timing used by the renderer. |
| [`living_earth/him3d/him_build.py`](living_earth/him3d/him_build.py) | 397 | Builds the stylized satellite and rocket in Blender. |
| [`living_earth/him3d/him_slots.py`](living_earth/him3d/him_slots.py) | 496 | Drives the character’s poses and screen framing at exact song times. |
| [`living_earth/him3d/him_check.py`](living_earth/him3d/him_check.py) | 111 | Checks the rendered character layers for missing frames, pops, jumps and flicker. |
| [`living_earth/le_render.sh`](living_earth/le_render.sh) | 41 | Queues resumable picture chunks and rebuilds exact frame timestamps at joins. |
| [`living_earth/le_grade.py`](living_earth/le_grade.py) | 89 | Applies the section color script while preserving the frame count. |

## By the numbers

- 3:37.6, 30 frames per second, 6,528 frames per master.
- 2560 × 1440 landscape and 1080 × 1920 portrait.
- Three ground inserts in each format: 72, 199 and 60 frames.
- Render chunks of 600 frames, with finished chunks reusable after a scoped change.
- BT.709 masters; soundtrack retained without another audio encode during the finish pass.

## Working with the source

The film uses Remotion, React Three Fiber and Three.js for the planetary scenes, and Blender Eevee for the character layers and ground inserts. Dependencies are pinned in `remotion/package-lock.json`.

```sh
cd songs/you-said-you-needed-space/remotion
npm ci
npm run typecheck
npx remotion studio src/le/film/index.tsx
```

This is a source release, not a self-contained media bundle. The song audio, generated character PNGs, rendered ground clips, planet maps and external asset cache are not included. The generated timing module is included so the shot structure can be studied without the audio. Full rendering requires restoring or rebuilding those assets under `remotion/public/le/` and the locations used by the source. `living_earth/him3d/him_build.py` creates the character geometry; `him_export.sh`, `him_run.sh` and `him_post.py` produce the timed character layers. `living_earth/ground/render_ground.sh` produces the three inserts in either aspect ratio. Set `AUDIO` explicitly when using `living_earth/le_render.sh` on another machine.

The ground recipe uses CC0 Poly Haven assets (calathea, fern, roots and rocks) and ambientCG material textures. `pitch_mockups/ground2/prep_tex.py` prepares the vein and texture masks. Asset names and cache paths remain in the recipe so the preparation is inspectable. The original library assets are not redistributed here.

The final pipeline checks every decoded frame timestamp, stream metadata and audio identity. A separate visual scan checks blank/frozen frames, one-frame pops and exposure; flagged transitions are reviewed against the shot timing. A camera that dipped below the ground in the last plant close-up was caught in the finish review and corrected before delivery.

---

Song, lyrics and concept by aditazzz. Video code made with Claude Fable 5.1 and Codex Astra. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
