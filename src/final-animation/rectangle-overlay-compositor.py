#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from scipy.spatial.transform import Rotation


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUTPUT_DIR = Path(
    os.environ.get(
        "VOLUME_OF_REVOLUTION_OUTPUT_DIR",
        str(REPO_ROOT / "output" / "final"),
    )
).expanduser()
THEME = os.environ.get("LINKED_RECTANGLES_THEME", os.environ.get("MANIM_THEME", "light")).strip().lower()
PLANE_TRACKING_ENABLED = os.environ.get("LINKED_RECTANGLES_USE_PLANE_TRACKING", "1").strip().lower() not in {"0", "false", "no"}
CAMERA_MODE = os.environ.get(
    "LINKED_RECTANGLES_CAMERA_MODE",
    os.environ.get("VOLUME_OF_REVOLUTION_CAMERA_MODE", "motion"),
).strip().lower()
BUILD_EMPHASIS = float(os.environ.get("LINKED_RECTANGLES_BUILD_EMPHASIS", "1.25"))
DEFAULT_LOWRES_SOURCE = OUTPUT_DIR / "volume-of-revolution-source-preview.mp4"
DEFAULT_MEDIUM_SOURCE = OUTPUT_DIR / "volume-of-revolution-source-1080p60.mp4"
DEFAULT_SOURCE_VIDEO = DEFAULT_MEDIUM_SOURCE if DEFAULT_MEDIUM_SOURCE.exists() else DEFAULT_LOWRES_SOURCE

SRC_VIDEO = Path(
    os.environ.get(
        "LINKED_RECTANGLES_SOURCE",
        str(DEFAULT_SOURCE_VIDEO),
    )
).expanduser()
OUT_VIDEO = Path(
    os.environ.get(
        "LINKED_RECTANGLES_OUTPUT",
        str(OUTPUT_DIR / "volume-of-revolution-overlay-1080p60.mp4"),
    )
).expanduser()
WORK_DIR = Path(
    os.environ.get(
        "LINKED_RECTANGLES_WORKDIR",
        str(OUTPUT_DIR / f"linked_rectangles_build_{SRC_VIDEO.stem}"),
    )
).expanduser()
SRC_FRAMES_DIR = WORK_DIR / "src_frames"
OUT_FRAMES_DIR = WORK_DIR / "out_frames"
SRC_INFO_FILE = WORK_DIR / "source_info.txt"
QA_CONTACT_SHEET = Path(
    os.environ.get(
        "LINKED_RECTANGLES_CONTACT",
        str(OUTPUT_DIR / "volume-of-revolution-overlay-contact.png"),
    )
).expanduser()
KEEP_OUT_FRAMES = os.environ.get("LINKED_RECTANGLES_KEEP_OUT_FRAMES", "1").strip().lower() not in {"0", "false", "no"}


def probe_video_metadata(video_path: Path) -> tuple[float, int, int]:
    if not video_path.exists():
        return 30.0, 854, 480

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-of",
            "default=nw=1",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()

    fps_text = data.get("r_frame_rate", "30/1")
    if "/" in fps_text:
        num, den = fps_text.split("/", 1)
        fps = float(num) / max(float(den), 1e-8)
    else:
        fps = float(fps_text)
    width = int(data.get("width", 854))
    height = int(data.get("height", 480))
    return fps, width, height


FPS, WIDTH, HEIGHT = probe_video_metadata(SRC_VIDEO)
ASPECT_RATIO = WIDTH / HEIGHT
FRAME_HEIGHT = 8.0
FRAME_WIDTH = FRAME_HEIGHT * ASPECT_RATIO
CANONICAL_FOCAL_DISTANCE = 20.0

OPENING_SOURCE_START = 0.12
OPENING_DURATION = 6.40
FREEZE_SOURCE_TIME = OPENING_SOURCE_START + OPENING_DURATION
DIFF_SOURCE_START = FREEZE_SOURCE_TIME
SHOWCASE_SOURCE_START = 10.12
SHOWCASE_RUN_DURATION = 10.00
END_HOLD_DURATION = 2.00
SHOWCASE_AND_END_DURATION = SHOWCASE_RUN_DURATION + END_HOLD_DURATION

INTRO_DRAW_DURATION = 0.90
REMAINING_RECT_DRAW_DURATION = 2.80
TOTAL_DURATION = INTRO_DRAW_DURATION + OPENING_DURATION + REMAINING_RECT_DRAW_DURATION + SHOWCASE_AND_END_DURATION
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS))

X_AXIS_MAX = 4.25
SLICE_X0 = 2.0
SLICE_X1 = 2.3
CURVE_END = 4.15
ORIGIN_SHIFT = np.array([-1.35, -1.02, 0.0], dtype=float)
X_SCALE = 1.58
Y_SCALE = 1.86
Z_SCALE = Y_SCALE

SHOWCASE_KEYFRAME_TIMES = (
    0.00,
    0.25,
    0.41,
    0.58,
    0.80,
    1.00,
)
SHOWCASE_CAMERA_KNOTS = (
    np.array([72.00, -66.00, 0.00, 0.74], dtype=float),
    np.array([69.00, -35.60, 0.00, 0.72], dtype=float),
    np.array([113.20, 2.20, 0.00, 0.61], dtype=float),
    np.array([109.30, 22.20, 0.00, 0.66], dtype=float),
    np.array([49.00, 101.20, 0.00, 0.72], dtype=float),
    np.array([43.00, 156.00, 0.00, 1.13], dtype=float),
)
SHOWCASE_FRAME_CENTER_KNOTS = (
    np.array([0.426989000, -0.395389000, 0.781200000], dtype=float),
    np.array([-0.433600000, -0.737019000, 1.134600000], dtype=float),
    np.array([-0.272962400, -0.798748800, 1.562400000], dtype=float),
    np.array([0.462684000, -0.843348000, 0.372000000], dtype=float),
    np.array([0.526193000, -0.929207000, 1.841400000], dtype=float),
    np.array([-0.238553200, -1.079584400, 3.292200000], dtype=float),
)
SHOWCASE_SLICE_COUNT = 10
SHOWCASE_SLICE_STAGGER_START = 0.00
SHOWCASE_SLICE_STAGGER_END = 0.60
SHOWCASE_SLICE_DURATION = 0.18

