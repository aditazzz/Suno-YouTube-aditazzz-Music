#!/bin/bash
# The YouTube video from the 16:9 masters: upscaled to 2560x1440 (lanczos and a light unsharp), 16 Mbps, with the song.
#   AUDIO=path/to/song.wav ./assemble.sh [OUT.mp4]          (the audio is not in this repo)
set -e
cd "$(dirname "$0")"
AUDIO=${AUDIO:?set AUDIO to the song file}
OUT=${1:-build/youtube_16x9.mp4}; END=244.8; N=$(python3 -c "print(round($END * 30))")
ffmpeg -v error -y -framerate 30 -start_number 0 -i build/frames_16x9/f_%05d.jpg -t "$END" -i "$AUDIO" \
  -filter_complex "[0:v]trim=end_frame=$N,setpts=PTS-STARTPTS,scale=2560:1440:flags=lanczos,unsharp=3:3:0.3:3:3:0,format=yuv420p[v]" \
  -map "[v]" -map 1:a -c:v libx264 -preset slow -b:v 16M -maxrate 24M -bufsize 32M -pix_fmt yuv420p -r 30 \
  -af "afade=t=out:st=$(python3 -c "print($END - 0.3)"):d=0.3" -c:a aac -b:a 320k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,nb_frames -of compact "$OUT"
