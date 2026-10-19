# Unit squares in a rectangle: a measure bound for all real side lengths

This document states the claims and lemmas of the rectangle version of the
closed-form bound and says which check establishes each finite statement. It builds on the closed-form
certificate for squares in [`problems/closed-form/`](../closed-form/) (its `SPEC.md` is cited as CF) and uses
its families, local models and four-region checks unchanged.

## 1. Problem and notation

The container is [0, a] × [0, b] with a = k + δ_a, b = m + δ_b, k and m integers, δ_a, δ_b ∈ [0, 1).
ν(a, b) is the largest number of non-overlapping unit squares (any positions, any angles) that fit in it.

α = 9/5, R = 2, W = 2 + δ, r = √2/2. The parameter intervals J are the 34 intervals of CF (`intervals.json`;
they partition (0, 1], the last one is (99/100, 1]); d₀(J) < d₁(J) are the ends of J. Each interval has a
family (CF §3): corner pieces, a wall profile P_J of period 1 and mass 9/5 per period, a terminal line, and the
Lebesgue part U = [α, ∞)². S_J(δ) is the family's saving (CF §1.3); on J it is affine in δ and equals the
certified line α_J δ + β_J listed in `intervals.json` (checked for all 34 families at both ends).
σ(x, y) = (a − x, b − y) and τ(x, y) = (a − y, x).

## 2. The measure principle for rectangles

**Lemma M.** Let μ be a finite non-negative measure on [0, a′] × [0, b′] with μ(Q) ≥ 1 for every closed unit
square Q contained in it. Then ν(a, b) ≤ μ([0, a′] × [0, b′]) for all a < a′ and b < b′.

*Proof.* Put λ = min(a′/a, b′/b) > 1. Scale a packing of N squares in [0, a] × [0, b] by λ about the origin
and put a unit square with the same orientation at the centre of each scaled square. These N closed unit
squares are pairwise disjoint and lie in [0, λa] × [0, λb] ⊆ [0, a′] × [0, b′], so the total mass is at
least N. ∎

The scaling is the same in both directions (scaling the two axes differently would turn tilted squares into
parallelograms). Since both sides must grow, the bounds below are right limits in δ (§4).

## 3. The global layout and the same-interval case

| Part | Local form | Placement |
|---|---|---|
| corner SW | corner of the family of J_a at δ_a | [0, W_a] × [0, R] |
| bottom wall | periods of the profile(s), terminal line | x ∈ [W_a, a − R] |
| corner SE | corner of the family of J_b at δ_b | τ-image, [a − R, a] × [0, W_b] |
| right wall | periods of the profile(s), terminal line | τ-image |
| corners NE, NW, top and left walls | σ-images of the four above | |
| Lebesgue | density 1 | [α, a − α] × [α, b − α] |

**Lemma R1 (localisation).** Let k, m ≥ 7 and let δ_a, δ_b lie in the same interval J. For a closed unit
square Q with centre z, if z ∈ [0, a/2] × [0, b/2] then μ(Q) = μ_loc^{J, δ_a}(Q), and if
z ∈ [a/2, a] × [0, b/2] then μ(Q) = μ_loc^{J, δ_b}(τ⁻¹Q); the other two quarters map to these by σ.
Hence μ(Q) ≥ 1 for every Q if the family of J passes the checks of CF. (The table of distances showing that
no piece outside the local model reaches the quarter needs only a, b > 5.42; we keep k, m ≥ 7 as in CF.)

**Lemma R2 (total mass).** μ([0, a] × [0, b]) = ab − 2S_{J_a}(δ_a) − 2S_{J_b}(δ_b).

*Proof.* With M_C the corner mass and m_v the terminal line,
μ = (a − 2α)(b − 2α) + 2[(k − 4)α + M_C(δ_a) + m_v] + 2[(m − 4)α + M_C(δ_b) + m_v]. Substituting
k = a − δ_a and m = b − δ_b, the terms linear in a and b cancel and the constant is 4α² − 16α = −4 · 99/25,
so μ = ab − 2S(δ_a) − 2S(δ_b) with S(δ) = 99/25 + αδ − M_C(δ) − m_v (CF §1.3). ∎

`checker/validate_rect.py` checks R1 and R2 exactly for each family at both ends of its interval and several
(k, m) (windows of the corners against the local model, wall periods by integer shifts, terminal lines,
total mass, C2 symmetry, and for k = m, δ_a = δ_b agreement with the square construction).

## 4. Endpoints: the right-hand interval

For δ ∈ [0, 1) let J⁺(δ) be the interval J with d₀(J) ≤ δ < d₁(J), i.e. the interval containing (δ, δ + ε)
for small ε > 0 (J may be open at d₀).

**Theorem A (same interval).** Let δ_a, δ_b ∈ [0, 1), J⁺(δ_a) = J⁺(δ_b) = J and k, m ≥ 7. Then
ν(k + δ_a, m + δ_b) ≤ ab − 2S_J(δ_a) − 2S_J(δ_b).

