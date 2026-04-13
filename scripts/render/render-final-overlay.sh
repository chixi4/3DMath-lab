#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/final}"
SOURCE_VIDEO="${SOURCE_VIDEO:-$OUTPUT_DIR/volume-of-revolution-source-1080p60.mp4}"
OUTPUT_VIDEO="${OUTPUT_VIDEO:-$OUTPUT_DIR/volume-of-revolution-overlay-1080p60.mp4}"
CONTACT_SHEET="${CONTACT_SHEET:-$OUTPUT_DIR/volume-of-revolution-overlay-contact.png}"
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"

if [ ! -x "$PYTHON_BIN" ] && [ -x "/Users/yuookie/Documents/dev/manim/.venv/bin/python" ]; then
  PYTHON_BIN="/Users/yuookie/Documents/dev/manim/.venv/bin/python"
fi

mkdir -p "$OUTPUT_DIR"

MANIM_THEME=dark \
QUALITY_FLAG="${QUALITY_FLAG:---hd}" \
CONFIG_FILE_PATH="${CONFIG_FILE_PATH:-$REPO_ROOT/config/manimgl-60fps.yml}" \
"$REPO_ROOT/scripts/render/render-final-source.sh" "$(basename "${SOURCE_VIDEO%.mp4}")"

LINKED_RECTANGLES_THEME=dark \
LINKED_RECTANGLES_USE_PLANE_TRACKING=0 \
LINKED_RECTANGLES_KEEP_OUT_FRAMES=0 \
LINKED_RECTANGLES_SOURCE="$SOURCE_VIDEO" \
LINKED_RECTANGLES_OUTPUT="$OUTPUT_VIDEO" \
LINKED_RECTANGLES_CONTACT="$CONTACT_SHEET" \
"$PYTHON_BIN" "$REPO_ROOT/src/final-animation/rectangle-overlay-compositor.py"
