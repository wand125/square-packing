# Exact checker for unavoidable weighted point sets in a right isosceles triangle

This is the specification of `checker/check.py`. It is the equilateral checker of
`../../triangle/checker/SPEC.md` with three changes: the container, the number field and the
symmetry. Everything not listed here (poses, capture, the box subdivision, Bernstein tests, chord
pairs / Lemma P, features, segments, exclusions, output) is as in that file. A second, independent
checker should be written from the two specifications only, without reading this checker's code.

## Claim checked

Input: a leg length L, finite points p_i with rational weights w_i ≥ 0, optional chord pairs
(index pairs at exact distance 1), a symmetry flag. Proved:

    for every closed unit square Q with Q ⊆ T_L (any position, any angle):  Σ_{p_i ∈ Q} w_i ≥ 1

(closed containment on both sides). With chord pairs, a pose counts min(w_p, w_q) for a pair if
Lemma P applies on its box, each point used at most once. Margin zero must be supported.

T_L = conv{(0,0), (L,0), (0,L)}: the right angle at the origin, legs on the axes.

## Number field

Q(√2): values a + b√2 with a, b rational; sign by comparing a² with 2b². Certificate strings are
"a", "a+b*sqrt2", "b*sqrt2" (for example "5/2*sqrt2" for L = 5/√2).

## Admissibility

Q ⊆ T_L iff its four vertices satisfy y ≥ 0, x ≥ 0 and x + y ≤ L. As half-planes n·c ≤ b − n·(R_θ σ):

- n_0 = (0, −1), b_0 = 0;
- n_1 = (−1, 0), b_1 = 0;
- n_2 = (1, 1), b_2 = L.

The normals need not be unit vectors; for fixed θ each constraint is still a half-plane with a
constant normal and an offset rational in u = tan(θ/2).

## Symmetry

- `"none"`: u ∈ [0, 1] (θ ∈ [0, π/2]). Root u-breakpoints {0, √2 − 1, 1} (θ = 0, π/4, π/2).
- `"D1"`: first check exactly that the weighted points, the features and the segments are
  invariant under the reflection (x, y) ↦ (y, x), the only nontrivial symmetry of T_L. Then
  u ∈ [0, √2 − 1] exactly (θ ∈ [0, π/4]); the reflection maps a square of angle θ to angle
  π/2 − θ, i.e. −θ modulo the period π/2.

## Root grid

The root boxes cover [0, B]² with B = a rational upper bound of L, or a given rational B ≥ L
(`--bbox`, checked exactly). The bbox matters only for speed: it decides which lines are faces of
the boxes (for example B = 6 makes x = 3/2 a face for L = 5).

## Required tests

1. Q(√2) arithmetic and sign.
2. n = 1: L = 2, the point (1/2, 1/2) with weight 1 verifies (D1 and none); at L = 11/4 it fails.
3. n = 3: L = 3, points (3/4, 1), (1, 3/4), (3/4, 5/4), (5/4, 3/4) with weight 1/2 verify; at
   L = 301/100 they fail.
4. A certificate that is not reflection-invariant is rejected with symmetry D1.
