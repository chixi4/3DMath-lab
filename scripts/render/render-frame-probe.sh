#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/probes}"
OUTPUT_NAME="${1:-volume-of-revolution-frame-probe}"
QUALITY_FLAG="${QUALITY_FLAG:---hd}"
CLIP_TIME="${MANIM_CLIP_TIME:-8.98}"

mkdir -p "$OUTPUT_DIR"

MANIM_CLIP_TIME="$CLIP_TIME" \
"$REPO_ROOT/.venv-manimgl/bin/manimgl" \
  "$REPO_ROOT/src/final-animation/revolve-slice-differential.py" \
  RevolveSliceClipFrameMGLDifferential \
  -w \
  -s \
  "$QUALITY_FLAG" \
  --file_name "$OUTPUT_NAME" \
  --video_dir "$OUTPUT_DIR"
