#!/bin/bash
# Render every frame of the film as JPEG masters (frame n = time n/30): 16:9 at 1600x900 and 9:16 at 720x1280. The film
# reframes itself for vertical (VERT and V_OVR in web/js/film.js). Resumable: frames already on disk are skipped, so it
# can run in pieces (add t0 t1 to render a range: ./render.sh 42.34 69.6).
# First: cd web && npm install && npx playwright install chromium && node bake.mjs (the card faces), and the fonts in
# web/fonts/ (see README.md).
set -e
cd "$(dirname "$0")/web"
T0=${1:-0}; T1=${2:-244.8}
SKIP=1 node render.mjs frames 1600 900 ../build/frames_16x9 "$T0" "$T1"
SKIP=1 node render.mjs frames 720 1280 ../build/frames_9x16 "$T0" "$T1"