if THEME == "dark":
    RECT_FILL = (232, 148, 212, 84)
    RECT_STROKE = (255, 221, 244, 198)
    RECT_FILL_ACTIVE = (255, 146, 222, 148)
    RECT_STROKE_ACTIVE = (255, 241, 250, 242)
    RECT_FILL_FIRST = (238, 156, 216, 100)
    RECT_STROKE_FIRST = (255, 231, 247, 214)
    EDGE_BOOST_COLOR = np.array([255, 164, 226], dtype=np.float32) / 255.0
    EDGE_BOOST_ALPHA = 0.42
    EDGE_BOOST_SUPPORT_SAT = (0.05, 0.18)
    EDGE_BOOST_SUPPORT_VALUE = (0.28, 0.92)
    EDGE_BOOST_SUPPORT_PINKNESS = (-0.02, 0.10)
    EDGE_BOOST_PREBLUR_SIGMA = 1.1
    EDGE_BOOST_GRAD_LOW = 0.014
    EDGE_BOOST_GRAD_HIGH = 0.060
    PLANE_CLEAN_FILL = (18, 12, 24, 255)
    VOLUME_OCCLUDE_ALPHA = 0.28
    LINE_OCCLUDE_ALPHA = 0.80
    CONTACT_SHEET_BG = (10, 8, 16)
    CONTACT_TILE_BG = (18, 14, 26)
    CONTACT_LABEL = (244, 237, 252)
    FREEZE_RECT_VISIBILITY_BLEND = 0.94
    SHOWCASE_RECT_VISIBILITY_BLEND = 0.78
else:
    # Softer rectangle system so the plane does not get over-saturated.
    RECT_FILL = (236, 171, 205, 14)
    RECT_STROKE = (198, 127, 164, 70)
    RECT_FILL_ACTIVE = (236, 171, 205, 30)
    RECT_STROKE_ACTIVE = (198, 127, 164, 124)
    RECT_FILL_FIRST = (236, 171, 205, 20)
    RECT_STROKE_FIRST = (198, 127, 164, 98)
    EDGE_BOOST_COLOR = np.array([176, 92, 149], dtype=np.float32) / 255.0
    EDGE_BOOST_ALPHA = 0.42
    EDGE_BOOST_SUPPORT_SAT = (0.05, 0.15)
    EDGE_BOOST_SUPPORT_VALUE = (0.72, 0.90)
    EDGE_BOOST_SUPPORT_PINKNESS = (-0.01, 0.09)
    EDGE_BOOST_PREBLUR_SIGMA = 1.1
    EDGE_BOOST_GRAD_LOW = 0.016
    EDGE_BOOST_GRAD_HIGH = 0.064
    PLANE_CLEAN_FILL = (246, 233, 241, 255)
    VOLUME_OCCLUDE_ALPHA = 0.38
    LINE_OCCLUDE_ALPHA = 0.94
    CONTACT_SHEET_BG = (240, 240, 240)
    CONTACT_TILE_BG = (255, 255, 255)
    CONTACT_LABEL = (0, 0, 0)
    FREEZE_RECT_VISIBILITY_BLEND = 0.0
    SHOWCASE_RECT_VISIBILITY_BLEND = 0.0
RECT_EDGE_WIDTH = 3 if max(WIDTH, HEIGHT) >= 1600 else 2
RECT_EDGE_WIDTH_ACTIVE = RECT_EDGE_WIDTH + 1
CURVE_TRACK_BLUE_MIN = 0.72
CURVE_TRACK_BG_DIFF_MIN = 0.18
CURVE_TRACK_BR_DIFF_MIN = 0.03
CURVE_TRACK_SAT_MIN = 0.15
CURVE_TRACK_CORRIDOR = 28.0
CURVE_TRACK_SAMPLE_COUNT = 9
CURVE_TRACK_BLEND_RADIUS = 7.0
CURVE_TRACK_MAX_MATCH_DISTANCE = 34.0
CURVE_TRACK_MIN_PIXELS = 180
CURVE_TRACK_REPROJECTION_TOLERANCE = 9.0
CURVE_TRACK_VALIDATION_COUNT = 13
CURVE_TRACK_MAX_SHIFT = 18.0
CURVE_TRACK_MAX_VALIDATION_ERROR = 14.0
CURVE_TRACK_MEAN_VALIDATION_ERROR = 6.0
AXIS_TRACK_VALUE_MAX = 0.45
AXIS_TRACK_SAT_MAX = 0.12
AXIS_TRACK_CORRIDOR = 10.0
AXIS_TRACK_SAMPLE_COUNT = 6
AXIS_TRACK_BLEND_RADIUS = 4.0
AXIS_TRACK_MAX_MATCH_DISTANCE = 10.5
AXIS_TRACK_VALIDATION_COUNT = 9
AXIS_TRACK_MAX_VALIDATION_ERROR = 7.0
AXIS_TRACK_MEAN_VALIDATION_ERROR = 3.5
EDGE_BOOST_DOWNSCALE = 2 if max(WIDTH, HEIGHT) >= 1600 else 1


def y_of(x: float) -> float:
    return float(np.sqrt(max(x, 0.0)))


def to_world(x_ref: float, y_ref: float, z_ref: float) -> np.ndarray:
    return ORIGIN_SHIFT + np.array([X_SCALE * x_ref, -Z_SCALE * z_ref, Y_SCALE * y_ref], dtype=float)


