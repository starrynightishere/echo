import unittest

from experiments.select_frequency import score_frequencies, update_candidates
from tests.test_layers import transfer_coefficients


class FrequencyTests(unittest.TestCase):
    def setUp(self):
        self.left, self.right = 1.5e6, 1.0e6
        self.materials = [(3.2e6, 1800.0), (2.4e6, 2200.0)]
        self.candidates = [(a, b, 0.0) for a in (0.23, 1.13) for b in (0.37, 1.47)]

    def reflection(self, first, second, frequency):
        stack = [(3.2e6, 1800.0, first), (2.4e6, 2200.0, second)]
        return transfer_coefficients(self.left, stack, self.right, frequency)[0]

    def test_scores_match_pairwise_disagreement(self):
        scores = score_frequencies(self.left, self.materials, self.right,
                                   self.candidates, [1000.0, 1370.0, 2000.0])
        for frequency, score in scores:
            values = [self.reflection(a, b, frequency) for a, b, _ in self.candidates]
            pairwise = sum(abs(a - b)**2 for i, a in enumerate(values) for b in values[i + 1:])
            self.assertAlmostEqual(score, pairwise / len(values)**2, places=12)
        self.assertEqual(max(scores, key=lambda row: row[1])[0], 1370.0)

    def test_one_candidate_has_no_disagreement(self):
        scores = score_frequencies(self.left, self.materials, self.right,
                                   self.candidates[:1], [1000.0, 1370.0])
        self.assertTrue(all(score == 0.0 for _, score in scores))

    def test_update_matches_all_three_measurements(self):
        frequencies = [1000.0, 2000.0, 1370.0]
        observed = [self.reflection(0.23, 0.37, f) + 0.001 - 0.002j for f in frequencies]
        candidates = []
        for a, b, _ in self.candidates:
            initial_loss = sum(abs(self.reflection(a, b, f) - value)**2
                               for f, value in zip(frequencies[:2], observed[:2])) / 2
            candidates.append((a, b, initial_loss))
        kept = update_candidates(self.left, self.materials, self.right, candidates,
                                 frequencies[-1], observed[-1], previous_count=2, cutoff=10.0)
        self.assertEqual(len(kept), 4)
        for a, b, loss in kept:
            expected = sum(abs(self.reflection(a, b, f) - value)**2
                           for f, value in zip(frequencies, observed)) / 3
            self.assertAlmostEqual(loss, expected, places=12)

    def test_new_frequency_resolves_candidates(self):
        observed = self.reflection(0.23, 0.37, 1370.0)
        kept = update_candidates(self.left, self.materials, self.right, self.candidates,
                                 1370.0, observed, previous_count=2, cutoff=4 * 0.003**2)
        self.assertEqual([(a, b) for a, b, _ in kept], [(0.23, 0.37)])

    def test_harmonic_frequency_leaves_ambiguity(self):
        observed = self.reflection(0.23, 0.37, 3000.0)
        kept = update_candidates(self.left, self.materials, self.right, self.candidates,
                                 3000.0, observed, previous_count=2, cutoff=4 * 0.003**2)
        self.assertEqual(len(kept), 4)

    def test_bad_measurement_can_reject_every_candidate(self):
        kept = update_candidates(self.left, self.materials, self.right, self.candidates,
                                 1370.0, 3.0 + 3.0j, previous_count=2, cutoff=4 * 0.003**2)
        self.assertEqual(kept, [])

    def test_invalid_inputs(self):
        for candidates, frequencies in (([], [1000.0]), (self.candidates, []),
                                       (self.candidates, [-100.0])):
            with self.assertRaises(ValueError):
                score_frequencies(self.left, self.materials, self.right, candidates, frequencies)
        defaults = dict(frequency=1370.0, observed=0j, previous_count=2, cutoff=0.01)
        for name, value in (("previous_count", 0), ("previous_count", 1.5),
                            ("previous_count", True), ("cutoff", -1),
                            ("cutoff", float("nan")), ("observed", complex(float("inf"), 0))):
            with self.subTest(name=name, value=value):
                with self.assertRaises(ValueError):
                    update_candidates(self.left, self.materials, self.right, self.candidates,
                                      **{**defaults, name: value})


if __name__ == "__main__":
    unittest.main()
