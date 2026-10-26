#!/bin/bash
# build full vertical + clips once all chunks exist
cd "$(dirname "$0")"   # repo layout (the chat used an absolute path)
ls vchunks/v_*.mp4 | grep -v tmp | sort | sed "s/^/file '/; s/$/'/" > vlist.txt
ffmpeg -v error -y -f concat -safe 0 -i vlist.txt -c copy v_noaudio.mp4
ffmpeg -v error -y -i v_noaudio.mp4 -i audio_pad.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "out/AI Sycophant (RLHF) - Instagram 9x16 full.mp4"
clip () { # name start end
  d=$(python3 -c "print(round($3-$2,3))"); fo=$(python3 -c "print(round($3-$2-0.6,3))"); ao=$(python3 -c "print(round($3-$2-1.2,3))")
  ffmpeg -v error -y -ss $2 -t $d -i v_noaudio.mp4 -ss $2 -t $d -i audio_pad.wav -map 0:v -map 1:a \
    -vf "fade=t=in:st=0:d=0.25,fade=t=out:st=$fo:d=0.6" -af "afade=t=in:st=0:d=0.2,afade=t=out:st=$ao:d=1.2" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart "out/$1.mp4"
}
clip "AI Sycophant - Short 1 (chorus, 50s)" 49.6 99.65
clip "AI Sycophant - Short 2 (bridge to final chorus, 58s)" 172.2 230.45
clip "AI Sycophant - Reel 1 (kill her, 17s)" 13.9 31.0
clip "AI Sycophant - Reel 2 (chorus, 30s)" 61.6 91.25
clip "AI Sycophant - Reel 3 (bridge, 29s)" 172.2 201.3
ls -la out/
