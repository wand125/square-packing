# Second checker: unit squares in a right isosceles triangle (n = 2, 3, 4, 6, 10, 15)

An independent re-check of the point certificates behind:

| n | s(n) | certificate |
| --- | --- | --- |
| 2 | 2√2 | `certificates/n2/n2_cert.json` |
| 3 | 3 | `certificates/n3/n3_cert.json` |
| 4 | 5/√2 | `certificates/n4/n4_cert.json` |
| 6 | 4 | `certificates/n6/n6_cert.json` |
| 10 | 5 | `certificates/n10/n10_cert.json` |
| 15 | 6 | `certificates/n15/n15_cert.json` (checked by `local_sweep.py`, see below) |

## What is checked

`sweep_q2.py` proves the following for a certificate with side L, points p_i and rational weights w_i:

> every closed unit square Q ⊆ T_L = {x ≥ 0, y ≥ 0, x + y ≤ L}, at any position and any
> angle, contains points of total weight ≥ 1 (points on ∂Q count).

The lower bound s(n) ≥ L then follows from total weight < n and centre scaling. Centre scaling is
in the certificates' PROOF.md and is not re-checked by code.

## Method

This is the exact angular sweep of `../../triangle/checker2/sweep.py` (README there), with two
changes:

- the number field Q(√3) is replaced by Q(√2) (`q2.py`);
- the container is replaced by T_L.

Every angle u = tan(θ/2) ∈ [0, 1] is checked directly. Critical angles are the real roots of the
pair and triple determinants of the line arrangement. Each open gap between them gets one rational
sample. At each sample the capture weight is counted exactly on every open sector at every vertex
inside the admissible region.

Closure is by upper semicontinuity. It needs a disc of centres inside every admissible region. The
inradius L(2 − √2)/2 must exceed √2/2, that is L > 1 + √2, and this is checked exactly.

The method differs from the first checker:

- no box subdivision;
- no Bernstein bounds;
- no use of the D1 symmetry;
- no chord-pair lemma. Points are counted exactly in each cell, so the certificate's `pairs`
  field is not used.

## Results (2026-10-09, one machine, 6–8 processes; `runs/`)

| certificate | sha256 | points | total | lines | critical roots | vertices | sectors | min weight | time | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| n = 2 | `843e1baf…` | 1 | 1 | 16 | 61 | — | — | 1 | 2 s | verified |
| n = 3 | `a6b9a9e0…` | 4 | 2 | 28 | 331 | 100,320 | 10,206 | 1 | 7 s | verified |
| n = 4 | `ed75943f…` | 3 | 3 | 24 | 241 | 54,720 | 13,704 | 1 | 6 s | verified |
| n = 6 | `5f054136…` | 7 | 5 | 40 | 671 | 388,600 | 226,970 | 1 | 26 s | verified |
| n = 10 | `9460efbd…` | 15 | 19/2 | 72 | 1,863 | 3,105,816 | 3,714,890 | 1 | 262 s | verified |

Each total weight is below n: 1 < 2, 2 < 3, 3 < 4, 5 < 6 and 19/2 < 10.

## Negative controls (`controls/`)

Every failure comes with an explicit pose at a rational angle, whose capture is counted exactly.

| control | n = 2 | n = 3 | n = 4 | n = 6 | n = 10 |
| --- | --- | --- | --- | --- | --- |
| L + 1/100 | failed (0) | failed (1/2) | failed (0) | failed (0) | failed (0) |
| first weight × 99/100 | failed (99/100) | failed (199/200) | failed (99/100) | failed (199/200) | failed (199/200) |
| last point dropped | — | failed (1/2) | failed (0) | failed (0) | failed (1/2) |
| first point moved 1/50 in x | failed (0) | verified, see below | failed (0) | verified, see below | — |
| first point moved 1/5 in x | — | failed (1/2) | — | verified, see below | failed (1/2) |
| centre point (3/2, 3/2) moved to x = 8/5 | — | — | — | failed (1/2) | — |

Some point moves leave the certificate valid:

- n = 3, moved by 1/50;
- n = 6, first point (1/2, 3/2) of weight 1/2, moved by 1/50 or by 1/5.

These points have slack. A float Monte Carlo probe (`mc_rit.py`, 4 million random poses each) also
finds minimum capture 1 for these inputs, and finds 1/2 where the checker fails.

## Independence

- Written from the equilateral-triangle specification (`../../triangle/checker/SPEC.md`), the
  certificates and their PROOF.md files only. The first checker's code
  (`../checker/check.py`, `q2.py`, `poly.py`) was not opened.
