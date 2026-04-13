from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
from manimlib import *
from PIL import Image, ImageDraw
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
FINAL_DIR = os.path.join(REPO_ROOT, "src", "final-animation")
if FINAL_DIR not in sys.path:
    sys.path.insert(0, FINAL_DIR)

CORE_PATH = os.path.join(FINAL_DIR, "revolve-slice-core.py")
CORE_SPEC = importlib.util.spec_from_file_location("revolve_slice_core", CORE_PATH)
if CORE_SPEC is None or CORE_SPEC.loader is None:
    raise ImportError(f"Could not load revolve-slice-core.py from {CORE_PATH}")
base_scene = importlib.util.module_from_spec(CORE_SPEC)
CORE_SPEC.loader.exec_module(base_scene)


BACKGROUND = "#05070b"
AXIS_COLOR = "#f6f1e8"
CURVE_COLOR = "#8667ff"
PLANE_FILL = "#ffd5e6"
PLANE_EDGE = "#ffe5ef"
VOLUME_FILL = "#37d8df"
CAP_FILL = "#6ae9eb"
MESH_COLOR = "#168d90"
GUIDE_COLOR = "#c8cdd5"
BOTTOM_FILL = "#d9dce2"
END_FACE_FILL = "#dfe5ea"
END_FACE_OPACITY = 1.0
BOTTOM_MESH_COLOR = "#6d7782"
AXIS_LABEL_FILL = "#fffdf7"
GRID_LINE_RGBA = (255, 255, 255, 255)
CURVE_END = 4.0
SWEEP_DIRECTION = -1.0
SHOW_REFERENCE_PLANE = False
SHOW_SWEEP_FACE = True
REFERENCE_PREVIEW_PROGRESS = 0.56

ROTATION_RUN_TIME = 6.0
START_HOLD_TIME = 0.6
END_HOLD_TIME = 1.0

FIXED_CAMERA = np.array([70.00, -45.00, 0.00, 0.50], dtype=float)
FIXED_FRAME_CENTER = np.array([0.00, 0.00, 0.00], dtype=float)
REFERENCE_WORLD_ORIGIN_SHIFT = np.array([0.00, 0.00, -1.00], dtype=float)
REFERENCE_WORLD_SCALE = np.array([1.86, 1.86, 1.86], dtype=float)
REFERENCE_THETA_OFFSET = 90.00
REFERENCE_FOCAL_DISTANCE = 100.00
TOP_MESH_RING_COUNT = 24
OUTER_WALL_SPOKE_COUNT = 28
TOP_TEXTURE_GRID_COUNT = OUTER_WALL_SPOKE_COUNT
WALL_TEXTURE_HEIGHT_COUNT = 14
REFERENCE_TEXTURE_SIZE = 4096
REFERENCE_LABEL_HEIGHT = 0.60
TOP_SURFACE_RESOLUTION = (88, 300)
OUTER_WALL_RESOLUTION = (56, 300)
BOTTOM_SURFACE_RESOLUTION = (56, 300)
INNER_CAP_RESOLUTION = (48, 24)
OUTER_CAP_RESOLUTION = (84, 36)
REFERENCE_X_SAMPLES = 240
REFERENCE_CURVE_SAMPLES = 360
REFERENCE_CURVE_STEP = 0.008
REFERENCE_TEXTURE_DIR = os.path.join(REPO_ROOT, "assets", "reference-textures")
REFERENCE_LABEL_DIR = os.path.join(REPO_ROOT, "assets", "reference-labels")
REFERENCE_LABEL_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
GRID_SURFACE_EPSILON = 0.01


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[index:index + 2], 16) for index in (0, 2, 4))


def blend_hex(color_a: str, color_b: str, alpha: float) -> tuple[int, int, int]:
    rgb_a = np.array(hex_to_rgb(color_a), dtype=float)
    rgb_b = np.array(hex_to_rgb(color_b), dtype=float)
    blended = np.clip((alpha * rgb_a) + ((1.0 - alpha) * rgb_b), 0.0, 255.0)
    return tuple(int(round(value)) for value in blended)


