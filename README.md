# echo

Small experiments with reflected acoustic waves.

Pressure and energy reflection/transmission at one interface or through one
finite layer of lossless fluid, at normal incidence. Waves arrive from the left.

Impedance is `Z = density * sound_speed`. Use kg/m³, m/s, metres and Hz.
Layer amplitudes use `exp(-i*omega*t)`, with reflection measured at the front
face and transmission at the back face, relative to the incident pressure
at the front face.

Python 3. No dependencies.

```sh
python3 -m unittest
```