- `q2.py` here is derived from this author's own `../../triangle/checker2/q3.py`.
- Tools: Python, gmpy2 (exact rationals), sympy (real-root isolation of rational polynomials).

## Run

```sh
# from problems/right-isosceles; needs gmpy2 and sympy
python3 checker2/sweep_q2.py certificates/n3/n3_cert.json --n 3 --jobs 6 --out out.json
python3 checker2/sweep_q2.py checker2/controls/n3_Lplus.json --n 3 --jobs 4 --stop-early   # each control must fail
```

The recorded runs are in `runs/`.

## n = 15 (`local_sweep.py`)

The n = 15 certificate has 505 points. The whole-arrangement sweep of `sweep_q2.py` would have about
2,000 lines and 1.4 × 10⁹ triples, which is out of reach. `local_sweep.py` checks the same claim
by branch and bound over boxes in the pose space, with the same exact sweep inside each small box.

### Method

- Poses are (u, x, y): u = tan(θ/2) ∈ [0, 1], c = (x, y) the centre. The root boxes are 20 slices in
  u times a 16 × 16 grid over [0, 6]², 5,120 in all.
- On a box [u0, u1] × [x0, x1] × [y0, y1], cos θ and sin θ are monotone in u, so they have exact
  rational bounds. With exact interval arithmetic each box closes in one of three ways, or is split:
  - INADMISSIBLE: some vertex of Q is outside a side of T_L at every pose of the box.
  - SURE: the points inside Q at every pose of the box weigh ≥ 1.
  - SWEEP: at most K = 24 points change membership in the box (or the depth reaches 40). Then the box is
    swept exactly, using only the lines that matter: the box sides, the admissibility lines that are
    not always true, and the sides of Q crossed by those points.
- The exact sweep is the method of `sweep_q2.py`, restricted to the box:
  - critical u are roots of 3 × 3 determinants, isolated exactly with sympy;
  - one rational u is taken in each open gap;
  - at that u, the capture is counted exactly on every open sector at every vertex of the region.
  - A triple of lines is skipped when one of its pairs provably never meets inside the closed box
    (interval bound), or when Descartes' rule (after a Möbius map onto (u0, u1)) shows that its
    determinant has no root there.
- Closure is by upper semicontinuity, as for `sweep_q2.py`. Box boundaries have measure zero.
- As in `sweep_q2.py`, the certificate's `pairs` field and its D1 symmetry are not used.

Compared with the first checker, this checker:

- does not use Bernstein bounds;
- does not use the chord-pair lemma;
- counts points exactly in each cell.

The two checkers share only the certificate format.

### Result (2026-10-14, one machine, 3 processes; `runs/n15.json`)

| certificate | sha256 | points | total | root boxes | swept boxes | critical roots | min weight | time | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| n = 15 | `ddf736df…` | 505 | 1499/100 | 5,120 | 14,662 | 1,689,246 | 3512157/3504100 | 2.7 h | verified |

The total weight 1499/100 is below 15. The other counts are:

- 25,804 SURE boxes;
- 6,383 INADMISSIBLE boxes;
- at most 47 lines in one box;
- maximum depth 40.

The minimum is attained at u = 7/202, near the centre (1.4732, 3.5293).

### Negative controls

| control | root boxes run | result |
| --- | --- | --- |
| `controls/n15_Lplus.json`: L = 601/100 | 11, 12, 26, 27, 28 | failed (529147/1752050 ≈ 0.302) |
| `controls/n15_weight_all.json`: every weight × 99/100 | 56, 57, 58 | failed (347703543/350410000 ≈ 0.9923) |

Each failure is a pose at a rational angle whose capture is counted exactly:

- the L + 1/100 control fails at a square on the leg x = 0, around y ≈ 4.5;
- the weight control fails at the same pose as the minimum of the real run.

The root boxes are numbered as `local_sweep.py` lists them: slice k, column i, row j has index
256 k + 16 i + j.

### Run

```sh
# from problems/right-isosceles; needs gmpy2 and sympy
python3 checker2/local_sweep.py certificates/n15/n15_cert.json --n 15 --jobs 3 --K 24 \
    --uslices 20 --grid 16 --log n15.log.jsonl --resume --out n15.json
python3 checker2/local_sweep.py checker2/controls/n15_Lplus.json --n 15 --jobs 2 --K 24 \
    --uslices 20 --grid 16 --only 27,26,28,11,12 --stop-early        # must fail
python3 checker2/local_sweep.py checker2/controls/n15_weight_all.json --n 15 --jobs 2 --K 24 \
    --uslices 20 --grid 16 --only 57,56,58 --stop-early              # must fail
```

With `--log` and `--resume`, an interrupted run continues from the root boxes already logged.
