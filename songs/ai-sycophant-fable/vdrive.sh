#!/bin/bash
# usage: vdrive.sh worker_index n_workers
cd "$(dirname "$0")"   # repo layout (the chat used an absolute path)
CH=300; NF=7890
i=0
for ((s=0; s<NF; s+=CH)); do
  if (( i % $2 == $1 )); then
    e=$((s+CH)); (( e > NF )) && e=$NF
    f=vchunks/v_$(printf %05d $s).mp4
    if [ ! -f $f.done ]; then
      python3 render.py vrange $s $e $f.tmp.mp4 && mv $f.tmp.mp4 $f && touch $f.done
    fi
  fi
  i=$((i+1))
done
