#!/usr/bin/env python3

"""
GuideController

Koordinerer autoguiding.

Denne klasse indeholder endnu ingen guiding-logik.
Den fungerer kun som fælles indgangspunkt.
"""

from enum import Enum, auto


class GuideState(Enum):
    IDLE = auto()
    STAR_SELECTED = auto()
    CALIBRATING = auto()
    READY = auto()
    GUIDING = auto()
    PAUSED = auto()
    STOPPED = auto()


class GuideController:

    def __init__(self):

        self.state = GuideState.IDLE

        self.calibration = None
        self.guide_loop = None
        self.tracker = None

    def set_tracker(self, tracker):
        self.tracker = tracker

    def set_calibration(self, calibration):
        self.calibration = calibration

    def set_guide_loop(self, guide_loop):
        self.guide_loop = guide_loop

    def status(self):

        return {
            "state": self.state.name,
            "tracker": self.tracker is not None,
            "calibration": self.calibration is not None,
            "guide_loop": self.guide_loop is not None,
        }
