from __future__ import annotations

import importlib.util
import os
import sys
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

CORE_PATH = os.path.join(THIS_DIR, "revolve-slice-core.py")
CORE_SPEC = importlib.util.spec_from_file_location("revolve_slice_core", CORE_PATH)
if CORE_SPEC is None or CORE_SPEC.loader is None:
    raise ImportError(f"Could not load revolve-slice-core.py from {CORE_PATH}")
base_scene = importlib.util.module_from_spec(CORE_SPEC)
CORE_SPEC.loader.exec_module(base_scene)

for name in dir(base_scene):
    if not name.startswith("_"):
        globals()[name] = getattr(base_scene, name)


THEME = os.environ.get("MANIM_THEME", "light").strip().lower()

# Palette refresh: keep the existing pink-purple family, but lift the background
# slightly away from pure white / pure black so the inserted differential stage can
# feel softer and more editorial.
if THEME == "dark":
    palette = {
        "BACKGROUND": "#06040a",
        "AXIS_COLOR": "#f8f0ff",
        "CURVE_COLOR": "#9988ff",
        "PLANE_FILL": "#3a293d",
        "SLICE_FILL": "#ff53bd",
        "VOLUME_FILL": "#dc73b7",
        "GUIDE_COLOR": "#bea8c6",
    }
    DIFF_FILL = "#ff7cd0"
    DIFF_LABEL_COLOR = "#fff7ff"
else:
    palette = {
        "BACKGROUND": "#fcfbff",
        "AXIS_COLOR": "#2b2035",
        "CURVE_COLOR": "#8d58ff",
        "PLANE_FILL": "#f7d8df",
        "SLICE_FILL": "#d31cae",
        "VOLUME_FILL": "#de79ba",
        "GUIDE_COLOR": "#7d6875",
    }
    DIFF_FILL = "#ff4fa2"
    DIFF_LABEL_COLOR = "#4a3041"

for name, value in palette.items():
    setattr(base_scene, name, value)

# Keep the overall reveal length close to the current piece, but insert one calm
# explanatory beat between the hero disk and the sweeping camera showcase.
DIFF_RUN_TIME = 3.6
END_FADE_DELAY = 0.30
END_FADE_DURATION = 0.70
EXACT_CLIP_DURATION = (
    base_scene.START_HOLD_TIME
    + base_scene.ANIMATION_RUN_TIME
    + DIFF_RUN_TIME
    + base_scene.SHOWCASE_RUN_TIME
    + base_scene.END_HOLD_TIME
)

# Make the stagger start immediately once the differential stage is over so the
# camera motion and the second wave of disk generation feel causally linked.
base_scene.SHOWCASE_SLICE_STAGGER_START = 0.00
base_scene.SHOWCASE_SLICE_STAGGER_END = 0.60
base_scene.SHOWCASE_SLICE_DURATION = 0.18

# A thin representative strip on the plane, slightly to the left of the hero disk.
# This keeps it visible and lets the next left-adjacent showcase slice feel like a
# natural continuation.
DIFF_STRIP_X0 = 1.70
DIFF_STRIP_X1 = 1.84
DIFF_STRIP_CURVE_STEPS = 22


