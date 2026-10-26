# Ragnarök or Reach for Mars

[![Ragnarök or Reach for Mars: watch on YouTube](thumbnail.jpg)](https://youtu.be/Yo6UcXn4_kM)

**▶ [Watch it on YouTube](https://youtu.be/Yo6UcXn4_kM)**

> A man with a rocket sits down by the fire, and a Viking seeress reads his future in a deck of tarot cards. He turns up the Tower. "Twenty percent," he says with a grin, and the whole hall laughs: in their myth Ragnarök isn't a risk, it's certain, so twenty percent sounds like good odds. Every card she turns over is a future for all of us. 🚀

## What you see

A 3D film, carved and painted. The seeress, the man with the rocket and a hall full of Vikings are wooden puppets that move on twos, like stop-motion, in a longhouse lit by one long hearth. The deck is gold engraving on obsidian. The first card she lays down is two-faced: Ragnarök from one side, Mars from the other, and it was numbered 0 the whole time. Every card she turns up opens into a pop-up world of cut, gilded card: the Tower's lit windows spell 20%, the Sun's feast has a gate that swings shut, robots take the oars, the Red Planet gets named Greenland, and a Viking grows one tomato, voluntarily. The lyrics are embers from the fire that settle into gold letters and burn out, every one of the 16 HEYs is a slam on the table, and by the third chorus the robots are doing the slamming. At the end the doors open onto a headland: the Fool card made real, a ship of standing stones (after Ale's Stones in Sweden) pointing at Mars, and the cliff lined with people as far as you can see.

A tribute, not a roast. The 20% is Elon Musk's own number: "only a 20% chance of annihilation" from AI, he said on The Joe Rogan Experience (Feb 28, 2025).

## The code

| File | Lines | What it is |
|---|---:|---|
| [`web/js/film.js`](web/js/film.js) | 506 | The film. `renderAt(t)` draws the frame at time `t`, deterministically: the puppets and everything they handle move on twos (15 fps), the camera, fire, light and captions at 30. The opening (0:00–0:27) is shot here; per-shot vertical reframing and caption placement for 9:16 live here too. |
| [`web/js/full.js`](web/js/full.js) | 723 | Everything from the second HEY to the end, section by section: hooks, verses, refrains, the bridge, the outro. Poses everyone, lays out the cards, sets the light and picks the camera for each shot. |
| [`web/js/finale.js`](web/js/finale.js) | 117 | The outro: the man at the cliff edge with the rocket on his shoulder like the Fool's bundle, the little robot at his heel, then everyone in the stone ship and the cliff lined with figures. |
| [`web/js/hall.js`](web/js/hall.js) | 207 | The longhouse at night: the long hearth, carved posts, platforms where the Vikings sit, shields and hangings, a smoke hole that lets moonlight in, the seeress's high seat and the doors that open for the finale. |
| [`web/js/headland.js`](web/js/headland.js) | 150 | The headland outside the doors: a plateau ending in a cliff, the sea, Mars rising in the cards' engraved style, the Milky Way, and the stone ship whose prow points at Mars. |
| [`web/js/fire.js`](web/js/fire.js) | 126 | Shader flames on camera-facing quads (HDR, so the bloom makes them glow), a bed of embers and rising sparks. The sparks are the particles the captions are made of. |
| [`web/js/embers.js`](web/js/embers.js) | 121 | Ember captions: each sung word is built from sparks that fly up out of the fire, settle into gold letters, flicker while the line holds and burn out to ash. A HEY is a burst of sparks on the slam. |
| [`web/js/puppets.js`](web/js/puppets.js) | 460 | The carved, painted puppets on a jointed rig (two-bone IK arms, seated or standing legs): sanded faces with painted features that change by texture swap (the seeress opens her eyes, he grins on "twenty percent"), knife-cut clothing over fine wood grain. |
| [`web/js/robots.js`](web/js/robots.js) | 132 | The machines, the one thing in the hall that isn't carved: white enamel shells, a black glass face with a cyan eye strip, a thin gold seam. Same rig as the puppets, so they slam a table the same way. |
| [`web/js/rocket.js`](web/js/rocket.js) | 31 | The steel rocket he carries: ogive nose, forward and aft flaps, a black tile belly. No logos. |
| [`web/js/props.js`](web/js/props.js) | 61 | The feast on the tables: drinking horns, wooden cups, platters of bread, candles. They jump on every slam. |
| [`web/js/cards.js`](web/js/cards.js) | 367 | The cards: obsidian bodies, gilded edges, engraving drawn line by line on a canvas, and the two-faced (lenticular) front that shows one future from the left and another from the right. |
| [`web/js/cards2.js`](web/js/cards2.js) | 462 | The rest of the deck in the same engraved style: the Fool, the Magician, the Tower, the Star, the Sun, and the new cards past the classic 21 (XXII The Robot, XXIII The Red Planet, XXIV The Gardener). |
| [`web/js/popups.js`](web/js/popups.js) | 257 | The card worlds: a turned-up card's engraving rises off the table as a pop-up diorama of cut, gilded card, back layers first, with one moving part that carries the lyric. |
| [`web/js/stage.js`](web/js/stage.js) | 36 | Renderer and post chain: bloom, then vignette, grain, a touch of chromatic aberration, a flash and a fade, and a warm/cool split-tone for firelight. |
| [`web/js/merge.js`](web/js/merge.js) | 36 | Merges the hall's static meshes by material, so the CPU renderer issues hundreds fewer draw calls. |
| [`web/js/lib.js`](web/js/lib.js) | 91 | Shared helpers (from the "I have a blocker." 3D film): easing, seeded randomness, cheap good-looking materials, canvas textures. |
| [`web/js/lib2.js`](web/js/lib2.js) | 106 | This film's helpers: procedural textures, seeded noise, the hall's environment light, and the fonts. |
| [`web/render.mjs`](web/render.mjs) | 36 | The renderer: serves the film to headless Chromium (WebGL on the CPU through SwiftShader) and saves every frame as a JPEG master, or renders stills or a range straight to video. Resumable. |
| [`web/bake.mjs`](web/bake.mjs) | 13 | Draws the card faces once and saves them to `web/tex/`, which the film loads (drawing them per frame is too slow on the CPU). |
| [`web/bake.html`](web/bake.html) | 14 | The page `bake.mjs` opens: which faces to draw. |
| [`web/index.html`](web/index.html) | 3 | The page the renderer opens. |
| [`timing.py`](timing.py) | 110 | Everything the film is timed to, written to `web/data/timing.json`: the tracked beats (105.47 BPM, every HEY on beat 3), all 70 lyric lines word by word, the HEYs, the stomps, the card names, the sections. |
| [`cut.py`](cut.py) | 65 | Cuts any version from the frame masters and the song: segments snapped to frames, short equal-power audio crossfades at the joins, fades, a hold on the last frame. |
| [`render.sh`](render.sh) | 11 | Renders every frame, 16:9 at 1600×900 and 9:16 at 720×1280. |
| [`assemble.sh`](assemble.sh) | 12 | The YouTube video: the 16:9 masters upscaled to 2560×1440 at 16 Mbps, with the song. |
| [`cuts.sh`](cuts.sh) | 18 | The vertical versions: the full song, the under-3-minute cut for Instagram and one Short per card ([`cuts.json`](cuts.json)). |

That's **4,271 lines** for this one video: **3,989 lines** of JavaScript scene code in [`web/js/`](web/js), plus the renderer, the timing and the cuts. Like [I have a blocker.](../i-have-a-blocker), it's written in JavaScript instead of Python: a Three.js film rendered frame by frame in a headless browser, not with the Python engine in [`studio/`](../../studio). [`lyrics.txt`](lyrics.txt) holds the lyrics, [`web/data/timing.json`](web/data/timing.json) the timing and [`build/beats.json`](build/beats.json) the tracked beats it was built from.

## By the numbers

- 4:05 long, 14,688 frames rendered (16:9 and 9:16, 30 fps), plus a 2560×1440 master for YouTube
- 70 lyric lines and 306 words timed to the vocals, 105.47 BPM, every HEY on beat 3
- 16 HEYs, 16 slams on the table
- 11 card faces, each engraved line by line, numbered 0 to XXIV
- 1,400 people on the cliff edge at the end

## Render it

```bash
cd songs/ragnarok-or-reach-for-mars/web
npm install && npx playwright install chromium
node bake.mjs                                                    # the card faces, once
node render.mjs stills 1600 900 ../build/stills 5.5 52.9 227.2   # three stills
cd .. && ./render.sh                                             # every frame, 16:9 and 9:16 (resumable)
AUDIO=path/to/song.wav ./assemble.sh                             # the 1440p YouTube video
AUDIO=path/to/song.wav ./cuts.sh                                 # the vertical versions and the Shorts
```

The film loads five fonts from `web/fonts/`: Cormorant Garamond (Bold, SemiBold, Medium and Medium Italic) and Cormorant SC Medium, all free on [Google Fonts](https://fonts.google.com/specimen/Cormorant+Garamond) (see [assets/fonts/README.md](../../assets/fonts/README.md)). Everything renders on the CPU (WebGL through SwiftShader), about 3.5 seconds a frame at 1600×900 on two cores, so `render.sh` takes a range (`./render.sh 42.34 69.6`) for splitting the work. The audio isn't in this repo; the timing data derived from it is.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
