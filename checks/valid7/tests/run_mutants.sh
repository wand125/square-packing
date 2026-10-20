#!/bin/sh
# Each mutant must be refused.  Run from the repository root.
set -e
PY=${PY:-.venv/bin/python}
$PY tests/make_mutants.py ${COVER:-cover/L4_k02_box7.txt}
echo "--- M1 (wall), Tier B on [2.9,3.1]x[0.5,0.6], u in (0,1/64) and (-1/64,0): expect ok False"
$PY src/tier_b2.py tests/M1_wall_1e-4.txt 29/10 31/10 1/2 3/5 0 1/64
$PY src/tier_b2.py tests/M1_wall_1e-4.txt 29/10 31/10 1/2 3/5 -1/64 0
echo "--- M2 (Lebesgue), driver on centres [3.5,3.6]^2, u in [0,1/8]: expect COUNTEREXAMPLE"
$PY src/run_all.py tests/M2_leb_1e-4.txt --centers 7/2 18/5 7/2 18/5 --u 0 1/8 --ubins 2 --record /dev/null | tail -2
echo "--- M3 (corner), Tier B on [1.45,1.55]^2, u in (0,1/32): expect ok False"
$PY src/tier_b2.py tests/M3_corner_1e-4.txt 29/20 31/20 29/20 31/20 0 1/32
echo "--- P1 (positive control for Lemma B5, two rectangles + two segments), Tier B on [1.99,2.04]^2, u in (1/64-1/8192, 1/64): expect ok False, why face, mass 0.998"
$PY src/tier_b2.py tests/P1_faces.txt 199/100 204/100 199/100 204/100 127/8192 1/64
