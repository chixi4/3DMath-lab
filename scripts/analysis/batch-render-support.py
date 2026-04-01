from __future__ import annotations

import importlib
import importlib.util
import math
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from manim import RendererType, config, tempconfig
from manim.renderer.opengl_renderer import OpenGLRenderer


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
SCENE_FILE = REPO_ROOT / "src" / "prototype-manimce" / "revolve-slice-prototype.py"
MEDIA_DIR = REPO_ROOT / "media"


def parse_resolution(value: str) -> tuple[int, int]:
    width_text, height_text = [part.strip() for part in value.split(",", 1)]
    width = int(width_text)
    height = int(height_text)
    if width <= 0 or height <= 0:
        raise ValueError("Resolution must be positive.")
    return width, height


def exact_clip_total_frames(duration: float, fps: int) -> int:
    return int(math.ceil(duration * fps))


def reset_directory(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def load_scene_module(theme: str):
    os.environ["MANIM_THEME"] = theme
    module_name = "revolve_slice_prototype"
    existing = sys.modules.get(module_name)
    if existing is not None:
        spec = getattr(existing, "__spec__", None)
        if spec is not None and spec.loader is not None:
            return importlib.reload(existing)
    spec = importlib.util.spec_from_file_location(module_name, SCENE_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load prototype scene from {SCENE_FILE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def encode_video(frame_dir: Path, fps: int, end_hold_seconds: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%04d.png"),
        "-vf",
        f"tpad=stop_mode=clone:stop_duration={end_hold_seconds},format=yuv420p",
        "-an",
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-preset",
        "slow",
        "-crf",
        "18",
        str(output_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@contextmanager
def temporary_env(updates: dict[str, str | None]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class FrameRenderer:
    def __init__(self, renderer_name: str):
        if renderer_name not in {"cairo", "opengl"}:
            raise ValueError(f"Unsupported renderer: {renderer_name}")
        self.renderer_name = renderer_name
        self.opengl_renderer = OpenGLRenderer() if renderer_name == "opengl" else None

    def render_scene(
        self,
        scene_cls,
        output_path: Path,
        *,
        pixel_width: int,
        pixel_height: int,
        frame_rate: int,
        env: dict[str, str | None] | None = None,
    ) -> None:
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        render_config = {
            "renderer": RendererType.OPENGL if self.renderer_name == "opengl" else RendererType.CAIRO,
            "input_file": str(SCENE_FILE),
            "output_file": str(output_path),
            "save_last_frame": True,
            "write_to_movie": False,
            "disable_caching": True,
            "pixel_width": pixel_width,
            "pixel_height": pixel_height,
            "frame_rate": frame_rate,
            "preview": False,
            "show_in_file_browser": False,
            "format": "png",
            "notify_outdated_version": False,
            "media_dir": str(MEDIA_DIR),
        }

        with temporary_env(env or {}):
            with tempconfig(render_config):
                if self.opengl_renderer is not None:
                    scene = scene_cls(self.opengl_renderer)
                    rerun = scene.render()
                    if rerun:
                        raise RuntimeError(f"Unexpected rerun request while rendering {scene_cls.__name__}.")
                    self.opengl_renderer.num_plays = 0
                    self.opengl_renderer.time = 0
                else:
                    scene = scene_cls()
                    scene.render()
