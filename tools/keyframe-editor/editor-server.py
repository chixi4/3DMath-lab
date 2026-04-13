from __future__ import annotations

import argparse
import ast
import json
import math
import mimetypes
import os
import shutil
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
OUTPUT_ROOT = REPO_ROOT / "output"
SCENE_FILE = REPO_ROOT / "src" / "prototype-manimce" / "revolve-slice-prototype.py"
EDITOR_FILE = ROOT / "label-editor.html"
CAMERA_EDITOR_FILE = ROOT / "camera-editor.html"
REFERENCE_SCENE_FILE = REPO_ROOT / "src" / "reference-animation" / "sqrtx_full_rotation.py"
REFERENCE_CAMERA_EDITOR_FILE = ROOT / "reference-camera-editor.html"
REFERENCE_LABEL_EDITOR_FILE = ROOT / "reference-label-editor.html"
REFERENCE_LABEL_LAYOUT_FILE = REPO_ROOT / "config" / "reference-label-layouts.json"
SHOWCASE_PREVIEW_RENDER_SCRIPT = REPO_ROOT / "scripts" / "render" / "render-showcase-previews.sh"
FRAME_HEIGHT = 8.0
FRAME_WIDTH = FRAME_HEIGHT * (16.0 / 9.0)
PREVIEW_COUNT = 6
LABEL_CONSTANTS = {
    "x": "X_LABEL_SCREEN_KNOTS",
    "y": "Y_LABEL_SCREEN_KNOTS",
    "z": "Z_LABEL_SCREEN_KNOTS",
    "o": "O_LABEL_SCREEN_KNOTS",
}
PREVIEW_DIR_CANDIDATES = (
    OUTPUT_ROOT / "previews-16x9",
    OUTPUT_ROOT / "previews_smooth6",
    OUTPUT_ROOT / "previews-raw",
)
SHOWCASE_TIME_CONSTANT = "SHOWCASE_KEYFRAME_TIMES"
SHOWCASE_CAMERA_CONSTANT = "SHOWCASE_CAMERA_KNOTS"
SHOWCASE_FOCUS_CONSTANT = "SHOWCASE_FOCUS_LOCAL_KNOTS"
SHOWCASE_OFFSET_CONSTANT = "SHOWCASE_CENTER_OFFSET_KNOTS"
SHOWCASE_PREVIEW_DIR = OUTPUT_ROOT / "showcase-previews-16x9"
SHOWCASE_PREVIEW_RAW_DIR = OUTPUT_ROOT / "showcase-previews-raw"
REFERENCE_CAMERA_CONSTANT = "FIXED_CAMERA"
REFERENCE_CENTER_CONSTANT = "FIXED_FRAME_CENTER"
REFERENCE_PROGRESS_CONSTANT = "REFERENCE_PREVIEW_PROGRESS"
REFERENCE_WORLD_ORIGIN_CONSTANT = "REFERENCE_WORLD_ORIGIN_SHIFT"
REFERENCE_WORLD_SCALE_CONSTANT = "REFERENCE_WORLD_SCALE"
REFERENCE_THETA_OFFSET_CONSTANT = "REFERENCE_THETA_OFFSET"
REFERENCE_FOCAL_DISTANCE_CONSTANT = "REFERENCE_FOCAL_DISTANCE"
REFERENCE_PREVIEW_DIR = OUTPUT_ROOT / "reference-editor"
REFERENCE_PREVIEW_NAME = "sqrtx-reference-preview"
REFERENCE_LABEL_PREVIEW_IMAGES = {
    "phi30": (
        OUTPUT_ROOT / "reference" / "checks" / "reference-label-editor-phi30-4k.png",
        OUTPUT_ROOT / "reference" / "checks" / "debug_4k_phi30_nolabel_v3.png",
    ),
    "phi70": (
        OUTPUT_ROOT / "reference" / "checks" / "reference-label-editor-phi70-4k.png",
        OUTPUT_ROOT / "reference" / "checks" / "debug_4k_phi70_nolabel_v3.png",
    ),
}
REFERENCE_LABEL_DEFAULTS = {
    "phi30": {
        "title": "phi = 30°",
        "baseWidth": 3840,
        "baseHeight": 2160,
        "labelHeightPx": 118.0,
        "labels": {
            "x": {"x": 2712.10, "y": 1834.86},
            "y": {"x": 1936.00, "y": 800.88},
            "z": {"x": 1540.64, "y": 1476.40},
        },
    },
    "phi70": {
        "title": "phi = 70°",
        "baseWidth": 3840,
        "baseHeight": 2160,
        "labelHeightPx": 118.0,
        "labels": {
            "x": {"x": 2740.00, "y": 1494.10},
            "y": {"x": 1940.00, "y": 577.01},
            "z": {"x": 1530.74, "y": 1342.99},
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve lightweight GUIs for editing label and camera keyframes in revolve-slice-prototype.py.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Launch the local editor server.")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--no-open", action="store_true")

    subparsers.add_parser("dump-json", help="Print the current editor payload as JSON.")
    subparsers.add_parser("dump-camera-json", help="Print the current showcase camera payload as JSON.")
    subparsers.add_parser("dump-reference-camera-json", help="Print the current sqrt(x) reference camera payload as JSON.")

    apply_parser = subparsers.add_parser("apply", help="Apply a JSON payload to revolve-slice-prototype.py.")
    apply_parser.add_argument("json_path", type=Path)

    args = parser.parse_args()
    if args.command is None:
        args.command = "serve"
        args.port = 8765
        args.no_open = False
    return args


def extract_number(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -extract_number(node.operand)
    raise ValueError(f"Unsupported numeric node: {ast.dump(node)}")


def extract_point(node: ast.AST) -> list[float]:
    if isinstance(node, ast.Call) and node.args:
        return extract_point(node.args[0])
    if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 2:
        return [extract_number(node.elts[0]), extract_number(node.elts[1])]
    raise ValueError(f"Unsupported point node: {ast.dump(node)}")


def extract_vector(node: ast.AST, *, length: int | None = None) -> list[float]:
    if isinstance(node, ast.Call) and node.args:
        return extract_vector(node.args[0], length=length)
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [extract_number(item) for item in node.elts]
        if length is not None and len(values) != length:
            raise ValueError(f"Expected {length} values but found {len(values)} in {ast.dump(node)}")
        return values
    raise ValueError(f"Unsupported vector node: {ast.dump(node)}")


def find_assignments(source: str) -> dict[str, ast.Assign]:
    tree = ast.parse(source)
    assignments: dict[str, ast.Assign] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments[node.targets[0].id] = node
    return assignments


def load_preview_paths() -> list[Path]:
    for directory in PREVIEW_DIR_CANDIDATES:
        candidates = [directory / f"preview_{idx:02d}.png" for idx in range(1, PREVIEW_COUNT + 1)]
        if all(path.exists() for path in candidates):
            return candidates

    raise FileNotFoundError(
        "Could not find six preview PNGs in output/previews-16x9, output/previews_smooth6, or output/previews-raw.",
    )


def read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG with a readable IHDR header.")
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def load_scene_payload() -> dict[str, object]:
    source = SCENE_FILE.read_text()
    assignments = find_assignments(source)

    times_node = assignments["PREVIEW_TIMES"].value
    panel_width = int(extract_number(assignments["PANEL_WIDTH"].value))
    panel_height = int(extract_number(assignments["PANEL_HEIGHT"].value))

    if not isinstance(times_node, (ast.Tuple, ast.List)):
        raise ValueError("PREVIEW_TIMES must be a tuple or list.")

    times = [extract_number(item) for item in times_node.elts]
    labels: dict[str, list[list[float]]] = {}
    for label_name, constant_name in LABEL_CONSTANTS.items():
        label_node = assignments[constant_name].value
        if not isinstance(label_node, (ast.Tuple, ast.List)):
            raise ValueError(f"{constant_name} must be a tuple or list.")
        labels[label_name] = [extract_point(item) for item in label_node.elts]

    preview_paths = load_preview_paths()
    preview_width, preview_height = read_png_size(preview_paths[0])
    return {
        "scenePath": str(SCENE_FILE),
        "frameWidth": FRAME_WIDTH,
        "frameHeight": FRAME_HEIGHT,
        "previewWidth": preview_width,
        "previewHeight": preview_height,
        "contentWidth": panel_width,
        "contentHeight": panel_height,
        "times": times,
        "labels": labels,
        "previewImages": [f"/{path.relative_to(REPO_ROOT).as_posix()}" for path in preview_paths],
    }


def load_showcase_preview_paths() -> list[Path]:
    return [SHOWCASE_PREVIEW_DIR / f"preview_{idx:02d}.png" for idx in range(1, PREVIEW_COUNT + 1)]


def load_camera_payload() -> dict[str, object]:
    source = SCENE_FILE.read_text()
    assignments = find_assignments(source)

    times_node = assignments[SHOWCASE_TIME_CONSTANT].value
    if not isinstance(times_node, (ast.Tuple, ast.List)):
        raise ValueError(f"{SHOWCASE_TIME_CONSTANT} must be a tuple or list.")
    times = [extract_number(item) for item in times_node.elts]

    if len(times) != PREVIEW_COUNT:
        raise ValueError(f"{SHOWCASE_TIME_CONSTANT} must contain exactly {PREVIEW_COUNT} values.")

    camera_node = assignments[SHOWCASE_CAMERA_CONSTANT].value
    focus_node = assignments[SHOWCASE_FOCUS_CONSTANT].value
    offset_node = assignments[SHOWCASE_OFFSET_CONSTANT].value
    if not isinstance(camera_node, (ast.Tuple, ast.List)):
        raise ValueError(f"{SHOWCASE_CAMERA_CONSTANT} must be a tuple or list.")
    if not isinstance(focus_node, (ast.Tuple, ast.List)):
        raise ValueError(f"{SHOWCASE_FOCUS_CONSTANT} must be a tuple or list.")
    if not isinstance(offset_node, (ast.Tuple, ast.List)):
        raise ValueError(f"{SHOWCASE_OFFSET_CONSTANT} must be a tuple or list.")

    camera_knots = [extract_vector(item, length=4) for item in camera_node.elts]
    focus_knots = [extract_vector(item, length=3) for item in focus_node.elts]
    offset_knots = [extract_vector(item, length=2) for item in offset_node.elts]

    if len(camera_knots) != len(times) or len(focus_knots) != len(times) or len(offset_knots) != len(times):
        raise ValueError("Showcase camera, focus, offset, and time counts must match.")

    preview_paths = load_showcase_preview_paths()
    preview_version = 0
    if any(path.exists() for path in preview_paths):
        preview_version = max((int(path.stat().st_mtime_ns) for path in preview_paths if path.exists()), default=0)

    return {
        "scenePath": str(SCENE_FILE),
        "times": times,
        "camera": camera_knots,
        "focus": focus_knots,
        "centerOffset": offset_knots,
        "previewReady": all(path.exists() for path in preview_paths),
        "previewVersion": preview_version,
        "previewImages": [
            f"/{path.relative_to(REPO_ROOT).as_posix()}" if path.exists() else None
            for path in preview_paths
        ],
    }


def load_reference_camera_payload() -> dict[str, object]:
    source = REFERENCE_SCENE_FILE.read_text()
    assignments = find_assignments(source)

    camera = extract_vector(assignments[REFERENCE_CAMERA_CONSTANT].value, length=4)
    center = extract_vector(assignments[REFERENCE_CENTER_CONSTANT].value, length=3)
    preview_progress = extract_number(assignments[REFERENCE_PROGRESS_CONSTANT].value)
    world_origin = extract_vector(assignments[REFERENCE_WORLD_ORIGIN_CONSTANT].value, length=3)
    world_scale = extract_vector(assignments[REFERENCE_WORLD_SCALE_CONSTANT].value, length=3)
    theta_offset = extract_number(assignments[REFERENCE_THETA_OFFSET_CONSTANT].value)
    focal_distance = extract_number(assignments[REFERENCE_FOCAL_DISTANCE_CONSTANT].value)

    preview_path = REFERENCE_PREVIEW_DIR / f"{REFERENCE_PREVIEW_NAME}.png"
    preview_ready = preview_path.exists()
    preview_version = preview_path.stat().st_mtime_ns if preview_ready else 0

    return {
        "scenePath": str(REFERENCE_SCENE_FILE),
        "camera": camera,
        "center": center,
        "previewProgress": preview_progress,
        "worldOrigin": world_origin,
        "worldScale": world_scale,
        "thetaOffset": theta_offset,
        "focalDistance": focal_distance,
        "previewReady": preview_ready,
        "previewVersion": preview_version,
        "previewImage": f"/{preview_path.relative_to(REPO_ROOT).as_posix()}" if preview_ready else None,
    }


def resolve_reference_label_preview_path(preset_name: str) -> Path | None:
    candidates = REFERENCE_LABEL_PREVIEW_IMAGES.get(preset_name, ())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def validate_reference_label_layout_payload(payload: dict[str, object]) -> dict[str, object]:
    raw_presets = payload.get("presets")
    if not isinstance(raw_presets, dict):
        raise ValueError("Payload is missing presets.")

    normalized_presets: dict[str, object] = {}
    for preset_name in REFERENCE_LABEL_DEFAULTS:
        raw_preset = raw_presets.get(preset_name)
        if not isinstance(raw_preset, dict):
            raise ValueError(f"Preset {preset_name!r} is missing.")

        try:
            base_width = int(raw_preset.get("baseWidth"))
            base_height = int(raw_preset.get("baseHeight"))
            label_height = float(raw_preset.get("labelHeightPx"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Preset {preset_name!r} contains invalid numeric values.") from exc

        if base_width <= 0 or base_height <= 0:
            raise ValueError(f"Preset {preset_name!r} must use positive base dimensions.")
        if not math.isfinite(label_height) or label_height <= 0.0:
            raise ValueError(f"Preset {preset_name!r} must use a positive labelHeightPx.")

        raw_labels = raw_preset.get("labels")
        if not isinstance(raw_labels, dict):
            raise ValueError(f"Preset {preset_name!r} is missing labels.")

        normalized_labels: dict[str, dict[str, float]] = {}
        for axis_name in ("x", "y", "z"):
            raw_label = raw_labels.get(axis_name)
            if not isinstance(raw_label, dict):
                raise ValueError(f"Preset {preset_name!r} is missing label {axis_name!r}.")
            try:
                x_coord = float(raw_label.get("x"))
                y_coord = float(raw_label.get("y"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Preset {preset_name!r} label {axis_name!r} must be numeric.") from exc
            if not (math.isfinite(x_coord) and math.isfinite(y_coord)):
                raise ValueError(f"Preset {preset_name!r} label {axis_name!r} must be finite.")
            normalized_labels[axis_name] = {"x": x_coord, "y": y_coord}

        normalized_presets[preset_name] = {
            "baseWidth": base_width,
            "baseHeight": base_height,
            "labelHeightPx": label_height,
            "labels": normalized_labels,
        }

    return {"presets": normalized_presets}


def load_reference_label_layout_payload() -> dict[str, object]:
    saved_payload: dict[str, object] | None = None
    if REFERENCE_LABEL_LAYOUT_FILE.exists():
        raw_payload = json.loads(REFERENCE_LABEL_LAYOUT_FILE.read_text(encoding="utf-8"))
        saved_payload = validate_reference_label_layout_payload(raw_payload)

    presets: dict[str, object] = {}
    for preset_name, defaults in REFERENCE_LABEL_DEFAULTS.items():
        preview_path = resolve_reference_label_preview_path(preset_name)
        preview_image = None
        preview_width = int(defaults["baseWidth"])
        preview_height = int(defaults["baseHeight"])
        if preview_path is not None and preview_path.exists():
            preview_width, preview_height = read_png_size(preview_path)
            preview_image = f"/{preview_path.relative_to(REPO_ROOT).as_posix()}"

        saved_preset = None
        if saved_payload is not None:
            saved_preset = saved_payload["presets"][preset_name]

        base_width = int(saved_preset["baseWidth"]) if saved_preset is not None else preview_width
        base_height = int(saved_preset["baseHeight"]) if saved_preset is not None else preview_height
        label_height = float(saved_preset["labelHeightPx"]) if saved_preset is not None else float(defaults["labelHeightPx"])
        labels_source = saved_preset["labels"] if saved_preset is not None else defaults["labels"]

        presets[preset_name] = {
            "name": preset_name,
            "title": defaults["title"],
            "previewImage": preview_image,
            "baseWidth": base_width,
            "baseHeight": base_height,
            "labelHeightPx": label_height,
            "labels": {
                axis_name: {
                    "x": float(labels_source[axis_name]["x"]),
                    "y": float(labels_source[axis_name]["y"]),
                }
                for axis_name in ("x", "y", "z")
            },
        }

    return {
        "configPath": str(REFERENCE_LABEL_LAYOUT_FILE),
        "presets": presets,
    }


def save_reference_label_layout_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = validate_reference_label_layout_payload(payload)
    REFERENCE_LABEL_LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE_LABEL_LAYOUT_FILE.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return load_reference_label_layout_payload()


def format_float(value: float, digits: int = 2) -> str:
    rounded = round(float(value), digits)
    if abs(rounded) < (0.5 * (10 ** (-digits))):
        rounded = 0.0
    return f"{rounded:.{digits}f}"


def render_knots_block(name: str, points: list[list[float]]) -> str:
    lines = [f"{name} = ("]
    for x_value, y_value in points:
        lines.append(f"    np.array([{format_float(x_value)}, {format_float(y_value)}], dtype=float),")
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_vector_knots_block(name: str, points: list[list[float]]) -> str:
    lines = [f"{name} = ("]
    for point in points:
        rendered = ", ".join(format_float(value) for value in point)
        lines.append(f"    np.array([{rendered}], dtype=float),")
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_float_tuple_block(name: str, values: list[float]) -> str:
    lines = [f"{name} = ("]
    for value in values:
        lines.append(f"    {format_float(value)},")
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_vector_assignment(name: str, values: list[float], *, digits: int = 2) -> str:
    rendered = ", ".join(format_float(value, digits=digits) for value in values)
    return f"{name} = np.array([{rendered}], dtype=float)\n"


def render_float_assignment(name: str, value: float, *, digits: int = 2) -> str:
    return f"{name} = {format_float(value, digits=digits)}\n"


def replace_assignment(source: str, name: str, replacement: str) -> str:
    assignments = find_assignments(source)
    target = assignments.get(name)
    if target is None:
        raise KeyError(f"Could not find assignment for {name} in {SCENE_FILE}.")

    lines = source.splitlines(keepends=True)
    start = target.lineno - 1
    end = target.end_lineno
    return "".join(lines[:start] + [replacement] + lines[end:])


def validate_payload(payload: dict[str, object]) -> dict[str, list[list[float]]]:
    labels = payload.get("labels")
    times = payload.get("times")
    if not isinstance(labels, dict):
        raise ValueError("Payload is missing a labels object.")
    if not isinstance(times, list):
        raise ValueError("Payload is missing times.")

    normalized: dict[str, list[list[float]]] = {}
    for name in LABEL_CONSTANTS:
        points = labels.get(name)
        if not isinstance(points, list) or len(points) != len(times):
            raise ValueError(f"Label {name!r} must have exactly {len(times)} points.")

        normalized_points: list[list[float]] = []
        for idx, point in enumerate(points):
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError(f"Point {idx + 1} for label {name!r} must be a 2-item list.")
            x_value = float(point[0])
            y_value = float(point[1])
            if not (math.isfinite(x_value) and math.isfinite(y_value)):
                raise ValueError(f"Point {idx + 1} for label {name!r} must be finite.")
            normalized_points.append([x_value, y_value])
        normalized[name] = normalized_points
    return normalized


def validate_camera_payload(payload: dict[str, object]) -> dict[str, object]:
    times = payload.get("times")
    camera = payload.get("camera")
    focus = payload.get("focus")
    center_offset = payload.get("centerOffset")

    if not isinstance(times, list) or len(times) != PREVIEW_COUNT:
        raise ValueError(f"times must contain exactly {PREVIEW_COUNT} values.")
    if not isinstance(camera, list) or len(camera) != PREVIEW_COUNT:
        raise ValueError(f"camera must contain exactly {PREVIEW_COUNT} items.")
    if not isinstance(focus, list) or len(focus) != PREVIEW_COUNT:
        raise ValueError(f"focus must contain exactly {PREVIEW_COUNT} items.")
    if not isinstance(center_offset, list) or len(center_offset) != PREVIEW_COUNT:
        raise ValueError(f"centerOffset must contain exactly {PREVIEW_COUNT} items.")

    normalized_times: list[float] = []
    previous_time = -math.inf
    for index, value in enumerate(times):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"time {index + 1} must be finite.")
        if not (0.0 <= number <= 1.0):
            raise ValueError(f"time {index + 1} must stay within [0, 1].")
        if number <= previous_time:
            raise ValueError("times must be strictly increasing.")
        normalized_times.append(number)
        previous_time = number

    def normalize_vectors(name: str, raw_vectors: list[object], expected_length: int) -> list[list[float]]:
        normalized: list[list[float]] = []
        for index, vector in enumerate(raw_vectors):
            if not isinstance(vector, list) or len(vector) != expected_length:
                raise ValueError(f"{name} item {index + 1} must contain {expected_length} values.")
            values = [float(item) for item in vector]
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"{name} item {index + 1} must contain only finite values.")
            normalized.append(values)
        return normalized

    return {
        "times": normalized_times,
        "camera": normalize_vectors("camera", camera, 4),
        "focus": normalize_vectors("focus", focus, 3),
        "centerOffset": normalize_vectors("centerOffset", center_offset, 2),
    }


def validate_reference_camera_payload(payload: dict[str, object]) -> dict[str, object]:
    camera = payload.get("camera")
    center = payload.get("center")
    preview_progress = payload.get("previewProgress")
    world_origin = payload.get("worldOrigin")
    world_scale = payload.get("worldScale")
    theta_offset = payload.get("thetaOffset")
    focal_distance = payload.get("focalDistance")

    if not isinstance(camera, list) or len(camera) != 4:
        raise ValueError("camera must contain exactly 4 values.")
    if not isinstance(center, list) or len(center) != 3:
        raise ValueError("center must contain exactly 3 values.")
    if not isinstance(world_origin, list) or len(world_origin) != 3:
        raise ValueError("worldOrigin must contain exactly 3 values.")
    if not isinstance(world_scale, list) or len(world_scale) != 3:
        raise ValueError("worldScale must contain exactly 3 values.")

    normalized_camera = [float(value) for value in camera]
    normalized_center = [float(value) for value in center]
    normalized_world_origin = [float(value) for value in world_origin]
    normalized_world_scale = [float(value) for value in world_scale]
    if not all(math.isfinite(value) for value in normalized_camera):
        raise ValueError("camera must contain only finite values.")
    if not all(math.isfinite(value) for value in normalized_center):
        raise ValueError("center must contain only finite values.")
    if not all(math.isfinite(value) for value in normalized_world_origin):
        raise ValueError("worldOrigin must contain only finite values.")
    if not all(math.isfinite(value) for value in normalized_world_scale):
        raise ValueError("worldScale must contain only finite values.")
    if any(abs(value) < 1e-6 for value in normalized_world_scale):
        raise ValueError("worldScale values must stay away from zero.")

    preview_value = float(preview_progress)
    if not math.isfinite(preview_value):
        raise ValueError("previewProgress must be finite.")
    if not (0.0 <= preview_value <= 1.0):
        raise ValueError("previewProgress must stay within [0, 1].")

    theta_value = float(theta_offset)
    focal_value = float(focal_distance)
    if not math.isfinite(theta_value):
        raise ValueError("thetaOffset must be finite.")
    if not math.isfinite(focal_value) or focal_value <= 0.0:
        raise ValueError("focalDistance must be a positive finite number.")

    return {
        "camera": normalized_camera,
        "center": normalized_center,
        "previewProgress": preview_value,
        "worldOrigin": normalized_world_origin,
        "worldScale": normalized_world_scale,
        "thetaOffset": theta_value,
        "focalDistance": focal_value,
    }


def apply_payload(payload: dict[str, object]) -> dict[str, object]:
    labels = validate_payload(payload)
    source = SCENE_FILE.read_text()
    for label_name, constant_name in LABEL_CONSTANTS.items():
        source = replace_assignment(source, constant_name, render_knots_block(constant_name, labels[label_name]))
    SCENE_FILE.write_text(source)
    return load_scene_payload()


def apply_camera_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = validate_camera_payload(payload)
    source = SCENE_FILE.read_text()
    source = replace_assignment(source, SHOWCASE_TIME_CONSTANT, render_float_tuple_block(SHOWCASE_TIME_CONSTANT, normalized["times"]))
    source = replace_assignment(source, SHOWCASE_CAMERA_CONSTANT, render_vector_knots_block(SHOWCASE_CAMERA_CONSTANT, normalized["camera"]))
    source = replace_assignment(source, SHOWCASE_FOCUS_CONSTANT, render_vector_knots_block(SHOWCASE_FOCUS_CONSTANT, normalized["focus"]))
    source = replace_assignment(source, SHOWCASE_OFFSET_CONSTANT, render_vector_knots_block(SHOWCASE_OFFSET_CONSTANT, normalized["centerOffset"]))
    SCENE_FILE.write_text(source)
    return load_camera_payload()


def apply_reference_camera_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = validate_reference_camera_payload(payload)
    source = REFERENCE_SCENE_FILE.read_text()
    source = replace_assignment(
        source,
        REFERENCE_CAMERA_CONSTANT,
        render_vector_assignment(REFERENCE_CAMERA_CONSTANT, normalized["camera"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_CENTER_CONSTANT,
        render_vector_assignment(REFERENCE_CENTER_CONSTANT, normalized["center"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_PROGRESS_CONSTANT,
        render_float_assignment(REFERENCE_PROGRESS_CONSTANT, normalized["previewProgress"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_WORLD_ORIGIN_CONSTANT,
        render_vector_assignment(REFERENCE_WORLD_ORIGIN_CONSTANT, normalized["worldOrigin"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_WORLD_SCALE_CONSTANT,
        render_vector_assignment(REFERENCE_WORLD_SCALE_CONSTANT, normalized["worldScale"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_THETA_OFFSET_CONSTANT,
        render_float_assignment(REFERENCE_THETA_OFFSET_CONSTANT, normalized["thetaOffset"], digits=2),
    )
    source = replace_assignment(
        source,
        REFERENCE_FOCAL_DISTANCE_CONSTANT,
        render_float_assignment(REFERENCE_FOCAL_DISTANCE_CONSTANT, normalized["focalDistance"], digits=2),
    )
    REFERENCE_SCENE_FILE.write_text(source)
    return load_reference_camera_payload()


def render_showcase_previews() -> dict[str, object]:
    if not SHOWCASE_PREVIEW_RENDER_SCRIPT.exists():
        raise FileNotFoundError(f"Missing render script: {SHOWCASE_PREVIEW_RENDER_SCRIPT}")

    completed = subprocess.run(
        ["zsh", str(SHOWCASE_PREVIEW_RENDER_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Showcase preview render failed."
        raise RuntimeError(message)
    return load_camera_payload()


def render_showcase_preview_frame(index: int) -> dict[str, object]:
    if not (0 <= index < PREVIEW_COUNT):
        raise ValueError(f"index must stay within [0, {PREVIEW_COUNT - 1}].")

    payload = load_camera_payload()
    preview_t = float(payload["times"][index])
    output_name = f"preview_{index + 1:02d}.png"
    output_path = SHOWCASE_PREVIEW_DIR / output_name
    raw_output_path = SHOWCASE_PREVIEW_RAW_DIR / output_name
    SHOWCASE_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    SHOWCASE_PREVIEW_RAW_DIR.mkdir(parents=True, exist_ok=True)

    manim_bin = REPO_ROOT / ".venv" / "bin" / "manim"
    if not manim_bin.exists():
        raise FileNotFoundError(f"Missing Manim executable: {manim_bin}")

    env = os.environ.copy()
    env.setdefault("MANIM_THEME", "light")
    env["MANIM_SHOWCASE_T"] = f"{preview_t:.12f}"

    completed = subprocess.run(
        [
            str(manim_bin),
            "-qk",
            "-s",
            "-r",
            "1280,720",
            "--disable_caching",
            str(SCENE_FILE),
            "ShowcaseStateFrame",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Single showcase preview render failed."
        raise RuntimeError(message)

    image_candidates = sorted(
        (REPO_ROOT / "media" / "images" / "revolve-slice-prototype").glob("ShowcaseStateFrame*.png"),
        key=lambda path: path.stat().st_mtime_ns,
    )
    if not image_candidates:
        raise FileNotFoundError("Could not find rendered ShowcaseStateFrame PNG.")

    latest_image = image_candidates[-1]
    shutil.copy2(latest_image, raw_output_path)
    shutil.copy2(latest_image, output_path)
    return load_camera_payload()


def render_reference_preview() -> dict[str, object]:
    payload = load_reference_camera_payload()
    preview_t = float(payload["previewProgress"])
    REFERENCE_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    manim_bin = REPO_ROOT / ".venv-manimgl" / "bin" / "manimgl"
    if not manim_bin.exists():
        raise FileNotFoundError(f"Missing ManimGL executable: {manim_bin}")

    env = os.environ.copy()
    env["SQRTX_REFERENCE_PROGRESS"] = f"{preview_t:.12f}"

    completed = subprocess.run(
        [
            str(manim_bin),
            str(REFERENCE_SCENE_FILE),
            "SqrtXReferenceFrame",
            "-w",
            "-s",
            "--hd",
            "--file_name",
            REFERENCE_PREVIEW_NAME,
            "--video_dir",
            str(REFERENCE_PREVIEW_DIR),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Reference preview render failed."
        raise RuntimeError(message)

    image_candidates = sorted(
        REFERENCE_PREVIEW_DIR.glob(f"{REFERENCE_PREVIEW_NAME}*.png"),
        key=lambda path: path.stat().st_mtime_ns,
    )
    if not image_candidates:
        raise FileNotFoundError("Could not find rendered sqrt(x) reference preview PNG.")

    preview_path = image_candidates[-1]
    canonical_path = REFERENCE_PREVIEW_DIR / f"{REFERENCE_PREVIEW_NAME}.png"
    if preview_path != canonical_path:
        shutil.copy2(preview_path, canonical_path)
    return load_reference_camera_payload()


class EditorHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            normalized_path = parsed.path.rstrip("/") or "/"
            if normalized_path in {"/", "/index.html"}:
                self.serve_file(EDITOR_FILE)
                return
            if normalized_path in {"/camera", "/camera.html"}:
                self.serve_file(CAMERA_EDITOR_FILE)
                return
            if normalized_path in {"/reference-camera", "/reference-camera.html"}:
                self.serve_file(REFERENCE_CAMERA_EDITOR_FILE)
                return
            if normalized_path in {"/reference-labels", "/reference-labels.html", "/reference-label-editor.html"}:
                self.serve_file(REFERENCE_LABEL_EDITOR_FILE)
                return
            if normalized_path == "/api/keyframes":
                self.respond_json(load_scene_payload())
                return
            if normalized_path == "/api/camera-keyframes":
                self.respond_json(load_camera_payload())
                return
            if normalized_path == "/api/reference-camera":
                self.respond_json(load_reference_camera_payload())
                return
            if normalized_path == "/api/reference-label-layouts":
                self.respond_json(load_reference_label_layout_payload())
                return
            self.serve_static_path(parsed.path)
        except Exception as exc:  # noqa: BLE001
            self.respond_error(exc)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            normalized_path = parsed.path.rstrip("/") or "/"
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

            if normalized_path == "/api/keyframes":
                payload = json.loads(raw_body)
                updated_payload = apply_payload(payload)
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/camera-keyframes":
                payload = json.loads(raw_body)
                updated_payload = apply_camera_payload(payload)
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/reference-camera":
                payload = json.loads(raw_body)
                updated_payload = apply_reference_camera_payload(payload)
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/camera-previews/render":
                updated_payload = render_showcase_previews()
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/camera-preview-frame":
                payload = json.loads(raw_body)
                if not isinstance(payload, dict):
                    raise ValueError("Payload must be a JSON object.")
                camera_payload = payload.get("payload")
                index = int(payload.get("index"))
                if not isinstance(camera_payload, dict):
                    raise ValueError("payload.payload must be a JSON object.")
                apply_camera_payload(camera_payload)
                updated_payload = render_showcase_preview_frame(index)
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/reference-camera-preview":
                payload = json.loads(raw_body)
                updated_payload = apply_reference_camera_payload(payload)
                updated_payload = render_reference_preview()
                self.respond_json(updated_payload)
                return
            if normalized_path == "/api/reference-label-layouts":
                payload = json.loads(raw_body)
                updated_payload = save_reference_label_layout_payload(payload)
                self.respond_json(updated_payload)
                return

            self.send_error(HTTPStatus.NOT_FOUND, f"Unknown API endpoint: {parsed.path}")
        except Exception as exc:  # noqa: BLE001
            self.respond_error(exc)

    def log_message(self, format: str, *args) -> None:
        return

    def respond_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_error(self, exc: Exception, status: int = 500) -> None:
        body = str(exc).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, f"File not found: {path.name}")
            return

        mime_type, _ = mimetypes.guess_type(path.name)
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type or 'application/octet-stream'}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static_path(self, raw_path: str) -> None:
        relative = unquote(raw_path.lstrip("/"))
        candidate = (REPO_ROOT / relative).resolve()
        try:
            candidate.relative_to(REPO_ROOT)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "Path escapes the project root.")
            return
        self.serve_file(candidate)


def print_json_payload() -> int:
    print(json.dumps(load_scene_payload(), ensure_ascii=False, indent=2))
    return 0


def print_camera_json_payload() -> int:
    print(json.dumps(load_camera_payload(), ensure_ascii=False, indent=2))
    return 0


def print_reference_camera_json_payload() -> int:
    print(json.dumps(load_reference_camera_payload(), ensure_ascii=False, indent=2))
    return 0


def apply_from_file(json_path: Path) -> int:
    payload = json.loads(json_path.read_text())
    apply_payload(payload)
    print(f"Updated {SCENE_FILE} from {json_path}.")
    return 0


def serve(port: int, open_browser: bool) -> int:
    server = ThreadingHTTPServer(("127.0.0.1", port), EditorHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Keyframe editor running at {url}")
    print(f"Editing {SCENE_FILE}")
    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping keyframe editor.")
    finally:
        server.server_close()
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "dump-json":
            return print_json_payload()
        if args.command == "dump-camera-json":
            return print_camera_json_payload()
        if args.command == "dump-reference-camera-json":
            return print_reference_camera_json_payload()
        if args.command == "apply":
            return apply_from_file(args.json_path)
        if args.command == "serve":
            return serve(args.port, not args.no_open)
        raise ValueError(f"Unknown command: {args.command}")
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
