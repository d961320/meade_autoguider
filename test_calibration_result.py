#!/usr/bin/env python3

from guiding.calibration_result import CalibrationResult


result = CalibrationResult(
    reference_x=214.3,
    reference_y=148.9,

    ra_dx=12.0,
    ra_dy=5.0,
    ra_pulse_ms=1000,

    dec_dx=-3.0,
    dec_dy=4.0,
    dec_pulse_ms=1000,

    completed=True,
)

print("Reference:")
print(
    result.reference_x,
    result.reference_y,
)

print()
print(
    "RA distance:",
    f"{result.ra_distance_pixels:.3f} px",
)
print(
    "RA pixels/ms:",
    f"{result.ra_pixels_per_ms:.6f}",
)

print()
print(
    "DEC distance:",
    f"{result.dec_distance_pixels:.3f} px",
)
print(
    "DEC pixels/ms:",
    f"{result.dec_pixels_per_ms:.6f}",
)

print()
print("Valid:", result.valid)

assert round(
    result.ra_distance_pixels,
    3,
) == 13.000

assert round(
    result.dec_distance_pixels,
    3,
) == 5.000

assert result.valid is True

print()
print("CalibrationResult-test bestået.")
