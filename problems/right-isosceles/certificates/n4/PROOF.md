# Four unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing four
non-overlapping unit squares has legs of length 5/√2 ≈ 3.5355.

Upper bound (Friedman, "Squares in Right Isosceles Triangles"): the 45° staircase. With the
hypotenuse as the base (length 5, height 5/2), three squares stand on it side by side and one
square stands on the middle one.

## Certificate

`n4_cert.json`, in the leg frame T = conv{(0,0), (L,0), (0,L)}, L = 5/√2. Three points of
weight 1 each (total 3 < 4):

- (√2/2, √2/2), the centre of the top square of the staircase;
- (5√2/8, 9√2/8) and (9√2/8, 5√2/8). In the hypotenuse frame they sit at height 3/4 above the
  hypotenuse, at offsets ∓1/2 from its midpoint, i.e. on the two vertical walls between the
  bottom squares. Their distance is exactly 1.

One chord pair: the last two points (Lemma P, see `../../README.md`: a closed unit square that
crosses the unit segment between them in the required way contains one of them). Without the
pair checker 1 cannot finish: near the hypotenuse midpoint at θ ≈ 45° the square switches
between the two points along the diagonal x = y, which is not a face of the axis-parallel boxes.

**Lemma.** Every closed unit square Q ⊆ T contains points of total weight ≥ 1.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n4/n4_cert.json --n 4 --max-depth 22`): symmetry D1, 304 nodes, 0 uncertified, maximum depth 12, 1.0 s (`check_record.json`).
- checker 2 (`../../checker2/sweep_q2.py`, all angles, no symmetry, no Lemma P): verified, minimum capture 1, 6 s (`../../checker2/runs/n4.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 3 < 4.

## Sanity checks (not part of the proof)

- Negative control (same certificate): L = 5/√2 + 1/100 gives 38 uncertified boxes at depth 22;
  L = 5/√2 + 1/10 gives 7,402.
- Exact random probe (`../../tools/probe_exact.py`, 20,000 rational poses, no symmetry): minimum capture 1.
