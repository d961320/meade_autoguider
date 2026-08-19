#!/usr/bin/env python3

"""
guide_star.py

Gemmer information om den valgte guide-stjerne.

Denne klasse indeholder ingen kamera- eller mountlogik.
Den fungerer kun som en delt datastruktur.
"""

from dataclasses import dataclass


@dataclass
class GuideStar:
    x: float = 0.0
    y: float = 0.0
    flux: float = 0.0
    radius: float = 0.0
    locked: bool = False

    def lock(self, star):
        """
        Lås en funden stjerne.

        Forventer et dictionary fra StarTracker.
        """

        self.x = float(star["x"])
        self.y = float(star["y"])
        self.flux = float(star.get("flux", 0))
        self.radius = float(star.get("radius", 0))
        self.locked = True

    def unlock(self):
        """Frigiv guide-stjernen."""

        self.locked = False

    def update_position(self, x, y):
        """Opdater den aktuelle position."""

        self.x = float(x)
        self.y = float(y)

    def as_dict(self):
        """Returnér indholdet som dictionary."""

        return {
            "x": self.x,
            "y": self.y,
            "flux": self.flux,
            "radius": self.radius,
            "locked": self.locked,
        }

    def __bool__(self):
        """if guide_star:" betyder at en stjerne er låst."""
        return self.locked
