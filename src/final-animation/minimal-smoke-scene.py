from manimlib import *


class MinimalProbe(Scene):
    def construct(self):
        circle = Circle(radius=1.5, color=BLUE)
        circle.set_fill(BLUE_E, opacity=0.5)
        self.play(ShowCreation(circle), run_time=0.2)
        self.wait(0.2)
