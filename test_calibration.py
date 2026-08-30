#!/usr/bin/env python3

from guiding.calibration import (
    Calibration,
    CalibrationState,
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
        self.commands.append(
            ("stop",)
        )


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

assert calibration.start()

assert (
    calibration.state
    == CalibrationState.READY_RA_EAST
)

# ØST: +12, +3
calibration.pulse_ra_east()

tracker.update(
    [
        {
            "x": 212.0,
            "y": 153.0,
            "flux": 9900,
        }
    ]
)

assert calibration.record_ra_east()

# VEST relativt til den nye reference: -11, -2.5
calibration.pulse_ra_west()

tracker.update(
    [
        {
            "x": 201.0,
            "y": 150.5,
            "flux": 9850,
        }
    ]
)

assert calibration.record_ra_west()

# NORD: +1, +10
calibration.pulse_dec_north()

tracker.update(
    [
        {
            "x": 202.0,
            "y": 160.5,
            "flux": 9800,
        }
    ]
)

assert calibration.record_dec_north()

# SYD relativt til den nye reference: -1, -9.5
calibration.pulse_dec_south()

tracker.update(
    [
        {
            "x": 201.0,
            "y": 151.0,
            "flux": 9750,
        }
    ]
)

assert calibration.record_dec_south()

assert calibration.completed
assert calibration.result.valid

assert round(
    calibration.result.ra_dx,
    3,
) == 11.500

assert round(
    calibration.result.ra_dy,
    3,
) == 2.750

assert round(
    calibration.result.dec_dx,
    3,
) == 1.000

assert round(
    calibration.result.dec_dy,
    3,
) == 9.750

print("Tilstand:")
print(calibration.state.value)

print()
print("RA-vektor:")
print(
    f"dx={calibration.result.ra_dx:+.3f}",
    f"dy={calibration.result.ra_dy:+.3f}",
)

print()
print("DEC-vektor:")
print(
    f"dx={calibration.result.dec_dx:+.3f}",
    f"dy={calibration.result.dec_dy:+.3f}",
)

print()
print("Pixels pr. ms:")
print(
    "RA:",
    f"{calibration.result.ra_pixels_per_ms:.6f}",
)
print(
    "DEC:",
    f"{calibration.result.dec_pixels_per_ms:.6f}",
)

print()
print("Kommandoer:")

for command in mount.commands:
    print(command)

print()
print("Fire-retningers kalibreringstest bestået.")
