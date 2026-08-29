#!/usr/bin/env python3

"""
Trinvis mount-kalibrering.

Kalibreringen sender guidepulser via MountController og
bruger positioner fra GuideTracker til at måle bevægelsen.

Kamera- og GUI-loopet ligger ikke i denne klasse.
Efter hver puls skal den kaldende kode opdatere GuideTracker
med nye kamerabilleder og derefter kalde record_measurement().
"""

from __future__ import annotations

from enum import Enum

from guiding.calibration_result import CalibrationResult


class CalibrationState(Enum):
    IDLE = "idle"
    READY = "ready"

    WAITING_RA = "waiting_ra"
    WAITING_DEC = "waiting_dec"

    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Calibration:
    """Styrer en enkel RA- og DEC-kalibrering."""

    def __init__(
        self,
        mount,
        tracker,
        pulse_ms=1000,
        minimum_movement_pixels=2.0,
    ):
        self.mount = mount
        self.tracker = tracker

        self.pulse_ms = int(pulse_ms)
        self.minimum_movement_pixels = float(
            minimum_movement_pixels
        )

        self.state = CalibrationState.IDLE
        self.result = CalibrationResult()
        self.message = "Ikke startet"

    @property
    def active(self):
        return self.state in {
            CalibrationState.READY,
            CalibrationState.WAITING_RA,
            CalibrationState.WAITING_DEC,
        }

    @property
    def completed(self):
        return self.state == CalibrationState.COMPLETED

    @property
    def failed(self):
        return self.state == CalibrationState.FAILED

    def start(self):
        """
        Start en ny kalibrering.

        GuideTracker skal allerede have en låst stjerne.
        """

        self.result.reset()

        if not self.mount.connected:
            return self._fail(
                "Mountet er ikke forbundet"
            )

        if not self.tracker.locked:
            return self._fail(
                "Ingen guide-stjerne er låst"
            )

        if self.tracker.lost:
            return self._fail(
                "Guide-stjernen er mistet"
            )

        if (
            self.tracker.current_x is None
            or self.tracker.current_y is None
        ):
            return self._fail(
                "Guide-stjernen har ingen position"
            )

        if not 100 <= self.pulse_ms <= 5000:
            return self._fail(
                "Kalibreringspulsen skal være 100-5000 ms"
            )

        self.result.reference_x = float(
            self.tracker.current_x
        )
        self.result.reference_y = float(
            self.tracker.current_y
        )

        self.tracker.reset_reference()

        self.state = CalibrationState.READY
        self.message = "Klar til RA-måling"

        return True

    def pulse_ra(self):
        """
        Send en puls mod øst.

        Efter pulsen skal kameraet levere nye frames,
        GuideTracker skal opdateres, og derefter skal
        record_ra_measurement() kaldes.
        """

        self._require_state(
            CalibrationState.READY
        )

        self.mount.pulse_east(
            self.pulse_ms,
            speed_mode="CENTER",
        )

        self.state = CalibrationState.WAITING_RA
        self.message = "Venter på RA-måling"

    def record_ra_measurement(self):
        """Gem RA-bevægelsen fra GuideTracker."""

        self._require_state(
            CalibrationState.WAITING_RA
        )
        self._require_valid_tracker()

        dx = float(self.tracker.dx)
        dy = float(self.tracker.dy)

        distance = (
            dx * dx
            + dy * dy
        ) ** 0.5

        if distance < self.minimum_movement_pixels:
            return self._fail(
                "RA-bevægelsen var for lille: "
                f"{distance:.2f} px"
            )

        self.result.ra_dx = dx
        self.result.ra_dy = dy
        self.result.ra_pulse_ms = self.pulse_ms

        self.tracker.reset_reference()

        self.state = CalibrationState.WAITING_DEC
        self.message = "RA målt - klar til DEC-puls"

        return True

    def pulse_dec(self):
        """
        Send en puls mod nord.

        Funktionen kaldes efter en vellykket RA-måling.
        """

        self._require_state(
            CalibrationState.WAITING_DEC
        )

        # WAITING_DEC bruges både før og efter DEC-pulsen.
        # Vi markerer fasen via beskeden.
        if self.message != "RA målt - klar til DEC-puls":
            raise RuntimeError(
                "DEC-pulsen er allerede sendt"
            )

        self.mount.pulse_north(
            self.pulse_ms,
            speed_mode="CENTER",
        )

        self.message = "Venter på DEC-måling"

    def record_dec_measurement(self):
        """Gem DEC-bevægelsen og afslut kalibreringen."""

        self._require_state(
            CalibrationState.WAITING_DEC
        )

        if self.message != "Venter på DEC-måling":
            raise RuntimeError(
                "DEC-pulsen er ikke sendt endnu"
            )

        self._require_valid_tracker()

        dx = float(self.tracker.dx)
        dy = float(self.tracker.dy)

        distance = (
            dx * dx
            + dy * dy
        ) ** 0.5

        if distance < self.minimum_movement_pixels:
            return self._fail(
                "DEC-bevægelsen var for lille: "
                f"{distance:.2f} px"
            )

        self.result.dec_dx = dx
        self.result.dec_dy = dy
        self.result.dec_pulse_ms = self.pulse_ms
        self.result.completed = True
        self.result.error = None

        self.state = CalibrationState.COMPLETED
        self.message = "Kalibrering færdig"

        return True

    def cancel(self):
        """Annuller og stop mountet sikkert."""

        self.mount.safe_stop()

        self.state = CalibrationState.CANCELLED
        self.message = "Kalibrering annulleret"

    def reset(self):
        """Nulstil kalibreringen."""

        self.mount.safe_stop()
        self.result.reset()

        self.state = CalibrationState.IDLE
        self.message = "Ikke startet"

    def status(self):
        """Returnér aktuel status som dictionary."""

        return {
            "state": self.state.value,
            "message": self.message,
            "active": self.active,
            "completed": self.completed,
            "failed": self.failed,
            "pulse_ms": self.pulse_ms,
            "result": self.result.as_dict(),
        }

    def _require_valid_tracker(self):
        if not self.tracker.locked:
            raise RuntimeError(
                "Ingen guide-stjerne er låst"
            )

        if self.tracker.lost:
            raise RuntimeError(
                "Guide-stjernen er mistet"
            )

        if (
            self.tracker.current_x is None
            or self.tracker.current_y is None
        ):
            raise RuntimeError(
                "Guide-stjernen har ingen aktuel position"
            )

    def _require_state(self, expected_state):
        if self.state != expected_state:
            raise RuntimeError(
                "Forkert kalibreringstilstand: "
                f"{self.state.value}; "
                f"forventede {expected_state.value}"
            )

    def _fail(self, message):
        self.mount.safe_stop()

        self.result.completed = False
        self.result.error = str(message)

        self.state = CalibrationState.FAILED
        self.message = str(message)

        return False
