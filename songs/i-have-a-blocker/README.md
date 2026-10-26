# I have a blocker. (Take It Offline)

[![I have a blocker. (Take It Offline): watch on YouTube](thumbnail.jpg)](https://youtu.be/UlPvIyV_Z58)

**▶ [Watch it on YouTube](https://youtu.be/UlPvIyV_Z58)**

> 9:15, cameras off, fifteen squares and somebody's dog. Yesterday: ticket. Today: ticket. No blockers. Then the new guy says "I have a blocker." Out loud. On the call. Fifteen people say the magic words, and we finally went to see where "offline" actually goes. 🚪

## What you see

A 3D film. The daily standup is fifteen floating rooms over the city at 9:15, one clay mannequin per square, cameras off, and Somebody's Dog in a headset. TAKE IT OFFLINE is exactly fifteen characters, spaces included, so in the choruses every room holds up a letter; the new guy's sixteenth room only gets a question mark. When he says "I have a blocker", a giant pink BLOCKER slams onto the roof and every other room goes dark. Five "take it offline"s shove it off the edge, and the bridge follows it down into Offline: a shaft through the years, and a field of every blocker ever taken offline, all the way down to the dinosaur and the asteroid. The lyrics are made of green particles that gather as each word is sung and blow away after the line.

(Sam, Ted, Dana and Somebody's Dog are fictional. Every team has them. Dana still has a hard stop.)

## The code

| File | Lines | What it is |
|---|---:|---|
| [`web/js/main.js`](web/js/main.js) | 318 | The film. `renderAt(t)` draws the frame at time `t`, deterministically: the camera, the city's dawn, the sixteen rooms (who's talking, whose light is on, which letter they hold), the BLOCKER's fall and the five knocks, the flying tickets, the particle lyrics and the meeting HUD. |
| [`web/js/rooms.js`](web/js/rooms.js) | 172 | The standup: fifteen diorama rooms floating in a grid over the city, plus the new guy's sixteenth. Each is an open-fronted box with painted walls, a desk, a laptop and a mannequin. |
| [`web/js/mannequin.js`](web/js/mannequin.js) | 172 | Smooth clay mannequins in hoodies and beanies, and Somebody's Dog. Arms are posed with two-bone IK: give each hand a target. |
| [`web/js/city.js`](web/js/city.js) | 90 | The city at 9:15: blue hour, towers full of lit windows, rows of street lights, one wide roof where the standup floats. All painted (unlit) geometry, so the CPU renderer stays fast and the bloom does the glow. |
| [`web/js/canyon.js`](web/js/canyon.js) | 83 | Offline: a shaft under the street through layers of rock (deeper is older, the years glow on the layers, old tickets stuck in them), opening onto a dark floor where every blocker ever taken offline sits in rows. In the middle: the dinosaur, and the asteroid somebody took offline 66 million years ago. |
| [`web/js/ptext.js`](web/js/ptext.js) | 78 | Lyric lines made of green particles: each word gathers out of a drifting cloud as it's sung, holds with a faint shimmer, then blows away. Built from the text's own pixels, so it stays readable at any size. |
| [`web/js/lib.js`](web/js/lib.js) | 91 | Shared helpers: easing, seeded randomness, cheap good-looking materials, canvas textures, the fonts. |
| [`web/render.mjs`](web/render.mjs) | 28 | The renderer: serves the film to headless Chromium (WebGL on the CPU through SwiftShader) and renders stills, or a range of frames straight to a silent video. |
| [`web/index.html`](web/index.html) | 3 | The page the renderer opens. |
| [`scene.py`](scene.py) | 59 | The bridge to the Python pipeline: reads the rendered 3D masters, upscales them and adds the channel's 2D layer (the mid-video subscribe pill and the end card), so `studio.render`, `studio.cuts` (Shorts and Reels) and `studio.thumbs` work unchanged. |

That's **1,094 lines** for this one video. It's the first video here made with Three.js: a JavaScript film rendered frame by frame in a headless browser, with [`scene.py`](scene.py) handing the result to the Python pipeline in [`studio/`](../../studio). The 3D film for [Ragnarök or Reach for Mars](../ragnarok-or-reach-for-mars) grew out of this one. [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) (copied to [`web/data/`](web/data) for the film) the word timings, beats and sections.

## By the numbers

- 3:03 long, 10,998 frames rendered (16:9 and 9:16, 30 fps), finished at 2560×1440 for YouTube
- 48 lyric lines and 269 words synced to the vocals
- 15 rooms that spell TAKE IT OFFLINE, plus the new guy's question mark
- 4 Shorts and 2 Reels cut from it

## Render it

```bash
cd songs/i-have-a-blocker/web
npm install && npx playwright install chromium
node render.mjs stills 1600 900 ../build/stills 30 97.75 120             # three stills (CLEAN=1 hides the lyrics and HUD)
node render.mjs range 1600 900 ../build/v2master_16x9.mp4 0 183.3 30     # the 16:9 master
node render.mjs range 900 1600 ../build/v2master_9x16.mp4 0 183.3 30     # the 9:16 master
cd ../../.. && python -m studio.render songs/i-have-a-blocker            # the final, with the subscribe pill and end card
```

The film loads its fonts from `web/fonts/`: Inter and Inter Display, JetBrains Mono and Cormorant Garamond Bold (the names are in [`web/js/lib.js`](web/js/lib.js) and [assets/fonts/README.md](../../assets/fonts/README.md)). Everything renders on the CPU; split a long render into ranges and join them. The audio isn't in this repo; the timing data derived from it is.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
