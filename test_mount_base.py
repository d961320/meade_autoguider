#!/usr/bin/env python3

from mount.base import MountBase


print("MountBase importeret korrekt.")
print("Driver info:")
print(MountBase.driver_info())

try:
    MountBase()
except TypeError as error:
    print()
    print("Forventet resultat:")
    print("MountBase kan ikke oprettes direkte.")
    print(error)

