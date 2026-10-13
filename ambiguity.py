import csv
from pathlib import Path
from random import Random

from invert import scan_pairs
from layers import pressure_coefficients


Z_LEFT, Z_RIGHT = 1.5e6, 1.0e6
MATERIALS = [(3.2e6, 1800.0), (2.4e6, 2200.0)]
TRUTH = [(3.2e6, 1800.0, 0.23), (2.4e6, 2200.0, 0.37)]
FREQUENCIES = [1000.0, 2000.0]
NOISE_STD = 0.003
CUTOFF = 4.0 * NOISE_STD**2
FIRST = [0.05 + 0.01 * i for i in range(121)]
SECOND = [0.05 + 0.01 * i for i in range(161)]


def main(output="."):
    rng = Random(7)
    observed = []
    for frequency in FREQUENCIES:
        reflection, _ = pressure_coefficients(Z_LEFT, TRUTH, Z_RIGHT, frequency)
        noise = complex(rng.gauss(0.0, NOISE_STD), rng.gauss(0.0, NOISE_STD))
        observed.append(reflection + noise)

    results = scan_pairs(Z_LEFT, MATERIALS, Z_RIGHT, FREQUENCIES, observed, FIRST, SECOND)
    candidates = [row for row in results if row[2] <= CUTOFF]

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "ambiguity_observations.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frequency_hz", "reflection_real", "reflection_imag"])
        writer.writerows((f, r.real, r.imag) for f, r in zip(FREQUENCIES, observed))
    with (output / "ambiguity.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["first_thickness_m", "second_thickness_m", "mean_squared_error", "accepted"])
        writer.writerows((*row, row[2] <= CUTOFF) for row in results)
    with (output / "candidates.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["first_thickness_m", "second_thickness_m", "mean_squared_error"])
        writer.writerows(candidates)
    return candidates


if __name__ == "__main__":
    main()
