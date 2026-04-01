from __future__ import annotations

import os
import numpy as np

from manim import *
from manim.mobject.opengl.opengl_image_mobject import OpenGLImageMobject
from manim.mobject.utils import get_mobject_class, get_vectorized_mobject_class
from manim.utils.space_ops import rotation_about_z


PANEL_WIDTH = 1280
PANEL_HEIGHT = 720

X_AXIS_MAX = 4.25
X_AXIS_MIN = -X_AXIS_MAX
Y_AXIS_MAX = 2.55
Y_AXIS_MIN = -Y_AXIS_MAX
Z_AXIS_MAX = 2.0
Z_AXIS_MIN = -Z_AXIS_MAX

SLICE_X0 = 2.0
SLICE_X1 = 2.3
CURVE_END = 4.15

THEME = os.environ.get("MANIM_THEME", "dark").strip().lower()
VIEW_MODE = os.environ.get("MANIM_VIEW", "tracking").strip().lower()

if THEME == "light":
    BACKGROUND = WHITE
    AXIS_COLOR = "#2f2438"
    CURVE_COLOR = "#8d58ff"
    PLANE_FILL = "#f6c0cb"
    SLICE_FILL = "#c91ab7"
    VOLUME_FILL = "#de79ba"
    MESH_COLOR = "#85638b"
    GUIDE_COLOR = "#6f5b69"
else:
    BACKGROUND = BLACK
    AXIS_COLOR = "#f4eef8"
    CURVE_COLOR = "#8d58ff"
    PLANE_FILL = "#f6c0cb"
    SLICE_FILL = "#c91ab7"
    VOLUME_FILL = "#de79ba"
    MESH_COLOR = "#85638b"
    GUIDE_COLOR = "#bca4b6"
AXIS_STROKE_WIDTH = 1.65
AXIS_TIP_SIZE = 0.22
TIP_BASE_DIRECTION = normalize(np.array([1.0, 1.0, 1.0]))

CAMERA_PHI = 68 * DEGREES
CAMERA_THETA = -60 * DEGREES
CAMERA_GAMMA = 0 * DEGREES
CAMERA_ZOOM = 1.26
START_CAMERA_PHI = 6 * DEGREES
START_CAMERA_THETA = -92 * DEGREES
START_CAMERA_ZOOM = 0.84
END_CAMERA_PHI = 90 * DEGREES
END_CAMERA_THETA = 0 * DEGREES
END_CAMERA_ZOOM = 1.12
CAMERA_MID_PORTION = 0.50
ANIMATION_RUN_TIME = 6.4
START_HOLD_TIME = 0.12
END_HOLD_TIME = 0.4
VIDEO_FPS = 24
CANONICAL_FOCAL_DISTANCE = 20.0
PLANE_START_PORTION = 0.05
PLANE_END_PORTION = 0.86
SECTOR_START_PORTION = 0.22
SECTOR_END_PORTION = 0.96
PREVIEW_TIMES = (0.0, 0.22, 0.42, 0.62, 0.84, 1.0)
SHOWCASE_KEYFRAME_TIMES = (
    0.00,
    0.18,
    0.38,
    0.58,
    0.80,
    1.00,
)
X_LABEL_SCREEN_KNOTS = (
    np.array([3.41, -0.93], dtype=float),
    np.array([3.41, -0.93], dtype=float),
    np.array([3.41, -0.93], dtype=float),
    np.array([3.41, -0.93], dtype=float),
    np.array([3.41, -0.93], dtype=float),
    np.array([3.41, -0.93], dtype=float),
)
Y_LABEL_SCREEN_KNOTS = (
    np.array([-1.90, 3.68], dtype=float),
    np.array([-1.90, 3.68], dtype=float),
    np.array([-1.90, 3.68], dtype=float),
    np.array([-1.90, 3.68], dtype=float),
    np.array([-1.90, 3.68], dtype=float),
    np.array([-1.90, 3.68], dtype=float),
)
Z_LABEL_SCREEN_KNOTS = (
    np.array([-3.58, -1.24], dtype=float),
    np.array([-3.58, -1.24], dtype=float),
    np.array([-3.58, -1.24], dtype=float),
    np.array([-3.58, -1.24], dtype=float),
    np.array([-3.58, -1.24], dtype=float),
    np.array([-3.58, -1.24], dtype=float),
)
O_LABEL_SCREEN_KNOTS = (
    np.array([-1.50, -0.49], dtype=float),
    np.array([-1.50, -0.49], dtype=float),
    np.array([-1.50, -0.49], dtype=float),
    np.array([-1.50, -0.49], dtype=float),
    np.array([-1.50, -0.49], dtype=float),
    np.array([-1.50, -0.49], dtype=float),
)
SHOWCASE_CAMERA_KNOTS = (
    np.array([72.00, -66.00, 0.00, 0.74], dtype=float),
    np.array([69.00, -35.60, 0.00, 0.72], dtype=float),
    np.array([113.20, 2.20, 0.00, 0.61], dtype=float),
    np.array([109.30, 22.20, 0.00, 0.66], dtype=float),
    np.array([49.00, 101.20, 0.00, 0.72], dtype=float),
    np.array([43.00, 156.00, 0.00, 1.13], dtype=float),
)
SHOWCASE_FOCUS_LOCAL_KNOTS = (
    np.array([1.52, 0.42, 0.00], dtype=float),
    np.array([0.58, 0.61, 0.00], dtype=float),
    np.array([0.67, 0.84, 0.00], dtype=float),
    np.array([1.11, 0.20, 0.00], dtype=float),
    np.array([1.13, 0.99, 0.00], dtype=float),
    np.array([0.64, 1.77, 0.05], dtype=float),
)
SHOWCASE_CENTER_OFFSET_KNOTS = (
    np.array([-0.65, 0.65], dtype=float),
    np.array([0.00, 0.30], dtype=float),
    np.array([0.02, 0.24], dtype=float),
    np.array([0.06, 0.18], dtype=float),
    np.array([0.10, 0.10], dtype=float),
    np.array([0.12, 0.04], dtype=float),
)
SHOWCASE_FRAME_CENTER_KNOTS = (
    np.array([0.426989000, -0.395389000, 0.781200000], dtype=float),
    np.array([-0.433600000, -0.737019000, 1.134600000], dtype=float),
    np.array([-0.272962400, -0.798748800, 1.562400000], dtype=float),
    np.array([0.462684000, -0.843348000, 0.372000000], dtype=float),
    np.array([0.526193000, -0.929207000, 1.841400000], dtype=float),
    np.array([-0.238553200, -1.079584400, 3.292200000], dtype=float),
)

