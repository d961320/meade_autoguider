#!/usr/bin/env python3

from mount.controller import MountController
from mount.manual_slew import ManualSlew


def main():

    mount = MountController()

    print("Forbinder til AutoStar...")

    if not mount.connect():
        print("Kunne ikke forbinde.")
        return

    print("Forbundet.")
    print()
    print("Hastigheder:")
    print("  g = GUIDE")
    print("  c = CENTER")
    print("  f = FIND")
    print("  m = MAX")
    print()
    print("Retninger:")
    print("  n s e w")
    print()
    print("x = STOP")
    print("q = Afslut")
    print()

    slew = ManualSlew(mount)

    while True:

        cmd = input("> ").strip().lower()

        try:

            if cmd == "g":
                slew.set_speed("GUIDE")
                print("GUIDE")

            elif cmd == "c":
                slew.set_speed("CENTER")
                print("CENTER")

            elif cmd == "f":
                slew.set_speed("FIND")
                print("FIND")

            elif cmd == "m":
                slew.set_speed("SLEW")
                print("MAX")

            elif cmd == "n":
                slew.start_north()

            elif cmd == "s":
                slew.start_south()

            elif cmd == "e":
                slew.start_east()

            elif cmd == "w":
                slew.start_west()

            elif cmd == "x":
                slew.stop()
                print("STOP")

            elif cmd == "q":
                break

        except Exception as err:
            print(err)

    slew.safe_stop()
    mount.disconnect()


if __name__ == "__main__":
    main()
