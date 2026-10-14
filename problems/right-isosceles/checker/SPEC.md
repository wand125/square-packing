# Exact checker for unavoidable weighted point sets in a right isosceles triangle

This is the specification of `squintan/checker/check.py`. It is the equilateral checker of
`../../tri_container/checker/SPEC.md` with six changes: the container, the number field, the
symmetry, segments of any length, an optional second frame and optional endpoint slices. Everything not listed here (poses, capture, the box subdivision, Bernstein tests, chord
pairs / Lemma P, features, segments, exclusions, output) is as in that file. A second, independent
checker should be written from the two specifications only, without reading this checker's code.

## Claim checked

Input: a leg length L, finite points p_i with rational weights w_i ≥ 0, optional chord pairs
(index pairs at a distance in (0, 1]; 10/10 widened from exactly 1, see "Short chord pairs"), a symmetry flag. Proved:

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

## Segments of any length (changed 2026-10-10)

The equilateral checker accepts only unit segments with density ρ. Here a segment pq may have any
length |q − p| > 0 (q − p with coordinates in Q(√2); a segment of length 0 is rejected), and ρ is
the **mass of the whole segment**, spread uniformly along it:

- **Capture.** A square Q captures ρ·|Q ∩ pq| / |pq|. With p + t(q − p), t ∈ [0, 1], this is
  ρ·(t_hi − t_lo), so every length in the vertex proofs and in the joint credit is measured in t.
  This is exactly what the equilateral checker computes for unit segments; no square roots occur.
- **Budget.** Σ w_p + Σ ρ < n (valid for pairwise disjoint closed squares, as before).
- **Lemma S** is unchanged: |Q(c, θ) ∩ ℓ| / |pq| is a positive multiple of the length, hence concave.

For a unit segment the old and new readings agree.

## Hypotenuse frame (added 2026-10-10)

Optional certificate field `"frame": "hyp"` (default `"legs"`). The container is then the same triangle
moved by an isometry so that its hypotenuse is [0, H] on the x-axis, H = L√2:

    T = {y ≥ 0, y ≤ x, y ≤ H − x},  half-planes (0, −1)·c ≤ 0, (−1, 1)·c ≤ 0, (1, 1)·c ≤ H.

- The symmetry D1 is the reflection (x, y) ↦ (H − x, y); it maps a square of angle θ to angle −θ, so
  the u-range with D1 is [0, √2 − 1] as before.
- The root grid covers [0, B] × [0, B/2] with B a rational upper bound of H, or a given rational
  bbox B ≥ H.
- Everything else (capture, Lemma P, segments, exclusions, budget) is unchanged: the claim is about
  the triangle, and the frame is only a choice of coordinates. A leg-frame point (x, y) corresponds to
  ((y − x + L)/√2, (L − x − y)/√2), and angles shift by 45° (`../to_hyp.py`).
- Purpose: for L ∈ Q·√2 (n = 4, 9, 12) the hypotenuse is rational, and the packings standing on it
  have rational coordinates, so dyadic box faces can lie on their lines.

## Endpoint slices (`--slices`, added 2026-10-10)

A square flush against a side at θ = 0 (or π/4, π/2) has admissible neighbours only at that exact angle.
If a box face lies on the contact line (for example cx = 1/2 at the side x = 0), the admissible part of the
box for u ∈ [0, u1] is a segment at u = 0, and halving u never removes it. With `--slices`, a box whose
u-interval begins at the lower end u_lo of the whole u-range (or ends at its upper end u_hi) that is not
otherwise certified is certified by two exact steps:

1. **Emptiness on the half-open interval** (u_lo, u1] (or [u0, u_hi)). All constraint normals are
   constant: the three container sides (four corners each) and the four box faces. A Farkas combination
   with constant multipliers λ ≥ 0 and Σ λ_i n_i = 0 exactly (two opposite normals, or three normals with
   λ = (n₂×n₃, n₃×n₁, n₁×n₂) of one sign) proves emptiness if −Σ λ_i O_i(u) > 0 on the half-open
   interval. This is proved from Bernstein coefficients: if b₀ ≥ 0 and b_i > 0 for i ≥ 1, the polynomial is
   positive on (a, b] (and symmetrically); otherwise halve, the half at the open end keeping that test.
2. **The slice itself.** At u = u_lo the admissible centres in the box form a polygon with exact vertices
   (pairwise intersections of the constraint lines that satisfy all constraints). For fixed θ the centres
   c with p ∈ Q(c, θ) form a square, a convex set, so p lies in Q(c, θ) for every centre of the polygon iff
   it does for every vertex. The slice is covered if those points weigh ≥ 1 (chord pairs and segments are
   not used here). An empty polygon is covered.

Leaves certified this way are counted as `slice_leaves`. Without the flag the checker behaves as before.

## Required tests

