#!/bin/bash
# Run from either Mac checkout. Every call takes the studio GPU queue.
# render_ground.sh SHOT FMT still FRAME [--draft]
# render_ground.sh SHOT FMT clip [--draft]
set -euo pipefail
shot="${1:?br_children|inst|fc_life}"
fmt="${2:?169|916}"
mode="${3:?still|clip}"
shift 3
here="$(cd "$(dirname "$0")" && pwd)"
song="$(cd "$here/../.." && pwd)"
root="$(cd "$song/../.." && pwd)"
out="$song/build/earth_ground"
mkdir -p "$out"
blender="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
ffprobe="${FFPROBE:-ffprobe}"
suffix=""
case "$fmt" in 169) ;; 916) suffix=_916 ;; *) exit 2 ;; esac
name="ground2_${shot}${suffix}${GROUND_VERSION:-}"
case "$mode" in
  still)
    frame="${1:?frame within the insert}"
    shift
    cd "$root"
    tools/gpuq.sh "earth-ground-$shot-$fmt-still" "$blender" -b --factory-startup --python-exit-code 1 --python "$here/render_ground.py" -- "$shot" "$fmt" "$out/${name}_f${frame}.png" --still "$frame" "$@"
    ;;
  clip)
    # Blender versions differ in whether a frame-range suffix is added.
    stage="$(mktemp -d "$out/${name}.XXXXXX")"
    cd "$root"
    tools/gpuq.sh "earth-ground-$shot-$fmt" "$blender" -b --factory-startup --python-exit-code 1 --python "$here/render_ground.py" -- "$shot" "$fmt" "$stage/insert.mp4" "$@"
    files=("$stage"/*.mp4)
    if [ "${#files[@]}" != 1 ] || [ ! -s "${files[0]}" ]; then
      echo "Expected one rendered MP4 in $stage" >&2
      exit 1
    fi
    case "$shot" in
      br_children) frames=72 ;;
      inst) frames=199 ;;
      fc_life) frames=60 ;;
      *) exit 2 ;;
    esac
    actual=$("$ffprobe" -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 "${files[0]}")
    if [ "$actual" != "$frames" ]; then
      echo "$shot: expected $frames frames, got $actual" >&2
      exit 1
    fi
    echo "Checked $actual frames: ${files[0]}"
    if [ "$#" != 0 ]; then
      echo "Draft stays in $stage"
    else
      target="$song/remotion/public/le/inserts/$name.mp4"
      mkdir -p "$(dirname "$target")"
      if [ -e "$target" ]; then
        echo "Existing insert kept at $target. Validated candidate: ${files[0]}" >&2
        exit 1
      fi
      mv "${files[0]}" "$target"
      echo "Insert: $target"
    fi
    ;;
  *) exit 2 ;;
esac
