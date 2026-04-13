#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/reference}"
OUTPUT_NAME="${1:-sqrtx-reference-black-1080p60}"
CONFIG_FILE_PATH="${CONFIG_FILE_PATH:-$REPO_ROOT/config/manimgl-60fps.yml}"

mkdir -p "$OUTPUT_DIR"

cmd=(
  "$REPO_ROOT/.venv-manimgl/bin/manimgl"
  "$REPO_ROOT/src/reference-animation/sqrtx_full_rotation.py"
  SqrtXReferenceRotation
  -w
  --hd
  --file_name "$OUTPUT_NAME"
  --video_dir "$OUTPUT_DIR"
)

if [ -n "$CONFIG_FILE_PATH" ]; then
  cmd+=(--config_file "$CONFIG_FILE_PATH")
fi

"${cmd[@]}"
