# Ten unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing ten
non-overlapping unit squares has legs of length 5.

Upper bound: the axis-parallel staircase with rows 4, 3, 2, 1 in T_5.

## Certificate

`n10_cert.json`: fifteen points, total weight 19/2 < 10, invariant under (x, y) ↦ (y, x):

| point | weight |
|---|---|
| (3/4, 1), (1, 3/4) | 1/2 each |
| (3/4, 2), (2, 3/4), (3/4, 3), (3, 3/4) | 1 each |
| (1, 3/2), (3/2, 1), (5/4, 5/2), (5/2, 5/4) | 1/2 each |
| (3/2, 3/2), (3/2, 5/2), (5/2, 3/2), (7/4, 2), (2, 7/4) | 1/2 each |

Eight chord pairs (all pairs at distance exactly 1). The root grid is taken over [0, 6]²
(`--bbox 6`), so that the lines x = 3/2 and y = 3/2 are box faces: at centre (3/2, 3/2), θ = 0 the
square [1,2]² has the four points (1,3/2), (3/2,1), (2,7/4), (7/4,2) on its boundary, and the
captured one changes across these lines. With the default bounding box 5 + 1/64 two boxes there stay
uncertified at depth 22.

**Lemma.** Every closed unit square Q ⊆ T_5 contains points of total weight ≥ 1.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n10/n10_cert.json --n 10 --max-depth 22 --bbox 6`): symmetry D1, 2,868 nodes, 0 uncertified, maximum depth 15, 6.8 s (`check_record.json`).
- checker 2 (`../../checker2/sweep_q2.py`, all angles, no symmetry, no Lemma P): verified, minimum capture 1, 262 s (`../../checker2/runs/n10.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 19/2 < 10.

## Sanity checks (not part of the proof)

- Negative control: L = 5 + 1/100 gives 43 uncertified boxes at depth 22.
- Exact random probe: 20,000 rational poses, minimum capture 1.
