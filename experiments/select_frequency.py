import csv
from math import isfinite
from pathlib import Path
from random import Random
from statistics import mean

from experiments import ambiguity
from echo.layers import pressure_coefficients


def predictions(z_left, materials, z_right, candidates, frequency):
    if len(materials) != 2:
        raise ValueError("provide two (impedance, speed) pairs")
    values = []
    for first, second, _ in candidates:
        stack = [(*materials[0], first), (*materials[1], second)]
        values.append(pressure_coefficients(z_left, stack, z_right, frequency)[0])
    return values


def score_frequencies(z_left, materials, z_right, candidates, frequencies):
    if not candidates or not frequencies:
        raise ValueError("provide candidates and measurement frequencies")
    scores = []
    for frequency in frequencies:
        values = predictions(z_left, materials, z_right, candidates, frequency)
        center = sum(values) / len(values)
        disagreement = sum(abs(value - center)**2 for value in values) / len(values)
        scores.append((frequency, disagreement))
    return scores


def update_candidates(z_left, materials, z_right, candidates, frequency,
                      observed, previous_count, cutoff):
    if isinstance(previous_count, bool) or not isinstance(previous_count, int) or previous_count < 1:
        raise ValueError("previous_count must be a positive integer")
    if not isfinite(cutoff) or cutoff < 0:
        raise ValueError("cutoff must be finite and nonnegative")
    if not isfinite(observed.real) or not isfinite(observed.imag):
        raise ValueError("measurement must be finite")
    if any(not isfinite(row[2]) or row[2] < 0 for row in candidates):
        raise ValueError("candidate losses must be finite and nonnegative")

    values = predictions(z_left, materials, z_right, candidates, frequency)
    kept = []
    for (first, second, loss), predicted in zip(candidates, values):
        combined = (previous_count * loss + abs(predicted - observed)**2) / (previous_count + 1)
        if combined <= cutoff:
            kept.append((first, second, combined))
    return kept


def contains_target(candidates, truth, tolerance):
    first, second = truth
    return any(abs(a - first) <= tolerance + 1e-12 and abs(b - second) <= tolerance + 1e-12
               for a, b, _ in candidates)


def run_trials(left, materials, right, truth, measured, first, second,
               noise_std, trials=200, tolerance=0.005, pool=None):
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 1:
        raise ValueError("trials must be a positive integer")
    if not isfinite(noise_std) or noise_std <= 0:
        raise ValueError("noise_std must be finite and positive")
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    if len(materials) != 2 or len(truth) != 2 or not measured or not first or not second:
        raise ValueError("provide two materials, two true thicknesses, frequencies and grids")
    if pool is None:
        pool = [float(f) for f in range(200, 3001, 25)]
    pool = sorted(set(pool) - set(measured))
    if not pool or any(not isfinite(f) or f <= 0 for f in pool):
        raise ValueError("provide positive finite unmeasured frequencies")
    cutoff = 4.0 * noise_std**2
    stack = [(*material, thickness) for material, thickness in zip(materials, truth)]
    grid = [(a, b, 0.0) for a in first for b in second]
    initial_predictions = [predictions(left, materials, right, grid, f) for f in measured]
    clean = [pressure_coefficients(left, stack, right, f)[0] for f in measured]
    rows, example, score_cache = [], {}, {}

    for seed in range(trials):
        rng = Random(seed)
        observed = [value + complex(rng.gauss(0, noise_std), rng.gauss(0, noise_std))
                    for value in clean]
        candidates = []
        for index, (first, second, _) in enumerate(grid):
            loss = sum(abs(values[index] - value)**2
                       for values, value in zip(initial_predictions, observed)) / len(measured)
            if loss <= cutoff:
                candidates.append((first, second, loss))

        key = tuple((a, b) for a, b, _ in candidates)
        if key not in score_cache:
            score_cache[key] = score_frequencies(left, materials, right, candidates, pool) if key else []
        scores = score_cache[key]
        if seed == min(7, trials - 1):
            example = {"seed": seed, "initial": candidates, "scores": scores}
        chosen = max(scores, key=lambda row: row[1])[0] if scores else None
        random_frequency = Random(10000 + seed).choice(pool) if candidates else None
        noise = complex(rng.gauss(0, noise_std), rng.gauss(0, noise_std))

        for method, frequency in (("disagreement", chosen), ("random", random_frequency)):
            value, kept = None, []
            if frequency is not None:
                value = pressure_coefficients(left, stack, right, frequency)[0] + noise
                kept = update_candidates(left, materials, right, candidates, frequency,
                                         value, len(measured), cutoff)
            if seed == min(7, trials - 1):
                example[method] = {"frequency_hz": frequency, "remaining": kept}
            rows.append({
                "seed": seed,
                "method": method,
                "initial_candidates": len(candidates),
                "initial_target_retained": contains_target(candidates, truth, tolerance),
                "frequency_hz": frequency,
                "observed_real": value.real if value is not None else None,
                "observed_imag": value.imag if value is not None else None,
                "remaining_candidates": len(kept),
                "target_retained": contains_target(kept, truth, tolerance),
                "unique_correct": len(kept) == 1 and contains_target(kept, truth, tolerance),
                "surviving_pairs": ";".join(f"{a:.12g},{b:.12g}" for a, b, _ in kept),
            })
    return rows, example


def summarize(rows):
    summary = []
    for method in ("disagreement", "random"):
        group = [row for row in rows if row["method"] == method]
        summary.append({
            "method": method,
            "trials": len(group),
            "initial_target_missing": sum(not r["initial_target_retained"] for r in group),
            "unique_correct": sum(r["unique_correct"] for r in group),
            "wrong_unique": sum(r["remaining_candidates"] == 1 and not r["target_retained"] for r in group),
            "ambiguous": sum(r["remaining_candidates"] > 1 for r in group),
            "empty": sum(r["remaining_candidates"] == 0 for r in group),
            "target_retained": sum(r["target_retained"] for r in group),
            "mean_remaining_candidates": mean(r["remaining_candidates"] for r in group),
        })
    return summary


def main(output=Path(__file__).resolve().parents[1] / "results" / "select_frequency", trials=200):
    truth = [layer[2] for layer in ambiguity.TRUTH]
    rows, example = run_trials(ambiguity.Z_LEFT, ambiguity.MATERIALS, ambiguity.Z_RIGHT,
                               truth, ambiguity.FREQUENCIES, ambiguity.FIRST, ambiguity.SECOND,
                               ambiguity.NOISE_STD, trials=trials)
    summary = summarize(rows)
    example_scores = [{"seed": example["seed"], "frequency_hz": f, "disagreement": score}
                      for f, score in example["scores"]]

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    tables = [("selection_trials.csv", rows), ("selection_summary.csv", summary)]
    tables.append(("frequency_scores.csv", example_scores))
    for filename, table in tables:
        with (output / filename).open("w", newline="") as file:
            fields = table[0].keys() if table else ["seed", "frequency_hz", "disagreement"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(table)
    return summary


if __name__ == "__main__":
    main()
