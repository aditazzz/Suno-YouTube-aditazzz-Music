# Publishing to YouTube and Instagram

The upload tools use your own Google and Instagram sign-ins, saved only in `secrets/` (which git ignores). Install
their extra packages first:

```bash
pip install -r requirements-publish.txt
```

Using this for your own channel? Change the links in `studio.yaml` (channel, playlist, Instagram, Spotify) first. They
end up in every description.

## YouTube

### One-time setup (about 10 minutes)

1. Go to https://console.cloud.google.com/ and create a project.
2. **APIs & Services → Library**: enable **YouTube Data API v3**.
3. **OAuth consent screen**: External. Add yourself as a **test user**, and add the scopes
   `https://www.googleapis.com/auth/youtube` and `https://www.googleapis.com/auth/youtube.force-ssl`.
4. **Credentials → Create credentials → OAuth client ID → Desktop app.** Download the JSON and save it as
   `secrets/client_secret.json`.
5. The first upload opens your browser to sign in. If your channel is a Brand Account, pick the brand account that owns
   the channel on the "choose an account" screen, not your personal one. While the Google project is in testing mode
   the sign-in lasts about a week, then it asks again.

### A release plan

Uploads are driven by a small YAML plan. Nothing goes public unless the plan says when: every video is uploaded
private and YouTube publishes it at the planned time (`draft` stays private), or `privacy: unlisted` uploads link-only
videos.

```yaml
# plans/my-release.yaml
timezone: America/Los_Angeles
songs:
  - song: songs/my-song
    full_video: 2026-11-03 09:00        # or: draft
    clips:                              # the Shorts, one every 2 days from the first date
      start: 2026-11-04 12:00
      every_days: 2
      order: [first chorus, setup, bridge, final chorus]
```

```bash
python tools/youtube_upload.py --plan plans/my-release.yaml --dry-run   # show the plan, no sign-in
python tools/youtube_upload.py --plan plans/my-release.yaml             # review it, type "upload", go
```

You see every title, file and publish time before anything is sent. Each Short's description links to its full video
automatically, and the thumbnail, playlist and AI-disclosure flag are set for you. Every upload is recorded in
`songs/<slug>/build/uploads.json`, so nothing is uploaded twice. YouTube allows about 100 API uploads a day; if a limit
is hit, run the same command the next day and it continues.

### After an upload

```bash
python tools/youtube_upload.py --status                         # what's uploaded, scheduled and live
python tools/youtube_upload.py songs/<slug> --publish-now       # make a song's private uploads public now
python tools/youtube_upload.py songs/<slug> --post-comments     # post the comment you'll pin
python tools/youtube_upload.py songs/<slug> --update            # re-send titles, descriptions and tags after edits
python tools/yt_recent.py                                       # the latest uploads: privacy, processing, schedule
```

Still by hand in YouTube Studio: pin the comment, set each Short's **Related video** to the full video, end screens and
Test & Compare thumbnails.

## Instagram

### One-time setup (about 15 minutes)

Instagram only accepts a video from a public link, so each Reel is parked in a temporary Google Cloud Storage bucket
for a minute and deleted right after it posts (the bucket also clears itself daily).

1. **Google Cloud** (the same project as YouTube): link a billing account (the temporary files fit in the free tier),
   then add the scope `https://www.googleapis.com/auth/devstorage.read_write` under Google Auth Platform → Data Access.
2. **A Meta app** (https://developers.facebook.com/apps): create an app with the use case **Manage messaging & content
   on Instagram**. Under App roles, add your account as an **Instagram Tester** and accept the invite on instagram.com
   (Settings → Apps and websites → Tester invites). Under **API setup with Instagram login**, generate an access token.
3. Save the token: `python tools/instagram_post.py --set-token` (it's stored only in `secrets/`). It lasts 60 days and
   renews itself whenever you post.

### Posting

Add the song to the plan under `instagram:`, listing what to post in order (`edit` is the under-3-minute Reel, then
clip labels):

```yaml
instagram:
  - song: songs/my-song
    post: [edit, first chorus, setup]
```

```bash
python tools/instagram_post.py --plan plans/my-release.yaml --dry-run
python tools/instagram_post.py --plan plans/my-release.yaml      # review it, type "post", go
python tools/instagram_post.py --recent                          # your latest posts
```

Reels go out right away (Instagram's API has no scheduler), each with its own cover and caption. Anything already on
your profile with the same caption is skipped. Music from Instagram's library, collaborators and location are still
added in the app.
