# Film direction: "Vacation (To My Bed)" by aditazzz

Written for this run on 18 Nov 2026. Both runs get this exact file, byte for byte.

**Whose is what.** The song, the lyric and every joke in it are **(hers)**. Everything else here was written by the
setup **(setup)**, because she asked for a full direction she could approve. Treat the setup parts as a strong first
plan, not a lock: if an idea doesn't frame well, doesn't read in its time, or a better one turns up while building,
change it and say why in `log.md`. Where this file and her words differ, her words win.

**What's already done.** Stages 0 to 2 are finished. The song exists and is final: don't write a lyric, don't open
Suno, don't make or download anything there. `song/` holds the master (`song/master/vacation.wav`, −14 LUFS, 3:04.92),
Suno's own stems and MIDI for this take (`song/stems/`, `song/midi/`), every sung word timed (`song/timing.json`, all 44
lines, cross-checked against the vocal MIDI), and the map (`song/map.md`). The lyric is `lyric/lyric.txt`. Start at
stage 3. Every time below comes from those files; re-measure anything you key to.

**Time.** 4 hours for the whole run, final render included. Plan the film around that from the start
(`pipeline/6-build.md`, "Time"). The order of what matters most is at the end of this file.

---

## The song

Laid-back tropical indie pop: ukulele, a whistled hook, finger snaps, warm bass, a female vocal with a sweet, deadpan
delivery. 104.4 BPM, so a beat is 0.575 s and a bar is 2.30 s. Most lines get about two bars, so each picture has about
**4 to 5 seconds**: one clear idea per line that reads at a glance, with the small print kept for anyone who pauses.

| Section | Time | What it is |
|---|---|---|
| Intro | 0:00–0:07.8 | a spoken flight-attendant announcement over a guitar |
| Groove | 0:07.8–0:17.6 | about four bars of band before the first word |
| Verse 1 | 0:17.6–0:34.9 | burned out at work, so she books the trip |
| Pre-Chorus 1 | 0:34.9–0:45.5 | packing, sunglasses on |
| Chorus 1 | 0:45.5–1:12.8 | she arrives |
| Verse 2 | 1:12.8–1:31.0 | the resort, line by line |
| Pre-Chorus 2 | 1:31.0–1:40.8 | phone down, blanket up |
| Chorus 2 | 1:40.8–2:08.7 | the resort at full holiday |
| Bridge | 2:08.7–2:26.7 | half-time, whispered, the lowest energy |
| Chorus 3 | 2:26.7–2:53.7 | the loudest section in the song |
| Outro + ending | 2:53.7–3:04.9 | spoken, muffled; the band drops out, then a short instrumental tail |

The biggest change in the song is Chorus 3 dropping into the Outro (energy −0.70). The film's punchline lives there.

## 1. The film in one paragraph (setup)

**A luxury travel commercial for a resort that is four seconds away.** It's shot with complete sincerity: an elegant
camera, golden light, a premium travel brand's typography and calm confidence. And every inch of the destination is her
own apartment. It opens in the grey-blue glow of a work desk on fire, with little flames on calendar squares and a
browser with far too many tabs, while the captain announces that we will not be going anywhere. She books a first-class
ticket on her laptop, and a boarding pass prints. The hallway becomes a jet bridge, and a departure board in it lists
every destination as CANCELLED except one: BED, ON TIME. She packs PJs and chips into a tiny carry-on, puts on her
sunglasses, and walks the three steps. The chorus is the arrival: the bedroom revealed as a five-star resort. The duvet
is an ocean, the ceiling is the sky, the nightstand is room service, and the do-not-disturb sign is an out-of-office
reply. The film never winks at the camera; the joke is how seriously the camera takes all this. It ends on a postcard of
the bed: "Wish you were here." Then she crosses it out.

**What the viewer should feel at the end:** seen, rested, and a little smug on her behalf.

## 2. The look (setup)

**A cozy diorama, shot like a high-end travel ad.** Build the sets as real 3D dioramas: an apartment at slightly toy-like
proportions, rounded edges, soft matte materials (linen, knit, painted wood, ceramic), cut open like a dollhouse where we
need to see inside. Use a gentle tilt-shift depth of field in the wide shots, so it always reads as a little world.

**The character is 2D in the 3D sets:** drawn, with a clean ink line, flat color and hard-edged shadow shapes (section 3).
This keeps her expressive and quick to animate, and it makes her pop against the soft 3D world.

