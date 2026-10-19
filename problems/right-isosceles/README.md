# Unit squares in a right isosceles triangle: optimal packings for n = 2, 3, 4, 6, 10, 15, 21

Let s(n) be the leg length of the smallest right isosceles triangle that contains n non-overlapping
unit squares (any positions, any angles).

| n | s(n) | ≈ | optimal packing (upper bound) | lower-bound certificate |
|---|---|---|---|---|
| 2 | 2√2 | 2.8284 | two squares side by side on the hypotenuse | one point, weight 1 (total 1) |
| 3 | 3 | 3 | axis-parallel staircase, rows 2 + 1 | 4 points of weight 1/2 (total 2) |
| 4 | 5/√2 | 3.5355 | three squares on the hypotenuse, one on top | 3 points of weight 1 (total 3) and Lemma P |
| 6 | 4 | 4 | axis-parallel staircase, rows 3 + 2 + 1 | 7 points (total 5) and Lemma P |
| 10 | 5 | 5 | axis-parallel staircase, rows 4 + 3 + 2 + 1 | 15 points (total 19/2) and Lemma P |
| 15 | 6 | 6 | axis-parallel staircase, rows 5 + 4 + 3 + 2 + 1 | 505 points (total 1499/100) and Lemma P |
| 21 | 7 | 7 | axis-parallel staircase, rows 6 + 5 + 4 + 3 + 2 + 1 | 503 points (total 2099/100), Lemma P, cone leaves and the two-point lemma |

Upper bounds: our packing certificates `certificates/nX/packing.json` (exact coordinates), checked
exactly by the two checkers in [`tools/packing_check/`](../../tools/packing_check/). The packings are
the ones listed in Erich Friedman's Packing Center, "Squares in Right Isosceles Triangles"
(https://erich-friedman.github.io/packing/squintan/), where n = 2, 3, 6, 10, 15 and 21 are listed as "Trivial"
and the packing for n = 4 was found by Erich Friedman in March 2005; we claim no originality for them.
The lower-bound certificates show that these packings are optimal. The results are computer-assisted and checked by two independent checkers.
They have not been peer reviewed.

## Novelty

- Friedman's table (as of 2026-10-09) gives the packings but no proofs or lower bounds. "Trivial" there
  means that the packing is obvious, not that its optimality is proved.
- We are not aware of a previous proof of optimality for any n ≥ 2 in this container. We checked
  Friedman's page and general web searches (which find translative and parallel packings of squares in
  right isosceles triangles, and circle packings, but no lower bounds for unit squares at arbitrary
  angles). If you know of one, please open an issue.

## The method

Each lower bound is a finite weighted point set in the triangle T_v = conv{(0,0), (v,0), (0,v)}, where
v is the claimed value. The checkers prove two things:

1. **Capture.** Every closed unit square Q ⊆ T_v, at any position and any angle, contains points of
   total weight ≥ 1. A point on the boundary of Q counts. This is checked at the container itself, with
   margin zero.
2. **Budget.** The total weight is < n.

Then n squares do not fit in a triangle with legs L < v.

- Suppose they did, with disjoint interiors, in T_L = G + λ(T_v − G) with λ = L/v and G any point of T_v.
  Translate each square by (1/λ − 1)(c_i − G), where c_i is its centre.
- The translated squares lie in T_v: for a point k of the centred square,
  (c_i − G)/λ + k = λ·((c_i + k − G)/λ) + (1 − λ)·((c_i − G)/λ), and both brackets lie in T_v − G
  because c_i + k and c_i lie in T_L. T_v is convex.
- They are pairwise disjoint closed squares: a separating direction w with w·(c_j − c_i) ≥ h_i + h_j > 0
  (h the support values) gets w·(c_j − c_i) multiplied by 1/λ > 1.
- Each of them captures weight ≥ 1, so the total would be ≥ n. This contradicts the budget.

With the packing of leg v, this gives s(n) = v. Details are in `certificates/n*/PROOF.md`.

**Lemma P (used for n = 4, 6, 10, 15, 21).** For two points p, q at distance exactly 1, a square whose chord
along the line pq crosses two opposite edges and meets the segment [p, q] contains p or q. It handles
poses where the captured point switches from p to q across a surface that is not parallel to the axes,
for example a square standing on the middle of the hypotenuse for n = 4. The pair counts min(w_p, w_q),
and no point is counted twice. Lemma P is used only by the first checker; the second checker counts the
points exactly in every cell and does not need it.

**Cone leaves and the two-point lemma (used for n = 21).** At θ = 0 the staircase for n = 21 has squares where two
switches between captured points meet: a corner on the hypotenuse with both other edges on grid lines, and a square
flush with a leg where the switch is of second order in θ. Checker 1 cuts the boxes at the first kind into cone
pieces, and closes the second kind with a two-point lemma whose multiplier depends on u. Both are described in
`checker/SPEC.md` and `certificates/n21/PROOF.md`. Checker 2 does not need them.

## Two independent checkers

- **`checker/`** subdivides pose space (centre box × angle bin, with u = tan(θ/2)).
  - It is the checker of `../triangle/checker/` with the container, the number field (Q(√2) instead of
    Q(√3)) and the symmetry (the reflection (x, y) ↦ (y, x)) changed. The changes are listed in
    `checker/SPEC.md`; the soundness argument is in `../triangle/checker/README.md`.
  - Standard library only.
