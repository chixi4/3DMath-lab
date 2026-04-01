from __future__ import annotations

import os
import numpy as np

from manimlib import *


X_AXIS_MAX = 4.25
X_AXIS_MIN = -X_AXIS_MAX
Y_AXIS_MAX = 2.55
Y_AXIS_MIN = -Y_AXIS_MAX
Z_AXIS_MAX = 2.0
Z_AXIS_MIN = -Z_AXIS_MAX

SLICE_X0 = 2.0
SLICE_X1 = 2.3
CURVE_END = 4.15

THEME = os.environ.get("MANIM_THEME", "light").strip().lower()

if THEME == "dark":
    BACKGROUND = BLACK
    AXIS_COLOR = "#f4eef8"
    CURVE_COLOR = "#8d58ff"
    PLANE_FILL = "#f6c0cb"
    SLICE_FILL = "#c91ab7"
    VOLUME_FILL = "#de79ba"
    GUIDE_COLOR = "#bca4b6"
else:
    BACKGROUND = WHITE
    AXIS_COLOR = "#2f2438"
    CURVE_COLOR = "#8d58ff"
    PLANE_FILL = "#f6c0cb"
    SLICE_FILL = "#c91ab7"
    VOLUME_FILL = "#de79ba"
    GUIDE_COLOR = "#6f5b69"

AXIS_STROKE_WIDTH = 2.0
AXIS_ARROW_LENGTH = 0.34
AXIS_ARROW_RADIUS = 0.12
AXIS_ARROW_STROKE_WIDTH = 0.8
AXIS_LABEL_FONT = "Times New Roman"
AXIS_LABEL_BUFF = 0.30
VOLUME_SURFACE_RESOLUTION = (18, 40)
CAP_SURFACE_RESOLUTION = (18, 48)
FACE_SURFACE_RESOLUTION = (12, 28)
CAP_POLYGON_POINT_COUNT = 192

START_CAMERA_PHI = 6.0
START_CAMERA_THETA = -92.0
START_CAMERA_ZOOM = 0.84
START_HOLD_TIME = 0.12
ANIMATION_RUN_TIME = 6.4
SHOWCASE_RUN_TIME = 10.0
END_HOLD_TIME = 2.0
CANONICAL_FOCAL_DISTANCE = 20.0
EXACT_CLIP_DURATION = START_HOLD_TIME + ANIMATION_RUN_TIME + SHOWCASE_RUN_TIME + END_HOLD_TIME

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
SHOWCASE_SLICE_STAGGER_START = 0.04
SHOWCASE_SLICE_STAGGER_END = 0.56
SHOWCASE_SLICE_DURATION = 0.16
OPENING_SAFE_ANGLE_FRACTION = 1.0
OPENING_HANDOFF_BLEND_START = 0.992
OPENING_STABLE_SWITCH_FRACTION = 1.0

ORIGIN_SHIFT = np.array([-1.35, -1.02, 0.0])
X_SCALE = 1.58
Y_SCALE = 1.86
Z_SCALE = Y_SCALE


def y_of(x: float) -> float:
    return float(np.sqrt(max(x, 0.0)))


