# Second checker: unit squares in a right isosceles triangle (n = 2, 3, 4, 6, 10)

An independent re-check of the point certificates behind:

| n | s(n) | certificate |
| --- | --- | --- |
| 2 | 2√2 | `certificates/n2/n2_cert.json` |
| 3 | 3 | `certificates/n3/n3_cert.json` |
| 4 | 5/√2 | `certificates/n4/n4_cert.json` |
| 6 | 4 | `certificates/n6/n6_cert.json` |
| 10 | 5 | `certificates/n10/n10_cert.json` |

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
