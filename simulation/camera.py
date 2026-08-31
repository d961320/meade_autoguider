#!/usr/bin/env python3

"""
Simuleret kamera.

Returnerer stjernen i samme dictionary-format,
som GuideTracker allerede bruger.
"""


class FakeCamera:
    def __init__(
        self,
        world,
        flux=15000.0,
    ):
        self.world = world
        self.flux = float(flux)

    def capture(self):
        position = self.world.position()

        return [
            {
                "x": position["x"],
                "y": position["y"],
                "flux": self.flux,
            }
        ]

    def read_stars(self):
        return self.capture()
