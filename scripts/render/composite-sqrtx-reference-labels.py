#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "output" / "reference"
REFERENCE_LABEL_LAYOUTS_FILE = REPO_ROOT / "config" / "reference-label-layouts.json"
FRAME_HEIGHT = 8.0
REFERENCE_FOCAL_DISTANCE = 100.0
REFERENCE_THETA_OFFSET = 90.0
REFERENCE_WORLD_ORIGIN_SHIFT = np.array([0.0, 0.0, -1.0], dtype=float)
REFERENCE_WORLD_SCALE = np.array([1.86, 1.86, 1.86], dtype=float)
X_AXIS_MAX = 4.25
Y_AXIS_MAX = 2.55
Z_AXIS_MAX = 2.0
LABEL_COLOR = (255, 255, 255, 255)
LABEL_SUPERSAMPLE = 4
BASE_PRESET_HEIGHT = 2160.0
DEFAULT_FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Supplemental/STIXTwoText-Italic.ttf"),
    Path("/System/Library/Fonts/Supplemental/STIXGeneralItalic.otf"),
    Path("/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"),
)


@dataclass(frozen=True)
class CameraPreset:
    phi: float
    theta: float
    gamma: float
    zoom: float
    x_outward_px: float
    x_normal_px: float
    y_outward_px: float
    y_normal_px: float
    z_outward_px: float
    z_normal_px: float
    label_height_px: int


PRESETS: dict[str, CameraPreset] = {
    "phi30": CameraPreset(
        phi=30.0,
        theta=-45.0,
        gamma=0.0,
        zoom=0.50,
        x_outward_px=30.0,
        x_normal_px=0.0,
        y_outward_px=18.0,
        y_normal_px=16.0,
        z_outward_px=30.0,
        z_normal_px=0.0,
        label_height_px=130,
    ),
    "phi70": CameraPreset(
        phi=70.0,
        theta=-45.0,
        gamma=0.0,
        zoom=0.50,
        x_outward_px=28.0,
        x_normal_px=0.0,
        y_outward_px=22.0,
        y_normal_px=20.0,
        z_outward_px=28.0,
        z_normal_px=0.0,
        label_height_px=130,
    ),
}


