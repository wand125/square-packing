# Three unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing three
non-overlapping unit squares has legs of length 3.

Upper bound (Friedman, "Squares in Right Isosceles Triangles", listed as trivial): the staircase
[0,1]², [1,2]×[0,1], [0,1]×[1,2] in T_3 = conv{(0,0), (3,0), (0,3)}. The top right corners of the
second and third squares, (2,1) and (1,2), lie on the hypotenuse x + y = 3.

## Certificate

`n3_cert.json` has four points of weight 1/2 each, so the total is 2 < 3:

    (3/4, 1), (1, 3/4), (3/4, 5/4), (5/4, 3/4).

The set is invariant under the reflection (x, y) ↦ (y, x), the symmetry of T_3.

**Lemma.** Every closed unit square Q ⊆ T_3 contains points of total weight ≥ 1, i.e. at least
two of the four points.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n3/n3_cert.json --n 3`): symmetry D1, 62 nodes, 0 uncertified, maximum depth 4, 0.2 s (`check_record.json`).
- checker 2 (`../../checker2/sweep_q2.py`, all angles, no symmetry, no Lemma P): verified, minimum capture 1, 7 s (`../../checker2/runs/n3.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): three disjoint closed
squares in T_3 would capture weight ≥ 3 > 2. ∎

## Sanity checks (not part of the proof)

- **Negative control.** The same points at L = 3 + 1/100 do not verify (64 uncertified boxes at
  depth 22); at L = 3 + 1/10, 12,191 uncertified boxes.
- **Exact random probe.** `../../tools/probe_exact.py`: 20,000 random rational admissible poses
  (rational centre, rational u), no symmetry used; minimum exact capture 1.
