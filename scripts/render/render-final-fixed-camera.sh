#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/final}"
SOURCE_VIDEO="${SOURCE_VIDEO:-$OUTPUT_DIR/volume-of-revolution-source-fixed-camera-1080p60.mp4}"
OVERLAY_VIDEO="${OVERLAY_VIDEO:-$OUTPUT_DIR/volume-of-revolution-overlay-fixed-camera-1080p60.mp4}"
FINAL_VIDEO="${FINAL_VIDEO:-$OUTPUT_DIR/volume-of-revolution-final-fixed-camera-1080p60.mp4}"
CONTACT_SHEET="${CONTACT_SHEET:-$OUTPUT_DIR/volume-of-revolution-overlay-fixed-camera-contact.png}"

mkdir -p "$OUTPUT_DIR"

export MANIM_THEME="${MANIM_THEME:-dark}"
export QUALITY_FLAG="${QUALITY_FLAG:---hd}"
export CONFIG_FILE_PATH="${CONFIG_FILE_PATH:-$REPO_ROOT/config/manimgl-60fps.yml}"
export VOLUME_OF_REVOLUTION_CAMERA_MODE="${VOLUME_OF_REVOLUTION_CAMERA_MODE:-fixed}"
export LINKED_RECTANGLES_CAMERA_MODE="${LINKED_RECTANGLES_CAMERA_MODE:-fixed}"
export LINKED_RECTANGLES_BUILD_EMPHASIS="${LINKED_RECTANGLES_BUILD_EMPHASIS:-1.35}"
export MANIMGL_BIN="${MANIMGL_BIN:-$REPO_ROOT/.venv-manimgl/bin/manimgl}"
export PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"

if [ ! -x "$MANIMGL_BIN" ] && [ -x "/Users/yuookie/Documents/dev/manim/.venv-manimgl/bin/manimgl" ]; then
  export MANIMGL_BIN="/Users/yuookie/Documents/dev/manim/.venv-manimgl/bin/manimgl"
fi

if [ ! -x "$PYTHON_BIN" ] && [ -x "/Users/yuookie/Documents/dev/manim/.venv/bin/python" ]; then
  export PYTHON_BIN="/Users/yuookie/Documents/dev/manim/.venv/bin/python"
fi

SOURCE_BASE="$(basename "${SOURCE_VIDEO%.mp4}")"
OVERLAY_BASE="$(basename "${OVERLAY_VIDEO%.mp4}")"

OUTPUT_DIR="$OUTPUT_DIR" \
"$REPO_ROOT/scripts/render/render-final-source.sh" "$SOURCE_BASE"

SOURCE_VIDEO="$SOURCE_VIDEO" \
OUTPUT_VIDEO="$OVERLAY_VIDEO" \
CONTACT_SHEET="$CONTACT_SHEET" \
"$REPO_ROOT/scripts/render/render-final-overlay.sh" "$OVERLAY_BASE"

"$REPO_ROOT/scripts/render/render-final-video.sh" "$OVERLAY_VIDEO" "$FINAL_VIDEO"

echo "Wrote $FINAL_VIDEO"