class RevolveSliceMGLDifferentialBase(base_scene.RevolveSliceMGLBase):
    samples = 0
    default_camera_config = {"background_color": base_scene.BACKGROUND}

    def set_base_opacity(self, mob: Mobject, opacity: float) -> Mobject:
        mob._base_opacity = float(opacity)
        if hasattr(mob, "set_opacity"):
            mob.set_opacity(float(opacity))
        return mob

    def make_billboard_text(
        self,
        content: str,
        position: np.ndarray,
        *,
        height: float,
        color: str,
        slant=ITALIC,
    ) -> Text:
        label = Text(
            content,
            font=base_scene.AXIS_LABEL_FONT,
            font_size=72,
            slant=slant,
            color=color,
        )
        label.set_height(height)
        label.set_fill(color, opacity=1.0)
        label.set_stroke(width=0.0)
        label.set_backstroke(base_scene.BACKGROUND, width=3.0)
        label.center()
        label.apply_matrix(self.frame.get_orientation().as_matrix())
        label.move_to(position)
        return label

    def timed_envelope(
        self,
        t: float,
        fade_in: tuple[float, float],
        fade_out: tuple[float, float],
    ) -> float:
        intro = self.staggered_progress(t, fade_in[0], fade_in[1], 0.14, 0.82)
        outro = self.staggered_progress(t, fade_out[0], fade_out[1], 0.18, 0.88)
        return float(intro * (1.0 - outro))

    def differential_strip_span(self) -> tuple[float, float]:
        return float(DIFF_STRIP_X0), float(DIFF_STRIP_X1)

    def differential_first_slice_opacity_scale(self, diff_t: float) -> float:
        dim = self.staggered_progress(diff_t, 0.14, 0.34, 0.18, 0.86)
        restore = self.staggered_progress(diff_t, 0.78, 0.96, 0.18, 0.86)
        return float(np.clip(1.0 - 0.42 * dim + 0.42 * restore, 0.56, 1.0))

    def differential_region_opacity_scale(self, diff_t: float) -> float:
        focus = self.timed_envelope(diff_t, (0.14, 0.34), (0.80, 0.98))
        return float(np.clip(1.0 - 0.18 * focus, 0.82, 1.0))

    def end_fade_progress(self, clip_time: float) -> float:
        showcase_end = (
            base_scene.START_HOLD_TIME
            + base_scene.ANIMATION_RUN_TIME
            + DIFF_RUN_TIME
            + base_scene.SHOWCASE_RUN_TIME
        )
        fade_start = showcase_end + END_FADE_DELAY
        fade_end = min(EXACT_CLIP_DURATION, fade_start + END_FADE_DURATION)
        if clip_time <= fade_start:
            return 0.0
        if clip_time >= fade_end:
            return 1.0
        return self.staggered_progress(clip_time, fade_start, fade_end, 0.16, 0.86)

    def end_volume_visibility_scale(self, fade_t: float) -> float:
        return float(np.clip(1.0 - fade_t, 0.0, 1.0))

    def make_curve_segment(self, x0: float, x1: float, *, color: str, stroke_width: float) -> ParametricCurve:
        return ParametricCurve(
            lambda t: self.to_world(t, y_of(t), 0.0),
            t_range=(x0, x1, max(0.01, (x1 - x0) / 18.0)),
            stroke_color=color,
            stroke_width=stroke_width,
        )

    def make_differential_strip_polygon(self, x0: float, x1: float) -> Polygon:
        points = [
            self.to_world(x0, 0.0, 0.0),
            self.to_world(x1, 0.0, 0.0),
        ]
        points.extend(
            self.to_world(x, y_of(x), 0.0)
            for x in np.linspace(x1, x0, DIFF_STRIP_CURVE_STEPS)
        )
        polygon = Polygon(*points)
        polygon.set_fill(DIFF_FILL, opacity=0.82)
        polygon.set_stroke(base_scene.CURVE_COLOR, width=2.2, opacity=0.88)
        return polygon

    def make_differential_guides(self) -> dict[str, Mobject]:
        x0, x1 = self.differential_strip_span()
        x_mid = 0.5 * (x0 + x1)
        y_mid = y_of(x_mid)
        guide_color = base_scene.GUIDE_COLOR
        baseline_y = -0.18
        tick_half = 0.04

        strip = self.set_base_opacity(self.make_differential_strip_polygon(x0, x1), 1.0)
        curve_segment = self.set_base_opacity(
            self.make_curve_segment(x0, x1, color=base_scene.CURVE_COLOR, stroke_width=6.0),
            1.0,
        )
        curve_segment.set_backstroke(base_scene.BACKGROUND, width=2.0)

        left_guide = DashedLine(
            self.to_world(x0, 0.0, 0.0),
            self.to_world(x0, y_of(x0), 0.0),
            dash_length=0.10,
        )
        left_guide.set_stroke(guide_color, width=1.5, opacity=0.62)
        self.set_base_opacity(left_guide, 1.0)

        right_guide = DashedLine(
            self.to_world(x1, 0.0, 0.0),
            self.to_world(x1, y_of(x1), 0.0),
            dash_length=0.10,
        )
        right_guide.set_stroke(guide_color, width=1.5, opacity=0.62)
        self.set_base_opacity(right_guide, 1.0)

        height_line = Line(
            self.to_world(x_mid, 0.0, 0.0),
            self.to_world(x_mid, y_mid, 0.0),
        )
        height_line.set_stroke(DIFF_FILL, width=2.4, opacity=0.88)
        self.set_base_opacity(height_line, 1.0)

        dx_line = Line(
            self.to_world(x0, baseline_y, 0.0),
            self.to_world(x1, baseline_y, 0.0),
        )
        dx_line.set_stroke(guide_color, width=1.7, opacity=0.78)
        dx_tick_l = Line(
            self.to_world(x0, baseline_y - tick_half, 0.0),
            self.to_world(x0, baseline_y + tick_half, 0.0),
        )
        dx_tick_l.set_stroke(guide_color, width=1.7, opacity=0.78)
        dx_tick_r = Line(
            self.to_world(x1, baseline_y - tick_half, 0.0),
            self.to_world(x1, baseline_y + tick_half, 0.0),
        )
        dx_tick_r.set_stroke(guide_color, width=1.7, opacity=0.78)
        self.set_base_opacity(dx_line, 1.0)
        self.set_base_opacity(dx_tick_l, 1.0)
        self.set_base_opacity(dx_tick_r, 1.0)
        dx_indicator = Group(dx_line, dx_tick_l, dx_tick_r)

        dx_label = self.make_billboard_text(
            "dx",
            self.to_world(x_mid, baseline_y - 0.12, 0.0),
            height=0.24,
            color=DIFF_LABEL_COLOR,
        )
        self.set_base_opacity(dx_label, 1.0)

        y_label = self.make_billboard_text(
            "y",
            self.to_world(x_mid + 0.12, 0.50 * y_mid, 0.0),
            height=0.24,
            color=DIFF_LABEL_COLOR,
        )
        self.set_base_opacity(y_label, 1.0)

        dA_label = self.make_billboard_text(
            "dA",
            self.to_world(x_mid, 0.60 * y_mid, 0.0),
            height=0.30,
            color=DIFF_LABEL_COLOR,
        )
        self.set_base_opacity(dA_label, 1.0)

        group = Group(
            strip,
            curve_segment,
            left_guide,
            right_guide,
            height_line,
            dx_indicator,
            dx_label,
            y_label,
            dA_label,
        )
        return {
            "group": group,
            "strip": strip,
            "curve": curve_segment,
            "left_guide": left_guide,
            "right_guide": right_guide,
            "height": height_line,
            "dx_indicator": dx_indicator,
            "dx_label": dx_label,
            "y_label": y_label,
            "dA_label": dA_label,
        }

    def apply_differential_overlay_state(self, parts: dict[str, Mobject], diff_t: float) -> None:
        strip_alpha = self.timed_envelope(diff_t, (0.18, 0.34), (0.82, 0.98))
        curve_alpha = self.timed_envelope(diff_t, (0.20, 0.36), (0.80, 0.96))
        guide_alpha = self.timed_envelope(diff_t, (0.24, 0.40), (0.78, 0.92))
        height_alpha = self.timed_envelope(diff_t, (0.34, 0.52), (0.74, 0.88))
        dx_alpha = self.timed_envelope(diff_t, (0.32, 0.48), (0.72, 0.86))
        y_alpha = self.timed_envelope(diff_t, (0.42, 0.60), (0.72, 0.88))
        da_alpha = self.timed_envelope(diff_t, (0.52, 0.70), (0.76, 0.94))

        self.set_group_opacity_scale(parts["strip"], strip_alpha)
        self.set_group_opacity_scale(parts["curve"], curve_alpha)
        self.set_group_opacity_scale(parts["left_guide"], guide_alpha)
        self.set_group_opacity_scale(parts["right_guide"], guide_alpha)
        self.set_group_opacity_scale(parts["height"], height_alpha)
        self.set_group_opacity_scale(parts["dx_indicator"], dx_alpha)
        self.set_group_opacity_scale(parts["dx_label"], dx_alpha)
        self.set_group_opacity_scale(parts["y_label"], y_alpha)
        self.set_group_opacity_scale(parts["dA_label"], da_alpha)

    def make_differential_overlay(self, diff_t: float) -> Group:
        parts = self.make_differential_guides()
        self.apply_differential_overlay_state(parts, diff_t)
        return parts["group"]

    def make_first_slice_showcase_group(self, showcase_t: float, opacity_scale: float = 1.0) -> Group:
        first_x0, first_x1 = self.showcase_slice_bounds()[0]
        first_slice = self.make_regular_showcase_slice(first_x0, first_x1)
        self.set_group_opacity_scale(first_slice, opacity_scale)
        return first_slice

    def make_dynamic_showcase_slice(self, x0: float, x1: float, progress: float) -> Group:
        if progress <= 1e-4:
            return Group()
        angle = max(1e-4, TAU * float(np.clip(progress, 0.0, 1.0)))
        return self.make_sector_volume_between(
            x0,
            x1,
            angle,
            resolution=base_scene.VOLUME_SURFACE_RESOLUTION,
            opacity_scale=1.0,
            include_start_face=True,
            prefer_polygon_caps_for_full_circle=False,
        )

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
            if slice_index == 0:
                slice_group = self.make_first_slice_showcase_group(showcase_t, opacity_scale=opacity_scale)
            else:
                progress = self.showcase_slice_angle_progress(showcase_t, slice_index)
                slice_group = self.make_dynamic_showcase_slice(x0, x1, progress)
                self.set_group_opacity_scale(slice_group, opacity_scale)
            slices.add(slice_group)
        return self.sort_mobject_to_camera(slices)

    def clip_progress(self, clip_time: float) -> tuple[float, float, float, float, str]:
        clip_time = float(np.clip(clip_time, 0.0, EXACT_CLIP_DURATION))
        opening_start = base_scene.START_HOLD_TIME
        opening_end = opening_start + base_scene.ANIMATION_RUN_TIME
        differential_end = opening_end + DIFF_RUN_TIME
        showcase_end = differential_end + base_scene.SHOWCASE_RUN_TIME
        end_fade_t = self.end_fade_progress(clip_time)

        if clip_time <= opening_start:
            return 0.0, 0.0, 0.0, 0.0, "opening"
        if clip_time < opening_end:
            return (clip_time - opening_start) / base_scene.ANIMATION_RUN_TIME, 0.0, 0.0, 0.0, "opening"
        if clip_time < differential_end:
            return 1.0, (clip_time - opening_end) / DIFF_RUN_TIME, 0.0, 0.0, "differential"

        showcase_t = 1.0 if clip_time >= showcase_end else (clip_time - differential_end) / base_scene.SHOWCASE_RUN_TIME
        phase = "end_hold" if clip_time >= showcase_end else "showcase"
        return 1.0, 1.0, showcase_t, end_fade_t, phase

    def add_clip_state(self, clip_time: float) -> None:
        opening_t, differential_t, showcase_t, end_fade_t, phase = self.clip_progress(clip_time)
        if phase in {"showcase", "end_hold"}:
            self.apply_active_showcase_camera_state(showcase_t)
        else:
            self.apply_showcase_camera_state(0.0)

        axes = self.make_axes()
        self.refresh_group_to_camera(axes)
        axis_labels = self.make_axis_labels()
        region = self.make_region()
        region._base_opacity = 0.45
        if phase == "differential":
            self.set_group_opacity_scale(region, self.differential_region_opacity_scale(differential_t))
        self.add(axes, axis_labels)
        self.add(region, set_depth_test=False)
        self.add(self.make_curve())

        volume_opacity = self.end_volume_visibility_scale(end_fade_t)

        if phase == "opening":
            if not self.opening_handoff_ready(opening_t):
                opening_x0, opening_x1 = self.opening_slice_bounds()
                hero_slice = self.make_sector_volume_between(
                    opening_x0,
                    opening_x1,
                    self.opening_dynamic_angle(opening_t),
                    opacity_scale=volume_opacity,
                    include_start_face=True,
                    prefer_polygon_caps_for_full_circle=True,
                )
                self.add(hero_slice)
            else:
                self.add(self.make_first_slice_showcase_group(0.0, opacity_scale=volume_opacity))
            return

        first_slice_opacity = volume_opacity
        if phase == "differential":
            first_slice_opacity *= self.differential_first_slice_opacity_scale(differential_t)
        self.add(self.make_first_slice_showcase_group(0.0, opacity_scale=first_slice_opacity))

        if phase == "differential":
            self.add(self.make_differential_overlay(differential_t), set_depth_test=False)
            return

        self.add(self.make_showcase_slice_group(showcase_t, opacity_scale=volume_opacity, include_first_slice=False))