*Proof.* For λ > 1 close to 1, δ′_a = λa − k and δ′_b = λb − m lie in (δ_a, d₁(J)) and (δ_b, d₁(J)), and the
integer parts do not change. There the measure of R1–R2 exists with total (λa)(λb) − 2S_J(δ′_a) − 2S_J(δ′_b),
so by Lemma M ν(a, b) is at most this. S_J is continuous, and λ ↓ 1 gives the claim. ∎

Only the part of J to the right of δ is used. In particular:
- δ = 0 (an integer side) is included, with J⁺(0) = (0, 1/50];
- at δ = 2/5 the bound uses the family of (2/5, 81/200], not the left branch of CF's target;
- δ ∈ [99/100, 1) uses the family of (99/100, 1].

An equivalent form uses the family at δ itself: if δ_a and δ_b lie in J (closed ends as listed in CF
`INTERVALS.md`), then ν(a′, b′) ≤ ab − 2S_J(δ_a) − 2S_J(δ_b) for all a′ < a, b′ < b.

## 5. Different intervals: seams

### 5.1 Seams and the path between two intervals

A **seam** joins the wall profile P of one interval to the profile P′ of another along a wall: periods of P
for x < S, one transition period T on [S, S + 1), periods of P′ for x ≥ S + 1 (the vertical line x = S + 1
belongs to P′). Its **seam family** is a family JSON in the CF format with all pieces in F (three periods of P,
the transition, three periods of P′, S = 5) and the Lebesgue part U; it does not depend on δ. Its extra mass
e = mass(T) − 9/5 is a rational recorded in the family.

We use 30 seams between pairs of the 34 intervals, each checked as in §5.3, and 4 pairs of adjacent intervals
with identical profiles (checked exactly), which need no seam (e = 0). The graph on the 34 intervals with these 34 edges is
connected. For intervals J_a, J_b a **path** J_a = J_0, J_1, …, J_b uses some of these edges; E is the sum of
the e on the path and r the number of seams (edges with e > 0) on it.

### 5.2 Layout with r seams

The bottom wall x ∈ [W_a, a − R] has k − 4 periods. It carries P_{J_0} for t₀ periods, a seam, P_{J_1} for
L₁ periods, a seam, …, and finally P_{J_b} for t_end periods (t_end counts the complete periods of P_{J_b}
before the terminal line; the terminal line x = a − R has no length and belongs to the corner SE band).
The right wall carries the same path in reverse; there each seam appears as (P′, P), and we place the mirror
image of the checked local model, transition included. The profiles are invariant under the reflection
within a period and the period boundaries stay at integer positions, and a mirror image of a closed unit
square is a closed unit square, so the check of one orientation suffices. The top and left walls are the
σ-images. The integer wall of corner SW is P_a and that of corner SE is P_b, as the local models of the two
corners require.

**Lemma R5 (band).** Let d = 2/5 and B = [S, S + d) × [0, α]. If the seam measure is at least the measure of
the pure P-wall on the open half-plane x < S + d, then every Q with z_x + w(θ) < S + d (w(θ) the half-width of
Q in x) has μ_seam(Q) ≥ μ_P(Q) ≥ 1, where the last inequality is the wall check of the family of P in CF (the
"right" and "top" regions cover every square on an infinite wall of P after an integer shift). The same holds
on the right with x > S + 1 − d and P′. So the seam check needs only the roots touching both bands:
11,206 of the 17,550 roots of the window.

**Lemma R7 (separation).** If t₀ ≥ 2, t_end ≥ 2 and every intermediate L_i ≥ 2, then μ(Q) ≥ 1 for every
closed unit square Q in the container.

*Proof.* We use r = √2/2 < 3/4. The seam check covers the squares with centre x ∈ [S − 3/4, S + 7/4] with the
local seam model. Such a square meets only x ∈ (S − 3/4 − r, S + 7/4 + r) ⊂ (S − 1.46, S + 2.46) ⊂ (S − 2, S + 3);
with two periods of P on [S − 2, S] and two of P′ on [S + 1, S + 3] the global measure agrees there with the
local model. A square outside the window has its left end right of S + 1.04 (centre right of S + 7/4) or its
right end left of S − 0.04 (centre left of S − 3/4); it does not meet the transition and meets a single
profile, so the wall check of that family applies. With L ≥ 2 the windows of neighbouring seams leave the gap
(S + 1.75, S + 2.25), so no square meets two seams; with t₀, t_end ≥ 2 no seam window reaches a corner piece,
and squares near a corner are handled by R1. The reduction R5 is not affected: a square whose right end is
left of S + 2/5 extends at most √2 + 2/5 ≈ 1.81 to the left and stays within the two periods of P (likewise on
the right). ∎

Counting periods, k − 4 ≥ 2 + 2 + 2(r − 1) + r, i.e. k ≥ 6 + 3r, and likewise m ≥ 6 + 3r. With r = 0 we keep
7 from R1; for r ≥ 1, 6 + 3r ≥ 9. So k₀(r) = max(7, 6 + 3r).

