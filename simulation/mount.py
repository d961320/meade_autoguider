#!/usr/bin/env python3

"""
Simuleret mount.

Guidepulser flytter stjernen i den simulerede World.
"""


class FakeMount:
    def __init__(
        self,
        world,
        pixels_per_100ms=1.0,
        ra_unit=(1.0, 0.0),
        dec_unit=(0.0, -1.0),
    ):
        self.world = world
        self.connected = True

        self.pixels_per_100ms = float(
            pixels_per_100ms
        )

        self.ra_unit = (
            float(ra_unit[0]),
            float(ra_unit[1]),
        )

        self.dec_unit = (
            float(dec_unit[0]),
            float(dec_unit[1]),
        )

        self.commands = []

    def _distance(self, milliseconds):
        milliseconds = int(milliseconds)

        if milliseconds <= 0:
            raise ValueError(
                "Pulslængden skal være positiv"
            )

        return (
            milliseconds
            / 100.0
            * self.pixels_per_100ms
        )

    def _move(self, unit, sign, milliseconds):
        distance = self._distance(milliseconds)

        self.world.move(
            unit[0] * distance * sign,
            unit[1] * distance * sign,
        )

    def pulse_east(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("east", int(milliseconds), speed_mode)
        )

        self._move(
            self.ra_unit,
            +1.0,
            milliseconds,
        )

    def pulse_west(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("west", int(milliseconds), speed_mode)
        )

        self._move(
            self.ra_unit,
            -1.0,
            milliseconds,
        )

    def pulse_north(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("north", int(milliseconds), speed_mode)
        )

        self._move(
            self.dec_unit,
            +1.0,
            milliseconds,
        )

    def pulse_south(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("south", int(milliseconds), speed_mode)
        )

        self._move(
            self.dec_unit,
            -1.0,
            milliseconds,
        )

    def safe_stop(self):
        self.commands.append(("stop",))

    def stop(self):
        self.safe_stop()

    def disconnect(self):
        self.connected = False