**Two worlds, one apartment:**
- **Work (the intro and verse 1 desk):** cold, low light from screens. Grey-blue, slate, a sickly monitor cyan. The only
  warm colors are the little flames.
- **Vacation (everything from the hallway on):** resort warmth. Cream and sand, terracotta, sea-glass teal (the duvet,
  the "ocean"), warm brass, a coral sunset. It starts as golden hour, goes to sunset in chorus 2, to blue night with
  ceiling stars in the bridge, and back to full gold in chorus 3.

Keep the two palettes distinguishable for colour-blind viewers. Value and saturation should carry the difference, not
just hue (`craft/light-colour.md`).

**Light:** one warm key, like a low sun through the window, with soft bounce and long, soft shadows. A screen glow for
the work desk. Practical lamps in the bedroom. No blown-out highlights, and no lamp brighter than the scene can carry.

**Type:** a premium travel brand's look: an elegant high-contrast serif for headings and a clean geometric sans for
small print. Use it on the boarding pass, the departure board, the signs and the postcard. No real airline, hotel or app
brand anywhere.

## 3. The characters

**Her (setup, from her standing description of her avatar).** The singer, about mid-to-late 20s, cute and likable,
never aged. Hazel eyes, darker eyebrows, hair down in loose, curly, playful curls. Her signature is a **red knit beanie
with a big white LOVE on it and a cream pom-pom**, pulled down so it slightly covers her ears: make her and the hat
iconic and memorable. **Sunglasses** go on in the pre-chorus and stay on for the whole vacation, the bridge included
(the bridge is the one exception, where she pushes them up onto the beanie to sleep). Cozy pajamas in a soft resort
pattern (no red sleeves). Never sexualized in any shot: the comedy is deadpan dignity, not glamour. Her expressions are
calm, satisfied and unbothered. Her biggest reaction in the whole film is a slow, serene nod.

Her mouth is simple 2D: open/closed shapes and a few vowel shapes, lip-synced on the lines where she faces camera (the
chorus "I'm goin' on vacation" lines especially). It doesn't need to sync everywhere.

**Nobody else is on screen.** The captain and the flight attendant are voices, never people. The "staff" of the resort
is her: her own arm reaching for room service, her own foot kicking the door shut.

## 4. The camera (setup)

**Luxury-ad camera language, taken seriously.** Slow dollies and push-ins, smooth crane and aerial moves over the bed,
symmetrical one-point compositions for the reveals, and gentle parallax in the wide shots. Nothing handheld, nothing
frantic. The comedy comes from treating a duvet with the reverence of a Maldives drone shot.

- **Cuts land on downbeats**, with the bar grid from `song/map.json`. Section changes cut or turn on the first downbeat
  of the new section.
- **The aerial over the duvet** is the film's signature move: low, gliding over the sheets as if over water, like a
  resort drone shot. Use it at the chorus 1 reveal, again in chorus 2, and biggest in chorus 3. Don't use it anywhere
  else.
- **Readable at half size.** This film will be shown side by side with another film at half width, so every key action
  and every word must read at that size. Favor medium and wide shots with one clear subject, and keep signs big.

## 5. Words on screen (setup)

**No subtitle-style lyrics.** Words appear only as part of the world: the boarding pass, the departure board, the
calendar, the forecast card, the door hanger, the phone, the postcard. Every word sits fully inside its object (no text
spilling over its card, sign or tile) and is large enough to read at half size. If a phone screen appears, it looks like
a real phone's lock screen, not a cartoon stand-in.

## 6. Line by line

Times are where each line starts singing (from `song/timing.json`).

### Intro: the announcement (0:00–0:17.6)

- **0:00 (guitar alone):** The first frame is a real picture, never black: the work desk in the dark, lit only by a
  monitor. Slow push in. On the screen is a browser with a dozen tabs crammed so small their titles are unreadable.
  Five coffee cups stand around the laptop in a little crowd.
- **0:01.6 "Ladies and gentlemen, this is your captain speaking."** Her spoken line, flight-attendant voice. A small
  "seatbelt" chime light glows above the desk, and the calendar on the wall shows two weeks of squares, each one with a
  tiny cartoon flame flickering in it. *(hers: "two weeks of fires")*
- **0:04.6 "We will not be going anywhere."** Hold on her from behind at the desk, slumped. The beanie is the only warm
  color in the room besides the flames.
- **0:07.8–0:17.6 (the band comes in, about four bars):** She closes eleven tabs one by one, in rhythm with the finger
  snaps, until one remains: a travel booking page. A clean, elegant page with no real brand, offering one destination.

