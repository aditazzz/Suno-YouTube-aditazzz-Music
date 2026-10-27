#!/bin/bash
# Assemble the silent 3D masters from the rendered frames (frame n = time n/30, all of 0..END):
#   build/h/f_%05d.jpg (1600x900) -> build/master_16x9.mp4,  build/v/f_%05d.jpg (900x1600) -> build/master_9x16.mp4
# Then: python3 -m studio.render songs/please-hold --fmt 16x9_1440 --skip-safe-check   (and --fmt 9x16)
#   ./assemble.sh [16x9|9x16|both] [END_SECONDS=213.0]
set -e
P=$(cd "$(dirname "$0")" && pwd); WHICH=${1:-both}; END=${2:-213.0}; N1=$(python3 -c "print(round($END*30))")
for F in 16x9 9x16; do
  [ "$WHICH" != both ] && [ "$WHICH" != $F ] && continue
  D=$P/build/$([ $F = 16x9 ] && echo h || echo v)
  python3 - "$D" "$N1" <<'PY'
import os, sys
d, n1 = sys.argv[1], int(sys.argv[2]); miss = [n for n in range(n1) if not os.path.exists(f'{d}/f_{n:05d}.jpg')]
if miss: print('MISSING', len(miss), 'frames in', d, 'first', miss[:10]); sys.exit(1)
print('frames ok', d, 0, '..', n1 - 1)
PY
  ffmpeg -v error -y -framerate 30 -start_number 0 -i $D/f_%05d.jpg -frames:v $N1 -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -r 30 $P/build/master_$F.mp4
  ffprobe -v error -show_entries stream=width,height,nb_frames -of compact $P/build/master_$F.mp4
done
