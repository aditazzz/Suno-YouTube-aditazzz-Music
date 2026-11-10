#!/bin/bash
# Living Earth film renders (engine: remotion/src/le/film, see build/le_cut0/ENGINE.md). Every GPU job goes through tools/gpuq.sh.
#   living_earth/le_render.sh bundle                                   (re)bundle the film -> build/le_cut0/bundle (after any code change)
#   living_earth/le_render.sh stills <comp> <outdir> <frame> [...]     quick look-dev stills, one browser (tools/le_stills.mjs)
#   living_earth/le_render.sh cut <comp> <outdir> [first last]         chunked mp4 render (resumable: finished chunks are kept),
#                                                                      joined, muxed with the song -> <outdir>/<name>.mp4
# comps: LivingEarthFilm (2560x1440), LivingEarthFilm916 (1080x1920), LivingEarthFilm720 (1280x720, beat labels on),
#        LivingEarthFilm916-540 (540x960, labels). Env: CHUNK=600 frames, CONC=6 tabs, PROPS='{"labels":false}' to override props,
#        INSERTS="le/inserts/a.mp4 ..." finished clips under remotion/public to show (sections' `inserts`; default: all of
#        public/le/inserts/*.mp4; INSERTS=none = engine only).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"; REM="$SONG/remotion"
BUNDLE="${BUNDLE:-$SONG/build/le_cut0/bundle}"
AUDIO="${AUDIO:-$HOME/Documents/Original Music/You Said You Needed Space (clean).wav}"   # song.yaml audio (her Nov 8 take)
MODE="${1:?bundle|stills|cut}"; shift
mkbundle() { (cd "$REM" && npx remotion bundle src/le/film/index.tsx --out-dir "$BUNDLE" --public-dir public --log=error); }
case "$MODE" in
bundle) mkbundle; echo "bundle: $BUNDLE";;
stills)
  COMP="$1"; OUT="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2; mkdir -p "$OUT"; [ -d "$BUNDLE" ] || mkbundle
  (cd "$ROOT" && tools/gpuq.sh le-stills bash -c "cd '$REM' && node tools/le_stills.mjs '$BUNDLE' $COMP '$OUT' $*");;
cut)
  COMP="$1"; OUT="$(mkdir -p "$2" && cd "$2" && pwd)"; NAME="$(basename "$OUT")"; [ -d "$BUNDLE" ] || mkbundle
  TOTAL=$(cd "$REM" && node -e "const fs=require('fs');const s=fs.readFileSync('src/le/film/timing.gen.ts','utf8');const d=+/\"duration\": ?([0-9.]+)/.exec(s)[1];console.log(Math.round(d*30))")
  FIRST="${3:-0}"; LAST="${4:-$((TOTAL-1))}"; CH="${CHUNK:-600}"; mkdir -p "$OUT/chunks"
  # inserts: default = every clip in remotion/public/le/inserts (INSERTS=none for the engine only, or a list of public/ paths)
  if [ -z "${INSERTS:-}" ]; then INSERTS="$(cd "$REM/public" && ls le/inserts/*.mp4 2>/dev/null | tr '\n' ' ')"; fi
  INS="[]"; if [ -n "$INSERTS" ] && [ "$INSERTS" != none ]; then INS="[$(for x in $INSERTS; do printf '"%s",' "$x"; done | sed 's/,$//')]"; fi
  P="${PROPS:-}"; [ -z "$P" ] && P="{\"inserts\":$INS}"
  for ((a=FIRST; a<=LAST; a+=CH)); do
    b=$((a+CH-1)); [ $b -gt $LAST ] && b=$LAST; f="$OUT/chunks/c_$(printf %05d $a)_$(printf %05d $b).mp4"
    [ -s "$f" ] && { echo "[chunk] $a-$b have"; continue; }
    echo "[chunk] $a-$b $(date +%T)"
    (cd "$ROOT" && tools/gpuq.sh le-cut bash -c "cd '$REM' && npx remotion render '$BUNDLE' $COMP '$f.part.mp4' --frames=$a-$b --codec=h264 --crf=18 --pixel-format=yuv420p --color-space=bt709 --muted --gl=angle --concurrency=${CONC:-6} --props='$P' --log=error && mv '$f.part.mp4' '$f'")
  done
  ls "$OUT"/chunks/c_*.mp4 | sed "s|^|file '|; s|$|'|" > "$OUT/chunks/list.txt"
  ffmpeg -v error -y -f concat -safe 0 -i "$OUT/chunks/list.txt" -an -vf "setpts=N/(30*TB),setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" -fps_mode cfr -r 30 -c:v libx264 -crf 12 -preset fast -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "$OUT/${NAME}_silent.mp4"
  SS=$(awk -v f=$FIRST 'BEGIN{printf "%.4f", f/30}'); DUR=$(awk -v a=$FIRST -v b=$LAST 'BEGIN{printf "%.4f", (b-a+1)/30}')
  ffmpeg -v error -y -i "$OUT/${NAME}_silent.mp4" -ss "$SS" -t "$DUR" -i "$AUDIO" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT/$NAME.mp4"
  echo "done: $OUT/$NAME.mp4";;
esac
