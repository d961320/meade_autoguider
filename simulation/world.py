#!/usr/bin/env python3

"""
Simuleret himmel.

World ejer guide-stjernens position og eventuelle drift.
"""


class World:
    def __init__(
        self,
        x=320.0,
        y=240.0,
        drift_x_per_step=0.0,
        drift_y_per_step=0.0,
    ):
        self.initial_x = float(x)
        self.initial_y = float(y)

        self.x = float(x)
        self.y = float(y)

        self.drift_x_per_step = float(
            drift_x_per_step
        )
        self.drift_y_per_step = float(
            drift_y_per_step
        )

        self.steps = 0

    def position(self):
        return {
            "x": self.x,
            "y": self.y,
        }

    def move(self, dx, dy):
        self.x += float(dx)
        self.y += float(dy)

    def step(self):
        """Udfør ét simuleret tidssteg."""

        self.x += self.drift_x_per_step
        self.y += self.drift_y_per_step
        self.steps += 1

    def reset(self, x=None, y=None):
        self.x = (
            self.initial_x
            if x is None
            else float(x)
        )

        self.y = (
            self.initial_y
            if y is None
            else float(y)
        )

        self.steps = 0
