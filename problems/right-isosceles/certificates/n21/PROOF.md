# Twenty-one unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing twenty-one
non-overlapping unit squares has legs of length 7.

Upper bound: our packing certificate `packing.json`, checked exactly by `check_packing.py` and,
independently, by `check_packing2.py` in [`tools/packing_check/`](../../../../tools/packing_check/).
The packing is the one listed in Erich Friedman's Packing Center ("Squares in Right Isosceles
Triangles"); we claim no originality for it. It is the axis-parallel staircase with rows 6, 5, 4, 3, 2, 1
in T_7.

## Certificate

`n21_cert.json` (sha256 `020a4eb5e6d932cd6a27e81928b8599461f2ef95c7c9eb9269d25e04b0b51bf1`): 503 points with rational
coordinates, total weight 2099/100 < 21, invariant under (x, y) ↦ (y, x), and 418 chord pairs.

**Lemma.** Every closed unit square Q ⊆ T_7 contains points of total weight ≥ 1.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n21/n21_cert.json --n 21 --bbox 8 --slices --max-depth 70 --root 32
  --cone 1/16`): symmetry D1, 1,024 root boxes, 168,868 nodes, 83,229 cover leaves, 1,655 empty leaves, 53 slice
  leaves, 1 open-end leaf, 8 cone leaves (136 pieces), 0 uncertified, maximum depth 30, about 12.7 hours on two cores
  (`check_record.json`; one line per root box in `check_record_roots.jsonl`, which the run wrote under the name given
  in the record's `checkpoint` field). One run from the root boxes with the checker of this repository.
- checker 2 (`../../checker2/`, all angles, no symmetry, no Lemma P): verified, minimum capture 1765259/1761660 ≈ 1.0020,
  about 2.9 hours on three cores (`../../checker2/runs/n21.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 2099/100 < 21.

## Why this certificate needs more than n = 15

The certificate has the same structure as for n = 15 (`../n15/PROOF.md`): a float LP with rows for the degenerate
poses of the staircase, here on the 1/8 grid, alternated with a float branch-and-bound over all poses until it found
no deficit pose. Then float screens of the degenerate poses at θ = 0 and at the poses with three points on edges, and
small LPs that only add weight there, with the total scaled back to 20.99. The tools are in `../../tools/n21/`; their
paths are those of our working tree. The points were not moved off the lattice lines (that opened holes near θ = 0).
The margin is smaller (total 20.99 against 21), and checker 1 needs two more tools, both in `checker/SPEC.md`:
- **Cone leaves** (`--cone 1/16`). At θ = 0 the square may have a corner on the hypotenuse and its two other edges on
  1/8-grid lines. Near such a pose, which points are inside depends on the direction of the move (the ratio of the
  centre offset to θ). A box touching the pose contains every direction, so plain subdivision never closes it. Cone
  leaves cut it into pieces by the offset divided by g = u/(1 + u²).
- **Two-point lemma.** Take two points q1, q2. Each may have at most two edge conditions that are not proved on the
  box; all its other edge conditions hold at every vertex. Suppose that for every pair (C1, C2) of these open
  conditions there is a λ(u) ∈ [0, 1] with λ C1 + (1 − λ) C2 ≥ 0 at every vertex. Then q1 or q2 is inside at every
  pose of the box, and the pair counts min(w1, w2). Here λ(u) is a constant, αu or 1 − αu, and the condition is
  checked exactly in Bernstein form.
  The lemma is needed for the square [33/8, 41/8] × [0, 1] at θ = 0, which is flush with the leg y = 0. The point
  (41/8, 1/2) leaves through the right edge, and (33/8, 1) through the top edge. The switch between them is of second
  order in θ, so Lemma P (one constant λ, segments of length 1) does not close the boxes there.
- Checker 2 counts the points exactly at every pose and needs neither.
