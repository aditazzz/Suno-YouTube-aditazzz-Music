#!/bin/bash
# my own bundle with EVERYTHING posted (staging), without touching what the other workers' bundles see for more than the bundle time:
#   living_earth/him3d/him_preview.sh            -> build/him_wire/bundle ; then the live manifest is put back
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/../.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"
"$ROOT/.venv/bin/python" "$HERE/him_post.py" --manifest stage
BUNDLE="$SONG/build/him_wire/bundle" "$SONG/living_earth/le_render.sh" bundle || true
"$ROOT/.venv/bin/python" "$HERE/him_post.py" --manifest live
