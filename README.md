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
