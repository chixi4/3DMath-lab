#!/bin/zsh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

source "$REPO_ROOT/.venv/bin/activate"

RAW_DIR="$REPO_ROOT/output/showcase-previews-raw"
PREVIEW_DIR="$REPO_ROOT/output/showcase-previews-16x9"
CHECK_DIR="$REPO_ROOT/output/preview-checks"
THEME="${MANIM_THEME:-light}"

rm -rf "$RAW_DIR" "$PREVIEW_DIR"
mkdir -p "$RAW_DIR" "$PREVIEW_DIR" "$CHECK_DIR"

scenes=(
  ShowcasePreview01
  ShowcasePreview02
  ShowcasePreview03
  ShowcasePreview04
  ShowcasePreview05
  ShowcasePreview06
)

outputs=(
  preview_01.png
  preview_02.png
  preview_03.png
  preview_04.png
  preview_05.png
  preview_06.png
)

for i in {1..6}; do
  scene_name="${scenes[$i]}"
  output_name="${outputs[$i]}"

  MANIM_THEME="$THEME" manim -qk -s -r 1280,720 --disable_caching src/prototype-manimce/revolve-slice-prototype.py "$scene_name"
  source_file="$(ls -t media/images/revolve-slice-prototype/${scene_name}*.png | head -n 1)"
  cp "$source_file" "$RAW_DIR/$output_name"
  cp "$source_file" "$PREVIEW_DIR/$output_name"
done

ffmpeg -y \
  -i "$PREVIEW_DIR/preview_01.png" \
  -i "$PREVIEW_DIR/preview_02.png" \
  -i "$PREVIEW_DIR/preview_03.png" \
  -i "$PREVIEW_DIR/preview_04.png" \
  -i "$PREVIEW_DIR/preview_05.png" \
  -i "$PREVIEW_DIR/preview_06.png" \
  -filter_complex "xstack=inputs=6:layout=0_0|1280_0|2560_0|0_720|1280_720|2560_720:fill=black" \
  -frames:v 1 \
  -update 1 \
  "$CHECK_DIR/showcase_camera_6up_16x9.png" \
  >/dev/null 2>&1