**Total mass.** μ([0, a] × [0, b]) = ab − 2S_{J_a}(δ_a) − 2S_{J_b}(δ_b) + 4E: every period has mass 9/5 in every
profile, a seam differs from plain periods only in its transition period (by e), seams are independent when
L ≥ 2, and each of the four walls carries the same path. The terminal lines sum as in R2.

**Theorem B (different intervals).** Let δ_a, δ_b ∈ [0, 1), J_a = J⁺(δ_a), J_b = J⁺(δ_b), K = min(k, m). If
there is a path from J_a to J_b with k₀(r) ≤ K, let E_K(J_a, J_b) be the least E over such paths. Then
ν(k + δ_a, m + δ_b) ≤ ab − 2S_{J_a}(δ_a) − 2S_{J_b}(δ_b) + 4E_K(J_a, J_b).
(Proof as for Theorem A, with the layout of §5.2 and Lemma R7.)

For the 30 seams used here, for every pair the path of least E also has the fewest seams, so E_K is the same
for all K ≥ k₀ (the table lists E, r and k₀ for all 595 pairs, `data/paths.json`).

### 5.3 How each seam was checked

For each seam:
1. The transition was found by a linear program on sampled poses with the band condition of R5 as lower
   bounds, and repaired monotonically (masses only increase) where a sampled or exact check found μ < 1.
2. Every root of the R5 list was proved by the 4D checker of CF (`run4d`), splitting roots where needed. When
   a piece failed, the family was repaired so that it dominates the previous one segment by segment, and only
   the failed pieces were checked again (levels 0, 1, …). A piece proved for an earlier level holds for the
   final family because the final family's measure is at least the earlier one's.
3. The records of each level were checked by `check_record4d` (all structural conditions; 2,000 leaves
   recomputed per record). The only findings are of the kind "roots are not the full grid", expected since R5
   removes roots and pieces are split; coverage is checked separately.
4. Coverage (`checker/seam_cover.py`, exact): every grid root left out of the R5 list is proved not to reach
   a band, the pieces passed at all levels lie in roots of the list, are pairwise interior-disjoint, have no
   uncertified leaves, and their volumes add up to the volume of the list.
5. Exact checks of the final families (`checker/seam_exact.py`): line densities are compared pointwise with the
   walls of the published interval families: the band condition of R5, agreement with P on [S − 3, S) and with
   P′ on [S + 1, S + 4), and domination of every earlier level's family.

In step 5 two seams (i005_012 | i012_020_a, right band; i012_020_a | i012_020_b, left band) failed the band
condition on one segment of length 2/5 at y = 8/5 (profile density 0.005): the lower bounds of step 1 were set
per grid cell of length 1/5 and missed a profile segment spanning two cells. We added that segment's missing
mass, rounded up to 2001/10⁶, to the final family of each of the two seams (`fam_r5.json`). Adding mass keeps
every proved piece valid, and the repaired families pass step 5; their e increased by 2001/10⁶ each.

### 5.4 Results

| | |
|---|---|
| seams checked | 30 (10 across the main interval boundaries of CF, 5 between finer intervals, 15 in (21/50, 1/2] joined to the hub interval (23/50, 93/200]) |
| e | from 0.0550 to 0.4994 |
| largest E | 2907373/10⁶ ≈ 2.91, for (0, 1/50] and (99/100, 1] (r = 16, k₀ = 54) |

Theorem B holds for all 595 pairs but improves on the area bound ν ≤ ab only where
2S_{J_a}(δ_a) + 2S_{J_b}(δ_b) > 4E. Counted exactly with the certified lines: of the 561 pairs of different
intervals, 224 improve on ab on the whole of J_a × J_b, 2 on part of it and 335 nowhere; the useful pairs have
r ≤ 4 and k₀ ≤ 18. All 120 pairs inside (21/50, 1/2] are useful (least net saving 1.30). The 34 same-interval
cases are useful everywhere except at δ_a = δ_b = 0. The table is `data/paths.json` (fields `useful`,
`net_min`, `net_max`).

## 6. Checks and records

| Checker | What it checks | Applied to |
|---|---|---|
| `checker/validate_rect.py` | Lemmas R1, R2 (exact) | the 34 published interval families |
| `run4d` (from CF) | every seam root, μ ≥ 1 | 30 seams, all levels |
| `check_record4d` (from CF) | record structure, sampled recomputation | every level record |
| `checker/seam_cover.py` | R5 root list and exact coverage by the pieces of all levels | 30 seams |
| `checker/seam_exact.py` | R5 band condition, structure against the published families, monotone levels (exact) | 30 final seam families (51 levels) |
| `checker/paths.py` | paths, E, r, k₀, usefulness | 595 pairs |
| `indep-checker/` (independent) | seam structure and e, R5 band condition, levels, R5 root list, coverage, every leaf of every record, paths | 30 seams, 52 records, 595 pairs |
| `checker/compare_bounds.py` | comparison with the area bound and Karakuş's bound | 595 pairs |

Release asset `rectangle-closed-form-v1.tar.xz`: the seam families of every level, the records per level, the
R5 root list, the 34 interval families (unchanged from CF) and SHA-256 sums. The records of the interval families
are those of CF. The outputs of the checks are in `receipts/`.
