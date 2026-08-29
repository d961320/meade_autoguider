from guiding.guide_loop import GuideLoop
from guiding.tracker import GuideTracker


class FakeMount:

    connected = True


tracker = GuideTracker()

tracker.lock(
    {
        "x": 320,
        "y": 240,
        "flux": 15000,
    }
)

tracker.update(
    [
        {
            "x": 323,
            "y": 238,
            "flux": 14900,
        }
    ]
)

loop = GuideLoop(
    tracker,
    FakeMount(),
)

status = loop.step()

print(status)