class RevolveSliceClipFrameMGLDifferential(RevolveSliceMGLDifferentialBase):
    def construct(self):
        clip_time = float(os.environ.get("MANIM_CLIP_TIME", "0.0"))
        self.add_clip_state(clip_time)


class RevolveSliceShowcaseMGLDifferential(RevolveSliceMGLDifferentialBase):
    def construct(self):
        opening_tracker = ValueTracker(0.0)
        differential_tracker = ValueTracker(0.0)
        showcase_tracker = ValueTracker(0.0)
        end_fade_tracker = ValueTracker(0.0)
        differential_started = {"value": False}
        differential_complete = {"value": False}
        showcase_started = {"value": False}

        def update_frame(frame):
            if showcase_started["value"]:
                self.apply_active_showcase_camera_state(showcase_tracker.get_value())
            else:
                self.apply_showcase_camera_state(0.0)

        self.frame.add_updater(update_frame)
        self.apply_showcase_camera_state(0.0)

        opening_x0, opening_x1 = self.opening_slice_bounds()

        showcase_bounds = self.showcase_slice_bounds()
        first_x0, first_x1 = showcase_bounds[0]
        first_slice = Group()

        def update_first_slice(mob):
            next_group = Group()
            volume_opacity = self.end_volume_visibility_scale(end_fade_tracker.get_value())
            if not differential_started["value"] and not showcase_started["value"] and opening_tracker.get_value() < 1.0:
                angle = self.opening_dynamic_angle(opening_tracker.get_value())
                if angle > 1e-4:
                    next_group = self.make_sector_volume_between(
                        opening_x0,
                        opening_x1,
                        angle,
                        opacity_scale=volume_opacity,
                        include_start_face=True,
                        prefer_polygon_caps_for_full_circle=True,
                    )
            else:
                opacity_scale = volume_opacity
                if differential_started["value"] and not showcase_started["value"]:
                    opacity_scale *= self.differential_first_slice_opacity_scale(differential_tracker.get_value())
                next_group = self.make_first_slice_showcase_group(0.0, opacity_scale=opacity_scale)

            mob.set_submobjects([submob.copy() for submob in next_group.submobjects])
            self.refresh_group_to_camera(mob)

        first_slice.add_updater(update_first_slice)

        showcase_slices = []
        for slice_index, (x0, x1) in enumerate(showcase_bounds[1:], start=1):
            slice_group = Group()

            def update_slice(mob, idx=slice_index, left=x0, right=x1):
                if not showcase_started["value"]:
                    mob.set_submobjects([])
                    return
                progress = self.showcase_slice_angle_progress(showcase_tracker.get_value(), idx)
                if progress <= 1e-4:
                    mob.set_submobjects([])
                    return
                next_group = self.make_dynamic_showcase_slice(left, right, progress)
                self.set_group_opacity_scale(next_group, self.end_volume_visibility_scale(end_fade_tracker.get_value()))
                mob.set_submobjects([submob.copy() for submob in next_group.submobjects])
                self.refresh_group_to_camera(mob)

            slice_group.add_updater(update_slice)
            showcase_slices.append(slice_group)

        showcase_group = Group(first_slice, *showcase_slices)
        showcase_group.add_updater(lambda mob: self.refresh_group_to_camera(mob))

        differential_parts = self.make_differential_guides()
        differential_group = differential_parts["group"]
        self.apply_differential_overlay_state(differential_parts, 0.0)

        def update_differential_overlay(mob):
            if not differential_started["value"] or showcase_started["value"]:
                self.set_group_opacity_scale(mob, 0.0)
                return
            self.apply_differential_overlay_state(differential_parts, differential_tracker.get_value())

        differential_group.add_updater(update_differential_overlay)

        axes = self.make_axes()
        axes.add_updater(lambda mob: self.refresh_group_to_camera(mob))
        axis_labels = Group()
        self.update_axis_labels(axis_labels)
        axis_labels.add_updater(lambda mob: self.update_axis_labels(mob))
        region = self.make_region()
        region._base_opacity = 0.45

        def update_region(mob):
            scale = 1.0
            if differential_started["value"] and not showcase_started["value"]:
                scale = self.differential_region_opacity_scale(differential_tracker.get_value())
            self.set_group_opacity_scale(mob, scale)

        region.add_updater(update_region)

        self.add(
            axes,
            axis_labels,
        )
        self.add(region, set_depth_test=False)
        self.add(
            self.make_curve(),
            differential_group,
            showcase_group,
        )
        self.wait(base_scene.START_HOLD_TIME)
        self.play(opening_tracker.animate.set_value(1.0), run_time=base_scene.ANIMATION_RUN_TIME, rate_func=linear)
        differential_started["value"] = True
        self.play(differential_tracker.animate.set_value(1.0), run_time=DIFF_RUN_TIME, rate_func=linear)
        differential_complete["value"] = True
        showcase_started["value"] = True
        self.play(showcase_tracker.animate.set_value(1.0), run_time=base_scene.SHOWCASE_RUN_TIME, rate_func=linear)
        self.wait(END_FADE_DELAY)
        self.play(end_fade_tracker.animate.set_value(1.0), run_time=END_FADE_DURATION, rate_func=smooth)
        remaining_hold = max(0.0, base_scene.END_HOLD_TIME - END_FADE_DELAY - END_FADE_DURATION)
        if remaining_hold > 1e-4:
            self.wait(remaining_hold)
