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
| [`city.py`](city.py) | 424 | First draft, not used by the final scene: the tower over the plaza as a true perspective scene, traced per pixel so her shadow could be a real projection that climbs the facade. |
| [`cty_city.py`](cty_city.py) | 929 | The plaza and its towers, drawn as projected polygons in a clean ligne-claire style, with an ID buffer so the sun's shadows and her (unnatural) shadow can be laid onto each visible surface afterwards. |
| [`cty_eng.py`](cty_eng.py) | 345 | A tiny vector 3D renderer for the illustrated city: projected polygons with flat fills and clean ink lines, an ID buffer for shadows and lights, and cameras with lens shift so the towers' verticals stay straight. |
| [`cty_fx.py`](cty_fx.py) | 279 | In-world effects: assistant chat bubbles rising from her phone like lanterns, notebook pages, ghost pedestrians, the LED band text, slop pictures inside close windows. |
| [`cty_her.py`](cty_her.py) | 417 | Her: an anonymous woman in a camel trench coat on the bench, head bowed over her phone. Every part is a closed spline authored for a few key poses and blended between them, like cut-out animation, so she stays on-model. |
| [`cty_kiosk.py`](cty_kiosk.py) | 139 | The newsstand insert: yellowed tabloids clipped to the rack, all invented and all decades older than any AI ("But you've been voting for that feeling / Long before there was me"), drawn once as a large illustration the shot pans across. |
| [`cty_phone.py`](cty_phone.py) | 462 | Her phone: a fictional feed app called "more" (as in "so I made you a hundred more"), drawn as clean UI at any scale: posts with the slop pictures, a comments sheet, an assistant chat, the lock screen and a low-battery alert, with the clock and battery following the story. |
| [`cty_phoneshot.py`](cty_phoneshot.py) | 191 | The close-up: her phone in her left hand, seen through her own eyes, thumb on the screen, with her lap and the plaza far out of focus below. The phone and hand are inked like the city; the screen is crisp UI. |
| [`cty_plaza.py`](cty_plaza.py) | 288 | Compose the plaza set for one frame: sky, ground, towers, props, sun shadows, glow. Her and her shadow are added by the caller through hooks so the same set serves every shot. |
| [`cty_shadow.py`](cty_shadow.py) | 111 | Her shadow: her silhouette projected from a point light onto the first surface each ray hits (the plaza or the Feed Tower's two faces). With the sun far away it's an honest shadow; pull the light close behind her and it outgrows her and climbs the tower. |
| [`cty_sky.py`](cty_sky.py) | 275 | Time of day for the city: the sun's path, the palettes and the illustrated sky (gradient, sun, clouds, stars, moon), with the sun rising behind the camera and setting behind the towers. |
| [`cty_slop.py`](cty_slop.py) | 288 | The slop: a dozen glossy, over-polished "AI pictures" for the feed, deliberately airbrushed so they clash with the hand-inked city. Each has its tell: six fingers, a garbled sign, a second sun. |
| [`cty_type.py`](cty_type.py) | 94 | Lyric typography: EB Garamond in warm white, each word easing up as it's sung, whispered asides and the spoken break in italic. Every shot places its words so they dodge the phone, her, and the 9:16 platform buttons. |
| [`scene.py`](scene.py) | 1,060 | The film: a day lost to the feed. At 2 a.m. a woman on a plaza bench likes one post; she never looks up while the day time-lapses past, and her shadow outgrows physics with every like until it climbs the Feed Tower. When she locks the phone the towers go dark, and she opens her notebook and writes. |
| [`woman.py`](woman.py) | 130 | First draft, not used by the final scene: her in a long camel coat, seen from behind, looking down at her phone, with poses for scrolling, lowering the phone, turning and walking. |

That's **5,432 lines** of Python written for this video: 4,878 in the 13 files the final scene uses, plus two first drafts (`city.py`, `woman.py`) kept for reference. It all sits on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats and sections.

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
