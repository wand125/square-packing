# 37 unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing 37 non-overlapping unit squares
has side v = 9 + 2/√3 ≈ 10.15470; that is, s△(37) = 9 + 2/√3.

- **Upper bound.** 37 squares fit in the triangle of side v: [`upper/`](upper/) gives a packing with exact
  coordinates in Q(√3), checked by two independent exact checkers. A tight bottom row of nine axis-parallel
  squares leaves an equilateral triangle of side 9 above height 1. It holds 28 squares in the shape of
  Friedman's n = 28 packing (side 3 + 10/√3 < 9): rows of 7, 6, 3 and 2 squares and two blocks of 3 + 2 squares,
  one aligned with each slanted side. We do not claim this construction as new: Friedman's table lists a
  packing of 37 squares by Gianluca Costantino (May 2026), and the upper part uses the shape of Friedman's
  n = 28 packing (1997).
- **Lower bound.** No 37 non-overlapping unit squares fit in a smaller equilateral triangle. The rest of this
  document proves this.

Axis-parallel rows alone do not reach 37: in the triangle of side v they hold 9 + 7 + 6 + 5 + 4 + 3 + 2 = 36
squares, and the eighth row does not fit, because at height 7 the width is 9 − 14/√3 ≈ 0.917 < 1.

## Certificate

`n37_cert.json` has 36 points of weight 1, so the total is 36 < 37:
- the points of the unit triangular lattice that form an equilateral triangle of side 7, with the
  same centroid as the container;
- the bottom row lies at height 1/3 + √3/3, with x-coordinates 1 + 1/√3 + i, i = 0..7.
  For m = 9, these are exactly the vertical edges shared by neighbouring squares of a bottom row of
  9 squares.

All 84 pairs of points at distance 1 are listed for Lemma P (see
`../../checker/README.md`, item 6a). The certificate is produced by `make_lattice_cert.py 9`
(see the series note).

**Lemma.** Every closed unit square Q ⊆ T_v contains at least one of the points.

*Proof.* The checker `../../checker/check.py` verified this. It used exact Q(√3) arithmetic and
symmetry D3, and needed 7668 nodes with maximum depth 25 (limit 40),
0 uncertified, in 171 s with 16 worker processes. The record is in `check_record.json`; it contains
the certificate sha256, the exact total weight and `total_weight_lt_n`.

## From the lemma to the theorem

The argument is the same centre-scaling argument as in `../n2/PROOF.md`. Squares with disjoint
interiors in T_L with L < v become pairwise disjoint closed unit squares in T_v. Together they would
capture weight ≥ 37 > 36, a contradiction. ∎

## Remarks on n = 37

- **Depth.** A first run with depth limit 22 stopped with 35 uncertified boxes. It was inconclusive,
  not a counterexample. The boxes lie along the left side of the triangle, at angles θ ≈ 10.7°–16°.
  There the square has a corner pointing at the side.
- **Worst pose.** A local float search around those boxes finds the tightest pose near centre
  (1.6496, 1.4430), θ = 14.44°. The points (1.5774, 0.9107) and (2.0774, 1.7767) are both captured
  there, with margin 0.0025. The same margin appears for n = 4. With depth limit 40 the checker
  verifies the lemma.
- **Friedman's table.** At the time of writing (2026-10-01), Erich Friedman's "Squares in Triangles"
  page lists n = 37 with side 10.15299 (Gianluca Costantino, May 2026). This is smaller than the lower bound
  above, so we take the listed value to be a typo.
  - The picture on that page appears to show a bottom row of nine axis-parallel squares standing on
    the base. Nine such squares need width 9 at height 1, that is, side at least 9 + 2/√3 ≈ 10.15470.
  - We do not have the coordinates of that packing. Our own packing in [`upper/`](upper/) has side exactly
    9 + 2/√3.

## Status

- Lower bound verified by `../../checker/`. See the repository README for the second, independent checker.
- Upper bound: the packing in `upper/` is checked by `upper/check_sat.py` and `upper/check_clip.py`, two independent exact checkers. Both reject five negative controls.
- The lower bound is also proved in Lean 4 and checked by the kernel: [`lean/triangle/`](../../../../lean/triangle/) at the repository root.
- Not peer reviewed.
