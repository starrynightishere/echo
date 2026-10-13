from cmath import exp
from math import isfinite, pi

from echo.interface import pressure_coefficients as interface_coefficients


def pressure_coefficients(z_left, z_layer, z_right, speed, thickness, frequency):
    if not isfinite(speed) or speed <= 0:
        raise ValueError("speed must be finite and positive")
    if any(not isfinite(v) or v < 0 for v in (thickness, frequency)):
        raise ValueError("thickness and frequency must be finite and nonnegative")

    r_left, t_left = interface_coefficients(z_left, z_layer)
    r_right, t_right = interface_coefficients(z_layer, z_right)
    phase = exp(2j * pi * frequency * thickness / speed)
    denominator = 1.0 + r_left * r_right * phase**2
    reflection = (r_left + r_right * phase**2) / denominator
    transmission = t_left * t_right * phase / denominator
    return reflection, transmission


def energy_coefficients(z_left, z_layer, z_right, speed, thickness, frequency):
    reflection, transmission = pressure_coefficients(
        z_left, z_layer, z_right, speed, thickness, frequency
    )
    return abs(reflection)**2, (z_left / z_right) * abs(transmission)**2
