from math import cos, pi, sin
from random import Random
import unittest

from echo.interface import pressure_coefficients as interface_coefficients
from echo.layer import pressure_coefficients as single_layer_coefficients
from echo.layers import energy_coefficients, pressure_coefficients


def transfer_coefficients(z_left, stack, z_right, frequency):
    a, b, c, d = 1.0, 0.0, 0.0, 1.0
    for impedance, speed, thickness in stack:
        angle = 2.0 * pi * frequency * thickness / speed
        p, q = cos(angle), -1j * impedance * sin(angle)
        r, s = -1j * sin(angle) / impedance, cos(angle)
        a, b, c, d = a * p + b * r, a * q + b * s, c * p + d * r, c * q + d * s
    pressure = a + b / z_right
    velocity = z_left * (c + d / z_right)
    return (pressure - velocity) / (pressure + velocity), 2.0 / (pressure + velocity)


class LayersTests(unittest.TestCase):
    def assert_coefficients_equal(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=11)

    def test_empty_stack(self):
        self.assertEqual(pressure_coefficients(1.5e6, [], 2.5e6, 1000.0),
                         interface_coefficients(1.5e6, 2.5e6))

    def test_single_layer(self):
        for frequency in (0.0, 100.0, 750.0, 2000.0):
            with self.subTest(frequency=frequency):
                self.assert_coefficients_equal(
                    pressure_coefficients(1.5e6, [(4.0e6, 2000.0, 0.3)], 2.5e6, frequency),
                    single_layer_coefficients(1.5e6, 4.0e6, 2.5e6, 2000.0, 0.3, frequency)
                )

    def test_splitting_a_layer(self):
        original = [(4.0e6, 2000.0, 0.3), (2.0e6, 1700.0, 0.2)]
        split = [(4.0e6, 2000.0, 0.1), (4.0e6, 2000.0, 0.2), (2.0e6, 1700.0, 0.2)]
        for frequency in (100.0, 750.0, 2000.0):
            self.assert_coefficients_equal(
                pressure_coefficients(1.5e6, original, 2.5e6, frequency),
                pressure_coefficients(1.5e6, split, 2.5e6, frequency)
            )

    def test_zero_thickness_layer(self):
        original = [(4.0e6, 2000.0, 0.3), (2.0e6, 1700.0, 0.2)]
        inserted = [original[0], (5.0e6, 2500.0, 0.0), original[1]]
        self.assert_coefficients_equal(
            pressure_coefficients(1.5e6, original, 2.5e6, 750.0),
            pressure_coefficients(1.5e6, inserted, 2.5e6, 750.0)
        )

    def test_transfer_matrix_and_energy(self):
        rng = Random(7)
        for count in range(1, 6):
            for case in range(10):
                left, right = rng.uniform(0.5e6, 6.0e6), rng.uniform(0.5e6, 6.0e6)
                stack = [(rng.uniform(0.5e6, 6.0e6), rng.uniform(1100.0, 2500.0),
                          rng.uniform(0.01, 0.7)) for _ in range(count)]
                frequency = rng.uniform(0.0, 3000.0)
                with self.subTest(layers=count, case=case):
                    self.assert_coefficients_equal(
                        pressure_coefficients(left, stack, right, frequency),
                        transfer_coefficients(left, stack, right, frequency)
                    )
                    reflected, transmitted = energy_coefficients(left, stack, right, frequency)
                    self.assertAlmostEqual(reflected + transmitted, 1.0, places=11)
                    self.assertGreaterEqual(reflected, 0.0)
                    self.assertGreaterEqual(transmitted, 0.0)
                    _, reverse = energy_coefficients(right, reversed(stack), left, frequency)
                    self.assertAlmostEqual(transmitted, reverse, places=11)

    def test_invalid_inputs(self):
        for bad in (-1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                pressure_coefficients(1.5e6, [], 2.5e6, bad)
        for index in range(3):
            invalid = [-1.0, float("nan"), float("inf")]
            if index < 2:
                invalid.append(0.0)
            for bad in invalid:
                layer = [4.0e6, 2000.0, 0.3]
                layer[index] = bad
                with self.subTest(index=index, value=bad):
                    with self.assertRaises(ValueError):
                        pressure_coefficients(1.5e6, [layer], 2.5e6, 1000.0)


if __name__ == "__main__":
    unittest.main()
