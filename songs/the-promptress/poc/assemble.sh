#!/bin/bash
# join the 27 chunks (stream copy, no re-encode) and lay the full song under them: AAC 320k at 48 kHz
cd "$(dirname "$0")/.."; C=build/film/chunks; OUT="${1:-build/film/The Promptress - Official Music Video.mp4}"
WAV="${WAV:-music/Abracadabra Autocomplete (clean).wav}"   # the song (not in the repo)
L=$(for k in $(seq 0 26); do printf "$C/chunk_%02d.ts|" $k; done); L=${L%|}
ffmpeg -v error -y -i "concat:$L" -i "$WAV" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -ac 2 \
  -metadata title="The Promptress" -metadata artist="aditazzz" "$OUT" && echo "assembled: $OUT"
