# Look What I Can Do · "Scope Creep" — brief for the 3D modules

The song: a bratty bubblegum-electropop duet. Adita (the artist) talks to Claude at her laptop, brags about making
everything with AI, Claude flatters her, she hits her usage limit and switches to ChatGPT. Her lines are white/green,
Claude's lines are amber. Her own words, her own footage and her real X posts are the jokes. She wrote the jokes;
the video's job is to STAGE them so each one lands and is easy to read.

Her review of the first cut: "LOOK WHAT I CAN DO covers the jokes a lot of the times. The movement is really basic. Not
a creative enough take. Use my footage but enhance it. Make it extremely high end and professional." Then: "Treat this
as a demonstration of what Claude Code Opus 5.5 can do. Really push it. Show how creative it can be."

## The concept: Scope Creep
The world gets bigger every time she says "Look what I can do". It starts as a terminal session on a laptop in a dark
room (2D, already made and approved, 0–42.94 s). Chorus 1 (hall.js, done): the camera pulls back out of the laptop
screen; screens playing her videos multiply around the desk (8 → 16 → … → 512) into a stadium of screens; a pink neon
ring "LOOK WHAT I CAN DO" lies on the floor around the desk. Then:
- **city.js — Chorus 2 + Verse 3 (84.34–122.94 s)**: we pull back to a CITY at night whose buildings' windows are her
  videos. The hook becomes a giant Hollywood-style hillside sign "LOOK WHAT I CAN DO" (white block letters, lit, on a
  dark hill behind the skyline). Verse 3 happens in the city as a Times-Square-style street of billboards showing her
  REAL X posts as receipts.
- **stage.js — Bridge (122.94–136.54 s)**: a huge keynote auditorium; her real TED Talk videos on a giant curved LED wall;
  every "Next slide." cuts the wall to the next TED video.
- **space.js — Final chorus (136.54–151.74), Drop (158.3–171.74), Outro (171.74–181.6)**: pull back from the stage to
  orbit to a galaxy made of her videos; "now I'm in it too" = this video playing on a screen in space (feedback Droste);
  "five-star review" = five stars in the galaxy flare gold + a review card. Drop = warp-speed flight through a tunnel of
  her videos. Outro = everything powers down (screens switch off in a wave), her real "usage limit" post, then her real
  phone (a 3D phone with her ChatGPT screen recording on it) lights up in the dark for "Hey ChatGPT?".
The breakdown (151.74–158.3) and the end card (181.6+) are 2D and are not yours.

## Look
- Deep black world; her screens are the light. Glossy black floors with reflections where there is a floor.
- Cinematic camera: continuous choreographed moves (dolly, crane, orbit, push-in), whip pans and hard cuts ON THE BEAT
  where it helps. Nothing static for long. Subtle handheld drift (L.noise1) on close shots.
- Colors: bubblegum pink neon #ff5fa2 (the hook, her brand energy), Claude amber #ffa840, her green #74e36a, ink #ece6d8,
  receipt highlighter yellow #ffe14d (multiply over the post's text), receipt stamp red #ff4248 (Anton, rotated ~8°).
- The hook text is ALWAYS built into the world (signs, neon, skyline, constellations) and NEVER sits over a joke.
- Jokes must be readable: text at least 34 px tall at 1920×1080 when it is the point of the shot; give each joke time.
  Text must never spill outside the box/card it is on.
- Fonts (lib.js FONT): anton (display), disp (Inter Display Bold), ui (Inter SemiBold), mono/monoB (JetBrains Mono), serif.
- Exclusions: do not use her Microsoft/Elon posts; never show her birthday or follower count; no children.

## Engine (read these files first)
- `js/lib.js` — easing, rng, noise1, timing (`ls(lineSubstring, nth)`, `wt(lineSubstring, word, nthLine, nthWord)`,
  `beatPulse(t)`, `TIMING.beats`), `textPlane`, `canvasTex`, `dotTex`, `camPath(keys)` (Catmull-Rom camera keys).
