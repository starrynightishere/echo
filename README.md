# echo

Small experiments with reflected acoustic waves: fit layer thicknesses, find
ambiguous solutions, and choose another frequency to measure.

## run

Python 3. The solver and tests use only the standard library.

```sh
python3 -m unittest
python3 recover.py
python3 ambiguity.py
python3 select_frequency.py
python3 benchmark.py
```

The scripts cover one-layer recovery, two-layer ambiguity, frequency selection,
and a benchmark of five configurations at three noise levels. The benchmark
runs 200 paired noise trials per case and noise level. Both methods get the
same initial measurements and extra noise sample.

[Plot](results/selection.png) · [Summary](results/summary.csv) ·
[Paired counts](results/paired.csv) · [Settings](results/setup.json)

To regenerate the plot after the benchmark:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-plot.txt
.venv/bin/python plot.py
```

Matplotlib is only needed for plotting.

## model

Lossless fluid layers, normal incidence, known material properties. Use SI
units and `(impedance, speed, thickness)` tuples ordered left to right.
Amplitudes use `exp(-i*omega*t)`: reflection at the front face, transmission
at the back face, both relative to incident pressure at the front face.

Fits use complex reflection measurements. The acceptance cutoff is mean squared
error ≤ `4 * noise_std**2`, with noise specified per real/imaginary component.
Frequency selection maximizes variance between equally weighted candidate
predictions. Correct recovery means one remaining pair within 5 mm of each
true thickness. Discarded candidates cannot return.

Selection helps in some cases and does worse in others. A coarse grid can
reject every candidate before the extra measurement. The cutoff is a fit rule,
not a confidence interval; the results depend on the grid, bounds and noise.
