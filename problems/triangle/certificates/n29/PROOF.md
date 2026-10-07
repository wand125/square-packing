# 29 unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing 29 non-overlapping
unit squares has side v = 8 + 2/√3 ≈ 9.1547.

Upper bound (Friedman, 1997): axis-parallel rows standing on the base. At height j the triangle has
width v − 2j/√3, so the rows from the bottom hold 8 + 6 + 5 + 4 + 3 + 2 + 1 = 29 squares.
Only the bottom row is tight: at height 1 the width is exactly 8.

## Certificate

`n29_cert.json` has 28 points of weight 1, so the total is 28 < 29:
- the points of the unit triangular lattice that form an equilateral triangle of side 6, with the
  same centroid as the container;
- the bottom row lies at height 1/3 + √3/3, with x-coordinates 1 + 1/√3 + i, i = 0..6.
  For m = 8, these are exactly the vertical edges shared by neighbouring squares of a bottom row of
  8 squares.

All 63 pairs of points at distance 1 are listed for Lemma P (see
`../../checker/README.md`, item 6a). The certificate is produced by `make_lattice_cert.py 8`
(see the series note).

**Lemma.** Every closed unit square Q ⊆ T_v contains at least one of the points.

*Proof.* The checker `../../checker/check.py` verified this. It used exact Q(√3) arithmetic and
symmetry D3, and needed 5770 nodes with maximum depth 25 (limit 36),
0 uncertified, in 91 s with 12 worker processes. The record is in `check_record.json`; it contains
the certificate sha256, the exact total weight and `total_weight_lt_n`.

## From the lemma to the theorem

The argument is the same centre-scaling argument as in `../n2/PROOF.md`. Squares with disjoint
interiors in T_L with L < v become pairwise disjoint closed unit squares in T_v. Together they would
capture weight ≥ 29 > 28, a contradiction. ∎

## Status

- Verified by `../../checker/`. See the repository README for the second, independent checker.
- Not peer reviewed.
