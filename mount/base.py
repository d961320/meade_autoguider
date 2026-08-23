#!/usr/bin/env python3

"""
Fælles interface for alle mount-drivere.

AutoStar-, LX200- og simulator-drivere skal tilbyde
de samme grundlæggende funktioner, så resten af
autoguideren ikke behøver kende mount-typen.
"""

from abc import ABC, abstractmethod
from typing import Any


class MountBase(ABC):
    """Abstrakt basisklasse for mount-drivere."""

    DRIVER_NAME = "Ukendt mount"
    DRIVER_VERSION = "0.0"

    CAPABILITIES = {
        "read_coordinates": False,
        "guide_pulse": False,
        "manual_slew": False,
        "goto": False,
    }

    @property
    @abstractmethod
    def connected(self) -> bool:
        """True, når forbindelsen til mountet er aktiv."""

    @abstractmethod
    def connect(self) -> bool:
        """Opret forbindelse til mountet."""

    @abstractmethod
    def disconnect(self) -> None:
        """Stop mountet og luk forbindelsen."""

    @abstractmethod
    def get_ra(self) -> str | None:
        """Returnér aktuel RA eller None."""

    @abstractmethod
    def get_dec(self) -> str | None:
        """Returnér aktuel DEC eller None."""

    @abstractmethod
    def stop(self) -> None:
        """Stop alle aktive mount-bevægelser."""

    def safe_stop(self) -> None:
        """
        Forsøg at stoppe mountet uden at rejse en ny fejl.

        Bruges ved programfejl og afslutning.
        """

        try:
            if self.connected:
                self.stop()
        except Exception:
            pass

    @abstractmethod
    def pulse_north(self, milliseconds: int) -> None:
        """Send en tidsbegrænset bevægelse mod nord."""

    @abstractmethod
    def pulse_south(self, milliseconds: int) -> None:
        """Send en tidsbegrænset bevægelse mod syd."""

    @abstractmethod
    def pulse_east(self, milliseconds: int) -> None:
        """Send en tidsbegrænset bevægelse mod øst."""

    @abstractmethod
    def pulse_west(self, milliseconds: int) -> None:
        """Send en tidsbegrænset bevægelse mod vest."""

    def status(self) -> dict[str, Any]:
        """
        Returnér fælles statusformat.

        Drivere må gerne udvide dictionaryen med flere felter.
        """

        ra = None
        dec = None
        error = None

        if self.connected:
            try:
                if self.supports("read_coordinates"):
                    ra = self.get_ra()
                    dec = self.get_dec()
            except Exception as exc:
                error = str(exc)

        return {
            "connected": self.connected,
            "driver": self.DRIVER_NAME,
            "driver_version": self.DRIVER_VERSION,
            "ra": ra,
            "dec": dec,
            "error": error,
        }

    @classmethod
    def supports(cls, capability: str) -> bool:
        """Returnér True, hvis driveren understøtter funktionen."""

        return bool(
            cls.CAPABILITIES.get(
                capability,
                False,
            )
        )

    @classmethod
    def driver_info(cls) -> dict[str, Any]:
        """Returnér navn, version og capabilities."""

        return {
            "name": cls.DRIVER_NAME,
            "version": cls.DRIVER_VERSION,
            "capabilities": dict(cls.CAPABILITIES),
        }
