#!/bin/bash
# the YouTube master: the whole song at 2560x1440 on the GPU in six chunks (three at a time),
# with the overlap/collision + sky-word check on every frame
cd "$(dirname "$0")/../web"; export CLEAN=1 GPU=1
C=../clips/master; mkdir -p $C
run() { node render.mjs range 2560 1440 $C/part$1.mp4 $2 $3 30 > $C/part$1.log 2>&1; echo "PART $1 DONE" >> $C/status.log; }
echo START > $C/status.log
(run 1 0 57; run 4 157.6 186.7) &
(run 2 57 113.7; run 5 186.7 226.6) &
(run 3 113.7 157.6; run 6 226.6 266.9) &
wait
echo ALL_DONE >> $C/status.log
