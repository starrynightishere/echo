from cmath import exp
from math import pi, sqrt
import unittest

from interface import pressure_coefficients as interface_coefficients
from layer import energy_coefficients, pressure_coefficients


class LayerTests(unittest.TestCase):
    def test_zero_thickness(self):
        expected = interface_coefficients(1.5e6, 2.5e6)
        actual = pressure_coefficients(1.5e6, 4.0e6, 2.5e6, 2000.0, 0.0, 1000.0)
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b)

    def test_zero_frequency(self):
        expected = interface_coefficients(1.5e6, 2.5e6)
        actual = pressure_coefficients(1.5e6, 4.0e6, 2.5e6, 2000.0, 0.3, 0.0)
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b)

    def test_identical_materials(self):
        r, t = pressure_coefficients(1.5e6, 1.5e6, 1.5e6, 1500.0, 0.2, 1000.0)
        self.assertAlmostEqual(r, 0.0)
        self.assertAlmostEqual(t, exp(2j * pi * 1000.0 * 0.2 / 1500.0))
        reflected, transmitted = energy_coefficients(
            1.5e6, 1.5e6, 1.5e6, 1500.0, 0.2, 1000.0
        )
        self.assertAlmostEqual(reflected, 0.0)
        self.assertAlmostEqual(transmitted, 1.0)

    def test_quarter_wave_matching(self):
        left, right = 1.5e6, 6.0e6
        speed, frequency = 2000.0, 1000.0
        thickness = speed / (4.0 * frequency)
        r, t = pressure_coefficients(left, sqrt(left * right), right,
                                     speed, thickness, frequency)
        self.assertAlmostEqual(r, 0.0)
        self.assertAlmostEqual(t, 1j * sqrt(right / left))

    def test_boundary_conditions_and_energy(self):
        for left, middle, right in ((1.5e6, 4.0e6, 2.5e6), (400.0, 1.5e6, 400.0),
                                    (2.5e6, 4.0e6, 1.5e6)):
            for frequency in (100.0, 750.0, 2000.0):
                with self.subTest(impedances=(left, middle, right), frequency=frequency):
                    r, t = pressure_coefficients(left, middle, right, 2000.0, 0.3, frequency)
                    forward = ((1.0 + r) + (middle / left) * (1.0 - r)) / 2.0
                    backward = ((1.0 + r) - (middle / left) * (1.0 - r)) / 2.0
                    phase = exp(2j * pi * frequency * 0.3 / 2000.0)
                    self.assertAlmostEqual(forward * phase + backward / phase, t)
                    self.assertAlmostEqual((forward * phase - backward / phase) / middle,
                                           t / right)
                    reflected, transmitted = energy_coefficients(
                        left, middle, right, 2000.0, 0.3, frequency
                    )
                    self.assertAlmostEqual(reflected + transmitted, 1.0)
                    self.assertGreaterEqual(reflected, 0.0)
                    self.assertGreaterEqual(transmitted, 0.0)

    def test_invalid_inputs(self):
        defaults = dict(z_left=1.5e6, z_layer=4.0e6, z_right=2.5e6,
                        speed=2000.0, thickness=0.3, frequency=1000.0)
        for name in defaults:
            invalid = [-1.0, float("nan"), float("inf")]
            if name not in ("thickness", "frequency"):
                invalid.append(0.0)
            for value in invalid:
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        pressure_coefficients(**{**defaults, name: value})


if __name__ == "__main__":
    unittest.main()
