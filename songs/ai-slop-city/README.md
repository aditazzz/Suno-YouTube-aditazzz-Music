# AI Slop? You're Absolutely Right (The City)

[![AI Slop? You're Absolutely Right: watch on YouTube](thumbnail.jpg)](https://youtu.be/M6K-TuGXqAY)

**▶ [Watch it on YouTube](https://youtu.be/M6K-TuGXqAY)**

> A song about AI slop, sung by the AI. 2 a.m., one woman on one bench, and a phone that agrees with everything she says. 🌆

## What you see

At 2 a.m. a woman on a plaza bench likes one post. She never looks up while the day time-lapses past. With every like her shadow outgrows physics: at dawn it climbs the Feed Tower, and every window it covers turns into a screen.

Her feed fills with a hundred identical sunsets, an LED band counts every scroll, the tower's windows spell SLOP, and the newsstand's yellowed tabloids (dated 1957 to 1994, all invented) show the same feeling decades before any AI. When her battery dies, so does the city's power, and the blackout finally shows the Milky Way. The final chorus reboots the city in neon.

Then she locks the phone, the towers go dark one by one, the sun comes up, and her shadow is just a shadow again. She opens her notebook and writes. The shadow waves.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`city.py`](city.py) | 424 | First draft, not used by the final scene. The city: a stone-and-glass tower over a plaza at golden hour (also at night and at dawn), rendered as a real perspective scene so the camera can move: dolly, crane, push in. Everything is a projection of world… |
| [`cty_city.py`](cty_city.py) | 929 | The plaza and its towers, drawn as projected polygons in a clean ligne-claire style. World: x = north (screen right in the main view), y = up, z = west (into the main view). The bench sits at the origin; the Feed… |
| [`cty_eng.py`](cty_eng.py) | 345 | Tiny vector 3D renderer for the illustrated city (ligne claire: flat fills, clean ink lines, real perspective). World: metres, y up. Everything is drawn as projected polygons on a uint8 canvas with anti-aliasing,… |
| [`cty_fx.py`](cty_fx.py) | 279 | In-world effects: assistant chat bubbles rising from her phone like lanterns, notebook pages, ghost pedestrians, the LED band text, slop pictures inside close windows. |
| [`cty_her.py`](cty_her.py) | 417 | Her: an anonymous woman in a camel trench coat, seated on the bench in profile (facing right), head bowed over her phone. Built like vector cut-out animation: every part is a closed spline whose control points are… |
| [`cty_kiosk.py`](cty_kiosk.py) | 139 | The newsstand insert: yellowed tabloids clipped to the rack, all invented, all decades older than any AI — 'But you've been voting for that feeling / Long before there was me'. Built once as a large flat… |
| [`cty_phone.py`](cty_phone.py) | 462 | Her phone. A fictional feed app called "more" (as in "so I made you a hundred more"), drawn as clean UI at any scale: feed posts with the glossy slop pictures, a comments sheet, an assistant chat, the lock screen,… |
| [`cty_phoneshot.py`](cty_phoneshot.py) | 191 | The close-up: her phone in her left hand, seen from her own eyes, thumb on the screen; her lap and the plaza beneath, far out of focus. The phone and hand are inked like the rest of the city; the screen is crisp… |
| [`cty_plaza.py`](cty_plaza.py) | 288 | Compose the plaza set for one frame: sky, ground, towers, props, sun shadows, glow. Her and her shadow are added by the caller through hooks so the same set serves every shot. |
| [`cty_shadow.py`](cty_shadow.py) | 111 | Her shadow: her silhouette (a mask in her own plane) projected from a point light onto the first surface each ray hits (plaza, the Feed Tower's two hero faces), warped straight into the screen with homographies.… |
| [`cty_sky.py`](cty_sky.py) | 275 | Time of day for the city: sun path, palettes, and the illustrated sky (gradient, sun, clouds, stars, moon). World axes: x = north (screen right in the main view), y = up, z = west (into the main view). The main… |
| [`cty_slop.py`](cty_slop.py) | 288 | The slop: a dozen glossy, over-polished 'AI pictures' for the feed. They are deliberately airbrushed (smooth gradients, glows, no ink) so they clash with the hand-inked city around them. Each has its tell (six… |
| [`cty_type.py`](cty_type.py) | 86 | Lyric typography for the city: EB Garamond, warm white, words easing up as they're sung; whispered asides and the spoken break in italic. Each shot says where the words sit (place = (cx, cy, maxw) as fractions of… |
| [`scene.py`](scene.py) | 1060 | AI Slop? YOU're Absolutely Right — The City. A day lost to the feed. At 2 a.m. a woman on a plaza bench likes one post. She never looks up while the day time-lapses past; her shadow outgrows physics with every… |
| [`woman.py`](woman.py) | 130 | First draft, not used by the final scene. Her: a woman in a long camel coat with long dark hair, seen from behind, looking down at her phone. She lives in billboard space: metres, x right, y up, feet at (0, 0). draw() renders her (colour + alpha) at any… |

That's **5,424 lines** of Python written for this video: 4,870 in the 13 files the final scene uses, plus two first drafts (`city.py`, `woman.py`) kept for reference. It all sits on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats and sections.

## How it's drawn

The city is vector art with real perspective. [`cty_eng.py`](cty_eng.py) is a small 3D renderer: it projects the city's polygons through a camera, clips them against the frame, and fills them with flat color and clean ink lines (the ligne-claire look). Her shadow is an actual projection from a point light onto the plaza and the tower's faces ([`cty_shadow.py`](cty_shadow.py)), which is why it can climb the building. The slop pictures in her feed are deliberately airbrushed, with no ink, so they clash with the hand-drawn city ([`cty_slop.py`](cty_slop.py)).

## By the numbers

- 3:42 long, 6,654 frames rendered (16:9, 30 fps)
- 82 lyric lines and 438 words synced to the vocals, 99 BPM
- 14 sections, every cut timed to the song

## Render it

```bash
python -m studio.render songs/ai-slop-city --stills 41.5 85.5
python -m studio.render songs/ai-slop-city --fmt 9x16 --stills 41.5 85.5
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md). Nothing else: the sky, the city, the newsstand and the slop pictures are all drawn by the code in this folder.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