def make_flat_texture(path: str, color: tuple[int, ...]) -> str:
    mode = "RGBA" if len(color) == 4 else "RGB"
    image = Image.new(mode, (REFERENCE_TEXTURE_SIZE, REFERENCE_TEXTURE_SIZE), color=color)
    image.save(path)
    return path


def make_grid_texture(
    path: str,
    *,
    base_color: tuple[int, ...],
    line_color: tuple[int, ...],
    major_line_color: tuple[int, ...],
    columns: int,
    rows: int,
    line_width: int,
    major_line_width: int,
    major_column_every: int = 0,
    major_row_every: int = 0,
    include_row_edges: bool = False,
) -> str:
    mode = "RGBA" if len(base_color) == 4 else "RGB"
    image = Image.new(mode, (REFERENCE_TEXTURE_SIZE, REFERENCE_TEXTURE_SIZE), color=base_color)
    draw = ImageDraw.Draw(image)
    max_coord = REFERENCE_TEXTURE_SIZE - 1

    for index in range(1, columns + 1):
        x_coord = round(max_coord * index / (columns + 1))
        is_major = major_column_every > 0 and (index % major_column_every == 0)
        draw.line(
            (x_coord, 0, x_coord, max_coord),
            fill=(major_line_color if is_major else line_color),
            width=(major_line_width if is_major else line_width),
        )

    for index in range(1, rows + 1):
        y_coord = round(max_coord * index / (rows + 1))
        is_major = major_row_every > 0 and (index % major_row_every == 0)
        draw.line(
            (0, y_coord, max_coord, y_coord),
            fill=(major_line_color if is_major else line_color),
            width=(major_line_width if is_major else line_width),
        )

    if include_row_edges:
        draw.line((0, 0, max_coord, 0), fill=major_line_color, width=major_line_width)
        draw.line((0, max_coord, max_coord, max_coord), fill=major_line_color, width=major_line_width)

    image.save(path)
    return path


def ensure_reference_textures() -> dict[str, str]:
    os.makedirs(REFERENCE_TEXTURE_DIR, exist_ok=True)
    top_fill_path = os.path.join(REFERENCE_TEXTURE_DIR, "sqrtx-top-fill.png")
    wall_fill_path = os.path.join(REFERENCE_TEXTURE_DIR, "sqrtx-wall-fill.png")
    top_grid_path = os.path.join(REFERENCE_TEXTURE_DIR, "sqrtx-top-grid-lines.png")
    wall_grid_path = os.path.join(REFERENCE_TEXTURE_DIR, "sqrtx-wall-grid-lines.png")

    make_flat_texture(
        top_fill_path,
        blend_hex(VOLUME_FILL, BACKGROUND, 0.88),
    )
    make_flat_texture(
        wall_fill_path,
        blend_hex(VOLUME_FILL, BACKGROUND, 0.82),
    )
    make_grid_texture(
        top_grid_path,
        base_color=(0, 0, 0, 0),
        line_color=GRID_LINE_RGBA,
        major_line_color=GRID_LINE_RGBA,
        columns=TOP_MESH_RING_COUNT,
        rows=TOP_TEXTURE_GRID_COUNT,
        line_width=4,
        major_line_width=7,
        major_column_every=4,
        major_row_every=4,
        include_row_edges=True,
    )
    make_grid_texture(
        wall_grid_path,
        base_color=(0, 0, 0, 0),
        line_color=GRID_LINE_RGBA,
        major_line_color=GRID_LINE_RGBA,
        columns=WALL_TEXTURE_HEIGHT_COUNT,
        rows=OUTER_WALL_SPOKE_COUNT,
        line_width=4,
        major_line_width=7,
        major_column_every=2,
        major_row_every=4,
        include_row_edges=True,
    )
    return {
        "top_fill": top_fill_path,
        "wall_fill": wall_fill_path,
        "top_grid": top_grid_path,
        "wall_grid": wall_grid_path,
    }


REFERENCE_TEXTURES = ensure_reference_textures()


