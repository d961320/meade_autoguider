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

    def pulse_north(
        self,
        milliseconds,
        speed_mode=None,
    ):
        self.commands.append(
            ("north", milliseconds, speed_mode)
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
assert calibration.state == CalibrationState.READY

calibration.pulse_ra()

tracker.update(
    [
        {
            "x": 212.0,
            "y": 153.0,
            "flux": 9900,
        }
    ]
)

assert calibration.record_ra_measurement()

calibration.pulse_dec()

tracker.update(
    [
        {
            "x": 210.0,
            "y": 164.0,
            "flux": 9800,
        }
    ]
)

assert calibration.record_dec_measurement()
assert calibration.completed
assert calibration.result.valid

print("Status:")
print(calibration.status())

print()
print("Kommandoer:")
for command in mount.commands:
    print(command)

print()
print("Calibration-test bestået.")