- **`checker2/`** is a second checker written from the specifications, the proof notes and the
  certificate format, with a different method (an exact sweep over all angles, without Bernstein bounds,
  the symmetry or Lemma P; for n = 2 to 10 over the whole arrangement, for n = 15 and 21 inside small pose
  boxes by `local_sweep.py`). Its README describes the method and what its author read.
  It verifies the same seven certificates and rejects the negative controls in `checker2/controls/`.

## Reproducing

Requirements: Python 3.10+. Checker 1 uses only the standard library. Checker 2 needs gmpy2 and sympy,
and the test suite needs pytest: `pip install gmpy2 sympy pytest`, or on Debian/Ubuntu
`sudo apt install python3-gmpy2 python3-sympy python3-pytest`.

```bash
# checker 1 (Python 3.10+, standard library)
python3 checker/check.py certificates/n2/n2_cert.json --n 2
python3 checker/check.py certificates/n3/n3_cert.json --n 3
python3 checker/check.py certificates/n4/n4_cert.json --n 4 --max-depth 22 --jobs 8
python3 checker/check.py certificates/n6/n6_cert.json --n 6 --max-depth 22 --jobs 8
python3 checker/check.py certificates/n10/n10_cert.json --n 10 --max-depth 22 --bbox 6 --jobs 8
python3 checker/check.py certificates/n15/n15_cert.json --n 15 --bbox 8 --slices --max-depth 70 --root 32 --jobs 8 \
    --checkpoint n15.ckpt.jsonl                     # hours; resumable
python3 checker/check.py certificates/n21/n21_cert.json --n 21 --bbox 8 --slices --max-depth 70 --root 32 --cone 1/16 \
    --jobs 8 --checkpoint n21.ckpt.jsonl            # about 25 core-hours; resumable
cd checker && python3 -m pytest -q tests          # needs pytest; a few seconds

# checker 2 (needs gmpy2 and sympy)
python3 checker2/sweep_q2.py certificates/n10/n10_cert.json --n 10 --jobs 8
python3 checker2/local_sweep.py certificates/n15/n15_cert.json --n 15 --jobs 8 --K 24 --uslices 20 --grid 16 \
    --log n15.log.jsonl --resume --out n15.json      # hours; resumable; see checker2/README.md
python3 checker2/local_sweep.py certificates/n21/n21_cert.json --n 21 --jobs 8 --K 24 --uslices 20 --grid 16 \
    --log n21.log.jsonl --resume --out n21.json      # hours; resumable; see checker2/README.md

# the packings (upper bounds); the second checker needs sympy
python3 ../../tools/packing_check/check_packing.py  certificates/n4/packing.json
python3 ../../tools/packing_check/check_packing2.py certificates/n4/packing.json
```

Each run prints a JSON summary with `"status": "verified"`. The summary also contains the certificate's
sha256, the exact total weight and whether it is < n. The recorded runs are
`certificates/n*/check_record.json` (checker 1) and `checker2/runs/n*.json` (checker 2; for n = 15 and 21 the
summary reports the minimum capture over the swept cells, 3512157/3504100 and 1765259/1761660). On one machine
checker 1 takes under 10 s for each certificate up to n = 10, about 11 core-hours for n = 15 and about 25
core-hours for n = 21. Checker 2 takes between 2 s (n = 2) and about 4.5 minutes (n = 10), about 2.7 hours for
n = 15 and about 2.9 hours for n = 21 (three processes each).

`--bbox 6` for n = 10 only changes the root grid (it covers [0, 6]² instead of [0, 5 + 1/64]²), so that
the line x = 3/2 is a face of the boxes; see `certificates/n10/PROOF.md`. For n = 15, `--bbox 8 --root 32` puts the
integer and half-integer lines on box faces, and `--slices` turns on the end-of-range leaves; see
`certificates/n15/PROOF.md`. n = 21 uses the same grid, and `--cone 1/16` turns on the cone leaves
(`certificates/n21/PROOF.md`). `--checkpoint` only saves finished root boxes so that a stopped run can continue.

`tools/` has the exact random probe used as a sanity check, the float LPs that found the certificates
(`lp_repair.py` adds the box rows at the degenerate poses for n = 15; `tools/n21/` has its later version and the
screens and additive repairs used for n = 21) and the script that adds the unit-distance pairs. They are not part of the proofs.

## Not done

- n = 5, 14, 20, … : s(5) ≤ s(6) = 4, s(14) ≤ s(15) = 6, and so on. A point certificate cannot prove these
  (a packing of n squares then has room to move).
- n = 7, 8, 11, 13: in the best known packings a row of tilted squares along the hypotenuse has room to
  slide, which a single point certificate cannot handle.
- n = 28 and the larger triangular numbers (staircase with legs k + 1): work in progress.
- n = 9, 12 (7/√2, 4√2): the packings are rigid staircases (rows 5 + 3 + 1 and 6 + 4 + 2 on the hypotenuse), but a single point certificate is not enough; work in progress.

## Licence

MIT (see `LICENSE`). The packings shown in the table are from Erich Friedman's Packing Center.