def cubic_bezier_value(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    mt = 1.0 - t
    return (mt ** 3) * p0 + 3.0 * (mt ** 2) * t * p1 + 3.0 * mt * (t ** 2) * p2 + (t ** 3) * p3


def bezier_ease(t: float, c1: float, c2: float) -> float:
    return float(cubic_bezier_value(0.0, c1, c2, 1.0, t))


def staggered_progress(t: float, start: float, end: float, c1: float, c2: float) -> float:
    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    return bezier_ease((t - start) / (end - start), c1, c2)


def smootherstep_scalar(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def smoothstep_array(values: np.ndarray, edge0: float, edge1: float) -> np.ndarray:
    t = np.clip((values - edge0) / max(edge1 - edge0, 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hermite_endpoint_progress(t: float, start_slope: float, end_slope: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    t2 = t * t
    t3 = t2 * t
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return float(h10 * start_slope + h01 + h11 * end_slope)


def hermite_interpolate(points: list[np.ndarray], times: list[float], t: float) -> np.ndarray:
    if t <= times[0]:
        return np.array(points[0], dtype=float)
    if t >= times[-1]:
        return np.array(points[-1], dtype=float)

    tangents: list[np.ndarray] = []
    for idx, point in enumerate(points):
        if idx == 0:
            tangent = (points[1] - point) / (times[1] - times[0])
        elif idx == len(points) - 1:
            tangent = (point - points[-2]) / (times[-1] - times[-2])
        else:
            tangent = (points[idx + 1] - points[idx - 1]) / (times[idx + 1] - times[idx - 1])
        tangents.append(np.array(tangent, dtype=float))

    for idx in range(len(times) - 1):
        left_t = times[idx]
        right_t = times[idx + 1]
        if left_t <= t <= right_t:
            dt = right_t - left_t
            u = (t - left_t) / dt
            u2 = u * u
            u3 = u2 * u
            h00 = 2 * u3 - 3 * u2 + 1
            h10 = u3 - 2.0 * u2 + u
            h01 = -2.0 * u3 + 3.0 * u2
            h11 = u3 - u2
            return (
                h00 * points[idx]
                + h10 * dt * tangents[idx]
                + h01 * points[idx + 1]
                + h11 * dt * tangents[idx + 1]
            )

    return np.array(points[-1], dtype=float)


def showcase_slice_bounds() -> list[tuple[float, float]]:
    opening = (float(SLICE_X0), float(SLICE_X1))
    remaining_count = max(0, SHOWCASE_SLICE_COUNT - 1)
    if remaining_count == 0:
        return [opening]

    left_span = max(0.0, opening[0])
    right_span = max(0.0, CURVE_END - opening[1])
    total_span = left_span + right_span
    if total_span <= 1e-6:
        return [opening]

    left_count = int(round(remaining_count * left_span / total_span))
    left_count = max(0, min(remaining_count, left_count))
    right_count = remaining_count - left_count

    other_bounds: list[tuple[float, float]] = []
    if left_count > 0:
        left_edges = np.linspace(0.0, opening[0], left_count + 1)
        other_bounds.extend(
            (float(left_edges[idx]), float(left_edges[idx + 1]))
            for idx in range(left_count)
        )
    if right_count > 0:
        right_edges = np.linspace(opening[1], CURVE_END, right_count + 1)
        other_bounds.extend(
            (float(right_edges[idx]), float(right_edges[idx + 1]))
            for idx in range(right_count)
        )

    opening_center = 0.5 * (opening[0] + opening[1])
    other_bounds.sort(
        key=lambda bound: (
            abs(0.5 * (bound[0] + bound[1]) - opening_center),
            0.5 * (bound[0] + bound[1]),
        )
    )
    return [opening, *other_bounds]


ALL_BOUNDS = showcase_slice_bounds()
FIRST_BOUND = ALL_BOUNDS[0]
REMAINING_BOUNDS = ALL_BOUNDS[1:]


def showcase_camera_state(showcase_t: float) -> tuple[float, float, float, float, np.ndarray]:
    motion_t = float(np.clip(showcase_t, 0.0, 1.0))
    phi_deg, theta_deg, gamma_deg, zoom = hermite_interpolate(
        list(SHOWCASE_CAMERA_KNOTS),
        list(SHOWCASE_KEYFRAME_TIMES),
        motion_t,
    )
    center = hermite_interpolate(
        list(SHOWCASE_FRAME_CENTER_KNOTS),
        list(SHOWCASE_KEYFRAME_TIMES),
        motion_t,
    )
    return float(phi_deg), float(theta_deg), float(gamma_deg), float(zoom), np.array(center, dtype=float)


def showcase_motion_camera_state(showcase_t: float) -> tuple[float, float, float, float, np.ndarray]:
    base_times = list(SHOWCASE_KEYFRAME_TIMES)
    return_duration = max(0.18, base_times[-1] - base_times[-2])
    motion_times = [*base_times, base_times[-1] + return_duration]

    motion_camera_knots = [np.array(knot, dtype=float) for knot in SHOWCASE_CAMERA_KNOTS]
    for idx in range(1, len(motion_camera_knots)):
        previous_theta = motion_camera_knots[idx - 1][1]
        theta = motion_camera_knots[idx][1]
        while theta - previous_theta > 180.0:
            theta -= 360.0
        while theta - previous_theta < -180.0:
            theta += 360.0
        motion_camera_knots[idx][1] = theta

    closing_camera_knot = np.array(motion_camera_knots[0], dtype=float)
    last_theta = motion_camera_knots[-1][1]
    previous_theta = motion_camera_knots[-2][1] if len(motion_camera_knots) >= 2 else motion_camera_knots[-1][1]
    if last_theta >= previous_theta:
        while closing_camera_knot[1] <= last_theta:
            closing_camera_knot[1] += 360.0
    else:
        while closing_camera_knot[1] >= last_theta:
            closing_camera_knot[1] -= 360.0

    motion_camera_knots.append(closing_camera_knot)
    motion_centers = [*list(SHOWCASE_FRAME_CENTER_KNOTS), np.array(SHOWCASE_FRAME_CENTER_KNOTS[0], dtype=float)]
    eased_t = hermite_endpoint_progress(showcase_t, 0.24, 0.0)
    motion_t = eased_t * motion_times[-1]
    phi_deg, theta_deg, gamma_deg, zoom = hermite_interpolate(
        motion_camera_knots,
        motion_times,
        motion_t,
    )
    center = hermite_interpolate(
        motion_centers,
        motion_times,
        motion_t,
    )
    return float(phi_deg), float(theta_deg), float(gamma_deg), float(zoom), np.array(center, dtype=float)


def projector_for_state(phi_deg: float, theta_deg: float, gamma_deg: float, zoom: float, center: np.ndarray):
    rotation = Rotation.from_euler("zxz", [gamma_deg, phi_deg, theta_deg + 90.0], degrees=True)
    inverse_rotation = rotation.as_matrix().T
    scale = 1.0 / max(zoom, 1e-8)

    def project(world_point: np.ndarray) -> tuple[float, float]:
        view = inverse_rotation.dot(world_point - center) / scale
        c = view[2] / CANONICAL_FOCAL_DISTANCE
        ndc_x = (2.0 / FRAME_WIDTH * view[0]) / (1.0 - c)
        ndc_y = (2.0 / FRAME_HEIGHT * view[1]) / (1.0 - c)
        px = (ndc_x + 1.0) * WIDTH / 2.0
        py = (1.0 - ndc_y) * HEIGHT / 2.0
        return float(px), float(py)

    return project


def static_projector():
    return projector_for_state(*showcase_camera_state(0.0))


STATIC_PROJECT = static_projector()
FIXED_SHOWCASE_PLANE_HOMOGRAPHY: np.ndarray | None = None


def use_fixed_showcase_camera() -> bool:
    return CAMERA_MODE in {"fixed", "static", "locked", "still"}


def slice_angle_progress(showcase_t: float, slice_index: int) -> float:
    if slice_index == 0:
        return 1.0
    remaining_count = max(1, SHOWCASE_SLICE_COUNT - 1)
    starts = np.linspace(SHOWCASE_SLICE_STAGGER_START, SHOWCASE_SLICE_STAGGER_END, remaining_count)
    start = float(starts[slice_index - 1])
    end = min(1.0, start + SHOWCASE_SLICE_DURATION)
    return staggered_progress(showcase_t, start, end, 0.10, 0.82)


def source_frame_index_for_time(source_time: float, frame_count: int) -> int:
    idx = int(round(source_time * FPS))
    return max(0, min(frame_count - 1, idx))


def ensure_source_frames() -> list[Path]:
    source_stat = SRC_VIDEO.stat()
    source_signature = (
        f"{SRC_VIDEO.resolve()}|{source_stat.st_mtime_ns}|{source_stat.st_size}|"
        f"{FPS:.6f}|{WIDTH}|{HEIGHT}"
    )
    if (
        SRC_FRAMES_DIR.exists()
        and SRC_INFO_FILE.exists()
        and SRC_INFO_FILE.read_text().strip() == source_signature
        and any(SRC_FRAMES_DIR.glob("frame_*.png"))
    ):
        frames = sorted(SRC_FRAMES_DIR.glob("frame_*.png"))
        if frames:
            return frames
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SRC_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(SRC_VIDEO),
            "-start_number",
            "0",
            str(SRC_FRAMES_DIR / "frame_%04d.png"),
        ],
        check=True,
    )
    frames = sorted(SRC_FRAMES_DIR.glob("frame_*.png"))
    if not frames:
        raise RuntimeError("No source frames were extracted.")
    SRC_INFO_FILE.write_text(source_signature)
    return frames


def clean_opening_slice(frame: Image.Image, project) -> Image.Image:
    clean = frame.copy()
    draw = ImageDraw.Draw(clean, "RGBA")
    x0, x1 = FIRST_BOUND
    left = max(0.0, x0 - 0.025)
    right = min(CURVE_END, x1 + 0.025)
    points = [
        project(to_world(left, 0.0, 0.0)),
        project(to_world(right, 0.0, 0.0)),
    ]
    for x in np.linspace(right, left, 32):
        points.append(project(to_world(float(x), y_of(float(x)), 0.0)))
    draw.polygon(points, fill=PLANE_CLEAN_FILL)
    return clean


CLEAN_INTRO_BASE: Image.Image | None = None
EDGE_MASK_CACHE_KEY: int | None = None
EDGE_MASK_CACHE_IMAGE: Image.Image | None = None
STATIC_PLANE_HOMOGRAPHY: np.ndarray | None = None
SHOWCASE_PLANE_HOMOGRAPHY_CACHE: dict[int, np.ndarray] = {}


def curve_color_mask(source_frame: Image.Image) -> np.ndarray:
    arr = np.asarray(source_frame.convert("RGBA"), dtype=np.float32) / 255.0
    rgb = arr[..., :3]
    value = rgb.max(axis=2)
    saturation = value - rgb.min(axis=2)
    blue = rgb[..., 2]
    green = rgb[..., 1]
    red = rgb[..., 0]
    return (
        (blue > CURVE_TRACK_BLUE_MIN)
        & ((blue - green) > CURVE_TRACK_BG_DIFF_MIN)
        & ((blue - red) > CURVE_TRACK_BR_DIFF_MIN)
        & (saturation > CURVE_TRACK_SAT_MIN)
    )


def axis_color_mask(source_frame: Image.Image) -> np.ndarray:
    arr = np.asarray(source_frame.convert("RGBA"), dtype=np.float32) / 255.0
    rgb = arr[..., :3]
    value = rgb.max(axis=2)
    saturation = value - rgb.min(axis=2)
    return (value < AXIS_TRACK_VALUE_MAX) & (saturation < AXIS_TRACK_SAT_MAX)


def fit_homography(src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray | None:
    if src_points.shape[0] < 4 or src_points.shape != dst_points.shape:
        return None

    rows: list[list[float]] = []
    for (x, y), (u, v) in zip(src_points, dst_points):
        rows.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        rows.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])

    matrix = np.asarray(rows, dtype=float)
    _, _, vh = np.linalg.svd(matrix)
    homography = vh[-1].reshape(3, 3)
    if abs(homography[2, 2]) < 1e-8:
        return None
    homography /= homography[2, 2]
    if not np.isfinite(homography).all():
        return None
    return homography


def fit_affine_transform(src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray | None:
    if src_points.shape[0] < 3 or src_points.shape != dst_points.shape:
        return None

    rows: list[list[float]] = []
    values: list[float] = []
    for (x, y), (u, v) in zip(src_points, dst_points):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0])
        rows.append([0.0, 0.0, 0.0, x, y, 1.0])
        values.extend([u, v])

    matrix = np.asarray(rows, dtype=float)
    rhs = np.asarray(values, dtype=float)
    params, _, _, _ = np.linalg.lstsq(matrix, rhs, rcond=None)
    affine = np.array(
        [
            [params[0], params[1], params[2]],
            [params[3], params[4], params[5]],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    if not np.isfinite(affine).all():
        return None
    return affine


def apply_homography_to_point(homography: np.ndarray, point: tuple[float, float] | np.ndarray) -> tuple[float, float]:
    x, y = float(point[0]), float(point[1])
    mapped = homography.dot(np.array([x, y, 1.0], dtype=float))
    if abs(mapped[2]) < 1e-8:
        return x, y
    return float(mapped[0] / mapped[2]), float(mapped[1] / mapped[2])


def apply_homography_to_points(homography: np.ndarray, points: np.ndarray) -> np.ndarray:
    homogeneous = np.concatenate([points, np.ones((points.shape[0], 1), dtype=np.float64)], axis=1)
    mapped = homogeneous.dot(homography.T)
    safe_w = np.where(np.abs(mapped[:, 2]) < 1e-8, 1.0, mapped[:, 2])
    return mapped[:, :2] / safe_w[:, None]


def homography_is_stable(
    homography: np.ndarray,
    projected_curve: np.ndarray,
    curve_points: np.ndarray,
    projected_axis: np.ndarray,
    axis_points: np.ndarray,
) -> bool:
    corrected_curve = apply_homography_to_points(homography, projected_curve)
    shifts = np.linalg.norm(corrected_curve - projected_curve, axis=1)
    if not np.isfinite(shifts).all() or float(np.max(shifts)) > CURVE_TRACK_MAX_SHIFT:
        return False

    curve_deltas = corrected_curve[:, None, :] - curve_points[None, :, :]
    curve_errors = np.sqrt(np.min(np.sum(curve_deltas * curve_deltas, axis=2), axis=1))
    curve_ok = (
        np.isfinite(curve_errors).all()
        and float(np.max(curve_errors)) <= CURVE_TRACK_MAX_VALIDATION_ERROR
        and float(np.mean(curve_errors)) <= CURVE_TRACK_MEAN_VALIDATION_ERROR
    )
    if not curve_ok:
        return False

    if axis_points.shape[0] == 0:
        return True

    corrected_axis = apply_homography_to_points(homography, projected_axis)
    axis_deltas = corrected_axis[:, None, :] - axis_points[None, :, :]
    axis_errors = np.sqrt(np.min(np.sum(axis_deltas * axis_deltas, axis=2), axis=1))
    return (
        np.isfinite(axis_errors).all()
        and float(np.max(axis_errors)) <= AXIS_TRACK_MAX_VALIDATION_ERROR
        and float(np.mean(axis_errors)) <= AXIS_TRACK_MEAN_VALIDATION_ERROR
    )


def collect_feature_matches(
    feature_points: np.ndarray,
    projected_samples: np.ndarray,
    *,
    blend_radius: float,
    max_match_distance: float,
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    src_points: list[np.ndarray] = []
    dst_points: list[np.ndarray] = []
    for predicted in projected_samples:
        sample_deltas = feature_points - predicted[None, :]
        sample_dist_sq = np.sum(sample_deltas * sample_deltas, axis=1)
        nearest_index = int(np.argmin(sample_dist_sq))
        nearest_dist_sq = float(sample_dist_sq[nearest_index])
        if nearest_dist_sq > max_match_distance ** 2:
            continue

        local_mask = sample_dist_sq <= blend_radius ** 2
        if np.any(local_mask):
            weights = np.exp(-0.5 * sample_dist_sq[local_mask] / max(blend_radius ** 2, 1e-8))
            matched = np.sum(feature_points[local_mask] * weights[:, None], axis=0) / np.sum(weights)
        else:
            matched = feature_points[nearest_index]

        src_points.append(np.array(predicted, dtype=np.float64))
        dst_points.append(np.array(matched, dtype=np.float64))
    return src_points, dst_points


def estimated_plane_homography(source_frame: Image.Image, project, *, fallback: np.ndarray | None = None) -> np.ndarray:
    candidate_mask = curve_color_mask(source_frame)
    ys, xs = np.nonzero(candidate_mask)
    if len(xs) < CURVE_TRACK_MIN_PIXELS:
        return np.array(fallback if fallback is not None else np.eye(3, dtype=float), dtype=float)

    candidate_points = np.column_stack([xs.astype(np.float64), ys.astype(np.float64)])
    curve_x_values = np.linspace(0.0, CURVE_END, 180)
    projected_curve = np.array(
        [project(to_world(float(x), y_of(float(x)), 0.0)) for x in curve_x_values],
        dtype=np.float64,
    )
    axis_candidate_mask = axis_color_mask(source_frame)
    axis_ys, axis_xs = np.nonzero(axis_candidate_mask)
    axis_candidate_points = np.column_stack([axis_xs.astype(np.float64), axis_ys.astype(np.float64)])
    axis_x_values = np.linspace(0.0, CURVE_END, 160)
    projected_axis = np.array(
        [project(to_world(float(x), 0.0, 0.0)) for x in axis_x_values],
        dtype=np.float64,
    )

    deltas = candidate_points[:, None, :] - projected_curve[None, :, :]
    distances_sq = np.sum(deltas * deltas, axis=2)
    near_curve = np.min(distances_sq, axis=1) <= CURVE_TRACK_CORRIDOR ** 2
    curve_points = candidate_points[near_curve]
    if curve_points.shape[0] < max(24, CURVE_TRACK_SAMPLE_COUNT * 3):
        return np.array(fallback if fallback is not None else np.eye(3, dtype=float), dtype=float)

    if axis_candidate_points.shape[0] > 0:
        axis_deltas = axis_candidate_points[:, None, :] - projected_axis[None, :, :]
        axis_distances_sq = np.sum(axis_deltas * axis_deltas, axis=2)
        near_axis = np.min(axis_distances_sq, axis=1) <= AXIS_TRACK_CORRIDOR ** 2
        axis_points = axis_candidate_points[near_axis]
    else:
        axis_points = np.empty((0, 2), dtype=np.float64)

    sample_x_values = np.linspace(0.0, CURVE_END, CURVE_TRACK_SAMPLE_COUNT)
    curve_sample_points = np.array(
        [project(to_world(float(x), y_of(float(x)), 0.0)) for x in sample_x_values],
        dtype=np.float64,
    )
    src_points, dst_points = collect_feature_matches(
        curve_points,
        curve_sample_points,
        blend_radius=CURVE_TRACK_BLEND_RADIUS,
        max_match_distance=CURVE_TRACK_MAX_MATCH_DISTANCE,
    )

    axis_sample_values = np.linspace(0.0, CURVE_END, AXIS_TRACK_SAMPLE_COUNT)
    axis_sample_points = np.array(
        [project(to_world(float(x), 0.0, 0.0)) for x in axis_sample_values],
        dtype=np.float64,
    )
    axis_src_points, axis_dst_points = collect_feature_matches(
        axis_points if axis_points.shape[0] else projected_axis,
        axis_sample_points,
        blend_radius=AXIS_TRACK_BLEND_RADIUS,
        max_match_distance=AXIS_TRACK_MAX_MATCH_DISTANCE,
    )
    src_points.extend(axis_src_points)
    dst_points.extend(axis_dst_points)

    if len(src_points) < 4:
        return np.array(fallback if fallback is not None else np.eye(3, dtype=float), dtype=float)

    src_array = np.vstack(src_points)
    dst_array = np.vstack(dst_points)
    homography = fit_affine_transform(src_array, dst_array)
    if homography is None:
        return np.array(fallback if fallback is not None else np.eye(3, dtype=float), dtype=float)

    reprojection = apply_homography_to_points(homography, src_array)
    reprojection_errors = np.linalg.norm(reprojection - dst_array, axis=1)
    inliers = reprojection_errors <= CURVE_TRACK_REPROJECTION_TOLERANCE
    if np.count_nonzero(inliers) >= 4 and np.count_nonzero(inliers) < len(src_array):
        refined = fit_affine_transform(src_array[inliers], dst_array[inliers])
        if refined is not None:
            homography = refined

    validation_x = np.linspace(0.0, CURVE_END, CURVE_TRACK_VALIDATION_COUNT)
    validation_curve = np.array(
        [project(to_world(float(x), y_of(float(x)), 0.0)) for x in validation_x],
        dtype=np.float64,
    )
    validation_axis_x = np.linspace(0.0, CURVE_END, AXIS_TRACK_VALIDATION_COUNT)
    validation_axis = np.array(
        [project(to_world(float(x), 0.0, 0.0)) for x in validation_axis_x],
        dtype=np.float64,
    )
    if not homography_is_stable(homography, validation_curve, curve_points, validation_axis, axis_points):
        return np.array(fallback if fallback is not None else np.eye(3, dtype=float), dtype=float)
    return homography


def make_corrected_projector(project, homography: np.ndarray):
    def corrected(world_point: np.ndarray) -> tuple[float, float]:
        return apply_homography_to_point(homography, project(world_point))

    return corrected


def static_plane_projector(src_frames: list[Path]):
    if not PLANE_TRACKING_ENABLED:
        return STATIC_PROJECT

    global STATIC_PLANE_HOMOGRAPHY

    if STATIC_PLANE_HOMOGRAPHY is None:
        source_frame = Image.open(src_frames[0]).convert("RGBA")
        STATIC_PLANE_HOMOGRAPHY = estimated_plane_homography(source_frame, STATIC_PROJECT)
    return make_corrected_projector(STATIC_PROJECT, STATIC_PLANE_HOMOGRAPHY)


def showcase_plane_projector(source_frame: Image.Image, showcase_motion_t: float, *, cache_key: int | None = None):
    global FIXED_SHOWCASE_PLANE_HOMOGRAPHY
    if use_fixed_showcase_camera():
        project = STATIC_PROJECT
        if not PLANE_TRACKING_ENABLED:
            return project
        if FIXED_SHOWCASE_PLANE_HOMOGRAPHY is None:
            FIXED_SHOWCASE_PLANE_HOMOGRAPHY = estimated_plane_homography(source_frame, project)
        return make_corrected_projector(project, FIXED_SHOWCASE_PLANE_HOMOGRAPHY)

    project = projector_for_state(*showcase_motion_camera_state(showcase_motion_t))
    if not PLANE_TRACKING_ENABLED:
        return project
    if cache_key is not None and cache_key in SHOWCASE_PLANE_HOMOGRAPHY_CACHE:
        homography = SHOWCASE_PLANE_HOMOGRAPHY_CACHE[cache_key]
    else:
        fallback = SHOWCASE_PLANE_HOMOGRAPHY_CACHE.get(cache_key - 1) if cache_key is not None else None
        homography = estimated_plane_homography(source_frame, project, fallback=fallback)
        if cache_key is not None:
            SHOWCASE_PLANE_HOMOGRAPHY_CACHE[cache_key] = homography
    return make_corrected_projector(project, homography)


def get_clean_intro_base(src_frames: list[Path]) -> Image.Image:
    global CLEAN_INTRO_BASE
    if CLEAN_INTRO_BASE is None:
        base = Image.open(src_frames[0]).convert("RGBA")
        CLEAN_INTRO_BASE = clean_opening_slice(base, static_plane_projector(src_frames))
    return CLEAN_INTRO_BASE.copy()


def get_source_frame(src_frames: list[Path], source_time: float) -> Image.Image:
    idx = source_frame_index_for_time(source_time, len(src_frames))
    return Image.open(src_frames[idx]).convert("RGBA")


def apply_source_occlusion(
    composited_frame: Image.Image,
    occlusion_source: Image.Image,
) -> Image.Image:
    source_rgba = occlusion_source.convert("RGBA")
    arr = np.asarray(source_rgba, dtype=np.float32) / 255.0
    rgb = arr[..., :3]
    value = rgb.max(axis=2)
    saturation = value - rgb.min(axis=2)
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]

    pinkness = 0.5 * (red + blue) - green
    colored_geometry = smoothstep_array(saturation, 0.08, 0.24) * smoothstep_array(pinkness, 0.01, 0.11)

    darkness = 1.0 - value
    neutral_dark = smoothstep_array(darkness, 0.22, 0.70) * (1.0 - smoothstep_array(saturation, 0.10, 0.26))

    alpha = np.maximum(
        VOLUME_OCCLUDE_ALPHA * colored_geometry,
        LINE_OCCLUDE_ALPHA * neutral_dark,
    )
    alpha = np.clip(alpha, 0.0, 1.0)

    top = source_rgba.copy()
    top.putalpha(Image.fromarray(np.round(alpha * 255.0).astype(np.uint8)))
    return Image.alpha_composite(composited_frame.convert("RGBA"), top)


def geometry_edge_mask(source_frame: Image.Image, *, cache_key: int | None = None) -> Image.Image:
    global EDGE_MASK_CACHE_KEY, EDGE_MASK_CACHE_IMAGE

    if cache_key is not None and cache_key == EDGE_MASK_CACHE_KEY and EDGE_MASK_CACHE_IMAGE is not None:
        return EDGE_MASK_CACHE_IMAGE

    working_frame = source_frame.convert("RGBA")
    if EDGE_BOOST_DOWNSCALE > 1:
        working_frame = working_frame.resize(
            (
                max(1, WIDTH // EDGE_BOOST_DOWNSCALE),
                max(1, HEIGHT // EDGE_BOOST_DOWNSCALE),
            ),
            Image.Resampling.BILINEAR,
        )

    arr = np.asarray(working_frame, dtype=np.float32) / 255.0
    rgb = arr[..., :3]
    value = rgb.max(axis=2)
    saturation = value - rgb.min(axis=2)
    pinkness = 0.5 * (rgb[..., 0] + rgb[..., 2]) - rgb[..., 1]

    support = smoothstep_array(saturation, *EDGE_BOOST_SUPPORT_SAT)
    support *= smoothstep_array(value, *EDGE_BOOST_SUPPORT_VALUE)
    support *= smoothstep_array(pinkness, *EDGE_BOOST_SUPPORT_PINKNESS)

    luma = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    blurred = gaussian_filter(luma, sigma=EDGE_BOOST_PREBLUR_SIGMA)
    grad_y, grad_x = np.gradient(blurred)
    grad_mag = np.hypot(grad_x, grad_y)
    edge_strength = smoothstep_array(grad_mag, EDGE_BOOST_GRAD_LOW, EDGE_BOOST_GRAD_HIGH)
    alpha = np.clip(EDGE_BOOST_ALPHA * edge_strength * support, 0.0, 1.0)
    alpha = np.clip(alpha, 0.0, 1.0)
    mask = Image.fromarray(np.round(alpha * 255.0).astype(np.uint8))
    if EDGE_BOOST_DOWNSCALE > 1:
        mask = mask.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

    if cache_key is not None:
        EDGE_MASK_CACHE_KEY = cache_key
        EDGE_MASK_CACHE_IMAGE = mask
    return mask


def apply_geometry_edge_boost(
    composited_frame: Image.Image,
    source_frame: Image.Image,
    *,
    cache_key: int | None = None,
) -> Image.Image:
    mask = geometry_edge_mask(source_frame, cache_key=cache_key)
    base = np.asarray(composited_frame.convert("RGBA"), dtype=np.float32) / 255.0
    alpha = np.asarray(mask, dtype=np.float32) / 255.0
    out_rgb = base[..., :3] * (1.0 - alpha[..., None]) + EDGE_BOOST_COLOR[None, None, :] * alpha[..., None]
    out_rgba = np.concatenate([np.clip(out_rgb, 0.0, 1.0), base[..., 3:4]], axis=2)
    return Image.fromarray(np.round(out_rgba * 255.0).astype(np.uint8))


def eased_unit(t: float) -> float:
    return smootherstep_scalar(np.clip(t, 0.0, 1.0))


def scale_rgba_alpha(rgba: tuple[int, int, int, int], alpha_scale: float) -> tuple[int, int, int, int]:
    alpha = int(round(rgba[3] * float(np.clip(alpha_scale, 0.0, 1.0))))
    return rgba[0], rgba[1], rgba[2], alpha


def emphasize_rgba(rgba: tuple[int, int, int, int], emphasis: float) -> tuple[int, int, int, int]:
    emphasis = max(float(emphasis), 0.0)
    if emphasis <= 1.0:
        return rgba
    return rgba[0], rgba[1], rgba[2], int(round(min(255.0, rgba[3] * emphasis)))


def curve_strip_polygon_points(
    project,
    bound: tuple[float, float],
) -> list[tuple[float, float]]:
    x0, x1 = bound
    if x1 <= x0 + 1e-4:
        return []

    curve_steps = 28

    points = [
        project(to_world(x0, 0.0, 0.0)),
        project(to_world(x1, 0.0, 0.0)),
    ]
    points.extend(
        project(to_world(float(x), y_of(float(x)), 0.0))
        for x in np.linspace(x1, x0, curve_steps)
    )
    return points


def draw_curve_strip(
    draw: ImageDraw.ImageDraw,
    project,
    bound: tuple[float, float],
    *,
    fill_rgba: tuple[int, int, int, int],
    stroke_rgba: tuple[int, int, int, int],
    alpha_scale: float = 1.0,
    edge_width: int = 1,
) -> None:
    x0, x1 = bound
    if x1 <= x0 + 1e-4:
        return

    curve_steps = 28
    bottom_left = project(to_world(x0, 0.0, 0.0))
    bottom_right = project(to_world(x1, 0.0, 0.0))
    curve_points = [
        project(to_world(float(x), y_of(float(x)), 0.0))
        for x in np.linspace(x1, x0, curve_steps)
    ]
    poly = [bottom_left, bottom_right, *curve_points]
    if not poly:
        return
    scaled_fill = scale_rgba_alpha(fill_rgba, alpha_scale)
    scaled_stroke = scale_rgba_alpha(stroke_rgba, alpha_scale)
    draw.polygon(
        poly,
        fill=scaled_fill,
    )
    if edge_width > 0 and scaled_stroke[3] > 0:
        # Draw the slice boundaries explicitly so the vertical strip cadence
        # stays readable on the dark theme instead of relying on a 1px polygon
        # outline that gets lost at 1080p.
        draw.line([curve_points[-1], bottom_left], fill=scaled_stroke, width=edge_width)
        draw.line([bottom_right, curve_points[0]], fill=scaled_stroke, width=edge_width)
        draw.line(curve_points, fill=scaled_stroke, width=max(1, edge_width - 1))


def draw_rectangles_for_intro(frame: Image.Image, intro_t: float, project) -> Image.Image:
    overlay = frame.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    progress = eased_unit(intro_t / max(INTRO_DRAW_DURATION * 0.88, 1e-8))
    if progress <= 1e-4:
        return overlay
    draw_curve_strip(
        draw,
        project,
        FIRST_BOUND,
        fill_rgba=emphasize_rgba(RECT_FILL_ACTIVE, BUILD_EMPHASIS),
        stroke_rgba=emphasize_rgba(RECT_STROKE_ACTIVE, BUILD_EMPHASIS),
        alpha_scale=progress,
        edge_width=RECT_EDGE_WIDTH_ACTIVE,
    )
    return apply_source_occlusion(overlay, frame)


def draw_first_rectangle_on_frame(frame: Image.Image, *, active: bool, project) -> Image.Image:
    overlay = frame.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw_curve_strip(
        draw,
        project,
        FIRST_BOUND,
        fill_rgba=RECT_FILL_FIRST if active else RECT_FILL,
        stroke_rgba=RECT_STROKE_FIRST if active else RECT_STROKE,
        edge_width=RECT_EDGE_WIDTH_ACTIVE if active else RECT_EDGE_WIDTH,
    )
    return apply_source_occlusion(overlay, frame)


def draw_remaining_rectangles_freeze(frame: Image.Image, freeze_t: float, project) -> Image.Image:
    overlay = frame.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")

    draw_curve_strip(
        draw,
        project,
        FIRST_BOUND,
        fill_rgba=RECT_FILL_FIRST,
        stroke_rgba=RECT_STROKE_FIRST,
        edge_width=RECT_EDGE_WIDTH_ACTIVE,
    )

    settle = 0.14
    usable = max(REMAINING_RECT_DRAW_DURATION - settle, 1e-6)
    active_time = min(max(freeze_t, 0.0), usable)
    slot = usable / max(len(REMAINING_BOUNDS), 1)
    active_index = (
        int(min(len(REMAINING_BOUNDS) - 1, math.floor(active_time / slot)))
        if active_time < usable
        else len(REMAINING_BOUNDS) - 1
    )

    for idx, bound in enumerate(REMAINING_BOUNDS):
        start = idx * slot
        end = start + slot
        if active_time >= end:
            settled_fill = blend_color(RECT_FILL, RECT_FILL_ACTIVE, FREEZE_RECT_VISIBILITY_BLEND)
            settled_stroke = blend_color(RECT_STROKE, RECT_STROKE_ACTIVE, FREEZE_RECT_VISIBILITY_BLEND)
            draw_curve_strip(
                draw,
                project,
                bound,
                fill_rgba=settled_fill,
                stroke_rgba=settled_stroke,
                edge_width=RECT_EDGE_WIDTH,
            )
        elif start <= active_time < end:
            local = (active_time - start) / max(slot, 1e-8)
            draw_curve_strip(
                draw,
                project,
                bound,
                fill_rgba=emphasize_rgba(RECT_FILL_ACTIVE, BUILD_EMPHASIS),
                stroke_rgba=emphasize_rgba(RECT_STROKE_ACTIVE, BUILD_EMPHASIS),
                alpha_scale=eased_unit(local),
                edge_width=RECT_EDGE_WIDTH_ACTIVE,
            )
            active_index = idx
            break
        else:
            break

    return apply_source_occlusion(overlay, frame)


def highlight_strength_for_showcase(showcase_t: float, slice_index: int) -> float:
    if slice_index == 0:
        return 0.0
    progress = slice_angle_progress(showcase_t, slice_index)
    if progress <= 0.0 or progress >= 1.0:
        return 0.0
    return float(np.sin(np.pi * np.clip(progress, 0.0, 1.0)) ** 0.7)


def blend_color(a: tuple[int, int, int, int], b: tuple[int, int, int, int], w: float) -> tuple[int, int, int, int]:
    w = float(np.clip(w, 0.0, 1.0))
    return tuple(int(round((1.0 - w) * av + w * bv)) for av, bv in zip(a, b))


def showcase_motion_t_for_elapsed(showcase_elapsed: float) -> float:
    return float(np.clip(showcase_elapsed / max(SHOWCASE_RUN_DURATION, 1e-8), 0.0, 1.0))


def draw_rectangles_for_showcase(
    frame: Image.Image,
    showcase_motion_t: float,
    *,
    project=None,
) -> Image.Image:
    overlay = frame.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    if project is None:
        project = showcase_plane_projector(frame, showcase_motion_t)

    for idx, bound in enumerate(ALL_BOUNDS):
        if idx == 0:
            fill = RECT_FILL_FIRST
            stroke = RECT_STROKE_FIRST
        else:
            strength = highlight_strength_for_showcase(showcase_motion_t, idx)
            visibility = SHOWCASE_RECT_VISIBILITY_BLEND + (1.0 - SHOWCASE_RECT_VISIBILITY_BLEND) * strength
            fill = blend_color(RECT_FILL, RECT_FILL_ACTIVE, visibility)
            stroke = blend_color(RECT_STROKE, RECT_STROKE_ACTIVE, visibility)
        draw_curve_strip(
            draw,
            project,
            bound,
            fill_rgba=fill,
            stroke_rgba=stroke,
            edge_width=RECT_EDGE_WIDTH_ACTIVE if idx == 0 else RECT_EDGE_WIDTH,
        )
    return apply_source_occlusion(overlay, frame)


def open_video_encoder() -> subprocess.Popen:
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s:v",
            f"{WIDTH}x{HEIGHT}",
            "-framerate",
            str(FPS),
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(OUT_VIDEO),
        ],
        stdin=subprocess.PIPE,
    )


def compose_output_frames(src_frames: list[Path]) -> list[tuple[float, Image.Image]]:
    if OUT_FRAMES_DIR.exists():
        shutil.rmtree(OUT_FRAMES_DIR)
    if KEEP_OUT_FRAMES:
        OUT_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    static_project = static_plane_projector(src_frames)
    sample_images: list[tuple[float, Image.Image]] = []
    sample_indices = {
        max(0, min(TOTAL_FRAMES - 1, int(round(t * FPS)))): t
        for t in [0.0, 0.8, 3.2, 7.0, 8.8, 11.0, 13.5, 16.5, 21.8]
    }
    encoder = None if KEEP_OUT_FRAMES else open_video_encoder()

    try:
        for out_idx in range(TOTAL_FRAMES):
            out_time = out_idx / FPS
            if out_time < INTRO_DRAW_DURATION:
                base = get_clean_intro_base(src_frames)
                frame = draw_rectangles_for_intro(base, out_time, static_project)
            elif out_time < INTRO_DRAW_DURATION + OPENING_DURATION:
                opening_t = out_time - INTRO_DRAW_DURATION
                source_time = OPENING_SOURCE_START + opening_t
                source_idx = source_frame_index_for_time(source_time, len(src_frames))
                base = Image.open(src_frames[source_idx]).convert("RGBA")
                frame = draw_first_rectangle_on_frame(base, active=True, project=static_project)
                frame = apply_geometry_edge_boost(frame, base, cache_key=source_idx)
            elif out_time < INTRO_DRAW_DURATION + OPENING_DURATION + REMAINING_RECT_DRAW_DURATION:
                freeze_t = out_time - INTRO_DRAW_DURATION - OPENING_DURATION
                source_idx = source_frame_index_for_time(FREEZE_SOURCE_TIME, len(src_frames))
                base = Image.open(src_frames[source_idx]).convert("RGBA")
                frame = draw_remaining_rectangles_freeze(base, freeze_t, static_project)
                frame = apply_geometry_edge_boost(frame, base, cache_key=source_idx)
            else:
                showcase_elapsed = out_time - INTRO_DRAW_DURATION - OPENING_DURATION - REMAINING_RECT_DRAW_DURATION
                source_time = SHOWCASE_SOURCE_START + showcase_elapsed
                source_idx = source_frame_index_for_time(source_time, len(src_frames))
                base = Image.open(src_frames[source_idx]).convert("RGBA")
                showcase_motion_t = showcase_motion_t_for_elapsed(showcase_elapsed)
                project = showcase_plane_projector(base, showcase_motion_t, cache_key=source_idx)
                frame = draw_rectangles_for_showcase(base, showcase_motion_t, project=project)
                frame = apply_geometry_edge_boost(frame, base, cache_key=source_idx)

            if out_idx in sample_indices:
                sample_images.append((sample_indices[out_idx], frame.convert("RGB").copy()))

            if KEEP_OUT_FRAMES:
                frame.save(OUT_FRAMES_DIR / f"frame_{out_idx:04d}.png", compress_level=1)
            else:
                assert encoder is not None and encoder.stdin is not None
                encoder.stdin.write(frame.convert("RGB").tobytes())
    finally:
        if encoder is not None and encoder.stdin is not None:
            encoder.stdin.close()
            return_code = encoder.wait()
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, encoder.args)

    return sample_images


def encode_video() -> None:
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(OUT_FRAMES_DIR / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(OUT_VIDEO),
        ],
        check=True,
    )


def make_contact_sheet(images: list[tuple[float, Image.Image]]) -> None:
    if not images:
        return

    tile_w = 320
    tile_h = 200
    cols = 3
    rows = int(math.ceil(len(images) / cols))
    sheet = Image.new("RGB", (tile_w * cols, tile_h * rows), CONTACT_SHEET_BG)
    for i, (t, im) in enumerate(images):
        thumb = im.copy()
        thumb.thumbnail((tile_w, tile_h - 20), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (tile_w, tile_h), CONTACT_TILE_BG)
        canvas.paste(thumb, ((tile_w - thumb.width) // 2, 0))
        label = f"t={t:.1f}s"
        draw = ImageDraw.Draw(canvas)
        draw.text((8, tile_h - 18), label, fill=CONTACT_LABEL)
        sheet.paste(canvas, ((i % cols) * tile_w, (i // cols) * tile_h))
    QA_CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(QA_CONTACT_SHEET)


def main() -> None:
    if not SRC_VIDEO.exists():
        raise FileNotFoundError(f"Missing source video: {SRC_VIDEO}")
    src_frames = ensure_source_frames()
    sample_images = compose_output_frames(src_frames)
    if KEEP_OUT_FRAMES:
        encode_video()
    make_contact_sheet(sample_images)
    print(f"Wrote {OUT_VIDEO}")
    print(f"Wrote {QA_CONTACT_SHEET}")


if __name__ == "__main__":
    main()
