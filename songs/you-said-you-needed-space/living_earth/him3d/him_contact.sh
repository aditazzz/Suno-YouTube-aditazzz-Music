#!/bin/bash
# the film WITH him, stills of every beat in both formats -> one contact sheet (<=1600 px): living_earth/him3d/him_contact.sh <name> [stage|live]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/../.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"; NAME="${1:-contact}"; OUT="$SONG/build/him_wire/contact/$NAME"; mkdir -p "$OUT"
F="${FRAMES:-150 172 188 215 1660 1690 1725 1745 1800 1845 1872 1890 1915 3165 3172 4700 4712 4724 4745 4780 4810 5675 5695 5715 6030 6080 6335 6362 6375}"
export BUNDLE="$SONG/build/him_wire/bundle"
if [ "${2:-stage}" = stage ]; then "$HERE/him_preview.sh" | tail -2; else "$SONG/living_earth/le_render.sh" bundle | tail -1; fi
FM="${FMTS:-169 916}"
[[ "$FM" == *169* ]] && { "$SONG/living_earth/le_render.sh" stills LivingEarthFilm "$OUT/f169" $F 2>&1 | grep -E "rror|finished" || true; }
[[ "$FM" == *916* ]] && { "$SONG/living_earth/le_render.sh" stills LivingEarthFilm916 "$OUT/f916" $F 2>&1 | grep -E "rror|finished" || true; }
PY="$ROOT/.venv/bin/python"; N=$(echo $F | wc -w); C=$(( (N + 3) / 4 )); [ $C -gt 8 ] && C=8
COLS="${COLS:-6}"; TW=$(( 1600 / COLS ))
[[ "$FM" == *169* ]] && "$PY" "$HERE/him_sheet.py" "$OUT/s169.jpg" $COLS $TW "$OUT"/f169/*.png > /dev/null
[[ "$FM" == *916* ]] && "$PY" "$HERE/him_sheet.py" "$OUT/s916.jpg" ${COLS916:-15} $(( 1600 / ${COLS916:-15} )) "$OUT"/f916/*.png > /dev/null
"$PY" - "$OUT" <<'PY'
import cv2, numpy as np, sys
import os
o = sys.argv[1]; ims = [cv2.imread(o + '/' + n) for n in ('s169.jpg', 's916.jpg') if os.path.exists(o + '/' + n)]; W = 1600
pad = lambda im: cv2.copyMakeBorder(im, 0, 4, 0, W - im.shape[1], cv2.BORDER_CONSTANT)
cv2.imwrite(o + '/contact.jpg', np.concatenate([pad(a) for a in ims], axis=0), [cv2.IMWRITE_JPEG_QUALITY, 86]); print(o + '/contact.jpg')
PY