- `js/media.js` — her footage: atlases `H1 H2` (16 clips each, 16:9 cells 480×270) and `V1 V2` (16 vertical 9:16 cells
  270×480), 15 fps 8 s loops; clip names per cell in `NAMES`. Hero sequences (30 fps, 960×540): `ted0 tedcharts
  tedshadow tedscreen tedstep` (her five TED Talk videos), `rage` (Rage Against the Machine Learning), `blocker`
  (I Have a Blocker — 16 video-call squares), `phone` (her real ChatGPT phone recording, 540×1106, 393 frames).
  `M.texOf(name)` gives the shared texture; you MUST call `M.use(name)` every frame for every atlas/hero you show (the
  film loads that frame after your frame() returns). `M.cellGeo(w,h,atlas,i)` / `M.cellRect(atlas,i)` for atlas cells.
  `await M.image('post_slopcore.png')` for static images: `post_back.png` ("Anyway, I'm back"), `post_tomatoes.png`
  ("we're finally free to grow our tomatoes. voluntarily."), `post_minis.png` ("Plotting how to acquire 10 Mac minis.
  For personal reasons."), `post_slopcore.png` ("Currently upskilling to transition into a Principal Slopcore Architect
  role…"), `post_usage.png` ("This will absolutely not do. I have an AI slop empire to build." + her "You're out of usage
  credits" screenshot), `profile.png` (her X profile header), `bio_end.png` (her bio line "Songs about the end of 🌍.
  Possibly."). Word boxes for highlighting (crop pixels, x0,y0,x1,y1): slopcore "Principal Slopcore" 435,197,998,259 and
  "Architect" 246,282,541,332; minis "10 Mac" 974,117,1193,166, "minis." 249,201,426,250, "For personal reasons."
  447,201,1105,263; tomatoes "voluntarily." 246,280,595,343; back "Anyway, I'm" 796,535,1167,596 and "back"
  246,617,376,668; usage "I have an AI slop empire to build." 250,283,1230,344.
- `js/sets.js` — `makeFloor(scene, envTex)` (black glass floor + a `mirror` group: add objects to it for reflections),
  `Field` (instanced screens from atlases), `Screen` (a framed screen: `.show(atlasOrHeroOrTexture, cell)`), `neon(text)`,
  `neonRing`, `flicker(t, t0)`, `Laptop`, `makeDesk`.
- `js/look.js` — renderer (ACES), EffectComposer: bloom (`ctx.look.bloom.strength/threshold/radius`) and a finish pass
  (`ctx.look.finish.uniforms`: `uVel` (vec2 screen-space motion blur for whips), `uFlash` + `uFlashCol`, `uFade` (to
  black), `uVig`, `uCA`, `uGrain`). film.js resets these every frame before calling your module.
- `js/hall.js` — the finished chorus-1 module; copy its patterns (structure, camera, field, mirror floor).
- `js/film.js` — the dispatcher. It imports `./hall.js ./city.js ./stage.js ./space.js` if present.

## Module contract (your file exports exactly these)
```js
export async function build(ctx)        // ctx = { THREE, L, M, S, look, W, H }; build scenes, load images; timing is loaded
export function covers(t)                // true for the song times this module draws
export async function frame(t, ctx)      // update everything for time t; call M.use(...); return { scene, camera }
```
- DETERMINISTIC: everything is a pure function of t. Frames are rendered in chunks, in any order. No state carried
  between frames (except caches), no Math.random (use L.rng(seed)), no Date.
- Performance: the final renders on this 2-core CPU (SwiftShader). Budget ≤ 1.5 s per 1920×1080 frame. No shadow maps,
  few lights (≤ 4 per scene), prefer MeshBasicMaterial/emissive screens, InstancedMesh for crowds/buildings/seats,
  canvas textures redrawn only when their content changes. Bloom does the glow.
- Do NOT edit film.js, lib.js, media.js, look.js, sets.js or hall.js (shared). Put your helpers in your own file. If you
  truly need a shared change, describe it in your report instead.

## Test
```bash
cd songs/look-what-i-can-do/web
node render.mjs stills 1280 720 <your scratch dir> 85 90 95 ...     # JPEG stills through the real film page
```
(Another render may be running; that's fine, just slower.) Look at your stills with the Read tool and critique them like
a master motion designer before you call it done: composition, readability, nothing clipping through the camera or
through other objects, text inside its boxes, motion between stills that reads as intentional.

## Song timing (seconds; word times in brackets)
```
 84.34 CH2   Look what I can do!                [84.34, 84.34, 85.5, 85.74, 85.92]
 86.42 CH2   Look what I can do!                [86.42, 87.02, 87.32, 87.56, 87.78]
 88.56 CH2   I made a thing that made a thing   [88.56, 88.62, 88.94, 89.12, 89.32, 89.56, 89.86, 90.02]
 90.24 CH2   That made another two!             [90.24, 90.46, 90.76, 91.22]
 91.86 CH2   Look what I can do!                [91.86, 92.52, 92.82, 93.04, 93.22]
 93.72 CH2   Look what I can do!                [93.72, 94.36, 94.64, 94.84, 95.04]
 95.28 CH2   My résumé is fourteen pages        [95.28, 95.5, 95.88, 96.34, 96.8]
 97.26 CH2   And my title's AI guru!            [97.26, 97.56, 97.78, 98.42, 98.56]
100.00 V3    I posted "We are so back!"         [100.0, 100.44, 100.44, 100.72, 100.98, 101.36]
101.62 V3    Then posted "We are doomed!"       [101.62, 101.84, 102.18, 102.58, 103.06]
103.46 V3    Then asked a bot to summarize      [103.46, 103.7, 103.94, 104.12, 104.34, 104.54]
105.02 V3    The panic in the room              [105.02, 105.44, 105.9, 106.36, 106.78]
107.14 V3    I bought ten little Mac minis      [107.14, 107.34, 107.56, 107.9, 108.4, 108.68]
109.14 V3    For reasons I can't share          [109.14, 109.6, 110.0, 110.26, 110.5]
110.70 V3    My agents formed a company         [110.7, 110.98, 111.34, 111.64, 111.84]
112.34 V3    And made me Employee of the Year   [112.34, 112.76, 112.98, 113.14, 113.5, 113.92, 114.1]
114.36 V3    I made a song about the end        [114.36, 114.56, 114.86, 115.02, 115.28, 115.7, 115.98]
116.20 V3    Of every job on Earth              [116.2, 116.46, 116.82, 117.24, 117.78]
117.99 V3    Then gave myself a brand-new one   [117.99, 118.2, 118.42, 118.82, 119.1, 119.58]
119.86 V3    And tripled my net worth!          [119.86, 120.0, 120.36, 120.84, 121.24]
122.94 BRIDGE Ladies and gentlemen               [122.94, 123.32, 123.6]
124.50 BRIDGE We are living through the greatest transformation in human history [124.5 … 127.48]
128.78 BRIDGE Next slide.   130.48 Next slide.   131.44 Next slide.
133.00 BRIDGE Would you like me to generate a conclusion?   (Claude, amber)
135.24 BRIDGE No, I think I nailed it.            (her)
136.54 FINAL Look what I can do!  138.50 Look what I can do!
140.00 FINAL I made a song about myself   142.04 And now I'm in it too!
143.70 FINAL Look what I can do!  145.54 Look what I can do!
147.12 FINAL I built an entire universe   149.24 And left it a five-star review!  [149.24 … 150.94]
151.74–158.3 BREAKDOWN (2D, not yours)   DROP_HIT = 158.3 (the drop lands)
161.74 DROP Look what I can do!  163.66 Look what I can do!  167.95 Look what I can do!  170.67 Look what I can do!
171.74 OUTRO Claude? (her)  172.24 Yes? (Claude)  173.04 Can we make one more? (her)
174.30 OUTRO You've reached your usage limit. (Claude)   176.78 Hey ChatGPT? (her)   178.15 the last musical blast
181.6 end card (2D, not yours; your last frame should be dark so the end card can fade in)
```
Tempo 129.2 BPM (beat ≈ 0.464 s); `L.TIMING.beats` has every beat time.
