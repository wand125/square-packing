# Fifteen unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing fifteen
non-overlapping unit squares has legs of length 6.

Upper bound: our packing certificate `packing.json`, checked exactly by `check_packing.py` and,
independently, by `check_packing2.py` in [`tools/packing_check/`](../../../../tools/packing_check/).
The packing is the one listed in Erich Friedman's Packing Center ("Squares in Right Isosceles
Triangles"); we claim no originality for it. It is the axis-parallel staircase with rows 5, 4, 3, 2, 1
in T_6.

## Certificate

`n15_cert.json` (sha256 `ddf736df0e6b80b0d4d3c8a844f6d95567578d11f87c29a70ccc6f7c13fc6b8d`): 505 points with rational
coordinates, total weight 1499/100 < 15, invariant under (x, y) ↦ (y, x), and 152 chord pairs (all pairs of points at
distance exactly 1).

**Lemma.** Every closed unit square Q ⊆ T_6 contains points of total weight ≥ 1.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n15/n15_cert.json --n 15 --bbox 8 --slices --max-depth 70 --root 32`):
  symmetry D1, 1,024 root boxes, 176,166 nodes, 87,416 cover leaves, 1,133 empty leaves, 45 slice leaves, 1 open-end
  leaf, 0 uncertified, maximum depth 26, about 5.6 hours on two cores (`check_record.json`; one line per root box in
  `check_record_roots.jsonl`, which the run wrote under the name given in the record's `checkpoint` field).
- checker 2 (`../../checker2/`, all angles, no symmetry, no Lemma P): verified, minimum capture 3512157/3504100,
  about 2.7 hours (`../../checker2/runs/n15.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 1499/100 < 15.

## Why this certificate needs more than the smaller ones

The optimal staircase is degenerate for a point certificate: at θ = 0 the squares of the packing have certificate
points exactly on their edges, so near those poses the captured points change with the direction of the move.
- Slabs (centre on x = k + 1/2 or y = j + 1/2, θ = 0): one of the two points (k, s), (k + 1, s) is inside, by Lemma P.
- Lattice crossings (centre (k + 1/2, j + 1/2), θ = 0, both directions at once): the weights were found by a float LP
  with one row per quarter box around each crossing and per slab height, counting only what checker 1 can prove on
  the whole box: interior points, edge points that stay inside, and chord pairs at min(w_p, w_q)
  (`tools/lp_repair.py`). Then the points off the integer lines were moved by at most 1/200, the weights scaled to
  total 14.99, and all unit-distance pairs added (`tools/add_pairs.py`).
- The square [0, 1] × [4, 5] at θ = 0 touches the wall and the hypotenuse. There three constraint lines meet at the end
  of the angle range, and checker 1 uses its open-end leaves (`checker/SPEC.md`, "Wedged squares at an end of the
  u-range").
- Checker 2 counts the points exactly at every pose and needs none of this.

## Sanity checks (not part of the proof)

- Negative control: with L = 601/100 the closed square [0, 1] × [4005/1000, 5005/1000] lies in the triangle and
  captures exactly 529147/1752050 ≈ 0.302 < 1.
- Exact random probe: 20,000 admissible poses with rational centres and rational tan(θ/2), minimum capture
  3772983/3504100 ≈ 1.077.
- Float screens: a grid at θ = 0 with ±2·10⁻⁶ shifts (minimum 1.044) and a float branch-and-bound over all poses
  (no pose below 1).
