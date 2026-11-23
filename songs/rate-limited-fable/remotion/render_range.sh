#!/bin/bash
# Render a range of the film through the GPU queue (silent; mux the song at the master step).
#   ./render_range.sh 16x9|9x16 <first frame> <last frame> [out.mp4] [name]     (30 fps; the hook = 0 899)
#   PREVIEW=1 for half size (1280x720 / 540x960). Silent: mux the WAV with ffmpeg (see render_animatic.sh). Runs in the foreground of the gpuq call:
#   submit it detached (nohup ./render_range.sh ... &) and check that its log appears in logs/gpuq/.
cd "$(dirname "$0")"; F=${1:?16x9 or 9x16}; A=${2:?first frame}; B=${3:?last frame}
OUT=${4:-../build/codecut/range_${F}_${A}-${B}.mp4}; NAME=${5:-rl_range_${F}_${A}_${B}}
P="\"preview\":$([ -n "$PREVIEW" ] && echo true || echo false),\"noAudio\":true"; MUTE=--muted
python3 tools/build_data.py || exit 1
D=$PWD; ROOT=$(cd ../../.. && pwd)
"$ROOT/tools/gpuq.sh" "$NAME" bash -c "cd '$D' && npx remotion render src/index.ts Film$F '$OUT' --frames=$A-$B $MUTE --props='{$P}' --crf=14 --concurrency=8 --log=error"
