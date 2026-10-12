# echo

Small experiments with reflected acoustic waves.

Pressure and energy reflection/transmission through lossless fluid layers
at normal incidence. Waves arrive from the left.

Impedance is `Z = density * sound_speed`. Use kg/m³, m/s, metres and Hz.
Layer amplitudes use `exp(-i*omega*t)`, with reflection measured at the front
face and transmission at the back face, relative to the incident pressure
at the front face.

For `layers.py`, pass a stack of `(impedance, speed, thickness)` tuples,
ordered from left to right. An empty stack gives a single interface.

Python 3. No dependencies.

```sh
python3 -m unittest
```

Recover one layer's thickness from synthetic complex reflection measurements:

```sh
python3 recover.py
```

The example uses a 0.317 m layer, six frequencies from 200 to 1,300 Hz, and
independent Gaussian noise with standard deviation 0.005 on each real and
imaginary component (seed 7). Material properties stay fixed. It searches
0.05–0.65 m in 1 mm steps and writes `observations.csv` and `thickness.csv`.
The best grid point has the lowest mean squared complex residual; it need not
be the only thickness consistent with the data.
