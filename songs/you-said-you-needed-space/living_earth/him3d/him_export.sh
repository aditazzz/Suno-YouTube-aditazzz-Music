#!/bin/bash
# his per-frame track from the film engine (remotion/src/le/film/him/export.ts): living_earth/him3d/him_export.sh <out dir> [diag]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/../.." && pwd)"; mkdir -p "$SONG/build/him_wire/tmp"
(cd "$SONG/remotion" && node_modules/.bin/esbuild src/le/film/him/export.ts --bundle --platform=node --format=cjs --log-level=error --outfile="$SONG/build/him_wire/tmp/export.cjs")
node "$SONG/build/him_wire/tmp/export.cjs" "$@"