def probe_video_metadata(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "default=nw=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return int(values["width"]), int(values["height"])


def resolve_font_path() -> Path:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No usable font file found for sqrt(x) reference labels.")


@lru_cache(maxsize=1)
def load_saved_layouts() -> dict[str, dict[str, object]]:
    if not REFERENCE_LABEL_LAYOUTS_FILE.exists():
        return {}

    payload = json.loads(REFERENCE_LABEL_LAYOUTS_FILE.read_text(encoding="utf-8"))
    raw_presets = payload.get("presets")
    if not isinstance(raw_presets, dict):
        return {}

    normalized: dict[str, dict[str, object]] = {}
    for preset_name, raw_preset in raw_presets.items():
        if not isinstance(raw_preset, dict):
            continue
        raw_labels = raw_preset.get("labels")
        if not isinstance(raw_labels, dict):
            continue

        labels: dict[str, tuple[float, float]] = {}
        for axis_name in ("x", "y", "z"):
            raw_label = raw_labels.get(axis_name)
            if not isinstance(raw_label, dict):
                break
            try:
                x_coord = float(raw_label.get("x"))
                y_coord = float(raw_label.get("y"))
            except (TypeError, ValueError):
                break
            if not (math.isfinite(x_coord) and math.isfinite(y_coord)):
                break
            labels[axis_name] = (x_coord, y_coord)
        if len(labels) != 3:
            continue

        try:
            base_width = int(raw_preset.get("baseWidth"))
            base_height = int(raw_preset.get("baseHeight"))
            label_height_px = float(raw_preset.get("labelHeightPx"))
        except (TypeError, ValueError):
            continue

        if base_width <= 0 or base_height <= 0 or label_height_px <= 0.0:
            continue

        normalized[preset_name] = {
            "baseWidth": base_width,
            "baseHeight": base_height,
            "labelHeightPx": label_height_px,
            "labels": labels,
        }

    return normalized


def to_world(x_ref: float, y_ref: float, z_ref: float) -> np.ndarray:
    return REFERENCE_WORLD_ORIGIN_SHIFT + np.array(
        [
            REFERENCE_WORLD_SCALE[0] * x_ref,
            -REFERENCE_WORLD_SCALE[2] * z_ref,
            REFERENCE_WORLD_SCALE[1] * y_ref,
        ],
        dtype=float,
    )


def project_point(
    point: np.ndarray,
    *,
    phi: float,
    theta: float,
    gamma: float,
    zoom: float,
    width: int,
    height: int,
) -> tuple[float, float]:
    aspect_ratio = width / max(height, 1)
    frame_width = FRAME_HEIGHT * aspect_ratio
    scale = 1.0 / max(zoom, 1e-8)

    orientation = Rotation.from_euler(
        "zxz",
        [gamma, phi, theta + REFERENCE_THETA_OFFSET],
        degrees=True,
    )
    inverse_rotation = orientation.as_matrix().T
    shifted = np.array(point, dtype=float)
    fixed = (inverse_rotation @ shifted) / scale

    x_clip = fixed[0] * (2.0 / frame_width)
    y_clip = fixed[1] * (2.0 / FRAME_HEIGHT)
    z_clip = (inverse_rotation @ shifted)[2] / REFERENCE_FOCAL_DISTANCE
    w_clip = 1.0 - z_clip

    ndc_x = x_clip / w_clip
    ndc_y = y_clip / w_clip
    pixel_x = (ndc_x + 1.0) * 0.5 * width
    pixel_y = (1.0 - ndc_y) * 0.5 * height
    return float(pixel_x), float(pixel_y)


def render_label_glyph(
    text: str,
    *,
    target_height_px: int,
    font_path: Path,
) -> Image.Image:
    supersampled_height = max(8, int(round(target_height_px * LABEL_SUPERSAMPLE)))
    font_size = supersampled_height * 3
    font = ImageFont.truetype(str(font_path), size=font_size)
    mask = Image.new("L", (font_size * 4, font_size * 4), 0)
    draw = ImageDraw.Draw(mask)
    anchor = (font_size, font_size)
    draw.text(anchor, text, font=font, fill=255)
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError(f"Could not render label glyph for {text!r}")

    glyph_mask = mask.crop(bbox)
    target_supersampled_height = supersampled_height
    target_supersampled_width = max(
        1,
        int(round(glyph_mask.width * (target_supersampled_height / max(glyph_mask.height, 1)))),
    )
    glyph_mask = glyph_mask.resize(
        (target_supersampled_width, target_supersampled_height),
        resample=Image.Resampling.LANCZOS,
    )
    glyph_mask = glyph_mask.resize(
        (
            max(1, int(round(target_supersampled_width / LABEL_SUPERSAMPLE))),
            max(1, int(round(target_supersampled_height / LABEL_SUPERSAMPLE))),
        ),
        resample=Image.Resampling.LANCZOS,
    )
    glyph = Image.new("RGBA", glyph_mask.size, LABEL_COLOR)
    glyph.putalpha(glyph_mask)
    return glyph


def normalize_2d(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-8:
        return np.array([0.0, -1.0], dtype=float)
    return vector / norm


def anchor_top_left(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord)), int(round(y_coord))


def anchor_top_right(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord - glyph.width)), int(round(y_coord))


def anchor_bottom_center(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord - glyph.width / 2.0)), int(round(y_coord - glyph.height))


def anchor_bottom_left(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord)), int(round(y_coord - glyph.height))


def anchor_bottom_right(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord - glyph.width)), int(round(y_coord - glyph.height))


def anchor_center(anchor_point: tuple[float, float], glyph: Image.Image) -> tuple[int, int]:
    x_coord, y_coord = anchor_point
    return int(round(x_coord - (glyph.width / 2.0))), int(round(y_coord - (glyph.height / 2.0)))


