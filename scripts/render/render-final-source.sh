#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/final}"
OUTPUT_NAME="${1:-volume-of-revolution-source-1080p60}"
QUALITY_FLAG="${QUALITY_FLAG:---hd}"
CONFIG_FILE_PATH="${CONFIG_FILE_PATH:-$REPO_ROOT/config/manimgl-60fps.yml}"

mkdir -p "$OUTPUT_DIR"

cmd=(
  "$REPO_ROOT/.venv-manimgl/bin/manimgl"
  "$REPO_ROOT/src/final-animation/revolve-slice-differential.py"
  RevolveSliceShowcaseMGLDifferential
  -w
  "$QUALITY_FLAG"
  --file_name "$OUTPUT_NAME"
  --video_dir "$OUTPUT_DIR"
)

if [ -n "$CONFIG_FILE_PATH" ]; then
  cmd+=(--config_file "$CONFIG_FILE_PATH")
fi

MANIM_THEME="${MANIM_THEME:-dark}" "${cmd[@]}"
