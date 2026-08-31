#!/usr/bin/env python3

"""
FakeSky

Simpel simulering af en guide-stjernes position.

Version 1:
- Fast stjerneposition.
- Kan flyttes manuelt.
- Ingen støj.
- Ingen drift.
"""

class FakeSky:

    def __init__(
        self,
        x=320.0,
        y=240.0,
    ):
        self.x = float(x)
        self.y = float(y)

    def position(self):
        """Returnér den aktuelle stjerneposition."""

        return {
            "x": self.x,
            "y": self.y,
        }

    def move(
        self,
        dx,
        dy,
    ):
        """Flyt stjernen."""

        self.x += float(dx)
        self.y += float(dy)

    def reset(
        self,
        x=320.0,
        y=240.0,
    ):
        """Nulstil positionen."""

        self.x = float(x)
        self.y = float(y)
