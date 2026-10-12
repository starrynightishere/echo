from random import Random
import unittest

from invert import reflection_loss, scan_thickness
from test_layers import transfer_coefficients


class InversionTests(unittest.TestCase):
    def setUp(self):
        self.materials = (1.5e6, 4.0e6, 2.5e6, 2000.0)
        self.frequencies = [200.0, 350.0, 500.0, 750.0, 1000.0, 1300.0]

    def observations(self, thickness, frequencies=None):
        if frequencies is None:
            frequencies = self.frequencies
        left, middle, right, speed = self.materials
        return [transfer_coefficients(left, [(middle, speed, thickness)], right, f)[0]
                for f in frequencies]

    def test_noiseless_recovery(self):
        observed = self.observations(0.317)
        results = scan_thickness(*self.materials, self.frequencies, observed, 0.05, 0.65)
        best, loss = min(results, key=lambda row: row[1])
        self.assertEqual(len(results), 601)
        self.assertEqual(results[0][0], 0.05)
        self.assertEqual(results[-1][0], 0.65)
        self.assertAlmostEqual(best, 0.317)
        self.assertLess(loss, 1e-25)

    def test_thickness_between_grid_points(self):
        observed = self.observations(0.3174)
        results = scan_thickness(*self.materials, self.frequencies, observed, 0.05, 0.65)
        best, _ = min(results, key=lambda row: row[1])
        self.assertLessEqual(abs(best - 0.3174), 0.0005)

    def test_noisy_recovery(self):
        clean = self.observations(0.317)
        for seed in (0, 7, 19):
            rng = Random(seed)
            observed = [r + complex(rng.gauss(0, 0.005), rng.gauss(0, 0.005)) for r in clean]
            results = scan_thickness(*self.materials, self.frequencies, observed, 0.05, 0.65)
            best, _ = min(results, key=lambda row: row[1])
            with self.subTest(seed=seed):
                self.assertLess(abs(best - 0.317), 0.01)

    def test_loss_uses_complex_measurements(self):
        observed = [r + 3.0 + 4.0j for r in self.observations(0.317)]
        loss = reflection_loss(*self.materials, 0.317, self.frequencies, observed)
        self.assertAlmostEqual(loss, 25.0)

    def test_one_frequency_can_have_equal_fits(self):
        frequencies = [1000.0]
        observed = self.observations(0.317, frequencies)
        for thickness in (0.317, 1.317):
            loss = reflection_loss(*self.materials, thickness, frequencies, observed)
            self.assertLess(loss, 1e-25)

    def test_invalid_measurements(self):
        for frequencies, observed in (([], []), ([100.0], []),
                                      ([100.0], [complex(0, float("nan"))]),
                                      ([100.0], [float("inf")]), ([-100.0], [0j])):
            with self.subTest(frequencies=frequencies, observed=observed):
                with self.assertRaises(ValueError):
                    reflection_loss(*self.materials, 0.317, frequencies, observed)

    def test_invalid_search(self):
        observed = self.observations(0.317)
        for lower, upper, points in ((-0.1, 0.5, 10), (0.5, 0.1, 10),
                                     (0.1, 0.1, 10), (0, float("inf"), 10),
                                     (float("nan"), 1, 10), (0, 1, 1),
                                     (0, 1, 1.5), (0, 1, True)):
            with self.subTest(lower=lower, upper=upper, points=points):
                with self.assertRaises(ValueError):
                    scan_thickness(*self.materials, self.frequencies, observed,
                                   lower, upper, points)


if __name__ == "__main__":
    unittest.main()
