import unittest

from echo.invert import scan_pairs, stack_loss
from tests.test_layers import transfer_coefficients


class AmbiguityTests(unittest.TestCase):
    def setUp(self):
        self.left, self.right = 1.5e6, 1.0e6
        self.materials = [(3.2e6, 1800.0), (2.4e6, 2200.0)]
        self.truth = [(3.2e6, 1800.0, 0.23), (2.4e6, 2200.0, 0.37)]
        self.frequencies = [1000.0, 2000.0]
        self.observed = [transfer_coefficients(self.left, self.truth, self.right, f)[0]
                         for f in self.frequencies]

    def test_distinct_pairs_fit_the_same_data(self):
        results = scan_pairs(self.left, self.materials, self.right, self.frequencies,
                             self.observed, [0.23, 0.5, 1.13], [0.37, 0.8, 1.47])
        self.assertEqual(len(results), 9)
        accepted = {(a, b) for a, b, loss in results if loss < 1e-25}
        self.assertEqual(accepted, {(0.23, 0.37), (0.23, 1.47),
                                    (1.13, 0.37), (1.13, 1.47)})

    def test_losses_match_transfer_matrices(self):
        observed = [r + 0.002 - 0.003j for r in self.observed]
        results = scan_pairs(self.left, self.materials, self.right, self.frequencies,
                             observed, [0.23, 0.5, 1.13], [0.37, 0.8, 1.47])
        for first, second, loss in results:
            with self.subTest(first=first, second=second):
                stack = [(3.2e6, 1800.0, first), (2.4e6, 2200.0, second)]
                predicted = [transfer_coefficients(self.left, stack, self.right, f)[0]
                             for f in self.frequencies]
                expected = sum(abs(a - b)**2 for a, b in zip(predicted, observed)) / 2
                self.assertAlmostEqual(loss, expected, places=12)

    def test_additional_frequency_can_distinguish_pairs(self):
        frequency = [1370.0]
        observed = [transfer_coefficients(self.left, self.truth, self.right, frequency[0])[0]]
        alternative = [(3.2e6, 1800.0, 1.13), (2.4e6, 2200.0, 0.37)]
        self.assertLess(stack_loss(self.left, self.truth, self.right, frequency, observed), 1e-25)
        self.assertGreater(stack_loss(self.left, alternative, self.right, frequency, observed), 1e-3)

    def test_invalid_grid(self):
        cases = [([], [0.37]), ([0.23], []), ([-0.1], [0.37]),
                 ([0.23], [float("nan")]), ([float("inf")], [0.37])]
        for first, second in cases:
            with self.subTest(first=first, second=second):
                with self.assertRaises(ValueError):
                    scan_pairs(self.left, self.materials, self.right, self.frequencies,
                               self.observed, first, second)
        with self.assertRaises(ValueError):
            scan_pairs(self.left, self.materials[:1], self.right, self.frequencies,
                       self.observed, [0.23], [0.37])


if __name__ == "__main__":
    unittest.main()
