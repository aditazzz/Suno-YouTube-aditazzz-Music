#!/bin/bash
# One run of the 3D him, one format, end to end: Blender RGBA through tools/gpuq.sh (collision gate included) -> post -> manifest.
#   living_earth/him3d/him_run.sh <run> <169|916> <version tag> [him_slots options, e.g. first=.. last=..]
# Frames: build/him_wire/rgba/<run>_<ver>/<fmt>/him_#####.png (resumable); layer: remotion/public/le/him/<run>_<ver>/<fmt>/.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/../.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"
RUN="$1"; FMT="$2"; VER="$3"; shift 3; OUT="$SONG/build/him_wire/rgba/${RUN}_$VER/$FMT"; mkdir -p "$OUT" "$SONG/build/him_wire/logs"
LOG="$SONG/build/him_wire/logs/${RUN}_${VER}_$FMT.log"
echo "[him_run] $RUN $FMT $VER start $(date +%T)" | tee -a "$LOG"
(cd "$ROOT" && tools/gpuq.sh "him-$RUN-$FMT" /Applications/Blender.app/Contents/MacOS/Blender -b "$HERE/him.blend" --python "$HERE/him_slots.py" -- "$RUN" "$FMT" "$OUT" "$@") >> "$LOG" 2>&1 || { echo "[him_run] RENDER FAILED, see $LOG"; exit 1; }
grep -E "\[collide\]|Traceback|Error" "$LOG" | tail -3 || true
"$ROOT/.venv/bin/python" "$HERE/him_post.py" "$RUN" "$FMT" "$OUT" "$VER" | tee -a "$LOG"
echo "[him_run] $RUN $FMT $VER done $(date +%T) frames=$(ls "$OUT" | grep -c 'him_.*png')" | tee -a "$LOG"
