#!/bin/bash
# encode one 10 s chunk (300 frames) of the film from its frames: final-quality H.264 in MPEG-TS (inline headers, so chunks join cleanly)
# usage: chunk.sh <frames_dir> <k> <out_dir>   (identical on every render node)
D=$1; k=$2; O=$3; S=$((k*300)); N=300; [ $((S+N)) -gt 8052 ] && N=$((8052-S))
ffmpeg -v error -y -framerate 30 -start_number $S -i $D/%05d.jpg -frames:v $N \
  -vf "scale=1920:1080:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset medium -crf 21 -profile:v high -level 4.2 -x264-params keyint=60:min-keyint=30:repeat-headers=1 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -bsf:v h264_mp4toannexb -f mpegts $O/chunk_$(printf %02d $k).ts
