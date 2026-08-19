#!/usr/bin/env python3

from guiding.tracker import GuideTracker


tracker = GuideTracker()

reference_star = {
    "x": 214.30,
    "y": 148.90,
    "flux": 38000,
}

tracker.lock(reference_star)

print("Reference:")
print(tracker.status())
print()

frames = [
    [
        {"x": 214.80, "y": 148.40, "flux": 37900},
        {"x": 300.00, "y": 200.00, "flux": 15000},
    ],
    [
        {"x": 216.10, "y": 147.70, "flux": 38100},
        {"x": 299.00, "y": 201.00, "flux": 14900},
    ],
    [
        {"x": 218.25, "y": 146.95, "flux": 37700},
    ],
]

for number, stars in enumerate(frames, start=1):
    star = tracker.update(stars)

    print(
        f"Frame {number}:",
        f"x={tracker.current_x:.2f}",
        f"y={tracker.current_y:.2f}",
        f"dx={tracker.dx:+.2f}",
        f"dy={tracker.dy:+.2f}",
        f"lost={tracker.lost}",
    )
