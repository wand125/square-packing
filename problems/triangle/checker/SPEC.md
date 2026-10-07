# Exact checker for unavoidable weighted point sets in an equilateral triangle

## Claim checked

Input:
- a side L,
- finite points p_i with weights w_i ≥ 0 (rational),
- a symmetry flag.

The checker proves:

    for every closed unit square Q with Q ⊆ T_L (any position, any angle):  Σ_{p_i ∈ Q} w_i ≥ 1

(closed containment on both sides; a point on ∂Q counts). Margin zero must be supported.

Here T_L is the triangle with vertices (0,0), (L,0), (L/2, L√3/2).

## Exact number field

All geometry lives in Q(√3). Implement `class Q3` (a + b√3, with a and b `fractions.Fraction`):
- `+ − × /` and exact sign;
- sign(a + b√3) is decided by comparing a² with 3b² and the signs of a and b;
- no floats in any accepted inequality. Floats may only guide choices (which points to try, where to split).

L, point coordinates and weights are given in the certificate as exact values:
- L and coordinates are Q3, as strings "a" or "a+b*sqrt3" with a, b rationals like "3/2";
- weights are rationals.

## Poses

- Q(c, θ) = c + R_θ[−½, ½]².
- Parametrise θ = 2·arctan(u), with cos θ = (1 − u²)/(1 + u²) and sin θ = 2u/(1 + u²).
- Angle coverage:
  - `symmetry: "none"`: u ∈ [0, 1] (θ ∈ [0, π/2]; the square has period π/2).
  - `symmetry: "D3"`: the checker first verifies exactly that the weighted point set is invariant under
    the 6 symmetries of T_L (rotation by 2π/3 about the centroid, and the reflection x ↦ L − x).
    Then u ∈ [0, U] with a rational U whose tan-half-angle exceeds π/12: prove exactly that U > tan(π/24).
    tan(π/24) = √6 − √3 + √2 − 2; for example compare via θ(U) > π/12 ⟺ cos θ(U) < cos(π/12) = (√6 + √2)/4.
    Do this with an exact test, e.g. check (1 − U²)/(1 + U²) < (√6 + √2)/4 by squaring carefully, or
    use Q(√2, √3) ad hoc. U = 1/7 is a fine default.
    Reason for the reduction: rotation by 2π/3 maps θ ↦ θ + π/6 (mod π/2), and the reflection maps θ ↦ −θ.

**u-bin endpoints may be Q3 numbers**, not only rationals. Bernstein coefficients on [a, b] with
a, b ∈ Q3 are computed exactly in the same way. The root u-partition must include the breakpoints
where margin-zero contacts happen at irrational angles:
- For `symmetry: "none"`, the default root breakpoints are u ∈ {0, 2 − √3, √3/3, 1}, i.e.
  θ = 0, π/6, π/3, π/2. These are the images of θ = 0 under the symmetries.
- A CLI option `--u-breaks` adds more breakpoints.

A margin-zero contact at an angle strictly inside a bin cannot be certified (double zero), so the
breakpoints must sit exactly there.

## Admissibility as linear constraints (no absolute values)

Q ⊆ T_L if and only if all 4 vertices of Q lie in T_L. With outward unit normals n_k and offsets b_k of the
three sides:
- n_0 = (0, −1), b_0 = 0;
- n_1 = (√3/2, 1/2), b_1 = √3 L/2;
- n_2 = (−√3/2, 1/2), b_2 = 0;

and square vertices σ ∈ {(±½, ±½)}, the pose is admissible iff for all 12 pairs (k, σ):

    n_k · c ≤ b_k − n_k · (R_θ σ).

For fixed θ each of these is a half-plane in c with a **constant** normal n_k, and its offset is a rational
function of u with Q3 coefficients and denominator (1 + u²).

## Capture

p ∈ Q(c, θ) iff |(p − c)·e1| ≤ ½ and |(p − c)·e2| ≤ ½, with e1 = (cos θ, sin θ) and e2 = (−sin θ, cos θ).
This gives 4 linear inequalities in c. Their normals depend on θ.

