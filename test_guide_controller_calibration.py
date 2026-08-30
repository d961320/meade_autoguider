#!/usr/bin/env python3

from guiding.calibration import Calibration
from guiding.controller import (
    GuideController,
    GuideState,
)
from guiding.tracker import GuideTracker


class FakeMount:
    def __init__(self):
        self.connected = True
        self.commands = []

    def pulse_east(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("east", milliseconds, speed_mode)
        )

    def pulse_west(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("west", milliseconds, speed_mode)
        )

    def pulse_north(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("north", milliseconds, speed_mode)
        )

    def pulse_south(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("south", milliseconds, speed_mode)
        )

    def safe_stop(self):
        self.commands.append(("stop",))


mount = FakeMount()
tracker = GuideTracker()

tracker.lock(
    {
        "x": 200.0,
        "y": 150.0,
        "flux": 10000,
    }
)

calibration = Calibration(
    mount=mount,
    tracker=tracker,
    pulse_ms=1000,
)

controller = GuideController(
    tracker=tracker,
    calibration=calibration,
)

controller.select_star()

assert controller.start_calibration()
assert controller.state == GuideState.CALIBRATING

# Send RA øst.
assert controller.advance_calibration()

tracker.update(
    [{
        "x": 212.0,
        "y": 153.0,
        "flux": 9900,
    }]
)

# Mål RA øst.
assert controller.advance_calibration()

# Send RA vest.
assert controller.advance_calibration()

tracker.update(
    [{
        "x": 201.0,
        "y": 150.5,
        "flux": 9850,
    }]
)

# Mål RA vest.
assert controller.advance_calibration()

# Send DEC nord.
assert controller.advance_calibration()

tracker.update(
    [{
        "x": 202.0,
        "y": 160.5,
        "flux": 9800,
    }]
)

# Mål DEC nord.
assert controller.advance_calibration()

# Send DEC syd.
assert controller.advance_calibration()

tracker.update(
    [{
        "x": 201.0,
        "y": 151.0,
        "flux": 9750,
    }]
)

# Mål DEC syd og afslut.
assert controller.advance_calibration()

assert controller.state == GuideState.READY
assert calibration.completed
assert calibration.result.valid

print("Controller state:", controller.state.name)

print(
    "RA:",
    f"dx={calibration.result.ra_dx:+.3f}",
    f"dy={calibration.result.ra_dy:+.3f}",
)

print(
    "DEC:",
    f"dx={calibration.result.dec_dx:+.3f}",
    f"dy={calibration.result.dec_dy:+.3f}",
)

print()
print("Kommandoer:")

for command in mount.commands:
    print(command)

print()
print(
    "GuideController-kalibreringstest bestået."
)
