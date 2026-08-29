#!/usr/bin/env python3

from mount.autostar_v2 import AutoStarV2


def main():
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

        print(
            "Forbundet:",
            mount.product,
            mount.firmware,
        )
        print()
        print("Test: 300 ms mod øst")
        print("Ctrl+C kan bruges som nødstop.")

        input("Tryk Enter for at starte...")

        mount.pulse_east(
            300,
            speed_mode="CENTER",
        )

        print("Puls afsluttet.")

    except KeyboardInterrupt:
        print()
        print("Nødstop")

    finally:
        mount.safe_stop()
        mount.disconnect()
        print("Forbindelse lukket.")


if __name__ == "__main__":
    main()
