import csv
from pathlib import Path
from random import Random

from invert import scan_thickness
from layer import pressure_coefficients


def main(output="."):
    z_left, z_layer, z_right = 1.5e6, 4.0e6, 2.5e6
    speed = 2000.0
    thickness = 0.317
    frequencies = [200.0, 350.0, 500.0, 750.0, 1000.0, 1300.0]
    noise_std = 0.005
    rng = Random(7)
    observed = []
    for frequency in frequencies:
        reflection, _ = pressure_coefficients(
            z_left, z_layer, z_right, speed, thickness, frequency
        )
        noise = complex(rng.gauss(0.0, noise_std), rng.gauss(0.0, noise_std))
        observed.append(reflection + noise)

    results = scan_thickness(z_left, z_layer, z_right, speed, frequencies,
                             observed, lower=0.05, upper=0.65, points=601)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "observations.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frequency_hz", "reflection_real", "reflection_imag"])
        writer.writerows((f, r.real, r.imag) for f, r in zip(frequencies, observed))
    with (output / "thickness.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["thickness_m", "mean_squared_error"])
        writer.writerows(results)
    return min(results, key=lambda row: row[1])


if __name__ == "__main__":
    main()
