# Look What I Can Do · v3 "The Comic Book" — brief for the section builders

## The artist and the song
Adita (YouTube @adita_zzz) makes satirical songs about AI and tech life, with music videos she builds in code with
Claude in this repo (one folder per song under `songs/`). "Look What I Can Do" is a bratty electropop duet: she brags to
Claude about everything she makes with AI, Claude flatters her, she hits her usage limit and switches to ChatGPT.
Her lines are white/green, Claude's are amber. She wrote the jokes; the video stages them so each lands.

## The concept (approved by her)
**A trailer for everything we've made: the video steps into her own music videos like panels of a comic book.** Each
part of the song walks through the literal world of one of her published videos, rebuilt in that video's own code
(same look, same assets, same techniques), re-timed to this song and carrying this song's jokes. Between parts, a
compositing pass (done by the director, not you) pulls back to a clean comic page and steps into the next panel.

Her direction, verbatim: "clean, modern, very smart and clever." "If you literally were showing what you can do, try
to. If something works as a swarm use it. If something works as a window on a skyscraper use it." "It would be amazing to
walk through the literal scenes." Her favourite looks: TED Talk (Charts) newspaper, Please Hold, I have a blocker.

## Sections (30 fps; frame n = song time n/30; you render EXACTLY your frame range)
| id | frames | song | world (source folder) | builder |
|---|---|---|---|---|
| P1 | 0–1287 | intro→pre (terminal) | approved 2D part 1 | director |
| S1 | 1288–1712 | chorus 1 | Great Idea, Ted / I have a blocker city at blue hour, floating video-call rooms (`songs/great-idea-ted/web`, `songs/i-have-a-blocker/web`) | W1 (3D) |
| S2 | 1713–1962 | "Click! Click! Ship it!" | LGTM: the pull-request cathedral, stained-glass diff, Approve/Submit/merge, CI chips, LGTM stamp (`songs/lgtm`) | W2 (2D) |
| S3 | 1963–2399 | verse 2 (her titles) | Mirror, Mirror (The Comment Section): her real post filling with comments, stamps (`songs/mirror-comments`) | W2 (2D) |
| S4 | 2400–2529 | qualifications | OMG! In the Walls: night-vision security cameras (`songs/omg-agents-walls`) | W3 (2D) |
| S5 | 2530–2999 | chorus 2 | OMG! Call Us Swarm: the murmuration of agents that spells words (`songs/omg-agents-swarm`) | W3 (2D) |
| S6 | 3000–3687 | verse 3 (her posts) | TED Talk (Charts): the newspaper "The Daily Standup", a chart every few seconds (`songs/ted-talk-charts`) | W4 (2D) |
| S7 | 3688–4095 | bridge (keynote) | the keynote stage with her TED videos (existing `web/js/stage.js`) | director |
| S8 | 4096–4552 | final chorus | Ragnarök or Reach for Mars: the longhouse, the seeress, the tarot deck, pop-up card worlds (`songs/ragnarok-or-reach-for-mars/web`) | W5 (3D) |
| BD | 4553–4748 | breakdown | approved 2D terminal ("I KNEW IT!") | director |
| S9 | 4749–5151 | drop | Please Hold's neon reboot: the HOLD tower whose windows spell words, the dance-floor plaza, the robots (`songs/please-hold/web`) | W6 (3D) |
| S10 | 5152–5447 | outro | Please Hold by day/dusk: the robot, its eye-strip screen, her phone | W6 (3D) |
| END | 5448–5951 | end card | 2D | director |

Lyrics and word-level times: `songs/look-what-i-can-do/web/data/timed.json` (list of {sec, text, words, wt, s, e}),
beats: `web/data/beats.json` (tempo 129.2). 2D code gets the same through `studio.core.Timing(<this song dir>)` (see
`scene.py`: `T = C.Timing(HERE)`, helpers `line/ls/wt`). Key lines per section are in the table at the end.

## What each section must say (the jokes; stage them so they read)
- **S1 chorus 1**: the camera comes out of her laptop screen (the first frame continues from a dark terminal that reads
  "TOO LATE!") into the blue-hour city; on every "Look what I can do!" and "I made a thing that made a thing / That made
  another two!" the floating call rooms multiply (1→2→4→…, each new room grows out of its parent) and her videos play
  in them; LOOK WHAT I CAN DO appears built into the city (billboard, neon, tower clock, rooms arranged as letters…),
  never pasted over a joke. "I don't know how I got here / But I brought my laptop too!" lands on her own room with the
  laptop (a label like `laptop: brought ✓` worked well).
- **S2 Ship it** (57.10–65.44): "Click! Click! Ship it!" ×3, "Made it! Broke it!" ×2, "Fixed it! Shipped it!". Use LGTM's
  machinery: review dialog Approve → Submit on the clicks, merge on "Ship it", CI chip red on "Broke it", green on
  "Fixed it", the LGTM stamp (REVIEWED · APPROVED · 0 LINES READ), approval counter. Her video frames can be what is being
  shipped (the diff/stained glass shows her footage). Whip energy on every click.