def make_label_svg(path: str, text: str) -> str:
    font = TTFont(REFERENCE_LABEL_FONT_PATH)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    glyph_name = cmap[ord(text)]
    glyph = glyph_set[glyph_name]

    bounds_pen = BoundsPen(glyph_set)
    glyph.draw(bounds_pen)
    min_x, min_y, max_x, max_y = bounds_pen.bounds
    padding = 120.0

    path_pen = SVGPathPen(glyph_set)
    transform_pen = TransformPen(
        path_pen,
        (1, 0, 0, -1, -min_x + padding, max_y + padding),
    )
    glyph.draw(transform_pen)

    width = (max_x - min_x) + (2 * padding)
    height = (max_y - min_y) + (2 * padding)
    svg_markup = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}">'
        f'<path d="{path_pen.getCommands()}" fill="{AXIS_LABEL_FILL}" fill-rule="evenodd" clip-rule="evenodd" stroke="none"/>'
        '</svg>'
    )
    Path(path).write_text(svg_markup, encoding="utf-8")
    return path


def ensure_reference_label_textures() -> dict[str, str]:
    os.makedirs(REFERENCE_LABEL_DIR, exist_ok=True)
    label_paths: dict[str, str] = {}
    for axis_name in ("x", "y", "z"):
        label_path = os.path.join(REFERENCE_LABEL_DIR, f"sqrtx-axis-{axis_name}.svg")
        label_paths[axis_name] = make_label_svg(label_path, axis_name)
    return label_paths


REFERENCE_LABEL_TEXTURES = ensure_reference_label_textures()


for name, value in {
    "BACKGROUND": BACKGROUND,
    "AXIS_COLOR": AXIS_COLOR,
    "CURVE_COLOR": CURVE_COLOR,
    "PLANE_FILL": PLANE_FILL,
    "SLICE_FILL": PLANE_FILL,
    "VOLUME_FILL": VOLUME_FILL,
    "GUIDE_COLOR": GUIDE_COLOR,
}.items():
    setattr(base_scene, name, value)

for name, value in {
    "X_AXIS_MAX": 5.0,
    "X_AXIS_MIN": -5.0,
    "Y_AXIS_MAX": 2.8,
    "Y_AXIS_MIN": -2.8,
    "Z_AXIS_MAX": 5.0,
    "Z_AXIS_MIN": -5.0,
}.items():
    setattr(base_scene, name, value)

for name, value in {
    "ORIGIN_SHIFT": np.array(REFERENCE_WORLD_ORIGIN_SHIFT, dtype=float),
    "X_SCALE": float(REFERENCE_WORLD_SCALE[0]),
    "Y_SCALE": float(REFERENCE_WORLD_SCALE[1]),
    "Z_SCALE": float(REFERENCE_WORLD_SCALE[2]),
}.items():
    setattr(base_scene, name, value)


def y_of(x: float) -> float:
    return float(np.sqrt(max(x, 0.0)))


def env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value.strip() == "":
        return float(default)
    return float(raw_value)


