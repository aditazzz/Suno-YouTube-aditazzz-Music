# Please Hold (I'd Rather Chew Glass Than Call)

[![Please Hold: watch on YouTube](thumbnail.jpg)](https://youtu.be/RFosHOuu5JM)

**▶ [Watch it on YouTube](https://youtu.be/RFosHOuu5JM)**

> A $4 charge on my internet bill, 47 minutes on hold, and a millennial who would rather chew glass than read her card number out loud. So I sent a robot. It's got all day. 📞

## What you see

A 3D film. It opens through my eyes on my phone, on hold at 00:00:03, and the call leaves the phone as a streak of cyan light. The $4 charge gets circled in hot orange, 2 on the keypad is for despair, and 3 is an empty call-center cubicle with the chair still spinning. The light comes back down as a small white robot with a corded receiver plugged into its chest, and it sits down on the bench in my exact pose while I walk off to order Chinese. Days pass over the plaza. The cord runs across the plaza and up the HOLD tower, whose windows spell HOLD with a robot on hold in every one of them. I spend the wait at the salon under the dryer in foils, eating onion rings, and on "I don't wait anymore" the hood swings up, the foils burst off and I walk out with blonde waves and my wayfarers on. The robot's eye strip is its face and its screen: a hold-music waveform, a notepad, THANK YOU SO MUCH :), a survey that is page 1 of 400, five stars, and a battery at 1%. In the bridge it prints a receipt as long as a pharmacy receipt, and the $4 charge turns into $5 under a rubber stamp. Then the city reboots in neon, the man with the rocket from [Ragnarök or Reach for Mars](../ragnarok-or-reach-for-mars) conducts from the tower screen, and the little robots run the show. The video ends on the exact frame the audio stops: the battery dies.

The captions wait too. Each word pops in as it's sung; a line left waiting starts to slump, and when it's over its letters topple like dominoes and drop out of frame. The hold system's lines type out like an automated transcript (and fall over anyway). The robot's lines come up on a little LED panel in its dot-matrix font and never fall over, because it has all day. "I don't wait anymore" and "I've got better things to do" don't fall over either: they walk off.

The news behind it: on Oct 25, 2026, Elon Musk announced that Grok Bot can now call a person or a business for you. It makes the request on your behalf, takes notes on the answer and sends you a summary of the conversation. The other end of the line is going robot too: Starlink's support line already runs on Grok Voice, which xAI says handles about 20,000 calls a day and resolves about 70% of them without a human. We built machines to make us wait; now our machines wait on their machines.

(The robot is our own design, and the video isn't affiliated with xAI or Starlink. Every bill, brand and headline on screen is invented.)

## The code

| File | Lines | What it is |
|---|---:|---|
| [`web/js/film.js`](web/js/film.js) | 982 | The film. `renderAt(t)` draws the frame at time `t`, deterministically: the moods (night, days passing, dusk, neon), the shot list cut to the vocal, split screens (left/right in 16:9, top/bottom in 9:16), the glow-up, and the crisp 2D layer (the hook, the title, PASS., the end card). |
| [`web/js/captions.js`](web/js/captions.js) | 184 | The captions: small, crisp and drawn after the bloom. Words pop in as they're sung, waiting lines slump, finished lines topple like dominoes; typed lines for the hold system, a dot-matrix LED panel for the robot. |
| [`web/js/world.js`](web/js/world.js) | 419 | The city: a sky that runs from night to noon to neon, a toy-clean city in one instanced draw (procedural windows, neon edges), the plaza and its dance-floor tiles, the bench and lamp, and the HOLD tower: 900 real windows with rooms behind them, robots on hold in any of them, an LED dot-matrix band, and a facade that becomes one giant screen. |
| [`web/js/robot.js`](web/js/robot.js) | 180 | The hold-robot: the Ragnarök robots' family (white enamel, black glass face, gold seam), its corded receiver and coiled cord, the eye-strip screen and every mode it shows, thrusters, the receipt slot. |
| [`web/js/figure.js`](web/js/figure.js) | 169 | The rig (two-bone IK arms and legs, sitting, standing, walking) and me: the face (eyes, a smile, a raised brow), black wayfarers, the berry top, and a cape for the salon. |
| [`web/js/hair.js`](web/js/hair.js) | 183 | My hair in three looks: dark and pulled back into a low bun with a scrunchie, foils, and honey-blonde waves built from twisting ribbon locks that are rebuilt every frame so they hang with gravity, sway, and fall in with a bounce during the reveal. |
| [`web/js/props.js`](web/js/props.js) | 476 | Props: the phone and its screens, the bill, the keypad, the cubicle, takeout, the egg roll, the salon and its hood dryer, onion rings, the receipt and the stamp, the history pedestals, cobwebs, a pigeon, sax notes, invented tabloids. |
| [`web/js/lib.js`](web/js/lib.js) | 132 | Shared helpers: easing and keyframes, seeded randomness, clay and gloss materials with a soft rim, canvas textures, fonts. |
| [`web/js/font5.js`](web/js/font5.js) | 42 | A 5x7 dot-matrix font for the LED band, the windows that spell HOLD, the robot's eye strip and its captions. |
| [`web/render.mjs`](web/render.mjs) | 36 | The renderer: serves the film to headless Chromium (WebGL on the CPU through SwiftShader) and saves every frame as a JPEG master. Resumable. |
| [`scene.py`](scene.py) | 83 | The bridge to the Python pipeline: reads the rendered 3D masters, upscales them and adds the subscribe pill, so `studio.render`, `studio.cuts` and `studio.thumbs` work unchanged. |
| [`make_thumbs.py`](make_thumbs.py) | 22 | The thumbnail: the brand cover from [`studio/brand.py`](../../studio/brand.py) (the same photo chip, Anton headline and italic line as every video) over 3D plates rendered for it (`?look=thumb`). The words and framing are in `song.yaml`. |

The man with the rocket on the tower screen is a clip of frames rendered from the [Ragnarök or Reach for Mars](../ragnarok-or-reach-for-mars) film code (`web/tex/cameo/`, 124 JPEGs, not in the repo; without them the tower screen stays dark).

## By the numbers

- 3:26 song, 3:33 video, 12,780 frames rendered (16:9 and 9:16, 30 fps), finished at 2560×1440 for YouTube
- 47 lyric lines synced to the vocal
- 900 windows in the tower, 62 of them spell HOLD
- 1 receipt, 4 lines long, plus coupons

## Render it

```bash
cd songs/please-hold/web                                                    # copy the film's fonts into web/fonts/ first (see assets/fonts/README.md)
npm install && npx playwright install chromium
node render.mjs stills 1600 900 ../build/stills 0.5 72 149.7                 # three stills (CLEAN=1 hides the lyrics and HUD)
node render.mjs frames 1600 900 ../build/h 0 213                            # the 16:9 frames (SKIP=1 resumes)
node render.mjs frames 900 1600 ../build/v 0 213                            # the 9:16 frames
QS=look=thumb node render.mjs stills 1920 1080 ../build/thumb 0.1 1.1 2.1   # the three thumbnail plates
cd .. && ./assemble.sh && cd ../.. && python -m studio.render songs/please-hold --fmt 16x9_1440 --skip-safe-check
python songs/please-hold/make_thumbs.py "<out folder>" songs/please-hold/build/thumb/s_1.10.jpg songs/please-hold/build/thumb/s_0.10.jpg songs/please-hold/build/thumb/s_2.10.jpg
```

The audio isn't in this repo; the timing data derived from it is.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
