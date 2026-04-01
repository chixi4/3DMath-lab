from manim import *


class GPUProbe(ThreeDScene):
    def construct(self):
        if config.renderer == RendererType.OPENGL:
            self.renderer.camera.set_phi(70 * DEGREES)
            self.renderer.camera.set_theta(-60 * DEGREES)
            self.renderer.camera.set_gamma(0.0)
            self.renderer.camera.set_height(config.frame_height)
        else:
            self.set_camera_orientation(phi=70 * DEGREES, theta=-60 * DEGREES, zoom=1.0)
        sphere = Sphere(radius=1.1, resolution=(20, 20), fill_opacity=0.85)
        sphere.set_color(BLUE_E)
        axes = ThreeDAxes()
        self.add(axes, sphere)
        self.wait(0.1)
