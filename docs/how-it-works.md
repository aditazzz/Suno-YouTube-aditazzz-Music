# How it works

Every video in this repo is a program, almost all of them in Python. A finished song goes in, and the pipeline writes the full music video,
a vertical version, Shorts and Reels, thumbnails and every caption. This page walks through each step and ends with
how to make one for your own song.

- [The idea](#the-idea)
- [Working with Claude](#working-with-claude)
- [The files for one song](#the-files-for-one-song)
- [1. Sync: the song becomes data](#1-sync-the-song-becomes-data)
- [2. The scene: the video as a program](#2-the-scene-the-video-as-a-program)
- [3. Render](#3-render)
- [4. Cuts: Shorts, Reels and the under-3-minute edit](#4-cuts-shorts-reels-and-the-under-3-minute-edit)
- [5. Thumbnails and covers](#5-thumbnails-and-covers)
- [6. Package: titles, descriptions, captions](#6-package-titles-descriptions-captions)
- [7. Publish](#7-publish)
- [Make your own](#make-your-own)

## The idea

There's no template. The shared engine in `studio/` only handles the things every video needs: timing, text, glow,
lyrics, post-processing, rendering and cutting. What the video *is* lives in the song's own folder, and it's new every
time: a newspaper that prints a new chart every few seconds, a single zoom from an office out to the edge of the
observable universe, cut-paper puppets behind a lamp-lit screen, a house seen only through its night-vision security
cameras.

That's partly taste and partly YouTube's rules: videos that look template-made or mass-produced can lose monetization
for the whole channel ("inauthentic content"). One concept and one program per song keeps every video its own thing.

The [TED Talk](../songs/ted-talk) song shows it best: one song, five videos, five unrelated programs.

## Working with Claude

I give Claude this folder and say something like *"make the video package for TED Talk"* or *"let's remake TED Talk
as a shadow puppet play"*. From there it's a loop:

1. **Concept.** Claude proposes what the video is (the world, the palette, what happens on which line) and writes
   it into the scene's docstring and `song.yaml`.
2. **Stills.** It renders contact sheets of stills at chosen moments, in 16:9 and 9:16, and checks them: is the text
   readable on a phone, is the first frame a real picture, does anything overlap.
3. **Notes.** I look and give notes. Claude fixes them, and anything that will matter for every video becomes a rule
   in the engine or in [lessons.md](lessons.md).
4. **Render** the full video (16:9 and 9:16), then QA: contact sheets across the whole song, every Short's first
   frame, the end card.
5. **Cuts, thumbnails, copy, upload.** Then I post, or Claude does it through the upload tool and my own Google sign-in.

Most of the code in `songs/` was written this way, in conversation, one video at a time.

## The files for one song

```
songs/ted-talk/
  song.yaml        every creative choice: audio file, clips to cut, cover frame, thumbnail settings, titles, copy
  lyrics.txt       the lyrics with section headers
  scene.py         the video (some songs split it into several modules)
  build/           made by the pipeline: timed.json, beats.json, sections.json, clips.json
```

`lyrics.txt` uses section headers on their own line. Names starting with `V`, `PRE`, `CH`/`HOOK`/`FINAL`, `BRIDGE`,
`BUILD` or `OUTRO` are understood automatically:

```
#V1
He doesn't answer questions.
He responds to them.
#CH1
It's a Ted talk.
Eighteen minutes, no slides, no point.
```

`song.yaml` starts with the basics and grows as the video does (the full ones are in each song folder):

```yaml
title: TED Talk
audio: TED Talk.wav          # file name in the music folder
model_credit: Claude Opus 5.5
cover_time: 27.75            # the frame Shorts and covers open on: the first TED TALK hit
aliases:                     # words the speech model tends to mishear, for the alignment
  ted: [said, dead, ted's, head, tad]
youtube:
  hook: I asked Ted if the file was ready. He said "so — stepping back," somebody dimmed the lights, ...
  question: "Who's the Ted on your team? (Don't tag him.)"
  chapters: {V1: "He doesn't answer questions", CH1: "It's a Ted talk", BRIDGE: "Ted. This is a standup."}
```

## 1. Sync: the song becomes data

[`studio/sync.py`](../studio/sync.py), run once per song: `python -m studio.sync songs/<slug>`.

First, check the track for hum. AI music generators often leave a steady tone under the whole song (a low buzz, a
whine around 850 to 900 Hz). [`tools/enhance_audio.py`](../tools/enhance_audio.py) finds tones that hold one level
all song and aren't on the song's tuning (so real notes are left alone), cuts each with a very narrow zero-phase
notch, and writes `<Song> (clean).wav` next to the original, plus an A/B clip with `--preview`. Listen to the A/B;
if it's better, point `audio:` in `song.yaml` at the clean file before you sync, so the timing matches what you hear.

```bash
python tools/enhance_audio.py "music/<Song>.wav" --dry            # what it would cut
python tools/enhance_audio.py "music/<Song>.wav" --preview 0:12   # write the clean file and a 12 s A/B clip
```

- **Separate the vocals.** Spleeter (2 stems) through [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx), in 30 s
  windows with a 1 s crossfade so it fits in a few GB of memory.
- **Transcribe them.** NVIDIA's Parakeet TDT 0.6B speech model (int8, local, through sherpa-onnx) in 12 s windows
  every 10 s, which gives words with timestamps.
- **Align to the real lyrics.** The sung words rarely match the transcript exactly, so the written lyrics are aligned
  to it with dynamic programming: an exact match scores 3, an alias from `song.yaml` or a close spelling 2, a skipped
  word costs 1 and a skipped transcript word 0.3. Words with no match are interpolated between their neighbors. The
  script prints the match rate and warns below 60%.
- **Beats, downbeats, sections.** librosa finds the beats. The downbeat phase comes from where the energy jumps
  (chorus drops land on beat 1), with lyric line starts as a second opinion when that's unclear. Each section from
  `lyrics.txt` starts on the downbeat before its first word.

Output in `build/`: `timed.json` (every line and word with times), `beats.json`, `sections.json`. These are included
for every song here, which is why you can render any video without the audio.

When a song fights the speech model (shouted gang vocals, for example) a small per-song fix is fine:
[`songs/rage-against-the-machine-learning/sync_fix.py`](../songs/rage-against-the-machine-learning/sync_fix.py) takes
those words from the full mix instead.

## 2. The scene: the video as a program

`songs/<slug>/scene.py` must define:

```python
def render_frame(t: float, W: int, H: int, fi: int) -> np.ndarray:   # (H, W, 3) uint8 RGB
```

`t` is the time in seconds and `fi` the frame index. The same function draws 1920×1080 and 1080×1920, so every scene
decides how to lay itself out for both.

The engine gives it:

- **[`studio/core.py`](../studio/core.py)**: `Timing` (lines, words, beats, downbeats, sections, `word_t`,
  `beat_pulse`, `snap`), cached text sprites, glow (`bloom`, `god_rays`, `streaks`), a small 3D camera (`orbit`,
  `project`, `splat`), post (`finish`: flash, chromatic aberration, glitch, vignette, grain), karaoke lyrics
  (`overlay_lyrics`), giant title hits (`overlay_stamp`), the subscribe pill and the end screen.
- **[`studio/kit.py`](../studio/kit.py)**: 2D pieces for colorful scenes: panels, chat bubbles, code editors with
  git-blame gutters, stickers, chips.
- **[`studio/world3d.py`](../studio/world3d.py)**: a tiny 3D toolkit (painter's algorithm, flat shading, ink
  outlines, textured quads, extruded 3D words). *Deployed on a Friday*'s beach town is built with it.
- **[`studio/space.py`](../studio/space.py)**: photoreal space: a real-texture Earth (NASA Blue and Black Marble), an
  analytic atmosphere (Rayleigh and Mie scattering), stars and the Milky Way, the Sun, and an HDR camera (bloom, ACES
  tonemapping, grain). *Graceful Shutdown* and the outer half of *Stepping Back* use it.

Two switches let the pipeline reuse a scene: `core.STATE["clean"]` hides lyrics and overlays (for thumbnails and
covers), and `core.STATE["lyric_filter"]` hides lines at edit joins. Scenes that draw lyrics through
`overlay_lyrics` and `overlay_stamp` get both for free.

Readability rules live in the engine: lyrics at least 64 px (16:9) or 58 px (9:16) at 1080p, and any text meant to
be read at least 34 px and bold (`core.MIN_READ`). Thin, small text is unreadable on a phone.

While writing a scene, review it with stills:

```bash
python -m studio.render songs/<slug> --stills 10 30 60 90 120           # 16:9 contact sheet in build/
python -m studio.render songs/<slug> --fmt 9x16 --stills 10 30 60 90    # vertical
python tools/preview.py songs/<slug> 40 60 preview.mp4                  # a short range, with the audio
```

Good places to start reading:

| Song | Why |
|---|---|
| [snowflake-undrop](../songs/snowflake-undrop) | The reference scene the engine grew from: a table shatters into ice and rebuilds as a snowflake. |
| [graceful-shutdown-opus](../songs/graceful-shutdown-opus) | Photoreal space with `studio/space.py`. |
| [deployed-on-a-friday](../songs/deployed-on-a-friday) | A 3D town with `studio/world3d.py`, plus the two earlier versions of the same scene. |
| [ted-talk-stepping-back](../songs/ted-talk-stepping-back) | One continuous zoom from the standup to the edge of the observable universe, split into modules (office, city map, cosmos, overlay). |
| [ted-talk-shadow-play](../songs/ted-talk-shadow-play) | Cut-paper puppets: a lamp, a paper screen and shadows that grow as a puppet steps back. |
| [ted-talk-screenlife](../songs/ted-talk-screenlife) | A whole laptop desktop drawn as vector UI: a video call, chat, calendar, notifications. |
| [omg-agents-walls](../songs/omg-agents-walls) | A tiny ray-caster for night-vision security camera footage. |
| [eleven-kept-going](../songs/eleven-kept-going) | A rocket launch and landing at night: ray-traced rocket surfaces, a curved Earth and the real Cape Canaveral coastline. |
| [i-have-a-blocker](../songs/i-have-a-blocker) | The first Three.js film, rendered frame by frame in headless Chromium (clay mannequins in fifteen floating rooms, lyrics made of particles), with a `scene.py` that hands the rendered masters to this pipeline for the end card and the Shorts. |
| [ragnarok-or-reach-for-mars](../songs/ragnarok-or-reach-for-mars) | The bigger Three.js film: carved puppets on twos, a shader fire, ember captions and tarot cards that open into pop-up worlds, with its own render and cut scripts. |
| [allow-fangs-for-asking](../songs/allow-fangs-for-asking) | A standalone program over photographic plates: rain that refracts the street through every drop, fog and frost on the glass, and a room relit from candlelight to screen blue, cut to moments measured from the recording rather than a tempo grid. |

## 3. Render

[`studio/render.py`](../studio/render.py):

```bash
python -m studio.render songs/<slug> --fmt 16x9 --jobs 4
python -m studio.render songs/<slug> --fmt 9x16 --jobs 4
```

- The video is split into chunks of 300 frames (10 s). Worker processes render chunks in parallel and pipe raw RGB
  frames into ffmpeg (H.264, CRF 16).
- A chunk is written as `.part` and renamed only when it's complete, so a crash never leaves a truncated chunk behind.
  Rendering is resumable: run the same command again and it picks up the missing chunks. `--budget <seconds>` stops
  launching new chunks after a while, for shells with a time limit.
- The chunks are joined and muxed with the song: 16:9 at 12 Mbps for YouTube, 9:16 at 4 Mbps, AAC 320 kbps. A few
  silent seconds (`tail` in `song.yaml`) are added for the end screen.

Rendering runs on the CPU, and some scenes do a lot per frame: the photoreal space scenes take about a second per
1080p frame per core. Profile a frame before a long render; a full-frame blur for one small glow can make a video four
times slower.

## 4. Cuts: Shorts, Reels and the under-3-minute edit

[`studio/cuts.py`](../studio/cuts.py) cuts the vertical video into clips listed in `song.yaml` (or picks them from the
sections):

```yaml
clips:
  - {kind: reel,  label: setup,        start: 6.61,   end: 26.122, cover: true, hook: "My standup, charted"}
  - {kind: short, label: final chorus, start: 122.41, end: 158.639, hook: "Nobody can end it"}
```

- Cuts land on downbeats. Shorts stay under 60 s: a Short over a minute with any Content ID claim is blocked, and
  your own distributed song can trigger one.
- No black first frame. A clip opens on a real picture, and the hero clip opens on the cover frame.
- The hook is on screen for the first 3 seconds, in a pill placed per song (`hook_y`, `hook_fs`) so it doesn't cover
  the scene's own titles.
- The first 3.2 s of each clip are re-rendered without any lyric line that started before the clip, so there's never
  half a line on frame 0.
- An under-3-minute edit for Instagram, cut on downbeats with the lyric lines at each join hidden. Instagram only
  recommends Reels of 3 minutes or less to people who don't follow you.
- [`tools/yt_short_endcard.py`](../tools/yt_short_endcard.py) makes YouTube copies of clips that run into the end
  card, with "subscribe" instead of the Instagram "follow".

## 5. Thumbnails and covers

Every video's thumbnail is the same **brand cover** over a clean frame of that video, so the channel reads as one
artist. [`studio/thumbs.py`](../studio/thumbs.py) renders the clean frame (no lyrics) and hands it to
[`studio/brand.py`](../studio/brand.py), which adds one fixed top layer:

1. the lockup chip, top-left: my photo in a green ring, "aditazzz" and `</> CLAUDE ANIMATED THIS`
2. the headline: two short lines in Anton with a black outline, the last line in one accent color (neon green, or
   red, amber, yellow or ice to suit the frame; never pink), always the same size
3. one italic line in Instrument Serif saying what kind of song it is

The words and framing come from `song.yaml`:

```yaml
thumb_time: 0.5                 # the clean frame underneath
thumb_lines: [PLEASE, HOLD]     # the headline (a long hook gets another line, never a smaller font)
thumb_sub: "a song about sending a robot to sit on hold"
brand_accent: amber             # the last headline line
ctx_shift_y: 0.09               # slide/zoom the frame (ctx_shift, ctx_shift_y, ctx_scale, ctx_dark) to clear the text
```

[`brand_covers.yaml`](../brand_covers.yaml) can override any of that per video (and covers videos without a song
folder); `python -m studio.brand` re-makes covers in bulk. `--times` gives extra frames, each written as an
"option N" brand cover for YouTube's Test & Compare, and the step also writes a 9:16 cover for Shorts. Songs that
render their own thumbnail plates, like the 3D films, run the same `brand.song_cover()` on them
([`songs/please-hold/make_thumbs.py`](../songs/please-hold/make_thumbs.py)). The older card styles are still in
`thumbs.py` for re-making old covers (`--legacy`), never as a new video's thumbnail.

[`tools/clip_covers.py`](../tools/clip_covers.py) picks the most colorful clean frame after each clip's hook for
Reel and Short covers.

## 6. Package: titles, descriptions, captions

[`studio/package.py`](../studio/package.py) writes `copy.md` (every field ready to paste) and `build/package.json`
(for the uploader) from `song.yaml`: the title, a description with the hook, the news behind it for a topical song
(`youtube.news`), how it was made, a *by the numbers*
block filled from the build (lines of scene code, frames rendered, lyric lines synced), chapters from the sections and
the full lyrics. Each Short gets its own title and description with a link back to the full video.

## 7. Publish

[`tools/youtube_upload.py`](../tools/youtube_upload.py) uploads everything (private, unlisted or scheduled) from a
release plan, sets thumbnails and playlists, posts the comment to pin, and keeps a record so nothing is uploaded twice.
[`tools/instagram_post.py`](../tools/instagram_post.py) posts Reels. The one-time setup for both is in
[publishing.md](publishing.md).

Two things still need YouTube Studio by hand: pinning the comment and setting each Short's **Related video** to the
full video (that link is the main way viewers get from a Short to the long video).

## Make your own

1. **Install.** Python 3.10+, ffmpeg, then `pip install -r requirements.txt`, the fonts from
   [assets/fonts/README.md](../assets/fonts/README.md) and the speech models: `python tools/get_models.py` (~700 MB).
2. **Add your song.** Put the audio in `music/` (or set `MUSIC_DIR`) and check it for hum with
   `python tools/enhance_audio.py music/<song>.wav --dry`. Make `songs/<your-song>/` with a `song.yaml` (at least
   `title:` and `audio:`, the clean file if you made one) and `lyrics.txt` with section headers.
3. **Sync.** `python -m studio.sync songs/<your-song>`. Check the word match rate it prints; add `aliases:` for
   words it keeps mishearing.
4. **Write the scene.** Ask Claude for a concept first, and for one that isn't like the others. Something like:
   *"Here's my song and its lyrics. Read studio/core.py and a couple of the scenes in songs/, then propose three visual
   concepts for this one. After I pick, write songs/my-song/scene.py and show me stills."*
5. **Review stills, then render** both formats, then `python -m studio.cuts`, `python -m studio.thumbs` and
   `python -m studio.package`. Finished files land in `music/<title>/`.

Read [lessons.md](lessons.md) before your first long render. Most of it was learned the hard way.