def build_overlay(
    *,
    preset_name: str,
    preset: CameraPreset,
    width: int,
    height: int,
    font_path: Path,
) -> Image.Image:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    saved_layout = load_saved_layouts().get(preset_name)
    scale = height / BASE_PRESET_HEIGHT

    if saved_layout is not None:
        base_width = int(saved_layout["baseWidth"])
        base_height = int(saved_layout["baseHeight"])
        layout_scale = height / max(base_height, 1)
        glyphs = {
            axis_name: render_label_glyph(
                axis_name,
                target_height_px=max(12, int(round(float(saved_layout["labelHeightPx"]) * layout_scale))),
                font_path=font_path,
            )
            for axis_name in ("x", "y", "z")
        }
        for axis_name in ("x", "y", "z"):
            saved_x, saved_y = saved_layout["labels"][axis_name]
            center_x = float(saved_x) * width / max(base_width, 1)
            center_y = float(saved_y) * height / max(base_height, 1)
            glyph = glyphs[axis_name]
            top_left = anchor_center((center_x, center_y), glyph)
            overlay.alpha_composite(glyph, dest=top_left)
        return overlay

    origin_screen = np.array(
        project_point(
            to_world(0.0, 0.0, 0.0),
            phi=preset.phi,
            theta=preset.theta,
            gamma=preset.gamma,
            zoom=preset.zoom,
            width=width,
            height=height,
        ),
        dtype=float,
    )
    endpoints = {
        "x": to_world(X_AXIS_MAX, 0.0, 0.0),
        "y": to_world(0.0, Y_AXIS_MAX, 0.0),
        "z": to_world(0.0, 0.0, Z_AXIS_MAX),
    }
    placements = {
        "x": (preset.x_outward_px, preset.x_normal_px, anchor_bottom_left),
        "y": (preset.y_outward_px, preset.y_normal_px, anchor_bottom_center),
        "z": (preset.z_outward_px, preset.z_normal_px, anchor_bottom_right),
    }

    glyphs = {
        axis_name: render_label_glyph(
            axis_name,
            target_height_px=max(12, int(round(preset.label_height_px * scale))),
            font_path=font_path,
        )
        for axis_name in ("x", "y", "z")
    }

    for axis_name in ("x", "y", "z"):
        endpoint = np.array(
            project_point(
                endpoints[axis_name],
                phi=preset.phi,
                theta=preset.theta,
                gamma=preset.gamma,
                zoom=preset.zoom,
                width=width,
                height=height,
            ),
            dtype=float,
        )
        direction = normalize_2d(endpoint - origin_screen)
        normal = np.array([-direction[1], direction[0]], dtype=float)
        outward_px, normal_px, anchor_fn = placements[axis_name]
        anchor_point = endpoint + scale * ((outward_px * direction) + (normal_px * normal))
        glyph = glyphs[axis_name]
        top_left = anchor_fn((float(anchor_point[0]), float(anchor_point[1])), glyph)
        overlay.alpha_composite(glyph, dest=top_left)

    return overlay


def composite_still(input_path: Path, output_path: Path, overlay: Image.Image) -> None:
    base = Image.open(input_path).convert("RGBA")
    result = Image.alpha_composite(base, overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)


def composite_video(input_path: Path, output_path: Path, overlay: Image.Image) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sqrtx_reference_overlay_") as temp_dir_name:
        overlay_path = Path(temp_dir_name) / "overlay.png"
        overlay.save(overlay_path)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-i",
                str(overlay_path),
                "-filter_complex",
                "overlay=0:0:format=auto",
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "12",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay crisp 2D x/y/z labels onto sqrt(x) reference renders.")
    parser.add_argument("--input", required=True, type=Path, help="Input still image or video.")
    parser.add_argument("--output", required=True, type=Path, help="Output still image or video.")
    parser.add_argument(
        "--preset",
        required=True,
        choices=sorted(PRESETS.keys()),
        help="Fixed-camera label placement preset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    preset = PRESETS[args.preset]
    font_path = resolve_font_path()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        with Image.open(input_path) as image:
            width, height = image.size
        overlay = build_overlay(
            preset_name=args.preset,
            preset=preset,
            width=width,
            height=height,
            font_path=font_path,
        )
        composite_still(input_path, output_path, overlay)
        return

    width, height = probe_video_metadata(input_path)
    overlay = build_overlay(
        preset_name=args.preset,
        preset=preset,
        width=width,
        height=height,
        font_path=font_path,
    )
    composite_video(input_path, output_path, overlay)


if __name__ == "__main__":
    main()