ORIGIN_SHIFT = np.array([-1.35, -1.02, 0.0])
X_SCALE = 1.58
Y_SCALE = 1.86
Z_SCALE = Y_SCALE
PLANE_START_ANGLE = -PI / 2

FRAME_ANGLES = (
    0.58 * PI,
    1.50 * PI,
    1.86 * PI,
    TAU,
)

STATIC_LATERAL_RESOLUTION = (30, 34)
STATIC_LATERAL_MESH = (16, 20)
STATIC_CAP_RESOLUTION = (18, 32)
STATIC_CAP_MESH = (12, 18)

ANIM_LATERAL_RESOLUTION = (18, 20)
ANIM_LATERAL_MESH = (10, 12)
ANIM_CAP_RESOLUTION = (12, 18)
ANIM_CAP_MESH = (8, 10)

REFERENCE_CAMERA = np.array([72 * DEGREES, -66 * DEGREES, 0.0, 0.74], dtype=float)
REFERENCE_FOCUS_LOCAL = np.array([1.52, 0.42, 0.0], dtype=float)
REFERENCE_CENTER_OFFSET = np.array([-0.65, 0.65], dtype=float)
REFERENCE_FRAME_CENTER = np.array(SHOWCASE_FRAME_CENTER_KNOTS[0], dtype=float)
SHOWCASE_RUN_TIME = 10.0
EXACT_CLIP_DURATION = START_HOLD_TIME + ANIMATION_RUN_TIME + SHOWCASE_RUN_TIME + END_HOLD_TIME
SHOWCASE_SLICE_COUNT = 10
SHOWCASE_SLICE_STAGGER_START = 0.04
SHOWCASE_SLICE_STAGGER_END = 0.82
SHOWCASE_SLICE_DURATION = 0.24


def y_of(x: float) -> float:
    return np.sqrt(x)