def smootherstep_scalar(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def hermite_endpoint_progress(t: float, start_slope: float, end_slope: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    t2 = t * t
    t3 = t2 * t
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return float(h10 * start_slope + h01 + h11 * end_slope)


class RevolveSliceMGLBase(ThreeDScene):
    samples = 0
    default_camera_config = {"background_color": BACKGROUND}

    def to_world(self, x_ref: float, y_ref: float, z_ref: float) -> np.ndarray:
        return ORIGIN_SHIFT + np.array([X_SCALE * x_ref, -Z_SCALE * z_ref, Y_SCALE * y_ref], dtype=float)

    def cubic_bezier_value(self, p0, p1, p2, p3, t: float):
        mt = 1 - t
        return (mt ** 3) * p0 + 3 * (mt ** 2) * t * p1 + 3 * mt * (t ** 2) * p2 + (t ** 3) * p3

    def bezier_ease(self, t: float, c1: float, c2: float) -> float:
        return float(self.cubic_bezier_value(0.0, c1, c2, 1.0, t))

    def staggered_progress(self, t: float, start: float, end: float, c1: float, c2: float) -> float:
        if t <= start:
            return 0.0
        if t >= end:
            return 1.0
        local_t = (t - start) / (end - start)
        return self.bezier_ease(local_t, c1, c2)

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

    def normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        vector = np.array(vector, dtype=float)
        norm = np.linalg.norm(vector)
        if norm < 1e-8:
            return np.array([1.0, 0.0, 0.0], dtype=float)
        return vector / norm

    def perpendicular_basis(self, direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        direction = self.normalize_vector(direction)
        trial = np.array([0.0, 0.0, 1.0], dtype=float)
        if abs(np.dot(direction, trial)) > 0.9:
            trial = np.array([0.0, 1.0, 0.0], dtype=float)
        basis_1 = self.normalize_vector(np.cross(direction, trial))
        basis_2 = self.normalize_vector(np.cross(direction, basis_1))
        return basis_1, basis_2

    def make_tetra_arrowhead(self, start: np.ndarray, end: np.ndarray) -> Group:
        start = np.array(start, dtype=float)
        tip = np.array(end, dtype=float)
        direction = self.normalize_vector(tip - start)
        base_center = tip - direction * AXIS_ARROW_LENGTH
        basis_1, basis_2 = self.perpendicular_basis(direction)
        base_vertices = [
            base_center + AXIS_ARROW_RADIUS * (np.cos(angle) * basis_1 + np.sin(angle) * basis_2)
            for angle in (0.0, TAU / 3.0, 2.0 * TAU / 3.0)
        ]

        faces = Group(
            Polygon(tip, base_vertices[0], base_vertices[1]),
            Polygon(tip, base_vertices[1], base_vertices[2]),
            Polygon(tip, base_vertices[2], base_vertices[0]),
            Polygon(*base_vertices),
        )
        for face in faces:
            face.set_fill(AXIS_COLOR, opacity=1.0)
            face.set_stroke(AXIS_COLOR, width=AXIS_ARROW_STROKE_WIDTH, opacity=0.9)
        return faces

    def make_axis_with_arrow(self, start: np.ndarray, end: np.ndarray) -> Group:
        start = np.array(start, dtype=float)
        end = np.array(end, dtype=float)
        direction = self.normalize_vector(end - start)
        shaft_end = end - direction * (AXIS_ARROW_LENGTH * 0.92)
        shaft = Line(
            start,
            shaft_end,
            stroke_color=AXIS_COLOR,
            stroke_width=AXIS_STROKE_WIDTH,
        )
        return Group(shaft, self.make_tetra_arrowhead(start, end))

    def make_axes(self) -> Group:
        return Group(
            self.make_axis_with_arrow(self.to_world(X_AXIS_MIN, 0.0, 0.0), self.to_world(X_AXIS_MAX, 0.0, 0.0)),
            self.make_axis_with_arrow(self.to_world(0.0, Y_AXIS_MIN, 0.0), self.to_world(0.0, Y_AXIS_MAX, 0.0)),
            self.make_axis_with_arrow(self.to_world(0.0, 0.0, Z_AXIS_MIN), self.to_world(0.0, 0.0, Z_AXIS_MAX)),
        )

    def axis_positive_endpoints(self) -> dict[str, np.ndarray]:
        return {
            "x": self.to_world(X_AXIS_MAX, 0.0, 0.0),
            "y": self.to_world(0.0, Y_AXIS_MAX, 0.0),
            "z": self.to_world(0.0, 0.0, Z_AXIS_MAX),
        }

    def axis_positive_directions(self) -> dict[str, np.ndarray]:
        origin = self.to_world(0.0, 0.0, 0.0)
        return {
            axis_name: self.normalize_vector(endpoint - origin)
            for axis_name, endpoint in self.axis_positive_endpoints().items()
        }

    def axis_label_templates(self) -> dict[str, Text]:
        if hasattr(self, "_axis_label_templates"):
            return self._axis_label_templates

        label_specs = {
            "x": ("x", 0.52),
            "y": ("y", 0.54),
            "z": ("z", 0.58),
        }
        templates: dict[str, Text] = {}
        for axis_name, (content, height) in label_specs.items():
            label = Text(content, font=AXIS_LABEL_FONT, font_size=72, slant=ITALIC, color=AXIS_COLOR)
            label.set_height(height)
            label.set_fill(AXIS_COLOR, opacity=1.0)
            label.set_stroke(width=0.0)
            label.set_backstroke(BACKGROUND, width=2.5)
            templates[axis_name] = label
        self._axis_label_templates = templates
        return templates

    def axis_label_offsets(self, axis_name: str) -> tuple[float, float]:
        return {
            "x": (0.00, 0.02),
            "y": (0.00, 0.06),
            "z": (-0.02, 0.02),
        }[axis_name]

    def axis_label_world_position(self, axis_name: str) -> np.ndarray:
        endpoints = self.axis_positive_endpoints()
        directions = self.axis_positive_directions()
        tip = endpoints[axis_name]
        axis_direction = directions[axis_name]
        camera_location = np.array(self.camera.get_location(), dtype=float)
        to_camera = self.normalize_vector(camera_location - tip)
        side = np.cross(to_camera, axis_direction)
        if np.linalg.norm(side) < 1e-6:
            side, up = self.perpendicular_basis(to_camera)
        else:
            side = self.normalize_vector(side)
            up = self.normalize_vector(np.cross(side, to_camera))
        side_offset, up_offset = self.axis_label_offsets(axis_name)
        return (
            tip
            + AXIS_LABEL_BUFF * axis_direction
            + side_offset * side
            + up_offset * up
        )

    def make_axis_labels(self) -> Group:
        rotation = self.frame.get_orientation().as_matrix()
        labels = Group()
        for axis_name, template in self.axis_label_templates().items():
            label = template.copy()
            label.center()
            label.apply_matrix(rotation)
            label.move_to(self.axis_label_world_position(axis_name))
            labels.add(label)
        return labels

    def update_axis_labels(self, labels: Group) -> None:
        next_group = self.make_axis_labels()
        labels.set_submobjects([submob.copy() for submob in next_group.submobjects])

    def opening_slice_bounds(self) -> tuple[float, float]:
        return float(SLICE_X0), float(SLICE_X1)

    def make_region(self) -> Polygon:
        points = [self.to_world(0.0, 0.0, 0.0)]
        points.extend(self.to_world(x, 0.0, 0.0) for x in np.linspace(0.0, CURVE_END, 72))
        points.extend(self.to_world(x, y_of(x), 0.0) for x in np.linspace(CURVE_END, 0.0, 96))
        region = Polygon(*points)
        region.set_fill(PLANE_FILL, opacity=0.45)
        region.set_stroke(width=0.0)
        return region

    def make_curve(self) -> ParametricCurve:
        return ParametricCurve(
            lambda t: self.to_world(t, y_of(t), 0.0),
            t_range=(0.0, CURVE_END, 0.03),
            stroke_color=CURVE_COLOR,
            stroke_width=4.0,
        )

    def sort_surface_to_camera(self, surface: ParametricSurface) -> ParametricSurface:
        if hasattr(surface, "sort_faces_back_to_front"):
            camera_location = np.array(self.camera.get_location(), dtype=float)
            surface_center = np.array(surface.get_center(), dtype=float)
            surface.sort_faces_back_to_front(camera_location - surface_center)
        return surface

    def camera_sort_key(self, mob: Mobject) -> float:
        camera_location = np.array(self.camera.get_location(), dtype=float)
        mob_center = np.array(mob.get_center(), dtype=float)
        return -float(np.linalg.norm(mob_center - camera_location))

    def sort_mobject_to_camera(self, mob: Mobject) -> Mobject:
        for submob in list(getattr(mob, "submobjects", [])):
            self.sort_mobject_to_camera(submob)
        if getattr(mob, "submobjects", None):
            mob.sort(submob_func=self.camera_sort_key)
        if hasattr(mob, "sort_faces_back_to_front"):
            self.sort_surface_to_camera(mob)
        return mob

    def refresh_group_to_camera(self, mob: Mobject) -> None:
        self.sort_mobject_to_camera(mob)

    def set_group_opacity_scale(self, mob: Mobject, scale: float) -> None:
        scale = float(np.clip(scale, 0.0, 1.0))
        for submob in mob.get_family():
            base_opacity = getattr(submob, "_base_opacity", None)
            if base_opacity is not None and hasattr(submob, "set_opacity"):
                submob.set_opacity(base_opacity * scale)

    def make_surface(
        self,
        func,
        u_range,
        v_range,
        color,
        opacity,
        resolution=VOLUME_SURFACE_RESOLUTION,
    ) -> ParametricSurface:
        surface = ParametricSurface(
            func,
            u_range=u_range,
            v_range=v_range,
            color=color,
            opacity=opacity,
            resolution=resolution,
            shading=(0.0, 0.0, 0.0),
        )
        surface._base_opacity = float(opacity)
        return self.sort_surface_to_camera(surface)

    def make_cap_polygon(
        self,
        x: float,
        angle: float,
        *,
        color: str,
        opacity: float,
        point_count: int = CAP_POLYGON_POINT_COUNT,
    ) -> Polygon:
        radius = y_of(x)
        if angle >= TAU - 0.03:
            angles = np.linspace(0.0, TAU, point_count, endpoint=False)
            points = [
                self.to_world(x, radius * np.cos(theta), radius * np.sin(theta))
                for theta in angles
            ]
        else:
            arc_steps = max(12, int(np.ceil(point_count * angle / TAU)))
            angles = np.linspace(0.0, angle, arc_steps + 1)
            points = [self.to_world(x, 0.0, 0.0)]
            points.extend(
                self.to_world(x, radius * np.cos(theta), radius * np.sin(theta))
                for theta in angles
            )
        polygon = Polygon(*points, stroke_width=0.0)
        polygon.set_fill(color, opacity=opacity)
        polygon._base_opacity = float(opacity)
        return polygon

    def make_radial_face_between(
        self,
        x0: float,
        x1: float,
        angle: float,
        *,
        color: str,
        opacity: float,
        resolution=FACE_SURFACE_RESOLUTION,
    ) -> ParametricSurface:
        return self.make_surface(
            lambda u, v: self.to_world(
                interpolate(x0, x1, u),
                v * y_of(interpolate(x0, x1, u)) * np.cos(angle),
                v * y_of(interpolate(x0, x1, u)) * np.sin(angle),
            ),
            u_range=(0.0, 1.0),
            v_range=(0.0, 1.0),
            color=color,
            opacity=opacity,
            resolution=resolution,
        )

    def make_strip_face_between(
        self,
        x0: float,
        x1: float,
        *,
        color: str,
        opacity: float,
        resolution=FACE_SURFACE_RESOLUTION,
    ) -> ParametricSurface:
        return self.make_surface(
            lambda u, v: self.to_world(
                interpolate(x0, x1, u),
                v * y_of(interpolate(x0, x1, u)),
                0.0,
            ),
            u_range=(0.0, 1.0),
            v_range=(0.0, 1.0),
            color=color,
            opacity=opacity,
            resolution=resolution,
        )

    def make_sector_volume_between(
        self,
        x0: float,
        x1: float,
        angle: float,
        resolution=VOLUME_SURFACE_RESOLUTION,
        opacity_scale: float = 1.0,
        include_start_face: bool = True,
        prefer_polygon_caps_for_full_circle: bool = False,
    ) -> Group:
        opacity_scale = float(np.clip(opacity_scale, 0.0, 1.0))
        safe_angle = max(float(angle), 1e-4)
        sector = Group()

        lateral = self.make_surface(
            lambda u, v: self.to_world(
                interpolate(x0, x1, u),
                y_of(interpolate(x0, x1, u)) * np.cos(v),
                y_of(interpolate(x0, x1, u)) * np.sin(v),
            ),
            u_range=(0.0, 1.0),
            v_range=(0.0, safe_angle),
            color=VOLUME_FILL,
            opacity=0.36 * opacity_scale,
            resolution=resolution,
        )
        sector.add(lateral)

        if y_of(x0) > 1e-4:
            # Flat cap polygons avoid the polar-center face artifacts that show
            # up as noisy mottling on transparent disks, especially in the
            # black-background renders.
            cap_x0 = self.make_cap_polygon(
                x0,
                safe_angle,
                color=VOLUME_FILL,
                opacity=0.30 * opacity_scale,
            )
            sector.add(cap_x0)

        cap_x1 = self.make_cap_polygon(
            x1,
            safe_angle,
            color=SLICE_FILL,
            opacity=0.28 * opacity_scale,
        )
        sector.add(cap_x1)

        if angle < TAU - 0.03:
            if include_start_face:
                start_face = self.make_strip_face_between(
                    x0,
                    x1,
                    color=SLICE_FILL,
                    opacity=0.16 * opacity_scale,
                    resolution=FACE_SURFACE_RESOLUTION,
                )
                sector.add(start_face)
            end_face = self.make_radial_face_between(
                x0,
                x1,
                safe_angle,
                color=SLICE_FILL,
                opacity=0.24 * opacity_scale,
                resolution=FACE_SURFACE_RESOLUTION,
            )
            sector.add(end_face)

        return sector

    def showcase_slice_bounds(self) -> list[tuple[float, float]]:
        opening = self.opening_slice_bounds()
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
        other_bounds.sort(key=lambda bound: (abs(0.5 * (bound[0] + bound[1]) - opening_center), 0.5 * (bound[0] + bound[1])))
        return [opening, *other_bounds]

    def showcase_slice_angle_progress(self, showcase_t: float, slice_index: int) -> float:
        if slice_index == 0:
            return 1.0

        remaining_count = max(1, SHOWCASE_SLICE_COUNT - 1)
        starts = np.linspace(SHOWCASE_SLICE_STAGGER_START, SHOWCASE_SLICE_STAGGER_END, remaining_count)
        start = float(starts[slice_index - 1])
        end = min(1.0, start + SHOWCASE_SLICE_DURATION)
        return self.staggered_progress(showcase_t, start, end, 0.10, 0.82)

    def make_showcase_slice_group(
        self,
        showcase_t: float,
        opacity_scale: float = 1.0,
        include_first_slice: bool = True,
    ) -> Group:
        slices = Group()
        for slice_index, (x0, x1) in enumerate(self.showcase_slice_bounds()):
            if not include_first_slice and slice_index == 0:
                continue
            progress = self.showcase_slice_angle_progress(showcase_t, slice_index)
            slice_group = self.make_regular_showcase_slice(x0, x1)
            self.set_group_opacity_scale(slice_group, opacity_scale * progress)
            slices.add(slice_group)
        return self.sort_mobject_to_camera(slices)

    def sector_angle_at(self, t: float) -> float:
        return interpolate(0.0, TAU, self.staggered_progress(t, 0.22, 0.96, 0.08, 0.74))

    def opening_handoff_ready(self, opening_t: float) -> bool:
        completion = self.sector_angle_at(opening_t) / TAU
        return bool(completion >= OPENING_STABLE_SWITCH_FRACTION)

    def opening_handoff_blend(self, opening_t: float) -> float:
        completion = self.sector_angle_at(opening_t) / TAU
        if completion <= OPENING_HANDOFF_BLEND_START:
            return 0.0
        if completion >= OPENING_STABLE_SWITCH_FRACTION:
            return 1.0
        local_t = (completion - OPENING_HANDOFF_BLEND_START) / (
            OPENING_STABLE_SWITCH_FRACTION - OPENING_HANDOFF_BLEND_START
        )
        return smootherstep_scalar(local_t)

    def opening_dynamic_angle(self, opening_t: float) -> float:
        return min(self.sector_angle_at(opening_t), TAU * OPENING_SAFE_ANGLE_FRACTION)

    def make_first_slice_showcase_group(self, showcase_t: float) -> Group:
        first_x0, first_x1 = self.showcase_slice_bounds()[0]
        return self.make_regular_showcase_slice(first_x0, first_x1)

    def make_regular_showcase_slice(self, x0: float, x1: float) -> Group:
        return self.make_sector_volume_between(
            x0,
            x1,
            TAU,
            resolution=VOLUME_SURFACE_RESOLUTION,
            opacity_scale=1.0,
            include_start_face=False,
            prefer_polygon_caps_for_full_circle=False,
        )

    def showcase_camera_state(self, showcase_t: float) -> tuple[float, float, float, float, np.ndarray]:
        motion_t = float(np.clip(showcase_t, 0.0, 1.0))
        phi_deg, theta_deg, gamma_deg, zoom = self.hermite_interpolate(
            list(SHOWCASE_CAMERA_KNOTS),
            list(SHOWCASE_KEYFRAME_TIMES),
            motion_t,
        )
        center = self.hermite_interpolate(
            list(SHOWCASE_FRAME_CENTER_KNOTS),
            list(SHOWCASE_KEYFRAME_TIMES),
            motion_t,
        )
        return float(phi_deg), float(theta_deg), float(gamma_deg), float(zoom), np.array(center, dtype=float)

    def showcase_motion_camera_state(self, showcase_t: float) -> tuple[float, float, float, float, np.ndarray]:
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
        phi_deg, theta_deg, gamma_deg, zoom = self.hermite_interpolate(
            motion_camera_knots,
            motion_times,
            motion_t,
        )
        center = self.hermite_interpolate(
            motion_centers,
            motion_times,
            motion_t,
        )
        return float(phi_deg), float(theta_deg), float(gamma_deg), float(zoom), np.array(center, dtype=float)

    def apply_camera_values(self, phi_deg: float, theta_deg: float, gamma_deg: float, zoom: float, center: np.ndarray) -> None:
        # ManimGL's theta zero-point differs from the ManimCE OpenGL camera we
        # derived these knots from, so we keep the same +90deg correction that
        # made the CE OpenGL replay line up with the reference framing.
        self.frame.reorient(
            theta_deg + 90.0,
            phi_deg,
            gamma_deg,
            center=center,
            height=FRAME_HEIGHT / max(zoom, 1e-6),
        )
        self.frame.set_focal_distance(CANONICAL_FOCAL_DISTANCE)

    def apply_showcase_camera_state(self, showcase_t: float) -> None:
        self.apply_camera_values(*self.showcase_camera_state(showcase_t))

    def apply_showcase_motion_camera_state(self, showcase_t: float) -> None:
        self.apply_camera_values(*self.showcase_motion_camera_state(showcase_t))

    def clip_progress(self, clip_time: float) -> tuple[float, float, bool]:
        clip_time = float(np.clip(clip_time, 0.0, EXACT_CLIP_DURATION))
        opening_start = START_HOLD_TIME
        opening_end = START_HOLD_TIME + ANIMATION_RUN_TIME
        showcase_end = opening_end + SHOWCASE_RUN_TIME

        if clip_time <= opening_start:
            return 0.0, 0.0, False
        if clip_time < opening_end:
            return (clip_time - opening_start) / ANIMATION_RUN_TIME, 0.0, False

        showcase_t = 1.0 if clip_time >= showcase_end else (clip_time - opening_end) / SHOWCASE_RUN_TIME
        return 1.0, showcase_t, True

    def add_clip_state(self, clip_time: float) -> None:
        opening_t, showcase_t, showcase_started = self.clip_progress(clip_time)
        if showcase_started:
            self.apply_showcase_motion_camera_state(showcase_t)
        else:
            self.apply_showcase_camera_state(0.0)

        axes = self.make_axes()
        self.refresh_group_to_camera(axes)
        axis_labels = self.make_axis_labels()
        region = self.make_region()
        self.add(axes, axis_labels)
        self.add(region, set_depth_test=False)
        self.add(self.make_curve())
        if showcase_started:
            self.add(self.make_showcase_slice_group(showcase_t, include_first_slice=False))
            self.add(self.make_first_slice_showcase_group(showcase_t))
        else:
            if not self.opening_handoff_ready(opening_t):
                opening_x0, opening_x1 = self.opening_slice_bounds()
                self.add(
                    self.make_sector_volume_between(
                        opening_x0,
                        opening_x1,
                        self.opening_dynamic_angle(opening_t),
                        opacity_scale=1.0,
                        include_start_face=True,
                        prefer_polygon_caps_for_full_circle=True,
                    )
                )
            else:
                self.add(
                    self.make_first_slice_showcase_group(0.0)
                )


class RevolveSliceClipFrameMGL(RevolveSliceMGLBase):
    def construct(self):
        clip_time = float(os.environ.get("MANIM_CLIP_TIME", "0.0"))
        self.add_clip_state(clip_time)


class RevolveSliceShowcaseMGL(RevolveSliceMGLBase):
    def construct(self):
        opening_tracker = ValueTracker(0.0)
        showcase_tracker = ValueTracker(0.0)
        opening_complete = {"value": False}
        showcase_started = {"value": False}

        def update_frame(frame):
            if showcase_started["value"]:
                self.apply_showcase_motion_camera_state(showcase_tracker.get_value())
            else:
                self.apply_showcase_camera_state(0.0)

        self.frame.add_updater(update_frame)
        self.apply_showcase_camera_state(0.0)

        opening_x0, opening_x1 = self.opening_slice_bounds()

        opening_sector = Group()

        def update_opening_sector(mob):
            if showcase_started["value"] or self.opening_handoff_ready(opening_tracker.get_value()):
                mob.set_submobjects([])
                return

            next_group = self.make_sector_volume_between(
                opening_x0,
                opening_x1,
                self.opening_dynamic_angle(opening_tracker.get_value()),
                opacity_scale=1.0,
                include_start_face=True,
                prefer_polygon_caps_for_full_circle=True,
            )
            mob.set_submobjects([submob.copy() for submob in next_group.submobjects])
            self.refresh_group_to_camera(mob)

        opening_sector.add_updater(update_opening_sector)
        showcase_slices = []
        showcase_bounds = self.showcase_slice_bounds()
        first_x0, first_x1 = showcase_bounds[0]

        first_slice = Group()

        def update_first_slice(mob):
            if not opening_complete["value"] and not self.opening_handoff_ready(opening_tracker.get_value()):
                mob.set_submobjects([])
                return

            showcase_t = showcase_tracker.get_value() if showcase_started["value"] else 0.0
            next_group = self.make_first_slice_showcase_group(showcase_t)
            mob.set_submobjects([submob.copy() for submob in next_group.submobjects])
            self.refresh_group_to_camera(mob)

        first_slice.add_updater(update_first_slice)
        showcase_slices.append(first_slice)

        for slice_index, (x0, x1) in enumerate(showcase_bounds[1:], start=1):
            slice_group = self.make_sector_volume_between(
                x0,
                x1,
                TAU,
                resolution=VOLUME_SURFACE_RESOLUTION,
                opacity_scale=1.0,
                include_start_face=False,
                prefer_polygon_caps_for_full_circle=False,
            )

            def update_slice(mob, idx=slice_index):
                progress = 0.0 if not showcase_started["value"] else self.showcase_slice_angle_progress(
                    showcase_tracker.get_value(),
                    idx,
                )
                self.set_group_opacity_scale(mob, progress)
                self.refresh_group_to_camera(mob)

            self.set_group_opacity_scale(slice_group, 0.0)
            slice_group.add_updater(update_slice)
            showcase_slices.append(slice_group)
        showcase_group = Group(*showcase_slices)
        showcase_group.add_updater(lambda mob: self.refresh_group_to_camera(mob))

        axes = self.make_axes()
        axes.add_updater(lambda mob: self.refresh_group_to_camera(mob))
        axis_labels = Group()
        self.update_axis_labels(axis_labels)
        axis_labels.add_updater(lambda mob: self.update_axis_labels(mob))
        region = self.make_region()
        self.add(
            axes,
            axis_labels,
        )
        self.add(region, set_depth_test=False)
        self.add(
            self.make_curve(),
            opening_sector,
            showcase_group,
        )
        self.wait(START_HOLD_TIME)
        self.play(opening_tracker.animate.set_value(1.0), run_time=ANIMATION_RUN_TIME, rate_func=linear)
        opening_complete["value"] = True
        opening_sector.clear_updaters()
        self.remove(opening_sector)
        showcase_started["value"] = True
        self.play(showcase_tracker.animate.set_value(1.0), run_time=SHOWCASE_RUN_TIME, rate_func=linear)
        self.wait(END_HOLD_TIME)
