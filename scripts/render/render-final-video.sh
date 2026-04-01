#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/output/final}"
INPUT_VIDEO="${1:-$OUTPUT_DIR/volume-of-revolution-overlay-1080p60.mp4}"
OUTPUT_VIDEO="${2:-$OUTPUT_DIR/volume-of-revolution-final-1080p60.mp4}"

FREEZE_START="${FREEZE_START:-20.10}"
CLEAR_FRAME_TIME="${CLEAR_FRAME_TIME:-21.80}"
HOLD_BEFORE="${HOLD_BEFORE:-0.30}"
CROSSFADE_DURATION="${CROSSFADE_DURATION:-0.70}"
FINAL_HOLD="${FINAL_HOLD:-1.00}"
CLEAR_FILL_STRENGTH="${CLEAR_FILL_STRENGTH:-0.62}"
CLEAR_LINE_STRENGTH="${CLEAR_LINE_STRENGTH:-0.80}"

PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="${PYTHON:-python3}"
fi

mkdir -p "$OUTPUT_DIR"

if [ ! -f "$INPUT_VIDEO" ]; then
  "$REPO_ROOT/scripts/render/render-final-overlay.sh"
fi

if [ ! -f "$INPUT_VIDEO" ]; then
  echo "Missing input video after overlay render: $INPUT_VIDEO" >&2
  exit 1
fi

FPS="$(
  ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=nw=1 "$INPUT_VIDEO" \
    | awk -F= '/r_frame_rate=/ {print $2}' \
    | awk -F/ 'NF==2 {printf "%.6f", $1 / $2} NF==1 {print $1}'
)"

FREEZE_INPUT_DURATION="$(awk -v a="$HOLD_BEFORE" -v b="$CROSSFADE_DURATION" 'BEGIN {printf "%.3f", a + b}')"
CLEAR_INPUT_DURATION="$(awk -v a="$CROSSFADE_DURATION" -v b="$FINAL_HOLD" 'BEGIN {printf "%.3f", a + b}')"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

FREEZE_FRAME="$TMP_DIR/freeze_frame.png"
CLEAR_FRAME="$TMP_DIR/clear_frame.png"
ENHANCED_CLEAR_FRAME="$TMP_DIR/clear_frame_enhanced.png"

ffmpeg -hide_banner -loglevel error -y -ss "$FREEZE_START" -i "$INPUT_VIDEO" -frames:v 1 "$FREEZE_FRAME"
ffmpeg -hide_banner -loglevel error -y -ss "$CLEAR_FRAME_TIME" -i "$INPUT_VIDEO" -frames:v 1 "$CLEAR_FRAME"

"$PYTHON_BIN" - "$CLEAR_FRAME" "$ENHANCED_CLEAR_FRAME" "$CLEAR_FILL_STRENGTH" "$CLEAR_LINE_STRENGTH" <<'PY'
from __future__ import annotations

import sys
import numpy as np
from PIL import Image, ImageFilter


def smoothstep(values: np.ndarray, edge0: float, edge1: float) -> np.ndarray:
    t = np.clip((values - edge0) / max(edge1 - edge0, 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


src_path, dst_path, fill_strength_text, line_strength_text = sys.argv[1:5]
fill_strength = float(fill_strength_text)
line_strength = float(line_strength_text)

image = Image.open(src_path).convert("RGBA")
rgba = np.asarray(image).astype(np.float32) / 255.0
rgb = rgba[..., :3]

r = rgb[..., 0]
g = rgb[..., 1]
b = rgb[..., 2]
value = rgb.max(axis=2)
min_value = rgb.min(axis=2)
chroma = value - min_value

purple_core = (
    (r > g * 1.02)
    & (b > g * 1.08)
    & (value > 0.08)
    & (chroma > 0.035)
).astype(np.float32)

fill_seed = purple_core * smoothstep(value, 0.06, 0.42) * (1.0 - smoothstep(value, 0.58, 0.92))
line_seed = purple_core * smoothstep(value, 0.16, 0.84)

fill_mask = np.asarray(
    Image.fromarray(np.round(fill_seed * 255.0).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=5.0))
).astype(np.float32) / 255.0
line_mask = np.asarray(
    Image.fromarray(np.round(line_seed * 255.0).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=1.5))
).astype(np.float32) / 255.0

fill_tint = np.array([0.96, 0.52, 0.87], dtype=np.float32)
line_tint = np.array([1.00, 0.92, 0.98], dtype=np.float32)

rgb = rgb * (1.0 + 0.18 * fill_strength * fill_mask[..., None])
rgb = rgb * (1.0 - fill_strength * 0.42 * fill_mask[..., None]) + fill_tint * (fill_strength * 0.42 * fill_mask[..., None])
rgb = rgb * (1.0 - line_strength * 0.56 * line_mask[..., None]) + line_tint * (line_strength * 0.56 * line_mask[..., None])
rgb = np.clip(rgb + line_strength * 0.10 * line_mask[..., None], 0.0, 1.0)

enhanced = np.dstack([rgb, rgba[..., 3]])
Image.fromarray(np.round(enhanced * 255.0).astype(np.uint8), mode="RGBA").save(dst_path)
PY

ffmpeg -hide_banner -loglevel error -y \
  -i "$INPUT_VIDEO" \
  -loop 1 -framerate "$FPS" -t "$FREEZE_INPUT_DURATION" -i "$FREEZE_FRAME" \
  -loop 1 -framerate "$FPS" -t "$CLEAR_INPUT_DURATION" -i "$ENHANCED_CLEAR_FRAME" \
  -filter_complex "\
[0:v]trim=0:${FREEZE_START},setpts=PTS-STARTPTS[head]; \
[1:v]format=rgba[freeze]; \
[2:v]format=rgba[clear]; \
[freeze][clear]xfade=transition=fade:duration=${CROSSFADE_DURATION}:offset=${HOLD_BEFORE},format=yuv420p[tail]; \
[head][tail]concat=n=2:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -r "$FPS" \
  -crf 18 \
  "$OUTPUT_VIDEO"

echo "Wrote $OUTPUT_VIDEO"
