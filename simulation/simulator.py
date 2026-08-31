#!/usr/bin/env python3

"""
Meade Autoguider – lukket RA-simulator.

Bruger de rigtige klasser:

- GuideTracker
- GuideController
- GuideLoop
- CalibrationResult
"""

from guiding.calibration_result import CalibrationResult
from guiding.controller import (
    GuideController,
    GuideState,
)
from guiding.guide_loop import GuideLoop
from guiding.tracker import GuideTracker

from simulation.camera import FakeCamera
from simulation.mount import FakeMount
from simulation.world import World


class Simulator:
    def __init__(
        self,
        start_error_pixels=18.0,
        maximum_frames=100,
        deadband_pixels=1.0,
        pulse_ms=200,
        pixels_per_100ms=1.0,
    ):
        self.start_error_pixels = float(
            start_error_pixels
        )
        self.maximum_frames = int(
            maximum_frames
        )
        self.deadband_pixels = float(
            deadband_pixels
        )

        self.world = World(
            x=320.0,
            y=240.0,
        )

        self.camera = FakeCamera(
            self.world
        )

        self.mount = FakeMount(
            self.world,
            pixels_per_100ms=pixels_per_100ms,
        )

        self.tracker = GuideTracker()

        # Kalibreringen beskriver:
        # 1000 ms EAST = +10 pixels i X.
        # 1000 ms NORTH = -10 pixels i Y.
        calibration = CalibrationResult(
            reference_x=320.0,
            reference_y=240.0,

            ra_dx=10.0,
            ra_dy=0.0,
            ra_pulse_ms=1000,

            dec_dx=0.0,
            dec_dy=-10.0,
            dec_pulse_ms=1000,

            completed=True,
        )

        if not calibration.valid:
            raise RuntimeError(
                "Simulatorens kalibrering er ugyldig"
            )

        self.guide_loop = GuideLoop(
            tracker=self.tracker,
            mount=self.mount,
            calibration=calibration,

            ra_deadband_pixels=deadband_pixels,
            ra_pulse_ms=pulse_ms,
            pulse_cooldown_seconds=0.0,

            ra_positive_direction="west",
            ra_negative_direction="east",
        )

        self.controller = GuideController(
            tracker=self.tracker,
            guide_loop=self.guide_loop,
        )

        self.errors = []

    def prepare(self):
        """Lås stjernen og opret en kendt startfejl."""

        stars = self.camera.capture()
        self.tracker.lock(stars[0])

        self.controller.select_star()

        # Flyt stjernen efter låsning, så der opstår
        # en guidefejl i positiv RA-retning.
        self.world.move(
            self.start_error_pixels,
            0.0,
        )

        self.controller.start_guiding()

        if (
            self.controller.state
            != GuideState.GUIDING
        ):
            raise RuntimeError(
                "Guiding kunne ikke startes"
            )

    def step(self):
        stars = self.camera.capture()

        self.tracker.update(stars)

        ra_error = (
            self.guide_loop._compute_ra_error()
        )

        self.errors.append(
            abs(ra_error)
        )

        self.controller.step()
        self.world.step()

        return ra_error

    def run(self):
        self.prepare()

        # Opdatér trackeren efter startforskydningen,
        # før startfejlen beregnes.
        self.tracker.update(
            self.camera.capture()
        )

        initial_error = abs(
            self.guide_loop._compute_ra_error()
        )

        frames_run = 0

        for frame in range(
            1,
            self.maximum_frames + 1,
        ):
            error = self.step()
            frames_run = frame

            print(
                f"Frame {frame:3d}: "
                f"RA error={error:+7.3f} px"
            )

            if abs(error) <= self.deadband_pixels:
                break

        # Opdatér trackeren efter den sidst sendte puls.
        self.tracker.update(
            self.camera.capture()
        )

        final_error = abs(
            self.guide_loop._compute_ra_error()
        )

        pulse_commands = [
            command
            for command in self.mount.commands
            if command[0] in {
                "east",
                "west",
                "north",
                "south",
            }
        ]

        return {
            "frames": frames_run,
            "initial_error": initial_error,
            "final_error": final_error,
            "pulses": len(pulse_commands),
            "commands": pulse_commands,
            "converged": (
                final_error
                <= self.deadband_pixels
            ),
        }


def print_report(report):
    print()
    print("=" * 40)
    print(" Meade Autoguider Simulator")
    print("=" * 40)

    print(
        "Frames       :",
        report["frames"],
    )

    print(
        "Startfejl    :",
        f"{report['initial_error']:.3f} px",
    )

    print(
        "Slutfejl     :",
        f"{report['final_error']:.3f} px",
    )

    print(
        "Pulser sendt :",
        report["pulses"],
    )

    print(
        "Konvergeret  :",
        "JA" if report["converged"] else "NEJ",
    )


def main():
    simulator = Simulator()
    report = simulator.run()

    print_report(report)

    if not report["converged"]:
        raise SystemExit(
            "Simulatoren konvergerede ikke"
        )


if __name__ == "__main__":
    main()