## Algorithm

Adaptive subdivision of boxes B = [x0, x1] × [y0, y1] × [u0, u1]. The x and y bounds are rational
centre ranges; the root grid covers the bounding box of T_L.

For fixed θ, the admissible centres in the rectangle form a convex polygon P_θ, the intersection of
16 half-planes: the 12 admissibility constraints and the 4 rectangle sides. **All 16 have normals
independent of θ.** Every vertex of P_θ is the intersection V_ij(θ) of two non-parallel lines i, j among
the 16. Its coordinates are rational functions of u with Q3 coefficients and denominator dividing
(1 + u²) (the rectangle lines are constant).

A point p is **captured on B** if for every u ∈ [u0, u1] and every vertex of P_θ the 4 capture
inequalities hold. Capture is convex in c, so vertices suffice. Soundly, for every non-parallel pair
(i, j) one of the following must hold:

- **(infeasible)** some third constraint m is strictly violated by V_ij(u) for all u ∈ [u0, u1]. Then
  V_ij is never a vertex on this bin.
- **(ok)** each of the 4 capture inequalities, g(u) = ½ ∓ (p − V_ij(u))·e(u) ≥ 0, holds for all
  u ∈ [u0, u1]. Multiply by the positive denominator (1 + u²)² to get a polynomial P(u) of degree ≤ 4
  with Q3 coefficients. Prove P ≥ 0 on [u0, u1] by exact Bernstein coefficients on that interval (all
  coefficients ≥ 0 suffices; the interval endpoints may be Q3). Before giving up, subdivide the u-interval of this one test to a small
  depth (e.g. 12 halvings), recursively.

  Margin zero works when the zero is at an endpoint of the interval: the first or last Bernstein
  coefficient is then 0 and the others are ≥ 0.

Strict infeasibility uses the same polynomial machinery: prove (offset constraint violated) > 0 on the
interval, i.e. all Bernstein coefficients > 0, or ≥ 0 with a positive endpoint value and no interior
zero. Keep it simple and sound: require every Bernstein coefficient > 0 after subdivision.

**Box certified** if either:
1. **EMPTY**: every pair (i, j) is infeasible. Then P_θ has no vertex for any θ in the bin; since P_θ is
   bounded, it is empty. Alternatively, a single admissibility or rectangle constraint pair shows
   emptiness directly.
2. **COVER**: a set S of points, each captured on B, has Σ_{p∈S} w ≥ 1.

To choose S cheaply, evaluate in floats at a few sample angles and the polygon vertices which points are
captured with margin. Try the heaviest candidates first, then prove exactly.

Otherwise split B: halve the longest side, with the u side scaled by a factor (default 4, configurable).
Stop at a depth limit and report the box as UNCERTIFIED. The verdict is "verified" only if there are
0 uncertified boxes.

**Pruning.** Precompute, per box, which of the 16 constraints can matter. A constraint whose offset keeps
the rectangle strictly inside for the whole bin is redundant and may be dropped, but only if this is
proved exactly with the same polynomial test. Pairs where one line is redundant can then be skipped.

## Output

A JSON summary with:
- the certificate sha256, L, the number of points, the exact total weight (as a fraction string, and
  as a Q3 string if needed), the symmetry used;
- counts of root boxes, EMPTY and COVER leaves, uncertified boxes (listing their coordinates);
- max depth, seconds, and `"status": "verified" | "failed"`.

Also print the exact total weight and whether it is < n when `n` is given (`--n`).

## Files

- `checker/q3.py`: the Q3 number class.
- `checker/poly.py`: polynomials over Q3, Bernstein coefficients on [a, b] (a, b in Q3),
  and a nonnegativity test with subdivision.
- `checker/check.py`: CLI `python check.py cert.json [--n N] [--root R] [--max-depth D] [--jobs J]`.
  Parallelise over root boxes with multiprocessing.
