from cmath import exp
from math import isfinite, pi

from interface import pressure_coefficients as interface_coefficients


def pressure_coefficients(z_left, stack, z_right, frequency):
    if not isfinite(frequency) or frequency < 0:
        raise ValueError("frequency must be finite and nonnegative")
    stack = list(stack)
    for impedance, speed, thickness in stack:
        if any(not isfinite(v) or v <= 0 for v in (impedance, speed)):
            raise ValueError("impedance and speed must be finite and positive")
        if not isfinite(thickness) or thickness < 0:
            raise ValueError("thickness must be finite and nonnegative")
    if not stack:
        return interface_coefficients(z_left, z_right)

    reflection, transmission = interface_coefficients(stack[-1][0], z_right)
    for index in range(len(stack) - 1, -1, -1):
        impedance, speed, thickness = stack[index]
        incoming = z_left if index == 0 else stack[index - 1][0]
        r, t = interface_coefficients(incoming, impedance)
        phase = exp(2j * pi * frequency * thickness / speed)
        denominator = 1.0 + r * reflection * phase**2
        transmission = t * transmission * phase / denominator
        reflection = (r + reflection * phase**2) / denominator

    return reflection, transmission


def energy_coefficients(z_left, stack, z_right, frequency):
    reflection, transmission = pressure_coefficients(z_left, stack, z_right, frequency)
    return abs(reflection)**2, (z_left / z_right) * abs(transmission)**2
