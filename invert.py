from math import isfinite

from layers import pressure_coefficients


def reflection_loss(z_left, z_layer, z_right, speed, thickness, frequencies, observed):
    return stack_loss(z_left, [(z_layer, speed, thickness)], z_right, frequencies, observed)


def stack_loss(z_left, stack, z_right, frequencies, observed):
    if not frequencies or len(frequencies) != len(observed):
        raise ValueError("provide one reflection measurement per frequency")
    if any(not isfinite(r.real) or not isfinite(r.imag) for r in observed):
        raise ValueError("measurements must be finite")

    total = 0.0
    for frequency, measured in zip(frequencies, observed):
        predicted, _ = pressure_coefficients(z_left, stack, z_right, frequency)
        total += abs(predicted - measured)**2
    return total / len(frequencies)


def scan_thickness(z_left, z_layer, z_right, speed, frequencies, observed,
                   lower, upper, points=601):
    if not isfinite(lower) or not isfinite(upper) or not 0 <= lower < upper:
        raise ValueError("bounds must be finite and satisfy 0 <= lower < upper")
    if isinstance(points, bool) or not isinstance(points, int) or points < 2:
        raise ValueError("points must be an integer of at least two")

    step = (upper - lower) / (points - 1)
    results = []
    for index in range(points):
        thickness = upper if index == points - 1 else lower + index * step
        loss = reflection_loss(z_left, z_layer, z_right, speed, thickness,
                               frequencies, observed)
        results.append((thickness, loss))
    return results


def scan_pairs(z_left, materials, z_right, frequencies, observed, first, second):
    if len(materials) != 2:
        raise ValueError("provide two (impedance, speed) pairs")
    if not first or not second:
        raise ValueError("provide thickness values for both layers")
    if any(not isfinite(d) or d < 0 for values in (first, second) for d in values):
        raise ValueError("thickness values must be finite and nonnegative")

    (z_first, c_first), (z_second, c_second) = materials
    results = []
    for d_first in first:
        for d_second in second:
            stack = [(z_first, c_first, d_first), (z_second, c_second, d_second)]
            loss = stack_loss(z_left, stack, z_right, frequencies, observed)
            results.append((d_first, d_second, loss))
    return results