- `checker/tests/`: pytest.
- `checker/README.md`: English, short: what is proved, the lemmas above, how to run.

Standard library only (fractions, json, multiprocessing, hashlib). Python 3.10+. pytest for tests.
**All comments and docs in English.**

## Certificate format (JSON)

```json
{"L": "2+2/3*sqrt3", "symmetry": "D3" | "none",
 "points": [{"x": "a+b*sqrt3", "y": "...", "w": "p/q"}, ...]}
```

(2/√3 = (2/3)√3.)

## Required tests

1. Q3 arithmetic and sign, including edge cases: a² = 3b² is impossible for nonzero rationals; zero.
2. Bernstein nonnegativity:
   - accepts (u − 1/3)² on [0, 1] only after the root is at a subdivision endpoint (or report that it
     cannot; margin-zero only at endpoints is fine);
   - accepts u(1 − u) on [0, 1];
   - rejects u − 1/10 on [0, 1].
3. **n = 2 certificate** (the key acceptance test): L = 2 + 2/√3, a single point at the centroid
   (L/2, L√3/6) with weight 1.
   - symmetry "D3" must return verified.
   - symmetry "none" must also return verified.
   (Known fact: at this L every closed unit square in T_L contains the centroid, with equality exactly
   at θ = 0 for the two bottom-corner squares and their images.)
4. **Negative test**: same point, L = 2 + 2/√3 + 1/100. Must NOT verify: a square avoiding the centroid
   exists. The run must end with uncertified boxes at the depth limit, never "verified".
5. Negative test: n = 2 point shifted by 1/50 in x, at L = 2 + 2/√3, symmetry "none". Must not verify.
6. A random soundness test: for random rational poses that are admissible (checked exactly), the
   exact capture sum of a verified certificate is ≥ 1.

Keep runtime of the test suite under ~2 minutes on one core.

## Extensions added after the first version (used by the n = 4 certificate; features not yet used)

### Chord pairs (Lemma P)

Certificate field `"pairs": [[i, j], ...]`, where i and j are indices into `points`. The checker
requires |p_j − p_i|² = 1 exactly.

Lemma: let d = p_j − p_i, p = p_i. Suppose that for some square axis e_k with d·e_k ≠ 0 (other
axis e_j), the line p + t d meets both edges {(x − c)·e_k = ±½} of Q(c, θ) inside those edges,
i.e. |(p + t_± d − c)·e_j| ≤ ½ at t_± = ((c − p)·e_k ± ½)/(d·e_k). Suppose also that the
chord [min t_±, max t_±] meets [0, 1]. Then Q contains p or p + d. The reason: the chord has length
1/|d·e_k| ≥ 1, and it lies in Q by convexity.

- For fixed θ all conditions are linear in c, so on a box they are checked at the vertices of the
  admissible-centre polygon, exactly like capture.
- On a box where the lemma is proved, the capture sum is at least min(w_p, w_q). Each point is
  counted at most once overall: points proved captured individually and pair members are disjoint.

### Threshold features (not used by any current certificate)

Certificate field `"features": [{"sites": [{"x":…, "y":…}, …], "k": k, "w": "p/q"}, …]`.

- A feature fires on Q if at least k of its m sites lie in Q, and then contributes w.
- Budget: Σ w_p + Σ_F ⌊m/k⌋ w_F < n. This is valid because pairwise disjoint closed squares share
  no site.
- With symmetry D3, the multiset of features must be invariant.
- On a box, a feature counts only if at least k of its sites are proved captured individually.

### Centre scaling (used for every theorem)

Squares with disjoint interiors in T_L, L < v, are translated by (v/L − 1)(c_i − G), where G is the
common centroid. The results are pairwise disjoint closed unit squares in T_v. Proofs are in
`../certificates/n2/PROOF.md`.

### Segment masses (implemented; not used by the published certificates)

Certificate field `"segments": [{"p": {"x":…, "y":…}, "q": {"x":…, "y":…}, "rho": "p/q"}, …]`:
mass spread uniformly with density ρ along the closed segment pq.

