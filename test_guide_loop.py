#!/usr/bin/env python3

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


mount = FakeMount()
tracker = GuideTracker()

tracker.lock(
    {
        "x": 320.0,
        "y": 240.0,
        "flux": 15000,
    }
)

loop = GuideLoop(
    tracker=tracker,
    mount=mount,
    ra_deadband_pixels=2.0,
    ra_pulse_ms=200,
    pulse_cooldown_seconds=0.0,
)

# Ingen fejl: ingen puls.
status = loop.step()

assert mount.commands == []
assert status.dx == 0.0
assert status.last_pulse_ms == 0

# Positiv dx: vest-puls.
tracker.update(
    [
        {
            "x": 324.0,
            "y": 240.5,
            "flux": 14900,
        }
    ]
)

status = loop.step()

assert mount.commands[-1] == (
    "west",
    200,
)
assert status.last_pulse_direction == "west"
assert status.last_pulse_ms == 200

# Ny reference til test af negativ dx.
tracker.reset_reference()

tracker.update(
    [
        {
            "x": 316.0,
            "y": 240.0,
            "flux": 14800,
        }
    ]
)

status = loop.step()

assert mount.commands[-1] == (
    "east",
    200,
)
assert status.last_pulse_direction == "east"

# Lille fejl inden for deadband: ingen ny puls.
tracker.reset_reference()

command_count = len(
    mount.commands
)

tracker.update(
    [
        {
            "x": 317.0,
            "y": 240.0,
            "flux": 14700,
        }
    ]
)

status = loop.step()

assert len(mount.commands) == command_count

print("Status:")
print(status)

print()
print("Kommandoer:")

for command in mount.commands:
    print(command)

print()
print("Aktiv RA GuideLoop-test bestået.")
