#!/bin/zsh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:/opt/homebrew/share/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
source "$REPO_ROOT/.venv/bin/activate"

OUTPUT_DIR="$REPO_ROOT/output/prototype"
FRAME_DIR="$OUTPUT_DIR/frames"
VIDEO_DIR="$OUTPUT_DIR/video"
mkdir -p "$FRAME_DIR" "$VIDEO_DIR"

render_frame() {
  local scene_name="$1"
  local output_name="$2"
  manim -qk -s -r 790,639 --disable_caching src/prototype-manimce/revolve-slice-prototype.py "$scene_name"
  local source_file
  source_file="$(ls -t media/images/revolve-slice-prototype/${scene_name}*.png | head -n 1)"
  cp "$source_file" "$FRAME_DIR/${output_name}"
}

render_frame Frame01 frame_01.png
render_frame Frame02 frame_02.png
render_frame Frame03 frame_03.png
render_frame Frame04 frame_04.png

manim -qk -r 790,640 --fps 24 --disable_caching src/prototype-manimce/revolve-slice-prototype.py RevolveSliceAnimation
video_source="$(ls -t media/videos/revolve-slice-prototype/640p24/RevolveSliceAnimation*.mp4 | head -n 1)"
cp "$video_source" "$VIDEO_DIR/revolve-slice-prototype.mp4"

python src/prototype-manimce/make-contact-sheet.py
