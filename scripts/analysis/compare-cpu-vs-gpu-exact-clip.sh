#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

source "$REPO_ROOT/.venv/bin/activate"

THEME="${MANIM_THEME:-light}"
FRAME_SIZE="${FRAME_SIZE:-1280,720}"
SAMPLE_TIMES="${SAMPLE_TIMES:-0.000000000000,0.120000000000,1.920000000000,6.500000000000,8.980000000000,12.240000000000,16.840000000000}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/output/analysis/cpu-gpu-exact-clip-compare}"

"$REPO_ROOT/.venv/bin/python" "$SCRIPT_DIR/batch-compare-exact-clip.py" \
  --theme "$THEME" \
  --frame-size "$FRAME_SIZE" \
  --sample-times "$SAMPLE_TIMES" \
  --out-dir "$OUT_DIR"
