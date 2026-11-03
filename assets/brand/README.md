# Brand photo

The brand covers ([`studio/brand.py`](../../studio/brand.py)) are a headline and a "Made with Claude <model>" credit
over a frame of the video; they don't use a photo. The older layout (`LOCKUP=1`, for re-making old covers) had a lockup
chip in the top-left with a photo in a green ring next to the name and "</> CLAUDE ANIMATED THIS". The photo isn't in
the repo: for that layout, put a square one here as `aditazzz.jpg` (or point `BRAND_PHOTO` at any image, and change
`NAME` in `studio/brand.py` for your own name). Without it the chip shows a plain dark disc in the ring.
