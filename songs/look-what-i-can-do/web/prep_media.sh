#!/bin/bash
# Footage for the 3D film: clip atlases (16 clips per texture, 15 fps, 8 s loops) and hero sequences (30 fps).
set -e
C="/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do/clips"
A="/home/claude/aditazzz/suno-youtube-aditazzz-music/music/Look What I Can Do/assets"
M="$(dirname "$0")/media"
atlas() {  # name cols rows cw ch clip...
  local name=$1 cols=$2 rows=$3 cw=$4 ch=$5; shift 5; local ins=() fl="" lay="" i=0
  for c in "$@"; do ins+=(-i "$C/$c"); fl+="[$i:v]trim=0:8,setpts=PTS-STARTPTS,fps=15,crop=iw:ih*0.86:0:0,scale=${cw}:${ch}:force_original_aspect_ratio=increase,crop=${cw}:${ch},pad=$((cw+4)):$((ch+4)):2:2:black[v$i];"; lay+="[v$i]"; i=$((i+1)); done
  local xs=""; for ((k=0; k<i; k++)); do x=$(( (k % cols) * (cw + 4) )); y=$(( (k / cols) * (ch + 4) )); xs+="${x}_${y}|"; done
  mkdir -p "$M/$name"
  ffmpeg -v error -y "${ins[@]}" -filter_complex "${fl}${lay}xstack=inputs=$i:layout=${xs%|}:fill=black[o]" -map "[o]" -frames:v 120 -q:v 4 "$M/$name/%03d.jpg"
  echo "$name $(ls "$M/$name" | wc -l) frames"
}
hero() {  # name clip w h trim
  mkdir -p "$M/$1"
  ffmpeg -v error -y -i "$C/$2" -t 8 -vf "fps=30,crop=iw:ih*(1-$5):0:0,scale=$3:$4:force_original_aspect_ratio=increase,crop=$3:$4" -q:v 3 "$M/$1/%03d.jpg"
  echo "$1 $(ls "$M/$1" | wc -l) frames"
}
atlas H1 4 4 480 270 ai-sycophant_1.mp4 asking-for-a-friend_0.mp4 deployed-on-a-friday_0.mp4 fangs-for-asking_0.mp4 i-have-a-blocker_1.mp4 rage-against-the-machine-learning_0.mp4 snowflake-undrop_0.mp4 spinning-cursor_1.mp4 take-it-offline_0.mp4 ted-talk-screenlife_1.mp4 ted-talk_1.mp4 the-promptress_1.mp4 thirsty-the-data-center-next-door_1.mp4 vacation-to-my-bed_0.mp4 deployed-on-a-friday-fable_0.mp4 allow-fangs-for-asking_s0.mp4
atlas H2 4 4 480 270 ai-sycophant_0.mp4 asking-for-a-friend_1.mp4 deployed-on-a-friday_1.mp4 fangs-for-asking_1.mp4 i-have-a-blocker_0.mp4 rage-against-the-machine-learning_1.mp4 snowflake-undrop_1.mp4 spinning-cursor_0.mp4 take-it-offline_1.mp4 ted-talk-screenlife_0.mp4 ted-talk_0.mp4 the-promptress_0.mp4 thirsty-the-data-center-next-door_0.mp4 vacation-to-my-bed_1.mp4 deployed-on-a-friday-fable_1.mp4 ai-sycophant_1.mp4
atlas V1 8 2 270 480 ai-slop-city_s0.mp4 ai-sycophant-fable_0.mp4 autocomplete_0.mp4 eleven-kept-going_0.mp4 git-blame-country_0.mp4 git-blame_0.mp4 graceful-shutdown-opus_0.mp4 great-idea-ted_0.mp4 mirror-comments_0.mp4 mirror-vanity_0.mp4 omg-agents-swarm_0.mp4 omg-agents-walls_0.mp4 please-hold_s0.mp4 ragnarok-or-reach-for-mars_s0.mp4 rate-limited_0.mp4 tech-debt_0.mp4
atlas V2 8 2 270 480 ai-slop-city_s1.mp4 ai-sycophant-fable_1.mp4 autocomplete_1.mp4 eleven-kept-going_1.mp4 git-blame-country_1.mp4 git-blame_1.mp4 graceful-shutdown-opus_1.mp4 great-idea-ted_1.mp4 mirror-comments_1.mp4 mirror-vanity_1.mp4 omg-agents-swarm_1.mp4 omg-agents-walls_1.mp4 please-hold_s1.mp4 ragnarok-or-reach-for-mars_s1.mp4 rate-limited_1.mp4 tech-debt_1.mp4
hero ted0 ted-talk_0.mp4 960 540 0.18
hero tedcharts ted-talk-charts_0.mp4 960 540 0.18
hero tedshadow ted-talk-shadow-play_0.mp4 960 540 0.18
hero tedscreen ted-talk-screenlife_0.mp4 960 540 0.18
hero tedstep ted-talk-stepping-back_0.mp4 960 540 0.18
hero rage rage-against-the-machine-learning_0.mp4 960 540 0.14
hero blocker i-have-a-blocker_1.mp4 960 540 0.14
mkdir -p "$M/phone"; ffmpeg -v error -y -i "$A/chatgpt.mp4" -vf "fps=30,scale=540:-2" -q:v 3 "$M/phone/%03d.jpg"; echo "phone $(ls "$M/phone" | wc -l)"
echo PREP DONE
