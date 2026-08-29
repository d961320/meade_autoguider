#!/usr/bin/env python3

import time

from mount.autostar_v2 import AutoStarV2


def main():

    mount = AutoStarV2(port="/dev/ttyUSB0")

    try:
        print("Forbinder...")

        if not mount.connect():
            raise RuntimeError(
                mount.last_error or
                "Kunne ikke forbinde"
            )

        print("Forbundet")
        print("Produkt :", mount.product)
        print("Firmware:", mount.firmware)
        print()

        input(
            "Tryk ENTER for at bevæge mod ØST i 2 sekunder..."
        )

        mount.start_move(
            "e",
            speed_mode="FIND",
        )

        time.sleep(2)

        mount.stop()

        print("Stop.")

    except KeyboardInterrupt:
        print()
        print("Nødstop")
        mount.safe_stop()

    finally:
        mount.disconnect()


if __name__ == "__main__":
    main()