- **Capture.** A square Q captures ρ·|Q ∩ pq|, the length of the intersection.
- **Budget.** Σ w_p + Σ ρ·|pq| < n. This is valid for pairwise disjoint closed squares, which is
  what centre scaling produces: their intersections with a segment are disjoint.
- **D3.** The multiset of segments must be invariant.

**Lemma S (concavity).** For fixed θ and a fixed segment σ, the function g(c) = |Q(c,θ) ∩ ℓ_σ|
(intersection with the full line, possibly negative when extended linearly) is concave on the set
where the intersection is non-empty. This is 1-D Brunn–Minkowski: a convex body translated across
a line. Hence on the admissible-centre polygon P_θ the minimum of |Q ∩ σ| = max(0, …) is attained
at a vertex, and it is enough to bound the length from below at every vertex V(u) of P_θ, for all
u in the bin. This is the same vertex machinery used for points and Lemma P.

**Exact lower bound at a vertex.** Parametrise σ as p + t(q − p), t ∈ [0, 1].
- For each square axis e_k, the slab |(p + t d − c)·e_k| ≤ ½ gives t in an interval with
  endpoints t = ((c − p)·e_k ± ½)/(d·e_k). If d·e_k = 0 there is no constraint, or no intersection.
- The intersection is [t_lo, t_hi] ∩ [0, 1], where t_lo is the maximum of the lower endpoints and
  t_hi the minimum of the upper endpoints.
- To prove |Q ∩ σ| ≥ ℓ_min on a bin, choose (by floats) which candidate endpoint is active for
  t_lo and for t_hi. Then prove exactly with Bernstein bounds:
  1. the signs of d·e_k on the bin;
  2. the chosen lower endpoint is ≥ every other lower candidate (including 0), and the chosen
     upper endpoint is ≤ every other upper candidate (including 1);
  3. (t_hi − t_lo)·|d| ≥ ℓ_min.
- Every inequality, multiplied by the positive denominators, is a polynomial in u with Q3
  coefficients.
- |d| may be irrational (d has Q3 coordinates). To avoid square roots, bound
  (t_hi − t_lo)·|d| ≥ ℓ_min using |d|² ≥ (rational lower bound)², or require the segments to have
  |d|² ∈ Q3 and compare squares. The simplest is to allow only segments of length exactly 1
  (checked exactly), which is the case in practice.
- A box gets capture weight Σ_points + Σ_segments ρ·ℓ_min(segment, box). It is COVER if this is ≥ 1.
  For each segment use the best ℓ_min that can be proved, e.g. try ℓ_min from the float minimum
  over the vertex samples, rounded down to a dyadic rational, and fall back to 0.

**As implemented** (`check.py`: `segment_credit`, `_seg_vertex_prove`, `_seg_vertex_exact`; README
item 6b):
- Only unit segments are accepted (|q − p|² = 1 exactly), with ρ ≥ 0. The budget adds Σ ρ. With D3,
  the multiset of (unordered endpoint pair, ρ) must be invariant.
- The vertex conditions are stated without dividing by d·e_k. For t0 = a0/b0 and t1 = a1/b1 with
  b0, b1 > 0 proved, require t0 ≥ 0, t1 ≤ 1, both slab inequalities
  −D²/2 ≤ N_k − t·D·M_k ≤ D²/2 for both axes at t = t0 and at t = t1, and t1 − t0 ≥ ℓ_min. They are
  linear in t, so they hold on [t0, t1]. An inactive axis with vanishing d·e_k is therefore fine.
- t0 is 0 or an active lower slab end, plus a rational slack δ0 ≥ 0. t1 is 1 or an active upper
  end, minus δ1 ≥ 0. Floats choose the active ends per vertex.
  - The slack-free attempt (δ0 = δ1 = 0) is tried first.
  - If no choice works on the u-interval, it is halved, up to 3 times, with a fresh choice per half.
