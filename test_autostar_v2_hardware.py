#!/usr/bin/env python3

from mount.autostar_v2 import AutoStarV2


mount = AutoStarV2(
    port="/dev/ttyUSB0",
)

try:
    print("Forbinder...")

    if not mount.connect():
        raise RuntimeError(
            mount.last_error
            or "Forbindelse mislykkedes"
        )

    print("Forbundet")
    print("Port:", mount.port)
    print("Produkt:", mount.product)
    print("Firmware:", mount.firmware)
    print("RA:", mount.get_ra())
    print("DEC:", mount.get_dec())

finally:
    mount.safe_stop()
    mount.disconnect()
