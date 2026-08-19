#!/usr/bin/env python3

"""
GuideTracker

Holder styr på én valgt guide-stjerne og beregner
dens forskydning i pixels fra referencepositionen.
"""


class GuideTracker:
    def __init__(self, max_distance=40.0):
        self.max_distance = float(max_distance)

        self.locked = False

        self.reference_x = None
        self.reference_y = None

        self.current_x = None
        self.current_y = None

        self.dx = 0.0
        self.dy = 0.0

        self.flux = 0.0
        self.lost = False

    def lock(self, star):
        """
        Lås på en stjerne fra StarTracker.

        star forventes at være en dictionary med mindst:
        x, y og eventuelt flux.
        """

        self.reference_x = float(star["x"])
        self.reference_y = float(star["y"])

        self.current_x = self.reference_x
        self.current_y = self.reference_y

        self.flux = float(star.get("flux", 0.0))

        self.dx = 0.0
        self.dy = 0.0

        self.locked = True
        self.lost = False

    def unlock(self):
        self.locked = False
        self.lost = False

        self.reference_x = None
        self.reference_y = None

        self.current_x = None
        self.current_y = None

        self.dx = 0.0
        self.dy = 0.0
        self.flux = 0.0

    def update(self, stars):
        """
        Find den stjerne, der ligger nærmest den seneste position.

        Returnerer den fundne stjerne eller None.
        """

        if not self.locked:
            return None

        if not stars:
            self.lost = True
            return None

        target_x = self.current_x
        target_y = self.current_y

        nearest_star = None
        nearest_distance_squared = None

        for star in stars:
            dx = float(star["x"]) - target_x
            dy = float(star["y"]) - target_y

            distance_squared = dx * dx + dy * dy

            if (
                nearest_distance_squared is None
                or distance_squared < nearest_distance_squared
            ):
                nearest_distance_squared = distance_squared
                nearest_star = star

        if nearest_star is None:
            self.lost = True
            return None

        if nearest_distance_squared > self.max_distance ** 2:
            self.lost = True
            return None

        self.current_x = float(nearest_star["x"])
        self.current_y = float(nearest_star["y"])

        self.flux = float(
            nearest_star.get(
                "flux",
                self.flux,
            )
        )

        self.dx = self.current_x - self.reference_x
        self.dy = self.current_y - self.reference_y

        self.lost = False

        return nearest_star

    def reset_reference(self):
        """
        Brug den aktuelle position som ny reference.
        """

        if not self.locked:
            raise RuntimeError(
                "Ingen guide-stjerne er låst"
            )

        self.reference_x = self.current_x
        self.reference_y = self.current_y

        self.dx = 0.0
        self.dy = 0.0

    def status(self):
        return {
            "locked": self.locked,
            "lost": self.lost,
            "reference_x": self.reference_x,
            "reference_y": self.reference_y,
            "current_x": self.current_x,
            "current_y": self.current_y,
            "dx": self.dx,
            "dy": self.dy,
            "flux": self.flux,
        }
