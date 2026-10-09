# Two unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing two
non-overlapping unit squares has legs of length 2√2 ≈ 2.8284.

Upper bound (Friedman, listed as trivial): with the hypotenuse (length 4) as the base, two squares
stand on it side by side; their top outer corners lie on the legs.

## Certificate

`n2_cert.json`: the single point (5√2/8, 5√2/8) with weight 1 (total 1 < 2). It lies on the axis of
symmetry, at height 3/4 above the hypotenuse.

**Lemma.** Every closed unit square Q ⊆ T_{2√2} contains (5√2/8, 5√2/8).

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n2/n2_cert.json --n 2`): symmetry D1, 16 nodes, 0 uncertified, maximum depth 0, 0.1 s (`check_record.json`).
- checker 2 (`../../checker2/sweep_q2.py`, all angles, no symmetry, no Lemma P): verified, minimum capture 1, 2 s (`../../checker2/runs/n2.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 1 < 2.

## Sanity checks (not part of the proof)

- Negative control: L = 2√2 + 1/100 gives 44 uncertified boxes at depth 22.