- **S3 verse 2** (65.44–80.00): titles she sings: Senior Slopcore Architect · Chief Executive of What's Next · VP of
  Things That Look Complete · Director of the Missing Feet · Head of Vibes and Synergy · Chief of Artificial Me · "A
  thought leader by half past three" · "By four I've got a TED Talk fee!". Her REAL X post `post_slopcore.png` ("Currently
  upskilling to transition into a Principal Slopcore Architect role…") is the post; the titles arrive as the replies/
  comments, Mirror-Comments style, each giving itself away (e.g. a "Missing Feet" reply with a 404 avatar). Her REAL X
  profile `profile.png` can grow a line per title. Highlighter yellow #ffe14d over the punchline words, RECEIPT stamp red.
- **S4 qualifications** (80.00–84.34): Claude (amber): "What are your qualifications?" Her: "I have a subscription."
  Claude: "To what?" Her: "Everything." Seen through In the Walls' night-vision security cameras (timestamps, REC dot,
  camera labels); "Everything." pays off visibly (e.g. every camera feed fills with subscription receipts/charges).
- **S5 chorus 2** (84.34–100.00): the swarm: "Look what I can do!" ×4, "I made a thing that made a thing / That made
  another two!" (agents splitting), "My résumé is fourteen pages / And my title's AI guru!". The murmuration spells LOOK
  WHAT I CAN DO on the hooks, a 14-page résumé (page counter 1/14 → 14/14), AI GURU. Swarm palette.
- **S6 verse 3** (100.00–122.94): The Daily Standup newspaper, one story/chart per couplet. Her REAL posts as the news:
  "I posted 'We are so back!'" = `post_back.png` · "Then posted 'We are doomed!'" = `post_tomatoes.png` · "Then asked a bot
  to summarize / The panic in the room" (a summary box that says everyone is panicking, including you) · "I bought ten
  little Mac minis / For reasons I can't share" = `post_minis.png` (REDACTED) · "My agents formed a company / And made me
  Employee of the Year" (org chart of agents; footage of the Claude robot from Asking for a Friend when it's available) ·
  "I made a song about the end / Of every job on Earth" · "Then gave myself a brand-new one" (HIRED BY MYSELF) · "And tripled
  my net worth!" — HER JOKE: she has made $0 from it, so the chart is $0 × 3 = $0, staged deadpan and precise (e.g. a
  bar chart of three identical empty bars, axis in $, footnote "growth: 200%"). Clever, not mean.
- **S8 final chorus** (136.54–151.74): the longhouse; the seeress turns cards; each card opens a pop-up world of her videos;
  "I made a song about myself / And now I'm in it too!" (a card showing this very video); "I built an entire universe /
  And left it a five-star review!" (five gold stars, one per beat; a review card "Great universe. — Adita"). She asked for
  the seeress and the man with the rocket to each get a full-screen moment. Hooks "Look what I can do!" ×4 built into the
  hall (embers, carved/gilded letters on a card, the hearth).
- **S9 drop** (158.30–171.74): Please Hold's neon reboot; the HOLD tower windows spell LOOK WHAT I CAN DO on each drop
  hook (161.74, 163.66, 167.95, 170.67); robots run the dance floor; her videos on the tower's screen face.
- **S10 outro** (171.74–181.60): Her "Claude?" Claude "Yes?" Her "Can we make one more?" Claude "You've reached your usage
  limit." (the robot's eye strip shows a battery at 1%, then her REAL post `post_usage.png` as the receipt) Her "Hey
  ChatGPT?" — her REAL phone screen recording `assets/chatgpt.mp4` lights up (Please Hold opens on her phone in her hand:
  reuse that). Last frame dark (the end card fades in from black at 181.6).

## Footage (her published videos, 100+ views, plus Asking for a Friend)
HD clips: `music/Look What I Can Do/hd/<key>.mp4` (1280×720, 30 fps, 5–6 s). 3D pages: the same as JPEG sequences in
`web/media/hd/<key>/001.jpg…` (960×540, 30 fps). Keys so far: ph_* (Please Hold), bl_* (I have a blocker), rage_* (Rage
Against the Machine Learning), ts_* (TED Talk Screenlife). More arrive while you work (Asking for a Friend's Claude robot
and purple GT3 RS "DK WHEEL", OMG, AI Slop, the Mirrors, TED Charts/Shadow, Ragnarök's seeress and man with the rocket,
Thirsty, Graceful Shutdown, Great Idea Ted, LGTM, Next Token): `ls` the folder again before you finalize; code against
keys with a fallback. NEVER use footage from anything not in that folder. Avoid frames that are blown out / glowing white.
Her X post images: `music/Look What I Can Do/assets/post_*.png`, `profile.png`, `bio_end.png`; word boxes for highlights in
`web/BRIEF.md` (search "Word boxes").

## Rules (hers; non-negotiable)
- Text that is the point of a shot: ≥ 34 px cap height at 1920×1080, and give it time to read. No subtitle-style lyric line.
  Text never spills outside its box/card/panel. Nothing covers a joke.
