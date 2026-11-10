#!/bin/bash
# Render a Living Earth shot of the mix through the GPU queue (one ticket per 150-frame chunk, resumable, never overwrites).
#   songs/you-said-you-needed-space/living_earth/render_le.sh stills LE3 [t1 t2 ...]   a few check stills first (seconds, song time; COMP_OVERRIDE=LE916 env for 9:16)
#   songs/you-said-you-needed-space/living_earth/render_le.sh frames LE1|LE2|LE3 [COMP]  the shot's PNG frames (COMP LE916 = the 9:16 render, out <shot>_916/)
# Out: build/living_earth/<shot>/f%05d.png (frame numbers = song frames at 30 fps) + a silent joined mp4 for checking.
# GPU: NOT before Asking for a Friend ships (its producer owns the queue until then); CPU-only prep until the director says go.
set -euo pipefail
MODE="${1:?stills|frames}"; SHOT="${2:?LE1|LE2|LE3}"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"; REM="$SONG/remotion"
PY="$ROOT/.venv/bin/python"
read -r _ COMP FIRST LAST < <("$PY" "$HERE/le_frames.py" "$SHOT")
COMP="${1:-${COMP_OVERRIDE:-$COMP}}"
OUT="$SONG/build/living_earth/$SHOT"; case "$COMP" in *916) OUT="${OUT}_916";; esac; mkdir -p "$OUT"   # 9:16 renders (comp LE916) in their own folder
BUNDLE="${BUNDLE:-$SONG/build/living_earth/bundle}"   # BUNDLE=<dir> to render from another bundle (e.g. bundle916, which has the LE916 comp)
if [ ! -d "$BUNDLE" ]; then (cd "$REM" && npx remotion bundle src/le/index.tsx --out-dir "$BUNDLE" --public-dir public --log=error); fi
PROPS="{\"slate\":false,\"le\":\"$SHOT\"}"
if [ "$MODE" = "stills" ]; then
  D="$OUT/stills_$(date +%H%M%S)"; mkdir -p "$D"
  TS=("$@"); [ ${#TS[@]} -eq 0 ] && TS=($(awk -v a=$FIRST -v b=$LAST 'BEGIN{for(i=0;i<5;i++) printf "%.2f ", (a+(b-a)*i/4)/30}'))
  for t in "${TS[@]}"; do
    f=$(awk -v t=$t 'BEGIN{printf "%d", t*30+0.5}')
    (cd "$ROOT" && tools/gpuq.sh ysyns-le bash -c "cd '$REM' && npx remotion still '$BUNDLE' $COMP '$D/${COMP}_f$(printf %05d $f).png' --frame=$f --props='$PROPS' --gl=angle --log=error")
  done
  echo "stills in $D"; exit 0
fi
CH=150
for ((a=FIRST; a<=LAST; a+=CH)); do
  b=$((a+CH-1)); [ $b -gt $LAST ] && b=$LAST
  have=$(ls "$OUT" 2>/dev/null | awk -v a=$a -v b=$b '/^f[0-9]+\.png$/ { n=substr($0,2,5)+0; if (n>=a && n<=b) c++ } END { print c+0 }')
  if [ "$have" != "$((b-a+1))" ]; then
    echo "[chunk] $a-$b queued $(date +%T)"
    (cd "$ROOT" && tools/gpuq.sh ysyns-le bash -c "cd '$REM' && npx remotion render '$BUNDLE' $COMP '$OUT/' --sequence --image-format=png --frames=$a-$b --props='$PROPS' --gl=angle --concurrency=${CONC:-4} --timeout=120000 --log=error")
    # remotion's --sequence names frames element-NNNNN.png with the ABSOLUTE frame number (checked Nov 7, le_gpu: LE1's f1479 came out
    # as element-01479; the old "+a" doubled the numbers; LE0 hid it because its range starts at 0): rename to f<song frame>.png
    for p in "$OUT"/element-*.png; do [ -e "$p" ] || continue; n=$(basename "$p" .png); n=$((10#${n#element-})); [ $n -lt $a ] && n=$((a+n)); mv "$p" "$OUT/f$(printf %05d $n).png"; done
  fi
done
ffmpeg -y -v error -framerate 30 -start_number $FIRST -i "$OUT/f%05d.png" -frames:v $((LAST-FIRST+1)) -c:v libx264 -crf 16 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -movflags +faststart "$OUT/${SHOT}_silent.mp4"
echo "done: $OUT ($FIRST-$LAST) -> ${SHOT}_silent.mp4"
