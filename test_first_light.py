#!/usr/bin/env python3

"""
First Light Integration Test - Niveau 4

Tester hele softwarekæden uden fysisk hardware:

    GuideTracker
           ↓
    GuideController
           ↓
    Fire-retningers Calibration
           ↓
    CalibrationResult
           ↓
    GuideLoop
           ↓
    FakeMount
"""

from guiding.calibration import Calibration
from guiding.controller import (
    GuideController,
    GuideState,
)
from guiding.guide_loop import GuideLoop
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

calibration = Calibration(
    mount=mount,
    tracker=tracker,
    pulse_ms=1000,
)

guide_loop = GuideLoop(
    tracker=tracker,
    mount=mount,

    # Det samme CalibrationResult-objekt bliver
    # udfyldt under kalibreringen.
    calibration=calibration.result,

    ra_deadband_pixels=2.0,
    ra_pulse_ms=200,
    pulse_cooldown_seconds=0.0,

    ra_positive_direction="west",
    ra_negative_direction="east",
)

controller = GuideController(
    tracker=tracker,
    calibration=calibration,
    guide_loop=guide_loop,
)

assert controller.state == GuideState.IDLE

# -------------------------------------------------
# Vælg guide-stjerne
# -------------------------------------------------

tracker.lock(
    {
        "x": 320.0,
        "y": 240.0,
        "flux": 15000,
    }
)

controller.select_star()

assert controller.state == GuideState.STAR_SELECTED

# -------------------------------------------------
# Fire-retningers kalibrering
# -------------------------------------------------

assert controller.start_calibration()
assert controller.state == GuideState.CALIBRATING

# Send RA øst.
assert controller.advance_calibration()

tracker.update(
    [
        {
            "x": 332.0,
            "y": 243.0,
            "flux": 14900,
        }
    ]
)

# Mål RA øst.
assert controller.advance_calibration()

# Send RA vest.
assert controller.advance_calibration()

tracker.update(
    [
        {
            "x": 321.0,
            "y": 240.5,
            "flux": 14850,
        }
    ]
)

# Mål RA vest.
assert controller.advance_calibration()

# Send DEC nord.
assert controller.advance_calibration()

tracker.update(
    [
        {
            "x": 322.0,
            "y": 250.5,
            "flux": 14800,
        }
    ]
)

# Mål DEC nord.
assert controller.advance_calibration()

# Send DEC syd.
assert controller.advance_calibration()

tracker.update(
    [
        {
            "x": 321.0,
            "y": 241.0,
            "flux": 14750,
        }
    ]
)

# Mål DEC syd og afslut.
assert controller.advance_calibration()

assert controller.state == GuideState.READY
assert calibration.completed
assert calibration.result.valid

print("Kalibrering færdig.")

print(
    "RA-vektor:",
    f"dx={calibration.result.ra_dx:+.3f}",
    f"dy={calibration.result.ra_dy:+.3f}",
)

print(
    "DEC-vektor:",
    f"dx={calibration.result.dec_dx:+.3f}",
    f"dy={calibration.result.dec_dy:+.3f}",
)

# -------------------------------------------------
# Kalibreret RA-guiding
# -------------------------------------------------

tracker.reset_reference()

controller.start_guiding()

assert controller.state == GuideState.GUIDING

calibration_command_count = len(
    mount.commands
)

# Flyt stjernen i positiv RA-retning.
tracker.update(
    [
        {
            "x": 327.0,
            "y": 242.5,
            "flux": 14700,
        }
    ]
)

positive_ra_error = (
    guide_loop._compute_ra_error()
)

assert positive_ra_error > 2.0

status = controller.step()

assert controller.state == GuideState.GUIDING

assert len(mount.commands) == (
    calibration_command_count + 1
)

assert mount.commands[-1] == (
    "west",
    200,
    None,
)

assert status["guide"]["last_pulse_direction"] == "west"
assert status["guide"]["last_pulse_ms"] == 200

print()
print(
    "Positiv RA-fejl:",
    f"{positive_ra_error:+.3f} px",
)

print(
    "Guidekommando:",
    mount.commands[-1],
)

# -------------------------------------------------
# Test negativ RA-retning
# -------------------------------------------------

tracker.reset_reference()

tracker.update(
    [
        {
            "x": 321.0,
            "y": 241.0,
            "flux": 14650,
        }
    ]
)

negative_ra_error = (
    guide_loop._compute_ra_error()
)

assert negative_ra_error < -2.0

status = controller.step()

assert mount.commands[-1] == (
    "east",
    200,
    None,
)

assert status["guide"]["last_pulse_direction"] == "east"

print()
print(
    "Negativ RA-fejl:",
    f"{negative_ra_error:+.3f} px",
)

print(
    "Guidekommando:",
    mount.commands[-1],
)

# -------------------------------------------------
# Stop guiding
# -------------------------------------------------

controller.stop_guiding()

assert controller.state == GuideState.STAR_SELECTED

print()
print("Sluttilstand:", controller.state.name)

print()
print("First Light Level 4 bestået.")