- **Order of ℓ_min candidates.** The first one that is proved for every vertex is used:
  1. **snap:** 1, if the float minimum exceeds 1 − 10⁻⁹;
  2. **snap:** the float minimum snapped by `Fraction(fmin).limit_denominator(1000)`, if it is within
     10⁻⁹ of the float minimum;
  3. the ladder: the float minimum minus 10⁻⁶, 10⁻⁵, 10⁻⁴, 10⁻³ and 10⁻², each rounded down to a
     multiple of 2⁻²⁰;
  4. half of the first ladder value;
  5. otherwise credit 0.

  The snap steps make margin-zero certificates at the container endpoint possible. There, a square
  stands exactly on a unit segment, the length is exactly 1, and any safety margin would make the
  box fail. Floats only propose the candidates; each accepted value is proved exactly.
- **Joint credit.** For each segment i and vertex candidate v, prove c_{i,v} ≤ len_i(V_v(u)) for all
  u in the bin, using the same proof and candidate list, starting above the per-segment credit.
  - Let P be the set of segments with c_{i,v} > 0 at every candidate. Then
    J = min_v Σ_{i∈P} ρ_i c_{i,v} + Σ_{i∉P} ρ_i·(per-segment credit) is a lower bound.
  - It is sound by concavity: for i ∈ P, g_i is concave on P_u, so the sum is concave, and its
    minimum is at an extreme point of P_u, which is among the candidates.
  - COVER uses max(J, Σ per-segment credits). J runs only when the float joint estimate clears the
    deficit and beats the per-segment credits.
- Segment credits are computed only when the float estimate of points + features + pairs is < 1. If
  the exact point proofs fall short, the segment credits are still tried.
- `seg_probe.py` is a float sanity tool: it gives the minimum capture over random admissible poses.

### Exclusion boxes and obstacle points (used for n = 6)

Both fields serve the localization tree of `../certificates/n6/PROOF.md`.

**Exclusions.** Certificate field `"exclusions": [{"x": [x0, x1], "y": [y0, y1], "u": [u0, u1]}, …]`,
with Q3 endpoints.
- A pose (c, u) is exempt if x0 ≤ c_x ≤ x1, y0 ≤ c_y ≤ y1 and u0 ≤ u ≤ u1 (closed box) for some entry.
- With `symmetry: "D3"`, the box is tested on the pose's image in the fundamental domain u ∈ [0, U].
  Equivalently, a pose is exempt if one of its 6 images (with u reduced mod the period) lies in a box.
  `../certificates/n6/loc3/cert_e1_100.json` is the only D3 certificate that uses exclusions.
- Claim checked: every admissible pose that is not exempt captures ≥ 1.

**Obstacle points.** Certificate field `"obstacle_points": [{"x": …, "y": …}, …]`, unweighted.
Only with `symmetry: "none"`.
- A pose whose closed square contains an obstacle point is exempt.
- Obstacle points are not part of the budget: the budget is Σ w_p < n over `points` only.
- Claim checked: every admissible pose that is neither excluded nor contains an obstacle point
  captures ≥ 1 from `points`. (The first checker implements this by giving obstacle points weight 1
  in the box test; any method proving the claim above is fine.)

**What makes obstacle points valid (not checked by this checker).** Each point lies strictly inside
every placement of an earlier-stage square allowed by its box, or is a wall or chain witness: a point
that no square disjoint from that earlier square can contain. These facts are proved by
`../certificates/n6/stage2/stage_inputs.py`, `wall_witness2.py` and `chain_witness.py`, with the statements in
their headers. A second system should re-prove them independently from those statements.

**Sizes.** The n = 6 certificates have 3 to 14 weighted points and 81 to 622 obstacle points, and
`cert_e1_100.json` has 138 weighted points with D3. A method whose cost grows like (number of
lines)³ over the whole triangle will not finish on them; localise (for example by centre cells or
short u-intervals), because only obstacle points near the exclusion boxes matter for most poses.
