#!/bin/bash
# usage: drive.sh projdir worker nworkers NF
P=$1; WK=$2; NW=$3; NF=$4; CH=300
mkdir -p $P/chunks
i=0
for mode in range vrange; do
  for ((s=0; s<NF; s+=CH)); do
    if (( i % NW == WK )); then
      e=$((s+CH)); (( e > NF )) && e=$NF
      f=$P/chunks/${mode}_$(printf %05d $s).mp4
      if [ ! -f $f.done ]; then
        python3 "$(dirname "$0")"/render.py $P $mode $s $e $f.tmp.mp4 && mv $f.tmp.mp4 $f && touch $f.done
      fi
    fi
    i=$((i+1))
  done
done