- Clean, modern, crisp: no grey haze, no muddy blacks, no blown-out whites, restrained bloom, little grain.
- No children. No subscribe ask mid-song. Don't show her birthday or follower count. Non-inflammatory.
- Recurring assets she loves stay recognizable: the Claude robot, the purple (Porsche "Ultraviolet") GT3 RS with yellow
  calipers. Her avatar wears black wayfarer sunglasses.
- Deterministic: every frame is a pure function of t (any frame, any order, any process). No Math.random/Date; seeded rngs.
- Performance on this 2-core box: 2D ≤ 0.8 s per 1080p frame, 3D ≤ 1.6 s.
- Don't edit files you don't own: read other songs' code, COPY what you need into your own section files. Own files only:
  2D → `songs/look-what-i-can-do/sections/<your_section>.py` (+ helpers prefixed with it); 3D → `songs/look-what-i-can-do/web/<sX>.html`
  + `web/js/<sX>/*`. Don't touch scene.py, studio/, web/js/*.js (shared), or any other song folder.
- Critique your own stills like a master motion designer before you call it done (composition, readability, nothing
  intersecting, motion that reads as intentional). Her bar: Imaginative Prompting-level quality.

## How to render
- 2D: module `songs/look-what-i-can-do/sections/<name>.py` exporting `render_frame(t, W, H) -> HxWx3 uint8 RGB`.
  Stills: `cd /home/claude/aditazzz/suno-youtube-aditazzz-music && python3 songs/look-what-i-can-do/sections/run.py <name> stills <dir> 57.3 58.2 … [--wh 1280 720]`
  Final: `… run.py <name> range <n0> <n1> songs/look-what-i-can-do/build/v3/<SX>.mp4`
- 3D: a page `web/<sX>.html` that defines `window.ready` and `window.renderTime(t) -> Promise<jpeg dataURL>` (see
  `web/film.html` + `web/js/film.js`). Stills: `cd songs/look-what-i-can-do/web && PAGE=<sX>.html node render.mjs stills 1280 720 <dir> t…`;
  final: `PAGE=<sX>.html node render.mjs range 1920 1080 ../build/v3/<SX>.mp4 <n0/30> <(n1+1)/30>`. The source songs'
  `web/` folders have their own render.mjs/film.js showing how they set up the renderer; port, don't import across folders.
- Deliver: your section mp4(s) in `build/v3/` with exactly the frame count of your range, plus a report: what's in it,
  first/last frame description (for the comic-page transitions the director composites at the boundaries — your first and
  last ~0.4 s may be seen inside a panel, so open and close on a strong, readable image), ms/frame, anything unfinished.

## Key times (seconds)
42.94 CH1 Look what I can do! (do 43.88) · 44.64 Look what I can do! (do 45.72) · 46.50 I made a thing that made a thing
(thing 47.12, 48.04) · 48.24 That made another two! (two 49.22) · 50.00 Look… (do 51.20) · 51.70 Look… (do 53.06) · 53.50 I
don't know how I got here · 55.36 But I brought my laptop too! · 57.10/58.52/62.24 Click! Click! Ship it! · 59.92/63.58 Made
it! Broke it! · 60.84 Fixed it! Shipped it! Shipped it! · 64.56 Fixed it! Shipped it! · 65.44 I'm a Senior Slopcore
Architect · 67.60 Chief Executive of What's Next · 69.20 VP of Things That Look Complete · 71.10 Director of the Missing
Feet · 73.08 Head of Vibes and Synergy · 74.56 Chief of Artificial Me · 76.50 A thought leader by half past three · 78.40 By
four I've got a TED Talk fee! · 80.00 What are your qualifications? · 82.10 I have a subscription. · 83.20 To what? · 83.64
Everything. · 84.34 CH2 Look… · 86.42 Look… · 88.56 I made a thing… · 90.24 That made another two! · 91.86 Look… · 93.72
Look… · 95.28 My résumé is fourteen pages · 97.26 And my title's AI guru! · 100.00 I posted "We are so back!" · 101.62 Then
posted "We are doomed!" · 103.46 Then asked a bot to summarize · 105.02 The panic in the room · 107.14 I bought ten little
Mac minis · 109.14 For reasons I can't share · 110.70 My agents formed a company · 112.34 And made me Employee of the Year ·
114.36 I made a song about the end · 116.20 Of every job on Earth · 117.99 Then gave myself a brand-new one · 119.86 And
tripled my net worth! · 122.94 BRIDGE … · 136.54 FINAL Look… · 138.50 Look… · 140.00 I made a song about myself · 142.04 And
now I'm in it too! · 143.70 Look… · 145.54 Look… · 147.12 I built an entire universe · 149.24 And left it a five-star
review! · 151.74 breakdown (2D) · 158.30 DROP hit · 161.74/163.66/167.95/170.67 Look what I can do! · 171.74 Claude? ·
172.24 Yes? · 173.04 Can we make one more? · 174.30 You've reached your usage limit. · 176.78 Hey ChatGPT? · 178.15 last
musical blast · 181.60 end card.
