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


def format_float(value: float) -> str:
    rounded = round(float(value), 2)
    if abs(rounded) < 0.005:
        rounded = 0.0
    return f"{rounded:.2f}"


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
            if normalized_path == "/api/keyframes":
                self.respond_json(load_scene_payload())
                return
            if normalized_path == "/api/camera-keyframes":
                self.respond_json(load_camera_payload())
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
