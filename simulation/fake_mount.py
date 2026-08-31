#!/usr/bin/env python3

"""
FakeMount

Simulerer et guide-mount.

Version 1:
- omsætter guidepulser til bevægelse af FakeSky
- ingen backlash
- ingen acceleration
- ingen mekaniske fejl
"""


class FakeMount:

    def __init__(
        self,
        sky,
        pixels_per_100ms=1.0,
    ):
        self.sky = sky

        self.connected = True

        self.pixels_per_100ms = float(
            pixels_per_100ms
        )

        self.commands = []

    def _pixels(
        self,
        milliseconds,
    ):
        return (
            milliseconds
            / 100.0
            * self.pixels_per_100ms
        )

    def pulse_east(
        self,
        milliseconds,
        speed_mode=None,
    ):
        pixels = self._pixels(milliseconds)

        self.commands.append(
            ("east", milliseconds)
        )

        self.sky.move(
            pixels,
            0.0,
        )

    def pulse_west(
        self,
        milliseconds,
        speed_mode=None,
    ):
        pixels = self._pixels(milliseconds)

        self.commands.append(
            ("west", milliseconds)
        )

        self.sky.move(
            -pixels,
            0.0,
        )

    def pulse_north(
        self,
        milliseconds,
        speed_mode=None,
    ):
        pixels = self._pixels(milliseconds)

        self.commands.append(
            ("north", milliseconds)
        )

        self.sky.move(
            0.0,
            -pixels,
        )

    def pulse_south(
        self,
        milliseconds,
        speed_mode=None,
    ):
        pixels = self._pixels(milliseconds)

        self.commands.append(
            ("south", milliseconds)
        )

        self.sky.move(
            0.0,
            pixels,
        )

    def safe_stop(self):
        self.commands.append(
            ("stop",)
        )