class SqrtXReferenceBase(base_scene.RevolveSliceMGLBase):
    samples = 4
    default_camera_config = {"background_color": BACKGROUND}

    def show_axis_labels(self) -> bool:
        return os.environ.get("SQRTX_REFERENCE_SHOW_LABELS", "1").strip().lower() not in {"0", "false", "no"}

    def axis_label_offsets(self, axis_name: str) -> tuple[float, float]:
        phi_deg = float(self.resolved_reference_camera()[0][0])
        y_offset = (0.12, 0.18) if phi_deg >= 50.0 else (-0.18, 0.90)
        return {
            "x": (0.00, 0.02),
            "y": y_offset,
            "z": (-0.02, 0.02),
        }[axis_name]

    def axis_label_templates(self) -> dict[str, Mobject]:
        if hasattr(self, "_reference_axis_label_templates"):
            return self._reference_axis_label_templates

        templates: dict[str, Mobject] = {}
        line_style = dict(stroke_color=AXIS_LABEL_FILL, stroke_width=10.0)
        geometric_templates: dict[str, VGroup] = {
            "x": VGroup(
                Line(np.array([-0.42, 0.42, 0.0]), np.array([0.42, -0.42, 0.0]), **line_style),
                Line(np.array([-0.42, -0.42, 0.0]), np.array([0.42, 0.42, 0.0]), **line_style),
            ),
            "y": VGroup(
                Line(np.array([-0.34, 0.46, 0.0]), np.array([0.00, 0.10, 0.0]), **line_style),
                Line(np.array([0.34, 0.46, 0.0]), np.array([0.00, 0.10, 0.0]), **line_style),
                Line(np.array([0.00, 0.10, 0.0]), np.array([0.00, -0.48, 0.0]), **line_style),
            ),
            "z": VGroup(
                Line(np.array([-0.42, 0.40, 0.0]), np.array([0.42, 0.40, 0.0]), **line_style),
                Line(np.array([0.42, 0.40, 0.0]), np.array([-0.42, -0.40, 0.0]), **line_style),
                Line(np.array([-0.42, -0.40, 0.0]), np.array([0.42, -0.40, 0.0]), **line_style),
            ),
        }
        for axis_name, template in geometric_templates.items():
            label = template.copy()
            label.set_height(REFERENCE_LABEL_HEIGHT)
            label.set_stroke(AXIS_LABEL_FILL, opacity=1.0)
            templates[axis_name] = label
        self._reference_axis_label_templates = templates
        return templates

    def make_axis_labels(self) -> Group:
        rotation = self.frame.get_orientation().as_matrix()
        labels = Group()
        for axis_name, template in self.axis_label_templates().items():
            label = template.copy()
            label.center()
            label.apply_matrix(rotation)
            label.move_to(self.axis_label_world_position(axis_name))
            label.deactivate_depth_test()
            label.set_z_index(10)
            labels.add(label)
        return labels

    def set_base_opacity(self, mob: Mobject, opacity: float) -> Mobject:
        mob._base_opacity = float(opacity)
        if hasattr(mob, "set_opacity"):
            mob.set_opacity(float(opacity))
        return mob

    def apply_camera_values(self, phi_deg: float, theta_deg: float, gamma_deg: float, zoom: float, center: np.ndarray) -> None:
        self.frame.reorient(
            theta_deg + REFERENCE_THETA_OFFSET,
            phi_deg,
            gamma_deg,
            center=np.array(center, dtype=float),
            height=FRAME_HEIGHT / max(zoom, 1e-6),
        )
        self.frame.set_focal_distance(REFERENCE_FOCAL_DISTANCE)

    def resolved_reference_camera(self) -> tuple[np.ndarray, np.ndarray]:
        camera = np.array(FIXED_CAMERA, dtype=float)
        center = np.array(FIXED_FRAME_CENTER, dtype=float)

        camera[0] = env_float("SQRTX_REFERENCE_PHI", camera[0])
        camera[1] = env_float("SQRTX_REFERENCE_THETA", camera[1])
        camera[2] = env_float("SQRTX_REFERENCE_GAMMA", camera[2])
        camera[3] = env_float("SQRTX_REFERENCE_ZOOM", camera[3])
        center[0] = env_float("SQRTX_REFERENCE_CENTER_X", center[0])
        center[1] = env_float("SQRTX_REFERENCE_CENTER_Y", center[1])
        center[2] = env_float("SQRTX_REFERENCE_CENTER_Z", center[2])
        return camera, center

    def apply_reference_camera(self) -> None:
        camera, center = self.resolved_reference_camera()
        self.apply_camera_values(
            float(camera[0]),
            float(camera[1]),
            float(camera[2]),
            float(camera[3]),
            center,
        )

    def eased_rotation_progress(self, progress: float) -> float:
        return base_scene.smootherstep_scalar(np.clip(progress, 0.0, 1.0))

    def rotation_angle(self, progress: float) -> float:
        return TAU * self.eased_rotation_progress(progress)

    def plane_visibility(self, progress: float) -> float:
        if progress <= 0.92:
            return 1.0
        if progress >= 1.0:
            return 0.0
        fade_t = (progress - 0.92) / 0.08
        return 1.0 - base_scene.smootherstep_scalar(fade_t)

    def make_reference_region(self) -> Group:
        points = [self.to_world(0.0, 0.0, 0.0)]
        points.extend(self.to_world(x, 0.0, 0.0) for x in np.linspace(0.0, CURVE_END, REFERENCE_X_SAMPLES))
        points.extend(self.to_world(x, y_of(x), 0.0) for x in np.linspace(CURVE_END, 0.0, REFERENCE_CURVE_SAMPLES))
        front = Polygon(*points)
        front.set_fill(PLANE_FILL, opacity=0.98)
        front.set_stroke(width=0.0)
        self.set_base_opacity(front, 0.98)

        back = Polygon(*reversed(points))
        back.set_fill(PLANE_FILL, opacity=0.98)
        back.set_stroke(width=0.0)
        self.set_base_opacity(back, 0.98)
        return Group(front, back)

    def make_reference_curve(self) -> ParametricCurve:
        curve = ParametricCurve(
            lambda t: self.to_world(t, y_of(t), 0.0),
            t_range=(0.0, CURVE_END, REFERENCE_CURVE_STEP),
            stroke_color=CURVE_COLOR,
            stroke_width=4.4,
        )
        return self.set_base_opacity(curve, 1.0)

    def make_reference_vertical_edge(self) -> Line:
        edge = Line(
            self.to_world(CURVE_END, 0.0, 0.0),
            self.to_world(CURVE_END, y_of(CURVE_END), 0.0),
            stroke_color=PLANE_EDGE,
            stroke_width=1.6,
        )
        return self.set_base_opacity(edge, 0.90)

    def make_reference_guide_line(self) -> DashedLine:
        guide = DashedLine(
            self.to_world(0.0, 0.0, 0.0),
            self.to_world(CURVE_END, 1.02, 0.0),
            dash_length=0.10,
            positive_space_ratio=0.56,
            stroke_color=GUIDE_COLOR,
            stroke_width=1.25,
        )
        return self.set_base_opacity(guide, 0.72)

    def make_plane_group(self, opacity_scale: float = 1.0) -> Group:
        if not SHOW_REFERENCE_PLANE:
            return Group()
        plane_group = Group(
            self.make_reference_region(),
            self.make_reference_curve(),
            self.make_reference_vertical_edge(),
            self.make_reference_guide_line(),
        )
        self.set_group_opacity_scale(plane_group, opacity_scale)
        return plane_group

    def rotate_point_about_y(self, radius: float, height: float, angle: float) -> np.ndarray:
        theta = SWEEP_DIRECTION * angle
        return self.to_world(radius * np.cos(theta), height, radius * np.sin(theta))

    def finalize_mesh_curve(self, curve: ParametricCurve, opacity: float) -> ParametricCurve:
        return self.set_base_opacity(curve, opacity)

    def make_textured_surface(
        self,
        func,
        *,
        u_range: tuple[float, float],
        v_range: tuple[float, float],
        texture_path: str,
        opacity: float,
        resolution: tuple[int, int],
    ) -> Surface:
        base_surface = ParametricSurface(
            func,
            u_range=u_range,
            v_range=v_range,
            color=WHITE,
            opacity=opacity,
            resolution=resolution,
            shading=(0.0, 0.0, 0.0),
        )
        textured_surface = TexturedSurface(base_surface, texture_path)
        textured_surface._base_opacity = float(opacity)
        textured_surface.set_opacity(float(opacity))
        return self.sort_surface_to_camera(textured_surface)

    def make_top_surface(self, angle: float) -> Surface:
        return self.make_textured_surface(
            lambda radius, theta: self.rotate_point_about_y(
                radius,
                y_of(radius),
                theta,
            ),
            u_range=(0.0, CURVE_END),
            v_range=(0.0, max(float(angle), 1e-4)),
            opacity=0.34,
            texture_path=REFERENCE_TEXTURES["top_fill"],
            resolution=TOP_SURFACE_RESOLUTION,
        )

    def make_top_mesh(self, angle: float) -> Group:
        return Group(
            self.make_textured_surface(
                lambda radius, theta: self.rotate_point_about_y(
                    radius,
                    y_of(radius) + GRID_SURFACE_EPSILON,
                    theta,
                ),
                u_range=(0.0, CURVE_END),
                v_range=(0.0, max(float(angle), 1e-4)),
                opacity=1.0,
                texture_path=REFERENCE_TEXTURES["top_grid"],
                resolution=TOP_SURFACE_RESOLUTION,
            ),
        )

    def make_outer_wall(self, angle: float) -> Surface:
        return self.make_textured_surface(
            lambda height, theta: self.rotate_point_about_y(
                CURVE_END,
                height,
                theta,
            ),
            u_range=(0.0, y_of(CURVE_END)),
            v_range=(0.0, max(float(angle), 1e-4)),
            opacity=0.30,
            texture_path=REFERENCE_TEXTURES["wall_fill"],
            resolution=OUTER_WALL_RESOLUTION,
        )

    def make_outer_wall_mesh(self, angle: float) -> Group:
        return Group(
            self.make_textured_surface(
                lambda height, theta: self.rotate_point_about_y(
                    CURVE_END + GRID_SURFACE_EPSILON,
                    height,
                    theta,
                ),
                u_range=(0.0, y_of(CURVE_END)),
                v_range=(0.0, max(float(angle), 1e-4)),
                opacity=1.0,
                texture_path=REFERENCE_TEXTURES["wall_grid"],
                resolution=OUTER_WALL_RESOLUTION,
            ),
        )

    def make_bottom_surface(self, angle: float) -> ParametricSurface:
        return self.make_surface(
            lambda radius, theta: self.rotate_point_about_y(radius, 0.0, theta),
            u_range=(0.0, CURVE_END),
            v_range=(0.0, max(float(angle), 1e-4)),
            color=BOTTOM_FILL,
            opacity=0.18,
            resolution=BOTTOM_SURFACE_RESOLUTION,
        )

    def make_bottom_mesh(self, angle: float) -> Group:
        return Group()

    def make_cap_face(self, angle: float) -> Group:
        split_x = 0.45
        split_y = y_of(split_x)

        inner_patch = self.make_surface(
            lambda y_value, alpha: self.rotate_point_about_y(
                (y_value * y_value) + alpha * (split_x - (y_value * y_value)),
                y_value,
                angle,
            ),
            u_range=(0.0, split_y),
            v_range=(0.0, 1.0),
            color=END_FACE_FILL,
            opacity=END_FACE_OPACITY,
            resolution=INNER_CAP_RESOLUTION,
        )
        outer_patch = self.make_surface(
            lambda x_value, alpha: self.rotate_point_about_y(
                x_value,
                alpha * y_of(x_value),
                angle,
            ),
            u_range=(split_x, CURVE_END),
            v_range=(0.0, 1.0),
            color=END_FACE_FILL,
            opacity=END_FACE_OPACITY,
            resolution=OUTER_CAP_RESOLUTION,
        )

        inner_patch.deactivate_depth_test()
        outer_patch.deactivate_depth_test()
        return Group(inner_patch, outer_patch)

    def make_cap_overlay_patch(self, angle: float) -> Polygon:
        points = [self.rotate_point_about_y(0.0, 0.0, angle)]
        points.extend(
            self.rotate_point_about_y(x_value, 0.0, angle)
            for x_value in np.linspace(0.0, CURVE_END, REFERENCE_X_SAMPLES)[1:]
        )
        points.extend(
            self.rotate_point_about_y(x_value, y_of(x_value), angle)
            for x_value in np.linspace(CURVE_END, 0.0, REFERENCE_CURVE_SAMPLES)
        )
        patch = Polygon(*points)
        patch.set_fill(END_FACE_FILL, opacity=END_FACE_OPACITY)
        patch.set_stroke(width=0.0)
        patch.set_shading(0.0, 0.0, 0.0)
        patch.deactivate_depth_test()
        return self.set_base_opacity(patch, END_FACE_OPACITY)

    def make_cap_curve(self, angle: float, color: str = CURVE_COLOR, opacity: float = 1.0) -> ParametricCurve:
        curve = ParametricCurve(
            lambda t: self.rotate_point_about_y(t, y_of(t), angle),
            t_range=(0.0, CURVE_END, REFERENCE_CURVE_STEP),
            stroke_color=color,
            stroke_width=3.2,
        )
        curve = self.set_base_opacity(curve, opacity)
        curve.deactivate_depth_test()
        return curve

    def make_body_group(self, angle: float) -> Group:
        angle = float(max(angle, 0.0))
        if angle <= 1e-4:
            return Group()

        body_group = Group(
            self.make_bottom_surface(angle),
            self.make_top_surface(angle),
            self.make_outer_wall(angle),
        )
        self.sort_mobject_to_camera(body_group)
        return body_group

    def make_body_mesh_group(self, angle: float) -> Group:
        angle = float(max(angle, 0.0))
        if angle <= 1e-4:
            return Group()

        mesh_group = Group(
            self.make_top_mesh(angle),
            self.make_outer_wall_mesh(angle),
        )
        self.sort_mobject_to_camera(mesh_group)
        return mesh_group

    def make_moving_cap_group(self, angle: float) -> Group:
        angle = float(max(angle, 0.0))
        if angle >= TAU - 0.03 or angle <= 0.01:
            return Group()
        return Group(
            self.make_cap_face(angle),
            self.make_cap_overlay_patch(angle),
            self.make_cap_curve(angle, color=VOLUME_FILL, opacity=0.92),
        )

    def make_start_cap_group(self, angle: float) -> Group:
        angle = float(max(angle, 0.0))
        if angle >= TAU - 0.03:
            return Group()
        return Group(
            self.make_cap_face(0.0),
            self.make_cap_overlay_patch(0.0),
            self.make_cap_curve(0.0, opacity=0.96),
        )

    def make_volume_layers(self, angle: float) -> tuple[Group, Group, Group, Group]:
        return (
            self.make_body_group(angle),
            self.make_body_mesh_group(angle),
            self.make_moving_cap_group(angle),
            self.make_start_cap_group(angle),
        )

    def build_reference_state_mobjects(self, progress: float) -> list[Mobject]:
        progress = float(np.clip(progress, 0.0, 1.0))
        axes = self.make_axes()
        self.refresh_group_to_camera(axes)
        body_group, body_mesh_group, moving_cap_group, start_cap_group = self.make_volume_layers(self.rotation_angle(progress))
        body_group.set_z_index(0)
        body_mesh_group.set_z_index(1)
        moving_cap_group.set_z_index(4)
        start_cap_group.set_z_index(4)
        mobjects: list[Mobject] = [
            axes,
            body_group,
            body_mesh_group,
            moving_cap_group,
            start_cap_group,
        ]
        if self.show_axis_labels():
            mobjects.insert(1, self.make_axis_labels())
        if SHOW_REFERENCE_PLANE:
            mobjects.append(self.make_plane_group(self.plane_visibility(progress)))
        return mobjects

    def add_reference_state(self, progress: float) -> None:
        self.apply_reference_camera()
        self.add(*self.build_reference_state_mobjects(progress))

    def rebuild_reference_state(self, progress: float) -> None:
        self.clear()
        self.add(*self.build_reference_state_mobjects(progress))

    def reference_progress_at_time(self, time_seconds: float) -> float:
        if time_seconds <= START_HOLD_TIME:
            return 0.0
        if time_seconds >= START_HOLD_TIME + ROTATION_RUN_TIME:
            return 1.0
        return float(np.clip((time_seconds - START_HOLD_TIME) / ROTATION_RUN_TIME, 0.0, 1.0))


class SqrtXReferenceFrame(SqrtXReferenceBase):
    def construct(self):
        progress = float(os.environ.get("SQRTX_REFERENCE_PROGRESS", f"{REFERENCE_PREVIEW_PROGRESS:.2f}"))
        self.add_reference_state(progress)


class SqrtXReferenceRotation(SqrtXReferenceBase):
    def construct(self):
        self.apply_reference_camera()
        total_duration = START_HOLD_TIME + ROTATION_RUN_TIME + END_HOLD_TIME
        fps = float(self.camera.fps)
        total_frames = max(1, int(round(total_duration * fps)))

        self.file_writer.total_frames = total_frames
        if self.file_writer.progress_display is not None:
            self.file_writer.progress_display.total = total_frames
            self.file_writer.progress_display.refresh()

        for frame_index in range(total_frames):
            time_seconds = frame_index / fps
            progress = self.reference_progress_at_time(time_seconds)
            self.rebuild_reference_state(progress)
            self.update_frame(
                dt=(0.0 if frame_index == 0 else 1.0 / fps),
                force_draw=True,
            )
            self.emit_frame()
