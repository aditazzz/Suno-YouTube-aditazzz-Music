#!/bin/bash
# join the six master chunks, lay the subscribe asks on top (the pill after the first chorus, the end card) and add the
# song. Run render_master.sh and `python3 make_overlays.py 2560 1440` first.
# usage: AUD=<the song .wav> ./assemble.sh            (the audio isn't in this repo)
set -e
cd "$(dirname "$0")"
M=master; O=overlay/2560x1440; AUD="${AUD:?set AUD to the song file}"; DEST=final; mkdir -p "$DEST"
printf "file 'part%d.mp4'\n" 1 2 3 4 5 6 > $M/list.txt
[ -s $M/master_silent.mp4 ] || ffmpeg -v error -y -f concat -safe 0 -i $M/list.txt -c copy $M/master_silent.mp4
ffmpeg -v error -y -i $M/master_silent.mp4 \
  -framerate 30 -start_number 1710 -i $O/pill_%05d.png \
  -framerate 30 -start_number 7806 -i $O/end_%05d.png \
  -i "$AUD" \
  -filter_complex "[1:v]setpts=PTS-STARTPTS+57.0/TB[p];[2:v]setpts=PTS-STARTPTS+260.2/TB[e];[0:v][p]overlay=eof_action=pass[a];[a][e]overlay=eof_action=pass,format=yuv420p[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset medium -crf 16 -profile:v high -c:a aac -b:a 320k -ar 48000 -t 266.92 -movflags +faststart \
  "$DEST/Great Idea, Ted - YouTube 16x9.mp4"
echo "done: $DEST/Great Idea, Ted - YouTube 16x9.mp4"
