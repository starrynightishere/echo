import csv
import json
from pathlib import Path

import ambiguity
from select_frequency import run_trials, summarize


CASES = [
    {"name": "reference", "left": 1.5e6, "right": 1.0e6,
     "materials": [(3.2e6, 1800.0), (2.4e6, 2200.0)], "truth": [0.23, 0.37]},
    {"name": "deeper", "left": 1.5e6, "right": 1.0e6,
     "materials": [(3.2e6, 1800.0), (2.4e6, 2200.0)], "truth": [0.58, 0.84]},
    {"name": "reversed", "left": 1.5e6, "right": 1.0e6,
     "materials": [(2.4e6, 2200.0), (3.2e6, 1800.0)], "truth": [0.37, 0.23]},
    {"name": "weak contrast", "left": 1.5e6, "right": 1.0e6,
     "materials": [(1.8e6, 1800.0), (1.4e6, 2200.0)], "truth": [0.23, 0.37]},
    {"name": "between grid points", "left": 1.5e6, "right": 1.0e6,
     "materials": [(3.2e6, 1800.0), (2.4e6, 2200.0)], "truth": [0.234, 0.376]},
]
NOISE_LEVELS = [0.001, 0.003, 0.01]
TOLERANCE = 0.005


def paired_counts(rows):
    adaptive = {r["seed"]: r["unique_correct"] for r in rows if r["method"] == "disagreement"}
    random = {r["seed"]: r["unique_correct"] for r in rows if r["method"] == "random"}
    return {
        "trials": len(adaptive),
        "both_correct": sum(adaptive[s] and random[s] for s in adaptive),
        "disagreement_only": sum(adaptive[s] and not random[s] for s in adaptive),
        "random_only": sum(random[s] and not adaptive[s] for s in adaptive),
        "neither_correct": sum(not adaptive[s] and not random[s] for s in adaptive),
    }


def main(output="results", trials=200):
    all_rows, summary, paired = [], [], []
    example = None
    for case in CASES:
        for noise in NOISE_LEVELS:
            rows, detail = run_trials(case["left"], case["materials"], case["right"], case["truth"],
                                      ambiguity.FREQUENCIES, ambiguity.FIRST, ambiguity.SECOND,
                                      noise, trials=trials, tolerance=TOLERANCE)
            label = {"case": case["name"], "noise_std": noise}
            all_rows.extend({**label, **row} for row in rows)
            summary.extend({**label, **row} for row in summarize(rows))
            paired.append({**label, **paired_counts(rows)})
            if case["name"] == "reference" and noise == 0.003:
                example = {**label, "truth": case["truth"], **detail}

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for filename, rows in (("trials.csv", all_rows), ("summary.csv", summary), ("paired.csv", paired)):
        with (output / filename).open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    setup = {
        "cases": CASES,
        "noise_std_per_component": NOISE_LEVELS,
        "trials_per_case_and_noise": trials,
        "noise_seeds": [0, trials - 1],
        "random_choice_seed_offset": 10000,
        "initial_frequencies_hz": ambiguity.FREQUENCIES,
        "frequency_pool_hz": {"start": 200, "stop": 3000, "step": 25,
                              "excluded": ambiguity.FREQUENCIES},
        "first_thickness_grid_m": {"start": 0.05, "stop": 1.25, "step": 0.01},
        "second_thickness_grid_m": {"start": 0.05, "stop": 1.65, "step": 0.01},
        "acceptance_mse": "4 * noise_std**2",
        "correct_within_m_per_layer": TOLERANCE,
        "selection_score": "population variance of complex candidate predictions, equal weights",
        "noise_model": "independent zero-mean Gaussian real and imaginary components",
        "paired_noise": "same initial observations and additional noise for both methods",
        "candidate_update": "filter initial candidates by combined three-measurement MSE",
    }
    (output / "setup.json").write_text(json.dumps(setup, indent=2) + "\n")
    (output / "example.json").write_text(json.dumps(example, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    main()
