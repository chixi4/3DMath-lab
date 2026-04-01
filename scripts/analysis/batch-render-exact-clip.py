from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORT_PATH = SCRIPT_DIR / "batch-render-support.py"
SUPPORT_SPEC = importlib.util.spec_from_file_location("batch_render_support", SUPPORT_PATH)
if SUPPORT_SPEC is None or SUPPORT_SPEC.loader is None:
    raise ImportError(f"Could not load batch-render-support.py from {SUPPORT_PATH}")
batch_render_support = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(batch_render_support)

FrameRenderer = batch_render_support.FrameRenderer
encode_video = batch_render_support.encode_video
exact_clip_total_frames = batch_render_support.exact_clip_total_frames
load_scene_module = batch_render_support.load_scene_module
parse_resolution = batch_render_support.parse_resolution
reset_directory = batch_render_support.reset_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renderer", choices=("cairo", "opengl"), required=True)
    parser.add_argument("--theme", default="light")
    parser.add_argument("--frame-size", default="1280,720")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--frame-dir", required=True)
    parser.add_argument("--canonical-dir")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--end-hold-seconds", type=float, default=2.0)
    return parser

def main() -> int:
    args = build_parser().parse_args()
    pixel_width, pixel_height = parse_resolution(args.frame_size)
    frame_dir = Path(args.frame_dir).resolve()
    output_path = Path(args.output_path).resolve()
    canonical_dir = Path(args.canonical_dir).resolve() if args.canonical_dir else None
    scene_module = load_scene_module(args.theme)
    exact_clip_duration = scene_module.EXACT_CLIP_DURATION
    exact_clip_frame = scene_module.ExactClipFrame
    canonical_frame_playback = scene_module.CanonicalFramePlayback

    reset_directory(frame_dir)

    if args.renderer == "opengl":
        if canonical_dir is None:
            raise ValueError("--canonical-dir is required for opengl rendering.")
        reset_directory(canonical_dir)

    cairo_renderer = FrameRenderer("cairo")
    opengl_renderer = FrameRenderer("opengl") if args.renderer == "opengl" else None

    total_frames = exact_clip_total_frames(exact_clip_duration, args.fps)
    for frame_index in range(total_frames):
        clip_time = f"{frame_index / args.fps:.12f}"
        env = {"MANIM_THEME": args.theme, "MANIM_CLIP_TIME": clip_time}

        if args.renderer == "cairo":
            cairo_renderer.render_scene(
                exact_clip_frame,
                frame_dir / f"frame_{frame_index:04d}.png",
                pixel_width=pixel_width,
                pixel_height=pixel_height,
                frame_rate=args.fps,
                env=env,
            )
            continue

        canonical_path = canonical_dir / f"frame_{frame_index:04d}.png"
        cairo_renderer.render_scene(
            exact_clip_frame,
            canonical_path,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            frame_rate=args.fps,
            env=env,
        )
        opengl_renderer.render_scene(
            canonical_frame_playback,
            frame_dir / f"frame_{frame_index:04d}.png",
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            frame_rate=args.fps,
            env={"MANIM_THEME": args.theme, "MANIM_CANONICAL_FRAME": str(canonical_path)},
        )

    encode_video(frame_dir, args.fps, args.end_hold_seconds, output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
