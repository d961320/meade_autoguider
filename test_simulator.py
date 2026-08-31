#!/usr/bin/env python3

from simulation.simulator import Simulator


simulator = Simulator(
    start_error_pixels=18.0,
    maximum_frames=30,
    deadband_pixels=1.0,
    pulse_ms=200,
    pixels_per_100ms=1.0,
)

report = simulator.run()

assert report["initial_error"] == 18.0
assert report["final_error"] <= 1.0
assert report["final_error"] < report["initial_error"]
assert report["pulses"] > 0
assert report["converged"] is True

assert all(
    command[0] == "west"
    for command in report["commands"]
)

print()
print("Lukket simulator-test bestået.")
