# Exact unavoidability checker for unit squares in a right isosceles triangle

## What is proved

Input: a leg length `L`, points `p_i` with rational weights `w_i >= 0`, optional chord pairs, and a
symmetry flag. When the output says `"status": "verified"`, the following holds:

    every closed unit square Q with Q ⊆ T_L (any centre, any angle) satisfies  Σ_{p_i ∈ Q} w_i ≥ 1,

where T_L = conv{(0,0), (L,0), (0,L)}. Points on ∂Q count. With chord pairs, a pair counts
min(w_p, w_q) on a box where Lemma P is proved, and no point is counted twice. Contacts with margin zero
are supported when they happen at a vertex of the admissible-centre polygon or at the endpoint of a
u-bin.

## How to run

```bash
python3 check.py ../certificates/n4/n4_cert.json --n 4 --max-depth 22 --jobs 8
python3 check.py cert.json --root 4 --max-depth 40 --jobs 8 --bbox 6 --u-breaks "1/3"
python3 -m pytest -q tests                                     # needs pytest
```

The certificate format is `{"L": "5/2*sqrt2", "symmetry": "D1"|"none", "points": [{"x", "y", "w"}],
"pairs": [[i, j], ...]}`. L and the coordinates are `a` or `a+b*sqrt2` with rational `a, b`. The weights
are rationals. The JSON summary contains the sha256 of the certificate, the exact total weight, the leaf
counts, the uncertified boxes, the depth and the time. Only the standard library is used; Python 3.10+.

Files: `q2.py` (the field Q(√2)), `poly.py` (polynomials and Bernstein tests), `check.py` (CLI and
subdivision), `tests/`.

## Relation to the equilateral checker

This checker is `../../triangle/checker/` with three changes (`SPEC.md`):

1. **Field.** Q(√2) instead of Q(√3). The sign of a + b√2 with a, b of opposite signs is the sign of
   a² − 2b², never 0.
2. **Container.** The three sides are y ≥ 0, x ≥ 0 and x + y ≤ L. The normals (0, −1), (−1, 0) and (1, 1)
   are not unit vectors; admissibility n·c ≤ b − n·R_θσ is unchanged by scaling a normal, and for fixed θ
   each constraint is a half-plane with a constant normal, as before.
3. **Symmetry.** `D1`: the checker verifies exactly that the weighted points (and features and segments,
   if any) are invariant under (x, y) ↦ (y, x), the only nontrivial symmetry of T_L. It maps a square of
   angle θ to one of angle π/2 − θ ≡ −θ (mod π/2), so u ∈ [0, √2 − 1] (θ ∈ [0, π/4]) suffices; the end
   √2 − 1 = tan(π/8) is exact in Q(√2). With `none`, u ∈ [0, 1] with root breakpoints 0, √2 − 1, 1.

The root grid covers [0, B]² with B a rational upper bound of L, or a given rational B ≥ L (`--bbox`,
checked exactly). Everything else (the box subdivision, the vertex argument, Bernstein bounds, Lemma P)
is unchanged; the soundness argument is in `../../triangle/checker/README.md`.
