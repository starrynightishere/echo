from random import Random
import unittest

from benchmark import paired_counts
from invert import stack_loss
from select_frequency import contains_target, run_trials, summarize
from test_layers import transfer_coefficients


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.materials = [(2.4e6, 2200.0), (3.2e6, 1800.0)]
        self.truth = [0.41, 0.29]
        self.first, self.second = [0.41, 1.51], [0.29, 1.19]
        self.measured = [1000.0, 2000.0]
        self.pool = [500.0, 1000.0, 1370.0, 2000.0, 2500.0]

    def reflection(self, first, second, frequency):
        stack = [(*self.materials[0], first), (*self.materials[1], second)]
        return transfer_coefficients(1.5e6, stack, 1.0e6, frequency)[0]

    def test_trials_against_transfer_matrices(self):
        rows, _ = run_trials(1.5e6, self.materials, 1.0e6, self.truth, self.measured,
                              self.first, self.second, 0.003, trials=8, pool=self.pool)
        self.assertEqual(len(rows), 16)
        self.assertTrue(any(row["unique_correct"] for row in rows))
        for row in rows:
            rng = Random(row["seed"])
            observations = [self.reflection(*self.truth, f)
                            + complex(rng.gauss(0, 0.003), rng.gauss(0, 0.003))
                            for f in self.measured]
            extra_noise = complex(rng.gauss(0, 0.003), rng.gauss(0, 0.003))
            initial = []
            for a in self.first:
                for b in self.second:
                    loss = sum(abs(self.reflection(a, b, f) - value)**2
                               for f, value in zip(self.measured, observations)) / 2
                    if loss <= 4 * 0.003**2:
                        initial.append((a, b, loss))
            self.assertEqual(row["initial_candidates"], len(initial))
            frequency = row["frequency_hz"]
            if frequency is None:
                self.assertEqual(initial, [])
                self.assertFalse(row["unique_correct"])
                continue
            self.assertNotIn(frequency, self.measured)
            measured = self.reflection(*self.truth, frequency) + extra_noise
            self.assertAlmostEqual(complex(row["observed_real"], row["observed_imag"]), measured)
            kept = [(a, b) for a, b, loss in initial
                    if (2 * loss + abs(self.reflection(a, b, frequency) - measured)**2) / 3 <= 4 * 0.003**2]
            self.assertEqual(row["remaining_candidates"], len(kept))
            correct = any(abs(a - self.truth[0]) < 0.005 and abs(b - self.truth[1]) < 0.005
                          for a, b in kept)
            self.assertEqual(row["unique_correct"], len(kept) == 1 and correct)
            if row["method"] == "disagreement":
                scores = {}
                for f in set(self.pool) - set(self.measured):
                    values = [self.reflection(a, b, f) for a, b, _ in initial]
                    center = sum(values) / len(values)
                    scores[f] = sum(abs(v - center)**2 for v in values) / len(values)
                self.assertAlmostEqual(scores[frequency], max(scores.values()), places=12)
        for item in summarize(rows):
            self.assertEqual(sum(item[key] for key in ("unique_correct", "wrong_unique", "ambiguous", "empty")), 8)
        paired = paired_counts(rows)
        self.assertEqual(sum(paired[key] for key in ("both_correct", "disagreement_only", "random_only", "neither_correct")), 8)

    def test_tolerance_uses_the_given_truth(self):
        candidates = [(0.23, 0.38, 0.0)]
        self.assertTrue(contains_target(candidates, [0.234, 0.376], 0.005))
        self.assertFalse(contains_target(candidates, [0.234, 0.376], 0.001))
        self.assertTrue(contains_target([(0.24, 0.37, 0.0)], [0.235, 0.37], 0.005))
        self.assertFalse(contains_target(candidates, [0.41, 0.29], 0.005))

    def test_stack_iterator_is_reused_across_frequencies(self):
        stack = [(*self.materials[0], 0.41), (*self.materials[1], 0.29)]
        observed = [self.reflection(0.41, 0.29, f) for f in self.measured]
        self.assertLess(stack_loss(1.5e6, iter(stack), 1.0e6, self.measured, observed), 1e-25)

    def test_invalid_trial_settings(self):
        for options in ({"trials": 0}, {"trials": True}, {"tolerance": -1},
                        {"pool": self.measured}, {"pool": [float("nan")]}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    run_trials(1.5e6, self.materials, 1.0e6, self.truth, self.measured,
                               self.first, self.second, 0.003, **options)


if __name__ == "__main__":
    unittest.main()