### Verse 1: booking (0:17.6–0:34.9)

- **0:17.6 "Two weeks of fires and a twelve-tab brain"** Close on the calendar's burning squares, then the tab bar.
  *(hers)*
- **0:21.1 "Coffee number five and I still missed the train"** The five cups in a neat row, like a bar menu. A toy train
  on the shelf leaves its little station without her. *(hers: the train)*
- **0:25.6 "So I booked a trip, first class, no fee"** Her finger clicks BOOK. Price: $0.00. A boarding pass prints out
  of the printer in one smooth slide and lands on the desk. *(setup)*
- **0:30.3 "One-way ticket down the hall for me"** An insert of the boarding pass, big enough to read at half size:
  FROM: DESK. TO: BED. GATE: DOOR. SEAT: 1A (CENTER). TRAVEL TIME: 4 SEC. *(setup, from her line)*

### Pre-Chorus 1: packing (0:34.9–0:45.5)

- **0:34.9 "Packed my PJs and a bag of chips"** A top-down shot of a tiny carry-on: folded pajamas, one bag of chips
  (no brand) placed in like a jewel, then the zip. *(hers)*
- **0:40.6 "Sunglasses on for the three-step trip"** Medium shot. She puts on her sunglasses with total seriousness. Cut
  to the hallway, framed like a jet bridge in one-point perspective. A departure board on the wall lists INBOX, MEETINGS,
  MONDAY and SOCIAL PLANS, all CANCELLED, then BED, ON TIME. She walks it in three steps, each on a beat. *(hers: the
  sunglasses and the three steps; setup: the board)*

### Chorus 1: arrival (0:45.5–1:12.8)

- **0:45.0 "I'm goin' on vacation"** The door opens on the downbeat, and golden light floods out. *(setup)*
- **0:46.7 "To my bed, bed, bed"** The reveal: the bedroom as a five-star resort, in a symmetrical wide shot. Light
  catches the bed on each "bed". *(hers: the line)*
- **0:48.6 "Five-star destination"** Five glow-in-the-dark stars on the ceiling light up one by one, like a hotel
  rating. *(setup)*
- **0:51.0 "Pillow for my head"** The signature aerial for the first time: low over the duvet as if over water, landing
  on the pillow like a resort pier. *(setup)*
- **0:53.3 "No passport, no plane, no airport line"** Three quick beats, one per item: a passport slides under the bed;
  a toy plane drifts off the shelf; a queue rope and stanchion fold away. *(hers: the items; setup: what happens to them)*
- **0:58.1 "Out of office, do not disturb, I'm doing fine"** A door hanger swings onto the knob. One side reads OUT OF
  OFFICE, and it flips to DO NOT DISTURB. She lies back, sunglasses on, and gives her first slow nod. *(setup, from her
  line)*
- **1:02.4 "I'm goin' on vacation"**, then **1:06.7 "To my bed, bed, bed"** She sings to camera, lip-synced, then sinks
  into the pillow on each "bed". *(setup)*

### Verse 2: the resort (1:12.8–1:31.0)

- **1:12.8 "The view is the ceiling, an ocean of sheets"** Her point of view straight up: the ceiling as a pale sky, with
  the ceiling fan turning slowly like a lazy sun. Then the duvet's folds roll in gentle waves. *(hers)*
- **1:17.4 "Room service is me reaching over for treats"** Her arm reaches for the nightstand, shot like an elegant crane
  move. On a little tray under a silver cloche: the bag of chips. *(hers: the line; setup: the cloche)*
- **1:22.1 "Forecast says duvet, seventy-two"** A forecast card on the bedside clock, in the travel type: DUVET, 72°,
  with a little cloud icon. *(hers)*
- **1:26.3 "Wi-Fi is on but I'm ignoring you"** Her phone lights up again and again as notifications stack on a
  realistic lock screen. She doesn't look. *(hers)*

### Pre-Chorus 2: low tide (1:31.0–1:40.8)

- **1:31.0 "Phone face down, the tide rolls in"** She turns the phone face down without looking. The duvet rises like a
  tide from her feet. *(hers)*
- **1:36.8 "Blanket up to my chin, chin, chin"** Three short pulls of the blanket, one on each "chin", until only the
  beanie, the sunglasses and the nose show. *(hers)*

### Chorus 2: full holiday (1:40.8–2:08.7)

Sunset now: coral and brass light. *(setup)*

