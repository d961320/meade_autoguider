#!/usr/bin/env python3

"""
Factory til valg af mount-driver.

Dette modul samler oprettelsen af mount-drivere ét sted.
Resten af programmet behøver derfor ikke importere de
enkelte drivere direkte.

Understøttede drivere:

    autostar
    autostar_v2

LX200 og simulator tilføjes senere.
"""

from __future__ import annotations

from typing import Any

from mount.autostar import AutoStar
from mount.autostar_v2 import AutoStarV2


DRIVER_ALIASES = {
    "autostar": "autostar",
    "legacy": "autostar",
    "autostar_legacy": "autostar",

    "autostar_v2": "autostar_v2",
    "autostar2": "autostar_v2",
    "v2": "autostar_v2",
}


def normalize_driver_name(
    driver_name: str,
) -> str:
    """
    Normalisér driverens navn.

    Eksempler:

        AutoStar    -> autostar
        autostar-v2 -> autostar_v2
        V2          -> autostar_v2
    """

    if not isinstance(driver_name, str):
        raise TypeError(
            "Driver-navnet skal være tekst"
        )

    normalized = (
        driver_name
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if not normalized:
        raise ValueError(
            "Driver-navnet må ikke være tomt"
        )

    return DRIVER_ALIASES.get(
        normalized,
        normalized,
    )


def available_drivers() -> tuple[str, ...]:
    """Returnér de drivere, factory-modulet kan oprette."""

    return (
        "autostar",
        "autostar_v2",
    )


def create_mount(
    driver_name: str = "autostar",
    port: str | None = None,
    **options: Any,
):
    """
    Opret en mount-driver.

    Parametre:

        driver_name:
            autostar
            autostar_v2

        port:
            Eksempel: /dev/ttyUSB0
            Hvis None, søger driveren selv.

        **options:
            Ekstra driver-specifikke indstillinger.

    Funktionen opretter kun driverobjektet.
    Den kalder ikke connect().
    """

    driver_name = normalize_driver_name(
        driver_name
    )

    if driver_name == "autostar":
        if options:
            unsupported = ", ".join(
                sorted(options)
            )

            raise TypeError(
                "Den gamle AutoStar-driver "
                "understøtter ikke disse indstillinger: "
                f"{unsupported}"
            )

        return AutoStar(
            port=port,
        )

    if driver_name == "autostar_v2":
        return AutoStarV2(
            port=port,
            **options,
        )

    supported = ", ".join(
        available_drivers()
    )

    raise ValueError(
        f"Ukendt mount-driver: {driver_name!r}. "
        f"Muligheder: {supported}"
    )
