#!/usr/bin/env python3

"""
Fire-retningers mount-kalibrering.

Sekvens:

    ØST  -> mål RA+
    VEST -> mål RA-
    NORD -> mål DEC+
    SYD  -> mål DEC-

Kamera- og GUI-loopet ligger uden for denne klasse.

Efter hver puls skal den kaldende kode:

1. hente nye kamerabilleder,
2. opdatere GuideTracker,
3. kalde den tilhørende record-metode.
"""

from __future__ import annotations

from enum import Enum

from guiding.calibration_result import CalibrationResult


class CalibrationState(Enum):
    IDLE = "idle"
    READY_RA_EAST = "ready_ra_east"
    WAITING_RA_EAST = "waiting_ra_east"
    READY_RA_WEST = "ready_ra_west"
    WAITING_RA_WEST = "waiting_ra_west"
    READY_DEC_NORTH = "ready_dec_north"
    WAITING_DEC_NORTH = "waiting_dec_north"
    READY_DEC_SOUTH = "ready_dec_south"
    WAITING_DEC_SOUTH = "waiting_dec_south"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Calibration:
    """Styrer en fire-retningers RA/DEC-kalibrering."""

    def __init__(
        self,
        mount,
        tracker,
        pulse_ms=1000,
        minimum_movement_pixels=2.0,
        speed_mode="CENTER",
    ):
        self.mount = mount
        self.tracker = tracker

        self.pulse_ms = int(pulse_ms)
        self.minimum_movement_pixels = float(
            minimum_movement_pixels
        )
        self.speed_mode = str(
            speed_mode
        ).strip().upper()

        self.state = CalibrationState.IDLE
        self.result = CalibrationResult()
        self.message = "Ikke startet"

        self.ra_east_dx = 0.0
        self.ra_east_dy = 0.0
        self.ra_west_dx = 0.0
        self.ra_west_dy = 0.0

        self.dec_north_dx = 0.0
        self.dec_north_dy = 0.0
        self.dec_south_dx = 0.0
        self.dec_south_dy = 0.0

    @property
    def active(self):
        return self.state not in {
            CalibrationState.IDLE,
            CalibrationState.COMPLETED,
            CalibrationState.FAILED,
            CalibrationState.CANCELLED,
        }

    @property
    def completed(self):
        return self.state == CalibrationState.COMPLETED

    @property
    def failed(self):
        return self.state == CalibrationState.FAILED

    def start(self):
        """Start en ny kalibrering."""

        self.result.reset()
        self._reset_measurements()

        if not self.mount.connected:
            return self._fail(
                "Mountet er ikke forbundet"
            )

        try:
            self._require_valid_tracker()
        except RuntimeError as error:
            return self._fail(str(error))

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

        self.state = CalibrationState.READY_RA_EAST
        self.message = "Klar til RA øst"

        return True

    def pulse_ra_east(self):
        self._require_state(
            CalibrationState.READY_RA_EAST
        )

        self.mount.pulse_east(
            self.pulse_ms,
            speed_mode=self.speed_mode,
        )

        self.state = CalibrationState.WAITING_RA_EAST
        self.message = "Venter på RA øst-måling"

    def record_ra_east(self):
        self._require_state(
            CalibrationState.WAITING_RA_EAST
        )

        dx, dy = self._read_movement("RA øst")

        if dx is None:
            return False

        self.ra_east_dx = dx
        self.ra_east_dy = dy

        self.tracker.reset_reference()

        self.state = CalibrationState.READY_RA_WEST
        self.message = "RA øst målt - klar til RA vest"

        return True

    def pulse_ra_west(self):
        self._require_state(
            CalibrationState.READY_RA_WEST
        )

        self.mount.pulse_west(
            self.pulse_ms,
            speed_mode=self.speed_mode,
        )

        self.state = CalibrationState.WAITING_RA_WEST
        self.message = "Venter på RA vest-måling"

    def record_ra_west(self):
        self._require_state(
            CalibrationState.WAITING_RA_WEST
        )

        dx, dy = self._read_movement("RA vest")

        if dx is None:
            return False

        self.ra_west_dx = dx
        self.ra_west_dy = dy

        # Positiv RA-vektor beskriver østretningen.
        self.result.ra_dx = (
            self.ra_east_dx
            - self.ra_west_dx
        ) / 2.0

        self.result.ra_dy = (
            self.ra_east_dy
            - self.ra_west_dy
        ) / 2.0

        self.result.ra_pulse_ms = self.pulse_ms

        if (
            self.result.ra_distance_pixels
            < self.minimum_movement_pixels
        ):
            return self._fail(
                "Samlet RA-bevægelse var for lille: "
                f"{self.result.ra_distance_pixels:.2f} px"
            )

        self.tracker.reset_reference()

        self.state = CalibrationState.READY_DEC_NORTH
        self.message = "RA målt - klar til DEC nord"

        return True

    def pulse_dec_north(self):
        self._require_state(
            CalibrationState.READY_DEC_NORTH
        )

        self.mount.pulse_north(
            self.pulse_ms,
            speed_mode=self.speed_mode,
        )

        self.state = CalibrationState.WAITING_DEC_NORTH
        self.message = "Venter på DEC nord-måling"

    def record_dec_north(self):
        self._require_state(
            CalibrationState.WAITING_DEC_NORTH
        )

        dx, dy = self._read_movement("DEC nord")

        if dx is None:
            return False

        self.dec_north_dx = dx
        self.dec_north_dy = dy

        self.tracker.reset_reference()

        self.state = CalibrationState.READY_DEC_SOUTH
        self.message = "DEC nord målt - klar til DEC syd"

        return True

    def pulse_dec_south(self):
        self._require_state(
            CalibrationState.READY_DEC_SOUTH
        )

        self.mount.pulse_south(
            self.pulse_ms,
            speed_mode=self.speed_mode,
        )

        self.state = CalibrationState.WAITING_DEC_SOUTH
        self.message = "Venter på DEC syd-måling"

    def record_dec_south(self):
        self._require_state(
            CalibrationState.WAITING_DEC_SOUTH
        )

        dx, dy = self._read_movement("DEC syd")

        if dx is None:
            return False

        self.dec_south_dx = dx
        self.dec_south_dy = dy

        # Positiv DEC-vektor beskriver nordretningen.
        self.result.dec_dx = (
            self.dec_north_dx
            - self.dec_south_dx
        ) / 2.0

        self.result.dec_dy = (
            self.dec_north_dy
            - self.dec_south_dy
        ) / 2.0

        self.result.dec_pulse_ms = self.pulse_ms

        if (
            self.result.dec_distance_pixels
            < self.minimum_movement_pixels
        ):
            return self._fail(
                "Samlet DEC-bevægelse var for lille: "
                f"{self.result.dec_distance_pixels:.2f} px"
            )

        self.result.completed = True
        self.result.error = None

        self.state = CalibrationState.COMPLETED
        self.message = "Kalibrering færdig"

        return True

    def cancel(self):
        """Annuller kalibreringen og stop mountet."""

        self.mount.safe_stop()

        self.result.completed = False
        self.result.error = "Kalibrering annulleret"

        self.state = CalibrationState.CANCELLED
        self.message = "Kalibrering annulleret"

    def reset(self):
        """Nulstil kalibreringen."""

        self.mount.safe_stop()
        self.result.reset()
        self._reset_measurements()

        self.state = CalibrationState.IDLE
        self.message = "Ikke startet"

    def status(self):
        return {
            "state": self.state.value,
            "message": self.message,
            "active": self.active,
            "completed": self.completed,
            "failed": self.failed,
            "pulse_ms": self.pulse_ms,
            "speed_mode": self.speed_mode,
            "measurements": {
                "ra_east": {
                    "dx": self.ra_east_dx,
                    "dy": self.ra_east_dy,
                },
                "ra_west": {
                    "dx": self.ra_west_dx,
                    "dy": self.ra_west_dy,
                },
                "dec_north": {
                    "dx": self.dec_north_dx,
                    "dy": self.dec_north_dy,
                },
                "dec_south": {
                    "dx": self.dec_south_dx,
                    "dy": self.dec_south_dy,
                },
            },
            "result": self.result.as_dict(),
        }

    def _read_movement(self, label):
        self._require_valid_tracker()

        dx = float(self.tracker.dx)
        dy = float(self.tracker.dy)

        distance = (
            dx * dx
            + dy * dy
        ) ** 0.5

        if distance < self.minimum_movement_pixels:
            self._fail(
                f"{label}-bevægelsen var for lille: "
                f"{distance:.2f} px"
            )
            return None, None

        return dx, dy

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

    def _reset_measurements(self):
        self.ra_east_dx = 0.0
        self.ra_east_dy = 0.0
        self.ra_west_dx = 0.0
        self.ra_west_dy = 0.0

        self.dec_north_dx = 0.0
        self.dec_north_dy = 0.0
        self.dec_south_dx = 0.0
        self.dec_south_dy = 0.0

    def _fail(self, message):
        self.mount.safe_stop()

        self.result.completed = False
        self.result.error = str(message)

        self.state = CalibrationState.FAILED
        self.message = str(message)

        return False