- **1:40.1 "I'm goin' on vacation"** The aerial again, wider this time, out over the duvet ocean.
- **1:41.7 "To my bed, bed, bed"** It pulls out through the window to the city at dusk: a block of apartments where
  every window glows cold with someone working, except hers, which glows gold. *(setup)*
- **1:43.7 "Five-star destination"** The five ceiling stars, seen from outside through her window.
- **1:46.3 "Pillow for my head"** Back inside: an eye mask goes on like a spa treatment.
- **1:48.4 "No passport, no plane, no airport line"** Resort amenities: a glass of water on the nightstand as the
  "infinity pool", and the lamp dimming like a sunset.
- **1:53.2 "Out of office, do not disturb, I'm doing fine"** The door hanger again, then the door shutting with her foot.
- **1:57.3 "I'm goin' on vacation"**, then **2:02.3 "To my bed, bed, bed"** Sung to camera once more, settling in.

### Bridge: lights out (2:08.7–2:26.7)

Half-time and whispered. Blue night, with the ceiling stars as the only light. Slow camera. *(setup)*

- **2:08.7 "Shhh, don't call, don't text"** A finger to her lips. The phone buzzes once, face down, then goes still.
- **2:12.4 "Monday's a rumor, I'll check it next"** The calendar again, now in the dark: Monday's square is covered by a
  sticky note that says UNCONFIRMED. *(hers: the line)*
- **2:16.9 "Shhh, the tide is coming in"** The duvet rises in slow, calm waves. She pushes her sunglasses up onto the
  beanie and closes her eyes.
- **2:21.7 "It's just my blanket, let it win"** The blanket covers her completely. The camera sinks with it into soft
  dark teal, as if going underwater. *(hers)*

### Chorus 3: the whole resort (2:26.7–2:53.7)

The loudest section, and the film's biggest. Full gold. *(setup)*

- **2:26.1 "I'm goin' on vacation"** She bursts up out of the blanket like surfacing from the sea, sunglasses back on.
- **2:27.6 "To my bed, bed, bed"** The departure board, now in the bedroom: BED, EXTENDED STAY.
- **2:29.5 "Five-star destination"** The biggest aerial: from the pillow, over the duvet ocean, every light in the room
  warm.
- **2:32.4 "Pillow for my head"** Her slow, serene nod.
- **2:34.2 "No passport, no plane, no airport line"** The passport, the toy plane and the queue rope all reappear, and
  are dismissed one per beat.
- **2:38.9 "Out of office, do not disturb, I'm doing fine"** The door hanger, then the out-of-office reply on her laptop
  across the room going to sleep mode.
- **2:43.2 "I'm goin' on vacation"**, then **2:48.1 "To my bed, bed, bed"** Three cuts, each closer, one per "bed",
  ending on her face, perfectly content.

### Outro: the postcard (2:53.7–3:04.9)

- **2:53.7 (the band drops out):** The last frame of the bed freezes and becomes a postcard: a cream border, "GREETINGS
  FROM BED" in the travel serif. *(setup)*
- **2:53.7 "Wish you were here."** Her handwriting appears on the back of the postcard. *(hers)*
- **2:57.6 "No I don't."** Her hand crosses out "Wish you were here" with one firm stroke. *(hers, setup staging)*
- **2:58.9–3:04.9 (the instrumental tail):** The postcard sits on the duvet as the light goes down. The film ends on
  that image, not on black.

## 7. Firm points (hers)

- Nothing sexualized. No real brands, logos or apps imitated, except a phone lock screen that looks real.
- No subtitle-style lyrics. All text inside its object and readable at half size.
- No objects passing through each other, and no bodies passing through furniture: check every shot
  (`tools/blender/clipping.py`).
- The first frame is a real picture, never black.
- 1920×1080, 30 fps, on the master audio, exactly 3:04.92 long.

## 8. If time runs short (setup)

The 4 hours are tight for this film. Protect, in this order:

1. **Chorus 1's arrival** (the door, the reveal, the first aerial) and **the postcard ending**. These are the film.
2. **Her**, consistent and appealing in every shot she's in.
3. **Verse 1 and the pre-chorus** (the desk, the boarding pass, the departure board, the three steps).
4. Everything else. If you need to, simplify verse 2 and chorus 2 into fewer, longer shots in the same bedroom set. Reuse
   the set and the lighting across all three choruses, changing only the time of day. Don't cut the bridge's mood; make
   it simpler instead.

Every section must have finished pictures, not placeholders. A simpler shot that is finished beats an ambitious one
that isn't.
