#!/usr/bin/env python3

"""
GuideStatus

Fælles status for autoguiding.
GUI'en skal kun læse denne klasse.
"""

from dataclasses import dataclass


@dataclass
class GuideStatus:

    state: str = "IDLE"

    mount_connected: bool = False

    locked: bool = False
    lost: bool = False

    current_x: float = 0.0
    current_y: float = 0.0

    dx: float = 0.0
    dy: float = 0.0

    guide_error: float = 0.0

    fps: float = 0.0

    last_pulse_direction: str = ""
    last_pulse_ms: int = 0

    calibrated: bool = False
