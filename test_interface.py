import unittest

from interface import energy_coefficients, pressure_coefficients


class InterfaceTests(unittest.TestCase):
    def test_matched_impedance(self):
        self.assertEqual(pressure_coefficients(1.5e6, 1.5e6), (0.0, 1.0))
        self.assertEqual(energy_coefficients(1.5e6, 1.5e6), (0.0, 1.0))

    def test_boundary_conditions_and_energy(self):
        for left, right in ((1.0, 3.0), (3.0, 1.0), (400.0, 1.5e6),
                            (1.5e6, 400.0), (1.5e6, 3.0e6)):
            with self.subTest(left=left, right=right):
                r, t = pressure_coefficients(left, right)
                self.assertAlmostEqual(1.0 + r, t)
                self.assertAlmostEqual((1.0 - r) / left, t / right)
                reflected, transmitted = energy_coefficients(left, right)
                self.assertAlmostEqual(reflected + transmitted, 1.0)
                self.assertGreaterEqual(reflected, 0.0)
                self.assertGreaterEqual(transmitted, 0.0)

    def test_pressure_and_energy_are_different(self):
        self.assertEqual(pressure_coefficients(1.0, 3.0), (0.5, 1.5))
        self.assertEqual(energy_coefficients(1.0, 3.0), (0.25, 0.75))

    def test_reversing_direction(self):
        r_forward, _ = pressure_coefficients(400.0, 1.5e6)
        r_backward, _ = pressure_coefficients(1.5e6, 400.0)
        self.assertEqual(r_forward, -r_backward)
        _, forward = energy_coefficients(400.0, 1.5e6)
        _, backward = energy_coefficients(1.5e6, 400.0)
        self.assertAlmostEqual(forward, backward)

    def test_invalid_impedance(self):
        for value in (0, -1, float("nan"), float("inf")):
            for left, right in ((value, 1.0), (1.0, value)):
                with self.subTest(left=left, right=right):
                    with self.assertRaises(ValueError):
                        pressure_coefficients(left, right)


if __name__ == "__main__":
    unittest.main()
