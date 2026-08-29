#!/usr/bin/env python3

"""
GuideController

Koordinerer tracking, kalibrering og guiding.

GUI'en skal senere kun kalde:

    controller.step()

GuideController udfører ikke selv billedbehandling eller
beregning af guidepulser. Den fordeler arbejdet til de
relevante guiding-moduler.
"""

from enum import Enum, auto


class GuideState(Enum):
    IDLE = auto()
    STAR_SELECTED = auto()
    CALIBRATING = auto()
    READY = auto()
    GUIDING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()


class GuideController:
    def __init__(
        self,
        tracker=None,
        calibration=None,
        guide_loop=None,
    ):
        self.state = GuideState.IDLE

        self.tracker = tracker
        self.calibration = calibration
        self.guide_loop = guide_loop

        self.last_error = None
        self.last_status = None

    def set_tracker(self, tracker):
        self.tracker = tracker
        self._update_tracking_state()

    def set_calibration(self, calibration):
        self.calibration = calibration

    def set_guide_loop(self, guide_loop):
        self.guide_loop = guide_loop

    def select_star(self):
        """
        Markér, at GuideTracker har fået en låst stjerne.

        Selve stjernen låses fortsat med tracker.lock(star).
        """

        if self.tracker is None:
            raise RuntimeError(
                "GuideTracker er ikke tilknyttet"
            )

        if not self.tracker.locked:
            raise RuntimeError(
                "Ingen guide-stjerne er låst"
            )

        if self.tracker.lost:
            raise RuntimeError(
                "Guide-stjernen er mistet"
            )

        self.state = GuideState.STAR_SELECTED
        self.last_error = None

    def release_star(self):
        """Frigiv guiding-tilstanden."""

        self.stop_guiding()

        if (
            self.tracker is not None
            and self.tracker.locked
        ):
            self.tracker.unlock()

        self.state = GuideState.IDLE
        self.last_status = None
        self.last_error = None

    def start_calibration(self):
        """Start det tilknyttede kalibreringsmodul."""

        if self.calibration is None:
            raise RuntimeError(
                "Calibration er ikke tilknyttet"
            )

        self._require_locked_star()

        if not self.calibration.start():
            error = getattr(
                self.calibration.result,
                "error",
                None,
            )

            self._set_error(
                error or "Kalibrering kunne ikke startes"
            )
            return False

        self.state = GuideState.CALIBRATING
        self.last_error = None
        return True

    def finish_calibration(self):
        """
        Opdatér tilstanden efter afsluttet kalibrering.

        Kalibreringssekvensen styres foreløbig af
        Calibration-objektets egne metoder.
        """

        if self.calibration is None:
            raise RuntimeError(
                "Calibration er ikke tilknyttet"
            )

        if self.calibration.completed:
            self.state = GuideState.READY
            self.last_error = None
            return True

        if self.calibration.failed:
            message = getattr(
                self.calibration,
                "message",
                "Kalibrering mislykkedes",
            )

            self._set_error(message)
            return False

        return False

    def start_guiding(self):
        """Aktivér guide-loopet."""

        if self.guide_loop is None:
            raise RuntimeError(
                "GuideLoop er ikke tilknyttet"
            )

        self._require_locked_star()

        self.state = GuideState.GUIDING
        self.last_error = None

    def pause_guiding(self):
        if self.state != GuideState.GUIDING:
            raise RuntimeError(
                "Guiding er ikke aktiv"
            )

        self.state = GuideState.PAUSED

    def resume_guiding(self):
        if self.state != GuideState.PAUSED:
            raise RuntimeError(
                "Guiding er ikke sat på pause"
            )

        self._require_locked_star()
        self.state = GuideState.GUIDING

    def stop_guiding(self):
        if self.state in {
            GuideState.GUIDING,
            GuideState.PAUSED,
        }:
            self.state = (
                GuideState.STAR_SELECTED
                if self._star_is_available()
                else GuideState.IDLE
            )

    def step(self):
        """
        Kaldes én gang efter hvert nyt kamerabillede.

        GuideTracker skal være opdateret, før denne metode
        bliver kaldt.
        """

        self._update_tracking_state()

        if self.state == GuideState.ERROR:
            return self.status()

        if self.state == GuideState.CALIBRATING:
            self.finish_calibration()
            return self.status()

        if self.state == GuideState.GUIDING:
            if self.guide_loop is None:
                self._set_error(
                    "GuideLoop er ikke tilknyttet"
                )
                return self.status()

            try:
                self.last_status = (
                    self.guide_loop.step()
                )

            except Exception as error:
                self._set_error(str(error))

        return self.status()

    def status(self):
        tracker_status = None

        if self.tracker is not None:
            tracker_status = (
                self.tracker.status()
            )

        calibration_status = None

        if self.calibration is not None:
            calibration_status = (
                self.calibration.status()
            )

        guide_status = self.last_status

        if hasattr(guide_status, "__dict__"):
            guide_status = dict(
                guide_status.__dict__
            )

        return {
            "state": self.state.name,
            "error": self.last_error,
            "tracker_available": (
                self.tracker is not None
            ),
            "calibration_available": (
                self.calibration is not None
            ),
            "guide_loop_available": (
                self.guide_loop is not None
            ),
            "tracker": tracker_status,
            "calibration": calibration_status,
            "guide": guide_status,
        }

    def reset(self):
        """Nulstil controllerens tilstand."""

        if self.calibration is not None:
            reset_method = getattr(
                self.calibration,
                "reset",
                None,
            )

            if callable(reset_method):
                reset_method()

        self.state = (
            GuideState.STAR_SELECTED
            if self._star_is_available()
            else GuideState.IDLE
        )

        self.last_status = None
        self.last_error = None

    def _update_tracking_state(self):
        if self.tracker is None:
            if self.state not in {
                GuideState.STOPPED,
                GuideState.ERROR,
            }:
                self.state = GuideState.IDLE

            return

        if self.tracker.lost:
            if self.state in {
                GuideState.CALIBRATING,
                GuideState.GUIDING,
            }:
                self._set_error(
                    "Guide-stjernen er mistet"
                )

            return

        if (
            self.tracker.locked
            and self.state == GuideState.IDLE
        ):
            self.state = GuideState.STAR_SELECTED

        elif (
            not self.tracker.locked
            and self.state
            not in {
                GuideState.ERROR,
                GuideState.STOPPED,
            }
        ):
            self.state = GuideState.IDLE

    def _require_locked_star(self):
        if self.tracker is None:
            raise RuntimeError(
                "GuideTracker er ikke tilknyttet"
            )

        if not self.tracker.locked:
            raise RuntimeError(
                "Ingen guide-stjerne er låst"
            )

        if self.tracker.lost:
            raise RuntimeError(
                "Guide-stjernen er mistet"
            )

    def _star_is_available(self):
        return bool(
            self.tracker is not None
            and self.tracker.locked
            and not self.tracker.lost
        )

    def _set_error(self, message):
        self.last_error = str(message)
        self.state = GuideState.ERROR
