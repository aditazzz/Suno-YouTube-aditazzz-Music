# Lessons learned

Everything here came out of making these videos: a note on a draft, a Short that underperformed, a render that died
at 2 a.m. Most of it is now built into the pipeline. The platform facts were researched in October 2026, and
platforms change often, so check them again before you rely on them (sources at the bottom).

- [Making the video](#making-the-video)
- [Shorts and Reels](#shorts-and-reels)
- [YouTube long-form](#youtube-long-form)
- [Rendering](#rendering)
- [Working with Claude](#working-with-claude)
- [Cadence and what to measure](#cadence-and-what-to-measure)
- [Sources](#sources)

## Making the video

- **One concept per song.** Every video gets its own world, palette and scene code; the shared engine only does
  timing, text, glow and post. A recurring style is fine. Near-identical lyric-slideshow videos are not: YouTube's
  "inauthentic content" policy (renamed from "repetitious content" in July 2025) can take monetization away from the
  whole channel for template-made or mass-produced videos.
- **Frame 0 is a real picture.** No fade in from black. The first frame often doubles as the preview people see on
  Instagram and YouTube, so an opening title has to be fully there on frame 0.
- **Check every AI-generated track for hum.** Suno tracks can carry a steady off-pitch tone under the whole song (a
  low buzz, a whine around 850 to 900 Hz) that you stop noticing after the tenth listen. `tools/enhance_audio.py --dry`
  lists them; clean them with narrow notches, A/B, and sync the video to the clean file.
- **No dead air.** An instrumental gap longer than about 4 seconds needs something to happen: a progress bar, a
  clock, a story beat.
- **Readable on a phone.** Lyrics at least 64 px tall in 16:9 and 58 px in 9:16 (at 1080p), anything else meant to be
  read at least 34 px and bold, code panels in 9:16 at least 38 to 40 px. If it doesn't fit, widen the panel or split
  the line; don't shrink the text. Outlined words need a faint fill and a dark shadow behind the line, or they vanish
  on a bright background. Two lines that share a spot hand off without overlapping.
- **Keep the safe frame.** On a phone, Shorts, Reels and TikTok crop about 9% off each side of a 9:16 video and draw
  their own controls on top: the back/search bar down to about 12% of the height, the channel name and caption from
  about 70% down, and the like/comment/share column on the right from about halfway down. `core.SAFE_9x16` holds that
  box, the lyric code fits each line into it (a line that already fits doesn't move), and
  `python -m studio.safezone songs/<slug>` renders every lyric line plus the end card and flags anything outside it.
  `studio.render` won't start a 9:16 render until that check passes. The hook pill is clamped below the top bar too.
- **Keep hooks playful.** Captions, hooks and thumbnails that pick a fight get attention you don't want.
- **Thumbnails say what the video is.** "CLAUDE ANIMATED THIS" alone told nobody anything. A short hook about the song,
  one plain line saying what kind of song it is, and a small badge works better. It also needs a bright subject you
  can recognize at phone size: two thin arcs over dark water read as a black square.
- **Every thumbnail matches the channel.** One video went out with a one-off card (a different badge, a different
  italic) and it looked like someone else's channel next to the others. Now the pipeline only makes the brand cover
  (`studio/brand.py`): the same photo chip, headline size and italic line on every video, with only the frame, the
  words and one accent color changing. A song that needs something special gets it added to the brand layer, not a
  hand-made card.
- **Titles: `Name (hook) - Claude Opus 5.5 Music Video`.** The hook in parentheses tells someone who has never heard
  the song what it's about ("Please Hold (I'd Rather Chew Glass Than Call)"), and the title always names the model
  that made the video. Covers and the title pill use the name alone (`config.public_name`).

## Shorts and Reels

- **Keep Shorts under 60 seconds.** A Short over a minute with any active Content ID claim is blocked worldwide, and
  your own distributed song can trigger that claim. Shorts here are cut at 58 seconds at most.
- **Set the Related video.** In YouTube Studio, link each Short to its full video. It's the main path from a Short to
  the long video, and the API can't set it, so it's done by hand.
- **Shorts don't hurt long-form.** YouTube runs separate recommendation systems for them.
- **Vertical and 3 minutes or less is a Short automatically.** `#shorts` isn't needed.
- **Instagram only recommends Reels of 3 minutes or less to non-followers**, which is why every song gets an
  under-3-minute edit, cut on downbeats.
- **Write hooks people send to a coworker.** Sends (shares in DMs) are the strongest signal for reaching people who
  don't follow you on Instagram. "POV: your standup just became a keynote" gets sent; "new song out now" doesn't.
- **Five hashtags at most on Instagram**, specific beats generic, and keywords in the caption do the search work.
- **Covers inside the 3:4 grid.** Instagram crops the profile grid to 3:4, so cover text stays between 12.5% and 87.5%
  of the height.
- **Match the end card to the platform.** A clip that runs into the video's end card said "follow on Instagram" on
  YouTube. YouTube copies of those clips now say "subscribe" instead.
- **Ask for the follow where people are hooked.** The 16:9 video shows a subscribe pill once, right after the first
  chorus. The last seconds are an end card with the right half kept clear for YouTube's end-screen elements, and every
  description link to the channel ends in `?sub_confirmation=1`, which opens the subscribe prompt. The 9:16 video has
  no mid-video pill because Shorts and Reels loop.

## YouTube long-form

- **The description**: a hook paragraph, how it was made, a question for the comments, subscribe and playlist links,
  other platforms, chapters, the full lyrics, then three hashtags. Only three show above the title, and too many makes
  YouTube ignore all of them. Tags barely matter.
- **Test & Compare** up to three thumbnails. The winner is picked by watch time, not click-through rate.
- **AI disclosure.** YouTube lists AI-generated music as something to disclose, so "Altered or synthetic content" is
  set to yes when the vocals or music are AI. YouTube says the label doesn't affect recommendations or monetization.
  The animation is drawn by code and isn't realistic, so it doesn't need the label on its own; realistic AI-generated
  pictures in the video (the photographic plates in Allow) do.
- **After publishing**: pin the comment, add the video to the series playlist, and point the end screen at the next
  video in the series.

## Rendering

- **Profile one frame before a long render.** A full-frame Gaussian blur for one small glow cost 0.64 s per frame;
  blurring only a box around the glow gave identical pixels about four times faster.
- **Small, resumable chunks.** 10-second chunks rendered in parallel, each written to a `.part` file and renamed when
  it's complete. A crash loses one chunk, and nothing truncated is ever joined into the final video. After a crash,
  check every chunk's frame count (`ffprobe`) before joining; "moov atom not found" means a chunk didn't finish.
- **Stale chunks keep the old look.** A chunk rendered before a change to `core.py` or `scene.py` still has the old
  picture. Compare chunk times with those files and delete the older chunks before resuming.
- **Re-check old scenes before re-rendering them.** A scene written before a lesson doesn't follow it yet. Render 9:16
  stills at t = 0, inside every instrumental gap longer than 4 seconds and at each clip's start + 0.5 s first.
- **Don't let `-shortest` eat the end card.** When a video runs past the last audio sample into the end card,
  `-shortest` cuts everything after the song. Pad the audio (`apad`) and cut to the planned length (`-t`) instead.
- **Cap caches by bytes, not entries.** 600 large float32 sprites came to about 1 GB per render worker.
- **Kill renders by PID.** `pkill -f <pattern>` and `pgrep -f` loops match the shell that's running them.
- **Clean up.** A full 16:9 + 9:16 render needs about 1 GB of chunks. Delete them once the final files are safe, or the
  next render can run out of disk halfway through a chunk.
- **Compare videos by stream, not md5.** Metadata can change on the way (some tools add a Content Credentials
  manifest, for example) while the picture and sound are identical. Check frame counts and `ffmpeg -f streamhash`.
- **Overlay on standard range.** A browser-rendered master (Remotion writes full-range `yuvj420p`) made the covers
  and hooks laid over it come out darker than the same images on their own. `studio/cuts.py` converts the video to
  standard range (`format=yuv420p`) before anything goes on top.
- **Contact sheets: sample exact frames.** `fps=1/8` gives the frame about 4 seconds after each label, so when you
  compare two versions, pick frames with `select=eq(n\,N)` or the captions will look out of sync when they aren't.

## Working with Claude

- **Turn notes into rules.** When a note applies to every video, it goes into the engine or the pipeline, not just a
  doc: the readability minimum is `core.MIN_READ`, "no black first frame" is in `cuts.py`, the per-song hook position is
  a `song.yaml` setting. The next video follows the rule without anyone remembering it.
- **Review with contact sheets.** Stills at chosen moments, in both formats, are much faster to review than a render,
  and they catch most problems (small text, overlaps, an empty first frame).
- **Keep the copy in `song.yaml`.** Titles, hooks, descriptions and captions live next to the creative settings, so
  fixing one and regenerating the package updates everything.
- **Ask for concepts before code.** "Propose three visual concepts for this song" gets more original videos than
  "make a video for this song".

## Cadence and what to measure

- One new song video a week, plus three to five vertical clips a week from the current and previous songs. Buffer's
  study of 2.1M posts found 3 to 5 posts a week grows followers about twice as fast as 1 to 2.
- Don't upload the same video twice. Post each clip once per platform; the same clip on YouTube and Instagram is fine.
- **YouTube long-form:** impressions click-through rate, average view duration, retention at 30 seconds, end-screen
  clicks, Test & Compare results.
- **Shorts:** viewed vs. swiped away, engaged views, percent watched (aim for 80%+), subscribers per Short, Related
  video clicks.
- **Instagram:** sends per reach, 3-second hold, average watch time, non-follower reach, follows per Reel.

## Sources

- Shorts length, classification and the Content ID rule for Shorts over a minute: https://support.google.com/youtube/answer/15424877
- Shorts myths (#shorts, separate recommendation systems), May 2025: https://blog.youtube/creator-and-artist-stories/debunking-common-myths-about-youtube-shorts/
- Test & Compare: https://support.google.com/youtube/answer/13861714
- Hashtags: https://support.google.com/youtube/answer/6390658
- AI disclosure: https://support.google.com/youtube/answer/14328491 and https://blog.youtube/news-and-events/improving-ai-labels-viewers-creators/
- Inauthentic content policy: https://support.google.com/youtube/answer/1311392
- Instagram's five-hashtag cap: https://www.techbuzz.ai/articles/instagram-caps-hashtags-at-five-to-combat-spam
- Mosseri on sends, and Instagram's originality updates: https://www.socialmediatoday.com/news/instagram-updates-algorithm-to-benefit-original-creators/819016/
- Posting frequency study: https://buffer.com/library/how-often-to-post-on-instagram/
