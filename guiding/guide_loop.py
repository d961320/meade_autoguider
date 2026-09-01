#!/usr/bin/env python3

"""
GuideLoop

Første aktive version af guide-loopet.

Denne version:
- opdaterer GuideStatus
- korrigerer kun RA-fejl
- bruger en fast pulslængde
- har deadband og cooldown
- korrigerer ikke DEC endnu
"""

import time

from guiding.status import GuideStatus


class GuideLoop:
    def __init__(
        self,
        tracker,
        mount,
        calibration=None,
        ra_deadband_pixels=2.0,
        ra_pulse_ms=200,
        pulse_cooldown_seconds=0.75,
        ra_positive_direction="west",
        ra_negative_direction="east",
        enabled=True,
    ):
        self.tracker = tracker
        self.mount = mount
        self.calibration = calibration

        self.ra_deadband_pixels = float(
            ra_deadband_pixels
        )
        self.ra_pulse_ms = int(
            ra_pulse_ms
        )
        self.pulse_cooldown_seconds = float(
            pulse_cooldown_seconds
        )

        self.ra_positive_direction = str(
            ra_positive_direction
        ).strip().lower()

        self.ra_negative_direction = str(
            ra_negative_direction
        ).strip().lower()

        self.enabled = bool(enabled)

        self.status = GuideStatus()
        self.last_pulse_time = 0.0

        self._validate_configuration()

    def step(self):
        """
        Kaldes én gang efter hvert nyt kamerabillede.

        GuideTracker skal være opdateret før dette kald.
        """

        self._update_status()

        if not self.enabled:
            self.status.state = "MONITORING"
            return self.status

        if not self.mount.connected:
            self.status.state = "MOUNT_OFFLINE"
            return self.status

        if not self.tracker.locked:
            self.status.state = "IDLE"
            return self.status

        if self.tracker.lost:
            self.status.state = "LOST"
            return self.status

        self.status.state = "GUIDING"

        if not self._cooldown_finished():
            return self.status

        ra_error = self._compute_ra_error()

        if abs(ra_error) <= self.ra_deadband_pixels:
            return self.status

        if ra_error > 0:
            direction = self.ra_positive_direction
        else:
            direction = self.ra_negative_direction

        self._send_ra_pulse(
            direction,
            self.ra_pulse_ms,
        )

        self.status.last_pulse_direction = direction
        self.status.last_pulse_ms = self.ra_pulse_ms

        self.last_pulse_time = time.monotonic()

        return self.status

    def set_enabled(self, enabled):
        """Slå automatiske korrektioner til eller fra."""

        self.enabled = bool(enabled)

        if not self.enabled:
            self.status.state = "MONITORING"

    def reset(self):
        """Nulstil pulsstatus og cooldown."""

        self.last_pulse_time = 0.0

        self.status.last_pulse_direction = ""
        self.status.last_pulse_ms = 0

    def _update_status(self):
        self.status.mount_connected = bool(
            self.mount.connected
        )

        self.status.locked = bool(
            self.tracker.locked
        )

        self.status.lost = bool(
            self.tracker.lost
        )

        if self.tracker.current_x is not None:
            self.status.current_x = float(
                self.tracker.current_x
            )

        if self.tracker.current_y is not None:
            self.status.current_y = float(
                self.tracker.current_y
            )

        self.status.dx = float(
            self.tracker.dx
        )

        self.status.dy = float(
            self.tracker.dy
        )

        self.status.guide_error = (
            self.status.dx ** 2
            + self.status.dy ** 2
        ) ** 0.5

    def _cooldown_finished(self):
        if self.last_pulse_time <= 0:
            return True

        elapsed = (
            time.monotonic()
            - self.last_pulse_time
        )

        return (
            elapsed
            >= self.pulse_cooldown_seconds
        )

    def _send_ra_pulse(
        self,
        direction,
        milliseconds,
    ):
        functions = {
            "east": self.mount.pulse_east,
            "west": self.mount.pulse_west,
        }

        try:
            function = functions[direction]
        except KeyError as error:
            raise ValueError(
                f"Ugyldig RA-retning: {direction}"
            ) from error

        function(milliseconds)

    def _compute_ra_error(self):
        """
        Beregn guidefejlen langs den målte RA-vektor.

        Hvis der ikke findes en gyldig kalibrering,
        bruges tracker.dx som fallback.
        """

        dx = float(self.tracker.dx)
        dy = float(self.tracker.dy)

        calibration = self.calibration

        if calibration is None:
            return dx

        if not calibration.valid:
            return dx

        ra_dx = float(calibration.ra_dx)
        ra_dy = float(calibration.ra_dy)

        ra_length = (
            ra_dx * ra_dx
            + ra_dy * ra_dy
        ) ** 0.5

        if ra_length <= 0:
            return dx

        return (
            dx * ra_dx
            + dy * ra_dy
        ) / ra_length

    def _validate_configuration(self):
        if self.ra_deadband_pixels < 0:
            raise ValueError(
                "RA deadband må ikke være negativ"
            )

        if not 100 <= self.ra_pulse_ms <= 5000:
            raise ValueError(
                "RA-pulsen skal være 100-5000 ms"
            )

        if self.pulse_cooldown_seconds < 0:
            raise ValueError(
                "Cooldown må ikke være negativ"
            )

        valid_directions = {
            "east",
            "west",
        }

        if (
            self.ra_positive_direction
            not in valid_directions
        ):
            raise ValueError(
                "Positiv RA-retning skal være east eller west"
            )

        if (
            self.ra_negative_direction
            not in valid_directions
        ):
            raise ValueError(
                "Negativ RA-retning skal være east eller west"
            )

        if (
            self.ra_positive_direction
            == self.ra_negative_direction
        ):
            raise ValueError(
                "RA-retningerne skal være forskellige"
            )