def smootherstep_scalar(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def env_vector(name: str, default: np.ndarray) -> np.ndarray:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return np.array(default, dtype=float)

    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != len(default):
        raise ValueError(f"{name} must have exactly {len(default)} comma-separated values.")
    return np.array([float(part) for part in parts], dtype=float)


class RevolveSliceBase(ThreeDScene):
    sector_angle = TAU

    def setup(self):
        config.background_color = BACKGROUND
        self.camera.background_color = BACKGROUND
        renderer = getattr(self, "renderer", None)
        if renderer is not None and hasattr(renderer, "background_color"):
            renderer.background_color = BACKGROUND

    def using_reference_view(self) -> bool:
        return VIEW_MODE in {"reference", "fixed", "static"}

    def using_opengl_renderer(self) -> bool:
        return config.renderer == RendererType.OPENGL

    def to_world(self, x_ref: float, y_ref: float, z_ref: float) -> np.ndarray:
        return ORIGIN_SHIFT + np.array(
            [X_SCALE * x_ref, -Z_SCALE * z_ref, Y_SCALE * y_ref],
        )

    def construct(self):
        self.set_camera_orientation(
            phi=CAMERA_PHI,
            theta=CAMERA_THETA,
            gamma=CAMERA_GAMMA,
            zoom=CAMERA_ZOOM,
        )
        self.add_scene_contents(self.sector_angle)

    def origin_world(self) -> np.ndarray:
        return self.to_world(0, 0, 0)

    def rotate_about_reference_x(self, mob: Mobject, angle: float) -> Mobject:
        return mob.rotate(angle, axis=RIGHT, about_point=self.origin_world())

    def rotate_world_point_about_reference_x(self, point: np.ndarray, angle: float) -> np.ndarray:
        origin = self.origin_world()
        rotation = rotation_matrix(angle, RIGHT)
        return origin + rotation @ (np.array(point) - origin)

    def camera_rotation_matrix(self, phi: float, theta: float, gamma: float) -> np.ndarray:
        matrices = [
            rotation_about_z(-theta - 90 * DEGREES),
            rotation_matrix(-phi, RIGHT),
            rotation_about_z(gamma),
        ]
        result = np.identity(3)
        for matrix in matrices:
            result = np.dot(matrix, result)
        return result

    def camera_offset_to_world(
        self,
        phi: float,
        theta: float,
        gamma: float,
        dx: float,
        dy: float,
        dz: float = 0.0,
    ) -> np.ndarray:
        rotation = self.camera_rotation_matrix(phi, theta, gamma)
        return np.array([dx, dy, dz], dtype=float) @ rotation

    def world_point_for_screen_offset(
        self,
        anchor_world: np.ndarray,
        phi: float,
        theta: float,
        gamma: float,
        zoom: float,
        dx: float,
        dy: float,
    ) -> np.ndarray:
        zoom = max(float(zoom), 1e-8)
        offset_world = self.camera_offset_to_world(
            phi,
            theta,
            gamma,
            dx / zoom,
            dy / zoom,
        )
        return np.array(anchor_world, dtype=float) - offset_world

    def project_points(
        self,
        points: np.ndarray | list,
        phi: float,
        theta: float,
        gamma: float,
        zoom: float,
        frame_center: np.ndarray,
    ) -> np.ndarray:
        rotation = self.camera_rotation_matrix(phi, theta, gamma)
        projected = np.array(points, dtype=float) - np.array(frame_center, dtype=float)
        projected = np.dot(projected, rotation.T)
        zs = projected[:, 2]
        factor = CANONICAL_FOCAL_DISTANCE / (CANONICAL_FOCAL_DISTANCE - zs)
        factor[(CANONICAL_FOCAL_DISTANCE - zs) < 0] = 10**6
        projected[:, 0] *= factor * zoom
        projected[:, 1] *= factor * zoom
        return projected

    def current_camera_values(self) -> tuple[float, float, float, float, np.ndarray]:
        camera = self.renderer.camera
        if self.using_opengl_renderer():
            theta, phi, gamma = np.array(camera.euler_angles, dtype=float)
            height = float(camera.get_height())
            zoom = config.frame_height / height if height > 1e-8 else 1.0
            frame_center = np.array(camera.get_center(), dtype=float)
            return float(phi), float(theta - 90 * DEGREES), float(gamma), float(zoom), frame_center
        return (
            float(camera.get_phi()),
            float(camera.get_theta()),
            float(camera.get_gamma()),
            float(camera.get_zoom()),
            np.array(camera.frame_center, dtype=float),
        )

    def fixed_in_frame_origin(self) -> np.ndarray:
        if self.using_opengl_renderer():
            return ORIGIN
        return np.array(self.renderer.camera.frame_center, dtype=float)

    def cubic_bezier_value(self, p0, p1, p2, p3, t: float):
        mt = 1 - t
        return (
            (mt**3) * p0
            + 3 * (mt**2) * t * p1
            + 3 * mt * (t**2) * p2
            + (t**3) * p3
        )

    def bezier_ease(self, t: float, c1: float, c2: float) -> float:
        return float(self.cubic_bezier_value(0.0, c1, c2, 1.0, t))

    def staggered_progress(self, t: float, start: float, end: float, c1: float, c2: float) -> float:
        if t <= start:
            return 0.0
        if t >= end:
            return 1.0
        local_t = (t - start) / (end - start)
        return self.bezier_ease(local_t, c1, c2)

    def smooth_motion_progress(self, t: float) -> float:
        t = float(np.clip(t, 0.0, 1.0))
        ease_in = 0.18
        ease_out = 0.18
        if t <= ease_in:
            u = t / ease_in
            # Quintic ease-in segment with zero start speed and unit speed at join.
            return ease_in * (3 * u**5 - 8 * u**4 + 6 * u**3)
        if t >= 1.0 - ease_out:
            u = (t - (1.0 - ease_out)) / ease_out
            # Quintic ease-out segment with unit speed at join and zero end speed.
            return 1.0 - ease_out + ease_out * (3 * u**5 - 7 * u**4 + 4 * u**3 + u)
        return t

    def hermite_interpolate(
        self,
        points: list[np.ndarray],
        times: list[float] | tuple[float, ...],
        t: float,
    ) -> np.ndarray:
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
                h10 = u3 - 2 * u2 + u
                h01 = -2 * u3 + 3 * u2
                h11 = u3 - u2
                return (
                    h00 * points[idx]
                    + h10 * dt * tangents[idx]
                    + h01 * points[idx + 1]
                    + h11 * dt * tangents[idx + 1]
                )

        return np.array(points[-1], dtype=float)

    def camera_state(self, t: float) -> np.ndarray:
        if self.using_reference_view():
            phi, theta, gamma, zoom = REFERENCE_CAMERA
            focus_world = self.to_world(*REFERENCE_FOCUS_LOCAL)
            reference_center_offset = env_vector("MANIM_REFERENCE_CENTER_OFFSET", REFERENCE_CENTER_OFFSET)
            frame_center = self.world_point_for_screen_offset(
                focus_world,
                phi,
                theta,
                gamma,
                zoom,
                reference_center_offset[0],
                reference_center_offset[1],
            )
            return np.array([phi, theta, gamma, zoom, *frame_center], dtype=float)

        motion_t = self.smooth_motion_progress(t)
        knot_times = list(PREVIEW_TIMES)
        camera_knots = [
            np.array([6 * DEGREES, -92 * DEGREES, 0.0, 0.58], dtype=float),
            np.array([14 * DEGREES, -90 * DEGREES, 0.0, 0.62], dtype=float),
            np.array([44 * DEGREES, -76 * DEGREES, 0.0, 0.64], dtype=float),
            np.array([72 * DEGREES, -36 * DEGREES, 0.0, 0.62], dtype=float),
            np.array([89.5 * DEGREES, -1.2 * DEGREES, 0.0, 0.66], dtype=float),
            np.array([73.5 * DEGREES, 42.0 * DEGREES, 0.0, 0.56], dtype=float),
        ]
        focus_knots = [
            np.array([0.72, 0.36, 0.0], dtype=float),
            np.array([0.80, 0.34, 0.0], dtype=float),
            np.array([0.92, 0.36, 0.0], dtype=float),
            np.array([1.00, 0.38, 0.0], dtype=float),
            np.array([1.02, 0.18, 0.0], dtype=float),
            np.array([1.06, 0.16, 0.0], dtype=float),
        ]
        center_offset_knots = [
            np.array([0.0, 0.0], dtype=float),
            np.array([0.0, 0.0], dtype=float),
            np.array([0.0, 0.0], dtype=float),
            np.array([0.0, 0.0], dtype=float),
            np.array([0.0, 0.46], dtype=float),
            np.array([0.0, 0.34], dtype=float),
        ]

        phi, theta, gamma, zoom = self.hermite_interpolate(camera_knots, knot_times, motion_t)
        focus_local = self.hermite_interpolate(focus_knots, knot_times, motion_t)
        focus_world = self.rotate_world_point_about_reference_x(
            self.to_world(*focus_local),
            self.plane_angle_at(t),
        )
        center_offset = self.hermite_interpolate(center_offset_knots, knot_times, motion_t)
        frame_center = self.world_point_for_screen_offset(
            focus_world,
            phi,
            theta,
            gamma,
            zoom,
            center_offset[0],
            center_offset[1],
        )
        return np.array([phi, theta, gamma, zoom, *frame_center], dtype=float)

    def showcase_camera_state(self, showcase_t: float) -> np.ndarray:
        motion_t = float(np.clip(showcase_t, 0.0, 1.0))
        knot_times = list(SHOWCASE_KEYFRAME_TIMES)
        return self.showcase_camera_state_from_knots(
            motion_t,
            knot_times,
            list(SHOWCASE_CAMERA_KNOTS),
            list(SHOWCASE_FOCUS_LOCAL_KNOTS),
            list(SHOWCASE_CENTER_OFFSET_KNOTS),
        )

    def showcase_motion_camera_state(self, showcase_t: float) -> np.ndarray:
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
        motion_focus_knots = [*list(SHOWCASE_FOCUS_LOCAL_KNOTS), np.array(SHOWCASE_FOCUS_LOCAL_KNOTS[0], dtype=float)]
        motion_offset_knots = [*list(SHOWCASE_CENTER_OFFSET_KNOTS), np.array(SHOWCASE_CENTER_OFFSET_KNOTS[0], dtype=float)]
        eased_t = smootherstep_scalar(np.clip(showcase_t, 0.0, 1.0))
        motion_t = eased_t * motion_times[-1]
        return self.showcase_camera_state_from_knots(
            motion_t,
            motion_times,
            motion_camera_knots,
            motion_focus_knots,
            motion_offset_knots,
        )

    def showcase_camera_state_from_knots(
        self,
        motion_t: float,
        knot_times: list[float],
        camera_knots: list[np.ndarray],
        focus_knots: list[np.ndarray],
        center_offset_knots: list[np.ndarray],
    ) -> np.ndarray:
        phi_deg, theta_deg, gamma_deg, zoom = self.hermite_interpolate(
            camera_knots,
            knot_times,
            motion_t,
        )
        focus_local = self.hermite_interpolate(
            focus_knots,
            knot_times,
            motion_t,
        )
        center_offset = self.hermite_interpolate(
            center_offset_knots,
            knot_times,
            motion_t,
        )
        focus_world = self.to_world(*focus_local)
        phi = phi_deg * DEGREES
        theta = theta_deg * DEGREES
        gamma = gamma_deg * DEGREES
        frame_center = self.world_point_for_screen_offset(
            focus_world,
            phi,
            theta,
            gamma,
            zoom,
            center_offset[0],
            center_offset[1],
        )
        return np.array([phi, theta, gamma, zoom, *frame_center], dtype=float)

    def apply_camera_values(self, state: np.ndarray) -> None:
        phi, theta, gamma, zoom, cx, cy, cz = state
        if self.using_opengl_renderer():
            camera = self.renderer.camera
            camera.set_phi(phi)
            camera.set_theta(theta + 90 * DEGREES)
            camera.set_gamma(gamma)
            camera.set_height(config.frame_height / zoom)
            camera.focal_distance = CANONICAL_FOCAL_DISTANCE / camera.get_height()
            camera.move_to(np.array([cx, cy, cz]))
            return
        self.renderer.camera.set_phi(phi)
        self.renderer.camera.set_theta(theta)
        self.renderer.camera.set_gamma(gamma)
        self.renderer.camera.set_zoom(zoom)
        self.renderer.camera.reset_rotation_matrix()
        self.renderer.camera._frame_center.move_to(np.array([cx, cy, cz]))

    def apply_camera_state(self, t: float) -> None:
        self.apply_camera_values(self.camera_state(t))

    def apply_showcase_camera_state(self, showcase_t: float) -> None:
        self.apply_camera_values(self.showcase_camera_state(showcase_t))

    def apply_showcase_motion_camera_state(self, showcase_t: float) -> None:
        self.apply_camera_values(self.showcase_motion_camera_state(showcase_t))

    def make_axis_line(
        self,
        start_ref: tuple[float, float, float],
        end_ref: tuple[float, float, float],
    ) -> Line:
        return Line(
            self.to_world(*start_ref),
            self.to_world(*end_ref),
            stroke_width=AXIS_STROKE_WIDTH,
            color=AXIS_COLOR,
        )

    def make_axes(self) -> Group:
        x_axis = self.make_axis_line((X_AXIS_MIN, 0, 0), (X_AXIS_MAX, 0, 0))
        y_axis = self.make_axis_line((0, Y_AXIS_MIN, 0), (0, Y_AXIS_MAX, 0))
        z_axis = self.make_axis_line((0, 0, Z_AXIS_MIN), (0, 0, Z_AXIS_MAX))
        return Group(x_axis, y_axis, z_axis)

    def axis_world_points(self, angle: float = 0.0) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        points = {
            "x": (self.to_world(X_AXIS_MAX - 0.82, 0.0, 0.0), self.to_world(X_AXIS_MAX - 0.26, 0.0, 0.0)),
            "y": (self.to_world(0.0, Y_AXIS_MAX - 1.08, 0.0), self.to_world(0.0, Y_AXIS_MAX - 0.56, 0.0)),
            "z": (self.to_world(0.0, 0.0, Z_AXIS_MAX - 0.86), self.to_world(0.0, 0.0, Z_AXIS_MAX - 0.26)),
        }
        return {
            axis_name: (
                self.rotate_world_point_about_reference_x(inner_world, angle),
                self.rotate_world_point_about_reference_x(end_world, angle),
            )
            for axis_name, (inner_world, end_world) in points.items()
        }

    def axis_positive_endpoints(self, angle: float = 0.0) -> dict[str, np.ndarray]:
        points = {
            "x": self.to_world(X_AXIS_MAX, 0.0, 0.0),
            "y": self.to_world(0.0, Y_AXIS_MAX, 0.0),
            "z": self.to_world(0.0, 0.0, Z_AXIS_MAX),
        }
        return {
            axis_name: self.rotate_world_point_about_reference_x(point, angle)
            for axis_name, point in points.items()
        }

    def axis_directions(self, angle: float = 0.0) -> dict[str, np.ndarray]:
        return {
            axis_name: normalize(end_world - inner_world)
            for axis_name, (inner_world, end_world) in self.axis_world_points(angle).items()
        }

    def orient_tip_to_direction(self, mob: Mobject, direction: np.ndarray) -> None:
        direction = normalize(direction)
        dot = np.clip(np.dot(TIP_BASE_DIRECTION, direction), -1.0, 1.0)
        axis = np.cross(TIP_BASE_DIRECTION, direction)
        axis_norm = np.linalg.norm(axis)

        if axis_norm < 1e-8:
            if dot < 0:
                fallback = np.cross(TIP_BASE_DIRECTION, RIGHT)
                if np.linalg.norm(fallback) < 1e-8:
                    fallback = np.cross(TIP_BASE_DIRECTION, UP)
                mob.rotate(PI, axis=normalize(fallback), about_point=ORIGIN)
            return

        mob.rotate(np.arccos(dot), axis=axis / axis_norm, about_point=ORIGIN)

    def screen_direction(self, start_world: np.ndarray, end_world: np.ndarray, fallback: np.ndarray) -> np.ndarray:
        phi, theta, gamma, zoom, frame_center = self.current_camera_values()
        projected = self.project_points(
            np.array([start_world, end_world]),
            phi,
            theta,
            gamma,
            zoom,
            frame_center,
        )
        direction = projected[1, :2] - projected[0, :2]
        norm = np.linalg.norm(direction)
        if norm < 1e-6:
            return fallback
        return direction / norm

    def axis_label_anchors(self, angle: float = 0.0) -> dict[str, np.ndarray]:
        anchors = {}
        axis_ends = self.axis_positive_endpoints(angle)
        axis_dirs = self.axis_directions(angle)
        anchor_backoffs = {
            "x": 0.06,
            "y": 0.05,
            "z": 0.08,
        }

        for axis_name, end_world in axis_ends.items():
            anchors[axis_name] = end_world - axis_dirs[axis_name] * anchor_backoffs[axis_name]
        return anchors

    def label_screen_offsets(self, t: float = 0.0) -> dict[str, np.ndarray]:
        label_t = float(np.clip(t, 0.0, 1.0))
        return {
            "x": self.hermite_interpolate(list(X_LABEL_SCREEN_KNOTS), list(PREVIEW_TIMES), label_t),
            "y": self.hermite_interpolate(list(Y_LABEL_SCREEN_KNOTS), list(PREVIEW_TIMES), label_t),
            "z": self.hermite_interpolate(list(Z_LABEL_SCREEN_KNOTS), list(PREVIEW_TIMES), label_t),
            "o": self.hermite_interpolate(list(O_LABEL_SCREEN_KNOTS), list(PREVIEW_TIMES), label_t),
        }

    def axis_label_positions(self, angle: float = 0.0, t: float = 0.0) -> dict[str, np.ndarray]:
        frame_center = self.fixed_in_frame_origin()
        screen_offsets = self.label_screen_offsets(t)
        return {
            axis_name: frame_center + np.array([offset_xy[0], offset_xy[1], 0.0])
            for axis_name, offset_xy in screen_offsets.items()
        }

    def make_axis_labels(self) -> dict[str, Text]:
        font = "Times New Roman"
        labels = {
            "x": Text("x", font=font, font_size=50, slant=ITALIC, color=AXIS_COLOR),
            "y": Text("y", font=font, font_size=52, slant=ITALIC, color=AXIS_COLOR),
            "z": Text("z", font=font, font_size=58, slant=ITALIC, color=AXIS_COLOR),
            "o": Text("O", font=font, font_size=44, slant=ITALIC, color=AXIS_COLOR),
        }
        return labels

    def clamp_fixed_in_frame_label(self, label: Text, margin: float = 0.18) -> Text:
        frame_center = np.array(self.renderer.camera.frame_center)
        half_width = config.frame_width / 2
        half_height = config.frame_height / 2

        min_x = frame_center[0] - half_width + margin
        max_x = frame_center[0] + half_width - margin
        min_y = frame_center[1] - half_height + margin
        max_y = frame_center[1] + half_height - margin

        left = label.get_left()[0]
        right = label.get_right()[0]
        bottom = label.get_bottom()[1]
        top = label.get_top()[1]

        shift_x = 0.0
        shift_y = 0.0
        if left < min_x:
            shift_x = min_x - left
        elif right > max_x:
            shift_x = max_x - right

        if bottom < min_y:
            shift_y = min_y - bottom
        elif top > max_y:
            shift_y = max_y - top

        if abs(shift_x) > 1e-6 or abs(shift_y) > 1e-6:
            label.shift(np.array([shift_x, shift_y, 0.0]))
        return label

    def make_axis_tip(self, axis_name: str, angle: float = 0.0) -> Tetrahedron:
        tip = Tetrahedron(
            edge_length=AXIS_TIP_SIZE,
            faces_config={
                "fill_color": AXIS_COLOR,
                "fill_opacity": 1.0,
                "stroke_width": 0.0,
                "stroke_opacity": 0.0,
                "shade_in_3d": True,
            },
            graph_config={
                "vertex_config": {
                    "radius": 0.0,
                    "fill_opacity": 0.0,
                    "stroke_opacity": 0.0,
                },
                "edge_config": {
                    "stroke_width": 0.0,
                    "stroke_opacity": 0.0,
                },
            },
        )

        direction = self.axis_directions(angle)[axis_name]
        endpoint = self.axis_positive_endpoints(angle)[axis_name]
        self.orient_tip_to_direction(tip, direction)
        tip_distance = np.linalg.norm(np.array(tip.vertex_coords[0]))
        tip.shift(endpoint - direction * tip_distance)
        return tip

    def make_axis_tips(self, angle: float = 0.0) -> dict[str, Tetrahedron]:
        tips = {}
        for name in ("x", "y", "z"):
            tips[name] = self.make_axis_tip(name, angle)
        return tips

    def plane_angle_at(self, t: float) -> float:
        if self.using_reference_view():
            return 0.0
        return interpolate(
            PLANE_START_ANGLE,
            0.0,
            self.staggered_progress(t, PLANE_START_PORTION, PLANE_END_PORTION, 0.18, 0.84),
        )

    def sector_angle_at(self, t: float) -> float:
        return interpolate(
            0.0,
            TAU,
            self.staggered_progress(t, SECTOR_START_PORTION, SECTOR_END_PORTION, 0.08, 0.74),
        )

    def add_axis_overlays(self, angle: float = 0.0, t: float = 0.0):
        label_positions = self.axis_label_positions(angle, t)
        labels = self.make_axis_labels()
        tips = self.make_axis_tips(angle)

        for name in ("x", "y", "z", "o"):
            labels[name].move_to(label_positions[name])
            self.clamp_fixed_in_frame_label(labels[name])
            labels[name].set_z_index(40)

        self.add_fixed_in_frame_mobjects(*labels.values())
        self.add(*tips.values())
        return labels, tips

    def make_region(self) -> VMobject:
        pts = [self.to_world(0, 0, 0)]
        pts.extend(self.to_world(x, 0, 0) for x in np.linspace(0, CURVE_END, 120))
        pts.extend(self.to_world(x, y_of(x), 0) for x in np.linspace(CURVE_END, 0, 180))
        region = get_vectorized_mobject_class()()
        region.set_points_as_corners([*pts, pts[0]])
        region.set_fill(PLANE_FILL, opacity=0.48)
        region.set_stroke(width=0)
        if hasattr(region, "set_shade_in_3d"):
            region.set_shade_in_3d(True)
        return region

    def make_curve(self) -> ParametricFunction:
        return ParametricFunction(
            lambda t: self.to_world(t, y_of(t), 0),
            t_range=[0, CURVE_END],
            color=CURVE_COLOR,
            stroke_width=4.2,
        )

    def make_guide_line(self) -> DashedLine:
        return DashedLine(
            self.to_world(0, 0, 0),
            self.to_world(SLICE_X0, y_of(SLICE_X0), 0),
            dash_length=0.11,
            dashed_ratio=0.56,
            color=GUIDE_COLOR,
            stroke_width=1.2,
        )

    def make_strip_edge(self) -> Line:
        return Line(
            self.to_world(SLICE_X0 - 0.02, y_of(SLICE_X0) - 0.02, -0.22),
            self.to_world(SLICE_X1 + 0.03, y_of(SLICE_X1) + 0.03, -0.42),
            color="#c6bcc7",
            stroke_width=1.9,
        )

    def make_surface(
        self,
        func,
        u_range,
        v_range,
        opacity: float,
        resolution=(26, 28),
        color: str = VOLUME_FILL,
        add_mesh: bool = True,
        mesh_resolution=(18, 20),
        mesh_width: float = 0.42,
    ) -> Group:
        surface = Surface(
            func,
            u_range=u_range,
            v_range=v_range,
            resolution=resolution,
            checkerboard_colors=[color, color],
            fill_opacity=opacity,
            stroke_opacity=0,
            shade_in_3d=True,
        )
        group = Group(surface)
        if add_mesh:
            mesh = Group()
            u0, u1 = u_range
            v0, v1 = v_range
            u_steps, v_steps = mesh_resolution

            for u in np.linspace(u0, u1, u_steps):
                mesh.add(
                    ParametricFunction(
                        lambda t, u_fixed=u: func(u_fixed, t),
                        t_range=[v0, v1],
                        color=MESH_COLOR,
                        stroke_width=mesh_width,
                    )
                )
            for v in np.linspace(v0, v1, v_steps):
                mesh.add(
                    ParametricFunction(
                        lambda t, v_fixed=v: func(t, v_fixed),
                        t_range=[u0, u1],
                        color=MESH_COLOR,
                        stroke_width=mesh_width,
                    )
                )
            group.add(mesh)
        return group

    def make_strip_face(self) -> Group:
        return self.make_surface(
            lambda u, v: self.to_world(
                interpolate(SLICE_X0, SLICE_X1, u),
                v * y_of(interpolate(SLICE_X0, SLICE_X1, u)),
                0,
            ),
            u_range=[0, 1],
            v_range=[0, 1],
            opacity=0.74,
            resolution=(8, 16),
            color=SLICE_FILL,
            add_mesh=False,
        )

    def make_sector_volume(
        self,
        angle: float,
        *,
        lateral_resolution=(STATIC_LATERAL_RESOLUTION),
        lateral_mesh=(STATIC_LATERAL_MESH),
        cap_resolution=(STATIC_CAP_RESOLUTION),
        cap_mesh=(STATIC_CAP_MESH),
        add_mesh: bool = True,
    ) -> Group:
        return self.make_sector_volume_between(
            SLICE_X0,
            SLICE_X1,
            angle,
            lateral_resolution=lateral_resolution,
            lateral_mesh=lateral_mesh,
            cap_resolution=cap_resolution,
            cap_mesh=cap_mesh,
            add_mesh=add_mesh,
        )

    def make_sector_volume_between(
        self,
        x0: float,
        x1: float,
        angle: float,
        *,
        lateral_resolution=(STATIC_LATERAL_RESOLUTION),
        lateral_mesh=(STATIC_LATERAL_MESH),
        cap_resolution=(STATIC_CAP_RESOLUTION),
        cap_mesh=(STATIC_CAP_MESH),
        add_mesh: bool = True,
    ) -> Group:
        if angle <= 1e-4:
            return Group()

        angle = float(angle)
        sector = Group()

        lateral = self.make_surface(
            lambda u, v: self.to_world(
                interpolate(x0, x1, u),
                y_of(interpolate(x0, x1, u)) * np.cos(v),
                y_of(interpolate(x0, x1, u)) * np.sin(v),
            ),
            u_range=[0, 1],
            v_range=[0, angle],
            opacity=0.33,
            resolution=lateral_resolution,
            color=VOLUME_FILL,
            add_mesh=add_mesh,
            mesh_resolution=lateral_mesh,
        )
        sector.add(lateral)

        if y_of(x0) > 1e-4:
            cap_x0 = self.make_surface(
                lambda u, v: self.to_world(
                    x0,
                    u * y_of(x0) * np.cos(v),
                    u * y_of(x0) * np.sin(v),
                ),
                u_range=[0, 1],
                v_range=[0, angle],
                opacity=0.29,
                resolution=cap_resolution,
                color=VOLUME_FILL,
                add_mesh=add_mesh,
                mesh_resolution=cap_mesh,
            )
            sector.add(cap_x0)

        cap_x1 = self.make_surface(
            lambda u, v: self.to_world(
                x1,
                u * y_of(x1) * np.cos(v),
                u * y_of(x1) * np.sin(v),
            ),
            u_range=[0, 1],
            v_range=[0, angle],
            opacity=0.25,
            resolution=cap_resolution,
            color=SLICE_FILL,
            add_mesh=add_mesh,
            mesh_resolution=cap_mesh,
        )
        sector.add(cap_x1)

        if angle < TAU - 0.035:
            end_face = self.make_surface(
                lambda u, v: self.to_world(
                    interpolate(x0, x1, u),
                    v * y_of(interpolate(x0, x1, u)) * np.cos(angle),
                    v * y_of(interpolate(x0, x1, u)) * np.sin(angle),
                ),
                u_range=[0, 1],
                v_range=[0, 1],
                opacity=0.22,
                resolution=(8, 16),
                color=SLICE_FILL,
                add_mesh=False,
            )
            sector.add(end_face)

        return sector

    def make_plane_group(self) -> Group:
        return Group(
            self.make_region(),
            self.make_curve(),
            self.make_strip_face(),
        )

    def make_static_plane_group(self) -> Group:
        return Group(
            self.make_region(),
            self.make_curve(),
        )

    def showcase_slice_bounds(self) -> list[tuple[float, float]]:
        edges = np.linspace(0.0, CURVE_END, SHOWCASE_SLICE_COUNT + 1)
        return [(float(edges[idx]), float(edges[idx + 1])) for idx in range(SHOWCASE_SLICE_COUNT)]

    def showcase_slice_angle_progress(self, showcase_t: float, slice_index: int) -> float:
        if slice_index == 0:
            return 1.0

        remaining_count = max(1, SHOWCASE_SLICE_COUNT - 1)
        starts = np.linspace(
            SHOWCASE_SLICE_STAGGER_START,
            SHOWCASE_SLICE_STAGGER_END,
            remaining_count,
        )
        start = float(starts[slice_index - 1])
        end = min(1.0, start + SHOWCASE_SLICE_DURATION)
        return self.staggered_progress(showcase_t, start, end, 0.10, 0.82)

    def make_showcase_slice_group(self, showcase_t: float) -> Group:
        slices = Group()
        for slice_index, (x0, x1) in enumerate(self.showcase_slice_bounds()):
            progress = self.showcase_slice_angle_progress(showcase_t, slice_index)
            angle = TAU * progress
            if angle <= 1e-4:
                continue
            slices.add(
                self.make_sector_volume_between(
                    x0,
                    x1,
                    angle,
                    lateral_resolution=(6, 10),
                    lateral_mesh=(3, 5),
                    cap_resolution=(5, 8),
                    cap_mesh=(3, 5),
                    add_mesh=False,
                )
            )
        return slices

    def add_animation_state(self, t: float) -> None:
        self.apply_camera_state(t)
        opening_x0, opening_x1 = self.showcase_slice_bounds()[0]
        self.add(self.make_axes())
        self.add(self.make_static_plane_group())
        self.add(
            self.make_sector_volume_between(
                opening_x0,
                opening_x1,
                self.sector_angle_at(t),
                lateral_resolution=ANIM_LATERAL_RESOLUTION,
                lateral_mesh=ANIM_LATERAL_MESH,
                cap_resolution=ANIM_CAP_RESOLUTION,
                cap_mesh=ANIM_CAP_MESH,
                add_mesh=False,
            )
        )
        self.add_axis_overlays(0.0, t=t)

    def add_scene_contents(self, angle: float) -> None:
        self.add(self.make_axes())
        self.add(self.make_plane_group())
        self.add(self.make_sector_volume(angle))
        self.add_axis_overlays(t=np.clip(angle / TAU, 0.0, 1.0))

    def add_showcase_state(self, showcase_t: float) -> None:
        self.apply_showcase_camera_state(showcase_t)
        self.add(self.make_axes())
        self.add(self.make_static_plane_group())
        self.add(self.make_showcase_slice_group(1.0))
        self.add_axis_overlays(t=1.0)


class Frame01(RevolveSliceBase):
    sector_angle = FRAME_ANGLES[0]


class Frame02(RevolveSliceBase):
    sector_angle = FRAME_ANGLES[1]


class Frame03(RevolveSliceBase):
    sector_angle = FRAME_ANGLES[2]


class Frame04(RevolveSliceBase):
    sector_angle = FRAME_ANGLES[3]


class PreviewFrame01(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[0])


class PreviewFrame02(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[1])


class PreviewFrame03(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[2])


class PreviewFrame04(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[3])


class PreviewFrame05(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[4])


class PreviewFrame06(RevolveSliceBase):
    def construct(self):
        self.add_animation_state(PREVIEW_TIMES[5])


class StateFrame(RevolveSliceBase):
    def construct(self):
        t = float(os.environ.get("MANIM_STATE_T", "0.0"))
        self.add_animation_state(np.clip(t, 0.0, 1.0))


class ShowcasePreview01(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[0])


class ShowcasePreview02(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[1])


class ShowcasePreview03(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[2])


class ShowcasePreview04(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[3])


class ShowcasePreview05(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[4])


class ShowcasePreview06(RevolveSliceBase):
    def construct(self):
        self.add_showcase_state(SHOWCASE_KEYFRAME_TIMES[5])


class ShowcaseStateFrame(RevolveSliceBase):
    def construct(self):
        showcase_t = float(os.environ.get("MANIM_SHOWCASE_T", "0.0"))
        self.add_showcase_state(np.clip(showcase_t, 0.0, 1.0))


class ExactClipFrame(RevolveSliceBase):
    def clip_progress(self, clip_time: float) -> tuple[float, float, bool]:
        clip_time = float(np.clip(clip_time, 0.0, EXACT_CLIP_DURATION))
        opening_start = START_HOLD_TIME
        opening_end = START_HOLD_TIME + ANIMATION_RUN_TIME
        showcase_end = opening_end + SHOWCASE_RUN_TIME

        if clip_time <= opening_start:
            return 0.0, 0.0, False
        if clip_time < opening_end:
            opening_t = (clip_time - opening_start) / ANIMATION_RUN_TIME
            return float(np.clip(opening_t, 0.0, 1.0)), 0.0, False

        showcase_t = 1.0 if clip_time >= showcase_end else (clip_time - opening_end) / SHOWCASE_RUN_TIME
        return 1.0, float(np.clip(showcase_t, 0.0, 1.0)), True

    def add_clip_state(self, clip_time: float) -> None:
        opening_t, showcase_t, showcase_started = self.clip_progress(clip_time)
        opening_x0, opening_x1 = self.showcase_slice_bounds()[0]

        if showcase_started:
            self.apply_showcase_motion_camera_state(showcase_t)
        else:
            self.apply_showcase_camera_state(0.0)

        self.add(self.make_axes())
        self.add(self.make_static_plane_group())

        if showcase_started:
            self.add(self.make_showcase_slice_group(showcase_t))
        else:
            self.add(
                self.make_sector_volume_between(
                    opening_x0,
                    opening_x1,
                    self.sector_angle_at(opening_t),
                    lateral_resolution=(8, 12),
                    lateral_mesh=(4, 6),
                    cap_resolution=(6, 10),
                    cap_mesh=(4, 6),
                    add_mesh=False,
                )
            )

        self.add(*self.make_axis_tips(0.0).values())

    def construct(self):
        clip_time = float(os.environ.get("MANIM_CLIP_TIME", "0.0"))
        self.add_clip_state(clip_time)


class CanonicalFramePlayback(Scene):
    def construct(self):
        frame_path = os.environ.get("MANIM_CANONICAL_FRAME", "").strip()
        if not frame_path:
            raise ValueError("MANIM_CANONICAL_FRAME is required.")

        if config.renderer == RendererType.OPENGL:
            image = OpenGLImageMobject(
                frame_path,
                width=config.frame_width,
                height=config.frame_height,
                resampling_algorithm=RESAMPLING_ALGORITHMS["nearest"],
                opacity=1.0,
                gloss=0.0,
                shadow=0.0,
            )
        else:
            image = ImageMobject(frame_path, scale_to_resolution=config.pixel_height)
            image.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
            image.stretch_to_fit_width(config.frame_width)
            image.stretch_to_fit_height(config.frame_height)
        image.move_to(ORIGIN)
        self.add(image)


class RevolveSliceAnimation(RevolveSliceBase):
    def construct(self):
        self.apply_showcase_camera_state(0.0)

        timeline = ValueTracker(0.0)
        showcase_timeline = ValueTracker(0.0)
        showcase_started = [False]
        self.add(timeline, showcase_timeline)

        camera_driver = get_mobject_class()()
        camera_driver.add_updater(
            lambda mob: self.apply_showcase_motion_camera_state(showcase_timeline.get_value())
            if showcase_started[0]
            else self.apply_showcase_camera_state(0.0)
        )
        self.add(camera_driver)

        opening_x0, opening_x1 = self.showcase_slice_bounds()[0]
        axes_group = self.make_axes()
        plane_group = self.make_static_plane_group()

        scene_mobjects = [axes_group, plane_group]
        if self.using_opengl_renderer():
            for slice_index, (x0, x1) in enumerate(self.showcase_slice_bounds()):
                slice_group = self.make_sector_volume_between(
                    x0,
                    x1,
                    TAU,
                    lateral_resolution=(8, 12),
                    lateral_mesh=(4, 6),
                    cap_resolution=(6, 10),
                    cap_mesh=(4, 6),
                    add_mesh=False,
                )
                slice_group.set_opacity(0.0)

                def update_slice(mob, idx=slice_index):
                    if idx == 0:
                        progress = 1.0 if showcase_started[0] else self.sector_angle_at(timeline.get_value()) / TAU
                    else:
                        progress = 0.0 if not showcase_started[0] else self.showcase_slice_angle_progress(
                            showcase_timeline.get_value(),
                            idx,
                        )
                    mob.set_opacity(np.clip(progress, 0.0, 1.0))

                slice_group.add_updater(update_slice)
                scene_mobjects.append(slice_group)
        else:
            sector_group = always_redraw(
                lambda: self.make_showcase_slice_group(showcase_timeline.get_value())
                if showcase_started[0]
                else self.make_sector_volume_between(
                    opening_x0,
                    opening_x1,
                    self.sector_angle_at(timeline.get_value()),
                    lateral_resolution=(8, 12),
                    lateral_mesh=(4, 6),
                    cap_resolution=(6, 10),
                    cap_mesh=(4, 6),
                    add_mesh=False,
                )
            )
            scene_mobjects.append(sector_group)

        axis_tips = self.make_axis_tips(0.0)
        scene_mobjects.extend(axis_tips.values())

        self.add(*scene_mobjects)
        self.wait(START_HOLD_TIME)
        self.play(timeline.animate.set_value(1.0), run_time=ANIMATION_RUN_TIME, rate_func=linear)
        showcase_started[0] = True
        self.play(showcase_timeline.animate.set_value(1.0), run_time=SHOWCASE_RUN_TIME, rate_func=linear)
        self.wait(END_HOLD_TIME)
