#!/bin/bash
# usage: drive_both.sh projdir worker nworkers NF [waitdir]
P=$1; WK=$2; NW=$3; NF=$4; WAIT=$5; CH=300
if [ -n "$WAIT" ]; then while pgrep -f "drive.sh $WAIT" > /dev/null; do sleep 20; done; fi
mkdir -p $P/chunks
i=0
for ((s=0; s<NF; s+=CH)); do
  if (( i % NW == WK )); then
    e=$((s+CH)); (( e > NF )) && e=$NF
    b=$P/chunks/$(printf %05d $s)
    if [ ! -f $b.done ]; then
      python3 "$(dirname "$0")"/render.py $P both $s $e $b.h.tmp.mp4 $b.v.tmp.mp4 && mv $b.h.tmp.mp4 $P/chunks/range_$(printf %05d $s).mp4 && mv $b.v.tmp.mp4 $P/chunks/vrange_$(printf %05d $s).mp4 && touch $b.done
    fi
  fi
  i=$((i+1))
done
