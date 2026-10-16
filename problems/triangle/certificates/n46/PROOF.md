# 46 unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing 46 non-overlapping unit squares
has side v = 10 + 2/√3 ≈ 11.15470; that is, s△(46) = 10 + 2/√3.

- **Upper bound.** 46 squares fit in the triangle of side v: [`upper/`](upper/) gives a packing with exact
  coordinates in Q(√3), checked by two independent exact checkers. It is Joshua Wolk's n = 46 packing from
  Friedman's table (September 2026), which lists the side 11.15470: a tight bottom row of ten axis-parallel
  squares, nine more axis-parallel squares above it, and two groups of tilted squares, 15 aligned with the left
  side and 12 aligned with the right side. We do not claim the packing as new; we give it with exact
  coordinates and an exact check.
- **Lower bound.** No 46 non-overlapping unit squares fit in a smaller equilateral triangle. The rest of this
  document proves this.

Axis-parallel rows alone do not reach 46: in the triangle of side v they hold
10 + 8 + 7 + 6 + 5 + 4 + 3 + 1 = 44 squares, and the ninth row does not fit, because at height 8 the width is
10 − 16/√3 ≈ 0.762 < 1.

## Certificate

`n46_cert.json` has 45 points of weight 1, so the total is 45 < 46:
- the points of the unit triangular lattice that form an equilateral triangle of side 8, with the
  same centroid as the container;
- the bottom row lies at height 1/3 + √3/3, with x-coordinates 1 + 1/√3 + i, i = 0..8.
  These are exactly the vertical edges shared by neighbouring squares of a bottom row of 10 squares.

All 108 pairs of points at distance 1 are listed for Lemma P (see
`../../checker/README.md`, item 6a). The certificate is produced by `make_lattice_cert.py 10`
(see the series note); its sha256 is `9ded09fb2f50147b851429213469b75f2bf246ed3b87d4c7b7e1483c61cff6bb`.

**Lemma.** Every closed unit square Q ⊆ T_v contains at least one of the points.

*Proof.* The checker `../../checker/check.py` verified this. It used exact Q(√3) arithmetic and
symmetry D3, and needed 7296 nodes with maximum depth 24 (limit 40),
0 uncertified, in 338 s with 4 worker processes. The record is in `check_record.json`; it contains
the certificate sha256, the exact total weight and `total_weight_lt_n`.

## From the lemma to the theorem

The argument is the same centre-scaling argument as in `../n2/PROOF.md`. Squares with disjoint
interiors in T_L with L < v become pairwise disjoint closed unit squares in T_v. Together they would
capture weight ≥ 46 > 45, a contradiction. ∎

## Status

- Lower bound verified by `../../checker/` (record `check_record.json`) and by the second, independent checker
  `../../checker2/sweep.py`, which checks every angle without symmetry and without Lemma P (16,309 critical
  angles, minimum captured weight 1, about 8 hours with 8 processes; the summary is the m = 10 entry of
  `../../checker2/series_results.json`).
- Upper bound: the packing in `upper/` is checked by `upper/check_sat.py` and `upper/check_clip.py`, two
  independent exact checkers, and by the repository's common checker. All three reject five negative controls.
- There is no Lean proof for n = 46.
- Not peer reviewed.
