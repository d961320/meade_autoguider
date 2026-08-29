#!/usr/bin/env python3

from mount.autostar import AutoStar
from mount.autostar_v2 import AutoStarV2
from mount.factory import (
    available_drivers,
    create_mount,
    normalize_driver_name,
)


print("Tilgængelige drivere:")
print(available_drivers())
print()

print("Normalisering:")
print(
    "AutoStar ->",
    normalize_driver_name("AutoStar"),
)
print(
    "autostar-v2 ->",
    normalize_driver_name("autostar-v2"),
)
print(
    "V2 ->",
    normalize_driver_name("V2"),
)
print()

legacy = create_mount(
    "autostar",
    port="/dev/ttyUSB0",
)

v2 = create_mount(
    "autostar_v2",
    port="/dev/ttyUSB0",
)

alias = create_mount(
    "v2",
    port="/dev/ttyUSB0",
)

assert isinstance(
    legacy,
    AutoStar,
)

assert isinstance(
    v2,
    AutoStarV2,
)

assert isinstance(
    alias,
    AutoStarV2,
)

assert legacy.requested_port == "/dev/ttyUSB0"
assert v2.serial.requested_port == "/dev/ttyUSB0"

print(
    "Legacy driver:",
    type(legacy).__name__,
)

print(
    "V2 driver:",
    type(v2).__name__,
)

print(
    "Alias driver:",
    type(alias).__name__,
)

print()

try:
    create_mount("ukendt")
except ValueError as error:
    print(
        "Forventet fejl:",
        error,
    )
else:
    raise AssertionError(
        "Ukendt driver skulle give ValueError"
    )

print()
print("Mount factory-test bestået.")
