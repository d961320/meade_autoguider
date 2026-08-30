#!/usr/bin/env python3

from mount.controller import MountController


def main():
    mount = MountController(
        port="/dev/ttyUSB0",
        driver_name="autostar_v2",
    )

    try:
        print("Driver:", type(mount.driver).__name__)
        print("Forbinder...")

        if not mount.connect():
            raise RuntimeError(
                mount.last_error
                or "Forbindelse mislykkedes"
            )

        print("Forbundet:", mount.connected)

        status = mount.status()

        print("Drivernavn:", status["driver"])
        print("Version:", status["driver_version"])
        print("Port:", status["port"])
        print("Produkt:", status["product"])
        print("Firmware:", status["firmware"])
        print("RA:", status["ra"])
        print("DEC:", status["dec"])

    finally:
        mount.safe_stop()
        mount.disconnect()
        print("Forbindelse lukket.")


if __name__ == "__main__":
    main()
