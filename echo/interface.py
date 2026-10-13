from math import isfinite


def pressure_coefficients(z_left, z_right):
    if any(not isfinite(z) or z <= 0 for z in (z_left, z_right)):
        raise ValueError("impedances must be finite and positive")
    total = z_left + z_right
    reflection = (z_right - z_left) / total
    transmission = 2.0 * z_right / total
    return reflection, transmission


def energy_coefficients(z_left, z_right):
    reflection, transmission = pressure_coefficients(z_left, z_right)
    return reflection**2, (z_left / z_right) * transmission**2
