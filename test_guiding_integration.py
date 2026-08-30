#!/usr/bin/env python3

from guiding.controller import GuideController, GuideState
from guiding.guide_loop import GuideLoop
from guiding.tracker import GuideTracker


class FakeMount:
    def __init__(self):
        self.connected = True
        self.commands = []

    def pulse_east(self, milliseconds):
        self.commands.append(
            ("east", milliseconds)
        )

    def pulse_west(self, milliseconds):
        self.commands.append(
            ("west", milliseconds)
        )


tracker = GuideTracker()

guide_loop = GuideLoop(
    tracker=tracker,
    mount=FakeMount(),
    pulse_cooldown_seconds=0.0,
)

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

controller.step()

assert controller.state == GuideState.STAR_SELECTED

tracker.update(
    [
        {
            "x": 323.0,
            "y": 238.0,
            "flux": 14900,
        }
    ]
)

controller.start_guiding()

status = controller.step()

assert controller.state == GuideState.GUIDING
assert status["guide"]["dx"] == 3.0
assert status["guide"]["dy"] == -2.0
assert round(
    status["guide"]["guide_error"],
    3,
) == 3.606

print("Guide state:", status["state"])
print("dx:", status["guide"]["dx"])
print("dy:", status["guide"]["dy"])
print(
    "Guide error:",
    status["guide"]["guide_error"],
)

print()
print("Guiding-integration bestået.")
