#!/usr/bin/env python3

"""
Resultat fra mount-kalibreringen.

Klassen indeholder kun kalibreringsdata.
Den kommunikerer ikke med kamera, GUI eller mount.
"""

from dataclasses import asdict, dataclass
from math import hypot
from typing import Any


@dataclass
class CalibrationResult:
    """Gemmer resultatet af RA- og DEC-kalibreringen."""

    reference_x: float = 0.0
    reference_y: float = 0.0

    ra_dx: float = 0.0
    ra_dy: float = 0.0
    ra_pulse_ms: int = 0

    dec_dx: float = 0.0
    dec_dy: float = 0.0
    dec_pulse_ms: int = 0

    completed: bool = False
    error: str | None = None

    @property
    def ra_distance_pixels(self) -> float:
        """Samlet målt RA-bevægelse i pixels."""

        return hypot(
            self.ra_dx,
            self.ra_dy,
        )

    @property
    def dec_distance_pixels(self) -> float:
        """Samlet målt DEC-bevægelse i pixels."""

        return hypot(
            self.dec_dx,
            self.dec_dy,
        )

    @property
    def ra_pixels_per_ms(self) -> float:
        """RA-bevægelse i pixels pr. millisekund."""

        if self.ra_pulse_ms <= 0:
            return 0.0

        return (
            self.ra_distance_pixels
            / self.ra_pulse_ms
        )

    @property
    def dec_pixels_per_ms(self) -> float:
        """DEC-bevægelse i pixels pr. millisekund."""

        if self.dec_pulse_ms <= 0:
            return 0.0

        return (
            self.dec_distance_pixels
            / self.dec_pulse_ms
        )

    @property
    def valid(self) -> bool:
        """True, når kalibreringsresultatet kan bruges."""

        return (
            self.completed
            and self.error is None
            and self.ra_pulse_ms > 0
            and self.dec_pulse_ms > 0
            and self.ra_distance_pixels > 0
            and self.dec_distance_pixels > 0
        )

    def reset(self) -> None:
        """Nulstil alle kalibreringsdata."""

        self.reference_x = 0.0
        self.reference_y = 0.0

        self.ra_dx = 0.0
        self.ra_dy = 0.0
        self.ra_pulse_ms = 0

        self.dec_dx = 0.0
        self.dec_dy = 0.0
        self.dec_pulse_ms = 0

        self.completed = False
        self.error = None

    def as_dict(self) -> dict[str, Any]:
        """Returnér resultatet som dictionary."""

        result = asdict(self)

        result.update(
            {
                "ra_distance_pixels": (
                    self.ra_distance_pixels
                ),
                "dec_distance_pixels": (
                    self.dec_distance_pixels
                ),
                "ra_pixels_per_ms": (
                    self.ra_pixels_per_ms
                ),
                "dec_pixels_per_ms": (
                    self.dec_pixels_per_ms
                ),
                "valid": self.valid,
            }
        )

        return result
