#!/bin/bash
# HD footage for the 3D pages: music/Look What I Can Do/hd/<key>.mp4 -> web/media/hd/<key>/001.jpg ... (960x540, 30 fps)
HD="/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do/hd"; M="$(dirname "$0")/media/hd"
for f in "$HD"/*.mp4; do k=$(basename "$f" .mp4); [ -d "$M/$k" ] && continue; mkdir -p "$M/$k"
  ffmpeg -v error -y -i "$f" -vf "fps=30,scale=960:540" -q:v 3 "$M/$k/%03d.jpg" && echo "$k $(ls "$M/$k" | wc -l)"; done
