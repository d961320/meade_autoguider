#!/usr/bin/env python3

from guiding.calibration_result import CalibrationResult
from guiding.guide_loop import GuideLoop
from guiding.tracker import GuideTracker


class FakeMount:
    connected = True

    def pulse_east(self, milliseconds):
        pass

    def pulse_west(self, milliseconds):
        pass


tracker = GuideTracker()

tracker.lock(
    {
        "x": 320.0,
        "y": 240.0,
        "flux": 15000,
    }
)

calibration = CalibrationResult(
    ra_dx=3.0,
    ra_dy=4.0,
    ra_pulse_ms=1000,

    dec_dx=-4.0,
    dec_dy=3.0,
    dec_pulse_ms=1000,

    completed=True,
)

loop = GuideLoop(
    tracker=tracker,
    mount=FakeMount(),
    calibration=calibration,
    enabled=False,
)

# Fejl præcis langs RA-vektoren.
tracker.current_x = 326.0
tracker.current_y = 248.0
tracker.dx = 6.0
tracker.dy = 8.0

ra_error = loop._compute_ra_error()

print("RA error:", ra_error)

assert round(
    ra_error,
    3,
) == 10.000

# Ren DEC-fejl skal give RA-fejl tæt på nul.
tracker.dx = -8.0
tracker.dy = 6.0

ra_error = loop._compute_ra_error()

print("RA error ved ren DEC:", ra_error)

assert round(
    ra_error,
    3,
) == 0.000

print()
print("RA-projektionstest bestået.")
