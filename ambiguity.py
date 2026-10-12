import csv
from pathlib import Path
from random import Random

from invert import scan_pairs
from layers import pressure_coefficients


def main(output="."):
    z_left, z_right = 1.5e6, 1.0e6
    materials = [(3.2e6, 1800.0), (2.4e6, 2200.0)]
    truth = [(3.2e6, 1800.0, 0.23), (2.4e6, 2200.0, 0.37)]
    frequencies = [1000.0, 2000.0]
    noise_std = 0.003
    cutoff = 4.0 * noise_std**2
    rng = Random(7)
    observed = []
    for frequency in frequencies:
        reflection, _ = pressure_coefficients(z_left, truth, z_right, frequency)
        noise = complex(rng.gauss(0.0, noise_std), rng.gauss(0.0, noise_std))
        observed.append(reflection + noise)

    first = [0.05 + 0.01 * i for i in range(121)]
    second = [0.05 + 0.01 * i for i in range(161)]
    results = scan_pairs(z_left, materials, z_right, frequencies, observed, first, second)
    candidates = [row for row in results if row[2] <= cutoff]

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "ambiguity_observations.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frequency_hz", "reflection_real", "reflection_imag"])
        writer.writerows((f, r.real, r.imag) for f, r in zip(frequencies, observed))
    with (output / "ambiguity.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["first_thickness_m", "second_thickness_m", "mean_squared_error", "accepted"])
        writer.writerows((*row, row[2] <= cutoff) for row in results)
    with (output / "candidates.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["first_thickness_m", "second_thickness_m", "mean_squared_error"])
        writer.writerows(candidates)
    return candidates


if __name__ == "__main__":
    main()
