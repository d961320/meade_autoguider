#!/usr/bin/env python3

from guiding.controller import (
    GuideController,
    GuideState,
)
from guiding.tracker import GuideTracker


class FakeGuideStatus:
    def __init__(self):
        self.dx = 3.0
        self.dy = -2.0
        self.guide_error = 3.6055


class FakeGuideLoop:
    def __init__(self):
        self.steps = 0

    def step(self):
        self.steps += 1
        return FakeGuideStatus()


tracker = GuideTracker()
guide_loop = FakeGuideLoop()

controller = GuideController(
    tracker=tracker,
    guide_loop=guide_loop,
)

assert controller.state == GuideState.IDLE

tracker.lock(
    {
        "x": 320.0,
        "y": 240.0,
        "flux": 15000,
    }
)

status = controller.step()

assert controller.state == GuideState.STAR_SELECTED
assert status["tracker"]["locked"] is True

controller.start_guiding()

assert controller.state == GuideState.GUIDING

status = controller.step()

assert guide_loop.steps == 1
assert status["guide"]["dx"] == 3.0
assert status["guide"]["dy"] == -2.0

controller.pause_guiding()
assert controller.state == GuideState.PAUSED

controller.resume_guiding()
assert controller.state == GuideState.GUIDING

controller.stop_guiding()
assert controller.state == GuideState.STAR_SELECTED

controller.release_star()
assert controller.state == GuideState.IDLE
assert tracker.locked is False

print("Slutstatus:")
print(controller.status())

print()
print("GuideController-integration bestået.")