1. Q(√2) arithmetic and sign.
2. n = 1: L = 2, the point (1/2, 1/2) with weight 1 verifies (D1 and none); at L = 11/4 it fails.
3. n = 3: L = 3, points (3/4, 1), (1, 3/4), (3/4, 5/4), (5/4, 3/4) with weight 1/2 verify; at
   L = 301/100 they fail.
4. A certificate that is not reflection-invariant is rejected with symmetry D1.
5. Short segments: at L = 2 the segment (1/4, 1/4)–(1/2, 1/2) with mass 1 verifies (D1 and none),
   and so do the two segments (1/4, 1/2)–(1/2, 1/2) and (1/2, 1/4)–(1/2, 1/2) with mass 1/2 each;
   at L = 11/4 both fail. A segment of length 0 is rejected.
6. Hypotenuse frame: the n = 3 certificate moved to the hypotenuse frame verifies (D1 and none), fails
   at L = 301/100, and without one of its points is rejected as not D1-invariant.
7. Endpoint slices: at L = 2 with bbox 4, the single point (1, 1/2) of weight 1 verifies with `--slices`
   (some slice leaves) and stays uncertified without it; at L = 3 it fails.

## Short chord pairs (2026-10-10)

Lemma P is accepted for pairs at any distance 0 < |q − p| ≤ 1 (exact test d·d ≤ 1, d ≠ 0). The proof is unchanged: the
line p + t d crosses the two edges of Q normal to e_k, the chord has t-length 1/|d·e_k| ≥ 1/|d| ≥ 1, and the checker proves
that it meets [0, 1]; an interval of length ≥ 1 that meets [0, 1] contains 0 or 1, so p or q lies in Q. Used for n = 9,
where points on the edges of a degenerate 45° pose are moved inward by 10⁻⁶ (inward.py) and pairs across the square
become slightly shorter than 1. Required test 8: the n = 4 points with the pair shortened symmetrically to 1 − 2√2·10⁻⁶ verify in T_L,
L = 5/√2 − 1/100, with the pair and fail without it; a pair at distance 1 + 10⁻¹² and a zero-length pair are rejected.

## Checkpoint (2026-10-11)

`--checkpoint FILE` writes one JSON line per finished root box (after a header line with the certificate hash, the
root boxes, the options and the points). A rerun with the same file reuses the finished root boxes and checks only
the rest; a file written for a different run is refused, and a line cut off when the machine stopped is ignored.
Root boxes are checked independently and deterministically, so the summary is the same as that of an uninterrupted
run (tested on n = 4: full, resumed from 12 of 32 roots with a cut line, and with --jobs 2 give identical summaries).

## Wedged squares at an end of the u-range (2026-10-12)

A square wedged at θ = 0 between a side and the hypotenuse (n = 15: [0, 1] × [4, 5]; T_3: [0, 1] × [1, 2]) is the
admissible pose where three constraint lines (the side, the hypotenuse and a face of the box) meet in one point at
u = 0. The vertex candidate (side, box face) is a vertex of P_0 and outside P_θ for every u > 0, so no proof on a closed
u-interval removes it, and a heavy point on the square's edge leaves the square at that candidate for u > 0. A box with
this pose at a corner was never certified (`pair_infeasible` needs strict violation on the whole closed interval).

With `--slices`, a box whose u-interval has an end u0 of the u-range at its lower (upper) end is also tried as an
**open-side leaf** ("OPEN", counted in `open_leaves`):
1. `certify_box(..., open_side)`: vertex candidates are dropped when a third constraint is strictly violated on the
   half-open interval (u0, ub] ([ua, u0)), proved by `bern_pos_open` (the violation may vanish only at u0); the float
   screen skips the sample at u0. For every u of the half-open interval each extreme point of P_θ is still the vertex
   of a kept pair, so EMPTY or COVER holds there (the capture proofs themselves are on the closed interval).
2. `slice_cover` at u = u0: the exact admissible polygon at u0 and the points in the square at all its vertices
   weigh ≥ 1 (step 2 of `endpoint_slice`).
Together they cover every pose of the box. Required tests: the T_3 root box [1/2, 3/4] × [5/4, 3/2] at depth 30
verifies with an open-side leaf (the checker before this change fails it), and with (3/4, 5/4) and its image at
weight 1/4 it fails.
Added after an independent review (2026-10-12, "sound"): the upper end — symmetry "none", root box
[5/4, 3/2] × [1/2, 3/4] × [3/4, 1] (the D1 image of the wedge, where the square turns the other way) verifies with an
open-side leaf and fails before this change; and the open-side test keeps real vertices — on [1/2, 3/4] × [5/4, y1] ×
[0, 1/1000] it drops candidates for y1 = 3/2 (three lines meet at u = 0) and none for y1 = 1499/1000 or 14999999/10^7.
