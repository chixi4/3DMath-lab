from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORT_PATH = SCRIPT_DIR / "batch-render-support.py"
SUPPORT_SPEC = importlib.util.spec_from_file_location("batch_render_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise ImportError(f"Could not load batch-render-support.py from {SUPPORT_PATH}")
batch_render_support = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(batch_render_support)

FrameRenderer = batch_render_support.FrameRenderer
load_scene_module = batch_render_support.load_scene_module
parse_resolution = batch_render_support.parse_resolution
reset_directory = batch_render_support.reset_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", default="light")
    parser.add_argument("--frame-size", default="1280,720")
    parser.add_argument("--sample-times", required=True)
    parser.add_argument("--out-dir", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pixel_width, pixel_height = parse_resolution(args.frame_size)
    sample_times = [value.strip() for value in args.sample_times.split(",") if value.strip()]
    out_dir = Path(args.out_dir).resolve()
    cpu_dir = out_dir / "cpu"
    gpu_dir = out_dir / "gpu"
    diff_dir = out_dir / "diff"
    scene_module = load_scene_module(args.theme)
    exact_clip_frame = scene_module.ExactClipFrame
    canonical_frame_playback = scene_module.CanonicalFramePlayback

    reset_directory(out_dir)
    cpu_dir.mkdir(parents=True, exist_ok=True)
    gpu_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    cairo_renderer = FrameRenderer("cairo")
    opengl_renderer = FrameRenderer("opengl")
    mismatches: list[tuple[str, str, str | int]] = []

    for index, sample_time in enumerate(sample_times, start=1):
        label = f"sample_{index:02d}"
        cpu_path = cpu_dir / f"{label}.png"
        gpu_path = gpu_dir / f"{label}.png"

        cairo_renderer.render_scene(
            exact_clip_frame,
            cpu_path,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            frame_rate=24,
            env={"MANIM_THEME": args.theme, "MANIM_CLIP_TIME": sample_time},
        )
        opengl_renderer.render_scene(
            canonical_frame_playback,
            gpu_path,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            frame_rate=24,
            env={"MANIM_THEME": args.theme, "MANIM_CANONICAL_FRAME": str(cpu_path)},
        )

        cpu_image = Image.open(cpu_path).convert("RGBA")
        gpu_image = Image.open(gpu_path).convert("RGBA")
        cpu_pixels = np.array(cpu_image)
        gpu_pixels = np.array(gpu_image)

        if cpu_pixels.shape != gpu_pixels.shape:
            mismatches.append((label, sample_time, "shape"))
            continue

        diff_mask = np.any(cpu_pixels != gpu_pixels, axis=2)
        if np.any(diff_mask):
            ImageChops.difference(cpu_image, gpu_image).save(diff_dir / f"{label}.png")
            mismatches.append((label, sample_time, int(np.count_nonzero(diff_mask))))

    if mismatches:
        for label, sample_time, detail in mismatches:
            print(f"MISMATCH {label} t={sample_time} detail={detail}")
        return 1

    for index, sample_time in enumerate(sample_times, start=1):
        print(f"MATCH sample_{index:02d} t={sample_time}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
