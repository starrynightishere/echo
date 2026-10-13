import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main(directory=Path(__file__).resolve().parents[1] / "results" / "benchmark"):
    directory = Path(directory)
    example = json.loads((directory / "example.json").read_text())
    setup = json.loads((directory / "setup.json").read_text())
    with (directory / "summary.csv").open(newline="") as file:
        summary = list(csv.DictReader(file))
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), layout="constrained")
    fig.suptitle("One more measurement", fontsize=16)
    initial = example["initial"]
    remaining = example["disagreement"]["remaining"]
    frequency = example["disagreement"]["frequency_hz"]
    after = (f"After {frequency:g} Hz: {len(remaining)} candidate{'s' if len(remaining) != 1 else ''}"
             if frequency is not None else "No initial candidates")
    titles = [f"Before: {len(initial)} candidates", after]
    for ax, candidates, title in zip(axes[0], (initial, remaining), titles):
        ax.scatter([r[0] for r in initial], [r[1] for r in initial],
                   s=90, facecolors="none", edgecolors="#b9bfc3")
        ax.scatter([r[0] for r in candidates], [r[1] for r in candidates],
                   s=65, color="#287e80", label="accepted")
        ax.scatter(*example["truth"], marker="x", s=60, color="#222222", label="true pair")
        ax.set(xlim=(0.0, 1.3), ylim=(0.0, 1.7), xlabel="layer 1 thickness (m)",
               ylabel="layer 2 thickness (m)", title=title)
        ax.grid(alpha=0.15)
        ax.legend(fontsize=8)

    cases = [case["name"] for case in setup["cases"]]
    noises = setup["noise_std_per_component"]
    for ax, method, title in zip(axes[1], ("disagreement", "random"), ("Disagreement", "Random")):
        rates = {(r["case"], float(r["noise_std"])): 100 * int(r["unique_correct"]) / int(r["trials"])
                 for r in summary if r["method"] == method}
        matrix = [[rates[case, noise] for noise in noises] for case in cases]
        heatmap = ax.imshow(matrix, vmin=0, vmax=100, cmap="Blues", aspect="auto")
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                ax.text(j, i, f"{value:.1f}%", ha="center", va="center",
                        color="white" if value > 55 else "#222222")
        ax.set(xticks=range(len(noises)), xticklabels=[f"{n:g}" for n in noises],
               yticks=range(len(cases)), yticklabels=cases, xlabel="noise std per component", title=title)
    fig.colorbar(heatmap, ax=list(axes[1]), shrink=0.8, label="correct unique fits (%)")
    fig.supxlabel(f"Top: reference case, seed {example['seed']}, noise {example['noise_std']:g}. "
                  f"Bottom: {setup['trials_per_case_and_noise']} trials per cell; "
                  f"within {1000 * setup['correct_within_m_per_layer']:g} mm per layer.",
                  fontsize=9)
    fig.savefig(directory / "selection.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
