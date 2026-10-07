# Exact unavoidability checker for unit squares in an equilateral triangle

## What is proved

Input: a side `L`, points `p_i` with rational weights `w_i >= 0`, and a symmetry flag.
When the output says `"status": "verified"`, the following holds:

    every closed unit square Q with Q ⊆ T_L (any centre, any angle) satisfies  Σ_{p_i ∈ Q} w_i ≥ 1,

where T_L has vertices (0,0), (L,0), (L/2, L√3/2). With segment masses (item 6b), the left side also
includes Σ rho·|Q ∩ pq| over the segments. Points on ∂Q count. Contacts with margin zero are
supported when they happen at the endpoint of a u-bin.

## How to run

```bash
python check.py examples/n2_centroid.json --n 2              # D3 symmetry, root grid 4x4
python check.py cert.json --root 4 --max-depth 40 --jobs 8 --u-breaks "1/3,2-sqrt3"
python -m pytest -q tests                                     # needs pytest
```

The certificate format is `{"L": "2+2/3*sqrt3", "symmetry": "D3"|"none", "points": [{"x", "y", "w"}]}`,
with optional `pairs`, `features` and `segments: [{"p": {"x", "y"}, "q": {"x", "y"}, "rho"}]`.
L and the coordinates are `a` or `a+b*sqrt3` with rational `a, b`. The weights are rationals.
The JSON summary contains the sha256 of the certificate, the exact total weight, the leaf counts,
the uncertified boxes (the first 200 are listed), the depth and the time.
Only the standard library is used; Python 3.10+.

Files: `q3.py` (the field Q(√3)), `poly.py` (polynomials and Bernstein tests), `check.py` (CLI and
subdivision), `seg_probe.py` (float sanity probe for points + segments), `tests/`.

## Why each accepted step is sound

Everything accepted is decided in exact arithmetic. Floats only choose which proof to attempt:
which points, which third constraint, which split axis. A wrong float guess costs time, never
soundness.

1. **Exact field.** A `Q3` is a + b√3 with `Fraction` a, b. When a and b have opposite signs, the sign
   of a + b√3 is the sign of a² − 3b², which is never 0 because √3 is irrational. Every `<`, `<=`
   and `== 0` in the checker goes through this.

2. **Angles.** θ = 2 arctan u, so cos θ = (1−u²)/D and sin θ = 2u/D with D = 1+u² > 0. The square has
   period π/2, so u ∈ [0,1] covers every angle.
   - With `D3`, the checker first verifies exactly that the weighted set is invariant under the
     rotation by 2π/3 about the centroid and under x ↦ L−x. These two maps generate the symmetry
     group of T_L.
   - Both maps preserve T_L and (as just checked) the weighted set, so the capture sum
     of Q equals that of its image. On angles the maps act as θ ↦ θ + π/6 and θ ↦ −θ (mod π/2),
     so every square is equivalent to one with θ ∈ [0, π/12].
   - The checker proves θ(U) > π/12 exactly: with c = (1−U²)/(1+U²) ≥ 0, it checks
     c² < (2+√3)/4 = cos²(π/12).
   - The root u-bins for `none` are cut at u = 0, 2−√3, √3/3, 1 (θ = 0, π/6, π/3, π/2). These are
     exactly the angles where a side of T_L is parallel to a side of the square.

3. **Admissibility as half-planes.** Q ⊆ T_L iff its 4 vertices lie in T_L. For each side k and
   each vertex σ this gives n_k·c ≤ b_k − n_k·R_θσ. Multiplied by D, the right-hand side is O(u)/D
   with O a polynomial of degree ≤ 2 over Q(√3). The normal n_k does not depend on θ.
   The box [x0,x1]×[y0,y1] adds 4 more half-planes, with offsets x1·D etc. So for each fixed u the
   admissible centres in the box form a polygon P_u, bounded because it sits inside the rectangle.

4. **Dropping constraints (exact).** A half-plane is dropped only if an exact Bernstein test shows
   that the rest of the system already implies it, for the whole bin:
   - a parallel constraint with the same normal is at least as tight (O_i ≤ O_j), or
   - the whole rectangle lies inside it: O(u) − max_corner(n·corner)·D ≥ 0.

   Either way P_u is unchanged. A box is **EMPTY** at once if all 4 corners strictly violate one
   constraint for every u.

5. **Vertices.** P_u is a compact convex polygon, so if it is non-empty it is the convex hull of its
   extreme points. Each extreme point has two linearly independent active constraints, so it is
   V_ij(u) = (X_ij(u), Y_ij(u))/D for some non-parallel pair (i, j) (Cramer's rule, exact).
   - A pair is discarded (**infeasible**) only when some third constraint m satisfies
     n_m·(X,Y) − O_m > 0 on the bin, proved with all Bernstein coefficients > 0. Then V_ij(u) ∉ P_u
     for every u.
   - If every pair is discarded, P_u has no extreme point for any u, so it is empty: **EMPTY**.

6. **Capture.** p ∈ Q(c,θ) iff |(p−c)·e_k| ≤ ½ for e1 = (1−u², 2u)/D and e2 = (−2u, 1−u²)/D.
   This set of c is convex, so if every remaining V_ij(u) satisfies it for all u in the bin, then
   so does all of P_u. Multiplied by D² > 0, each of the 4 conditions becomes a polynomial of
   degree ≤ 4 that must be ≥ 0. It is proved by exact Bernstein coefficients on [u0,u1]. The
   endpoints may be in Q(√3). De Casteljau halving is allowed up to 12 times.
   - Bernstein coefficients bound the polynomial from below on the interval.
   - The first and last coefficients are the endpoint values, so a margin-zero contact at a bin
     endpoint gives a coefficient exactly 0, and that is accepted.
   - A box is **COVER** when points proved captured on it have exact total weight ≥ 1.

6a. **Lemma P (chord pairs).** A certificate may list `pairs` [i, j] of its points. The checker
   verifies exactly that |p_j − p_i|² = 1. Let d = p_j − p_i and write p = p_i, q = p + d.
   - **Claim.** Fix an axis k with d·e_k ≠ 0, let j be the other axis, and put
     t_± = ((c − p)·e_k ± ½)/(d·e_k). Suppose both points p + t_± d lie on the corresponding edges,
     that is |(p + t_± d − c)·e_j| ≤ ½. Then the chord of Q along the line p + t d is
     [min t_±, max t_±]; its length is 1/|d·e_k| ≥ 1.
   - If this chord also meets [0, 1] (min t_± ≤ 1 and max t_± ≥ 0), it contains t = 0 or t = 1.
     So Q contains p or q.
   - For fixed u all these conditions are linear in c, so the vertex argument of step 6 applies.
     Multiplied by the positive factors D, D² and σ(d·e_k), each condition becomes a polynomial of
     degree ≤ 6 that must be ≥ 0 on the bin.
   - The sign σ of d·e_k must be proved constant on the bin: σ·(d·E_k) > 0, with all Bernstein
     coefficients > 0.
   - When the lemma holds on a box, the capture sum is at least min(w_p, w_q). No point is counted
     twice in the COVER sum: individually captured points and pair members are kept disjoint.
   - This handles the margin-zero families in which a pose captures one of two points at unit
     distance, and which of the two switches inside the box. An example is the middle square of the
     n = 4 row, where both points sit on its two vertical edges.

6b. **Segment masses.** A certificate may list `segments` {p, q, rho}: mass of density rho ≥ 0 spread
   along the closed segment pq. The checker verifies exactly that |q − p|² = 1 (unit segments only)
   and rho ≥ 0. A square Q captures rho·|Q ∩ pq|. The budget adds Σ rho·1. This is valid for
   pairwise disjoint closed squares (which centre scaling produces): their intersections with a
   segment are disjoint up to endpoints. With `D3`, the multiset of segments (unordered endpoint
   pair, rho) must be invariant under both generators, exactly like the points.
   - **Claim (vertices suffice).** Write σ = p + t d, t ∈ [0, 1], d = q − p. Fix θ. For each axis
     e_k with d·e_k ≠ 0, the slab |(p + t d − c)·e_k| ≤ ½ is an interval of t with endpoints affine
     in c. So the lower end a(c) = max(lower endpoints) is convex in c, and the upper end
     b(c) = min(upper endpoints) is concave. (An axis with d·e_k = 0 gives no constraint on t, but
     it restricts c to a strip.) The intersection is [max(a, 0), min(b, 1)], with length
     g(c) = min(b, 1) − max(a, 0), which is concave in c. Let K be the set of c (in the strip, if
     any) where g(c) ≥ 0. It is convex. If every vertex of the convex polygon P_θ has length
     ≥ lmin > 0, all vertices lie in K. Then P_θ ⊆ K, and the concave g attains its minimum over
     P_θ at a vertex. So the length is ≥ lmin on all of P_θ.
   - **Exact vertex proof.** At a vertex V(u) = (X, Y)/D, put N_k = (X,Y)·E_k − p·(D E_k)
     (= D² (V − p)·e_k) and M_k = d·E_k. The slab of axis k is
     −D²/2 ≤ N_k − t·D·M_k ≤ D²/2. This is linear in t and needs no sign of M_k.
     - Floats choose an active candidate for each end: t0 is 0 or the lower slab end
       (s N_k − D²/2)/(s D M_k) of some axis k with sign s, plus a rational slack δ0 ≥ 0;
       t1 is 1 or an upper end (s N_k + D²/2)/(s D M_k), minus δ1 ≥ 0.
     - First s·M_k > 0 is proved strictly on the u-interval, so the denominators are positive.
     - Then, multiplied by the positive denominators, these polynomials in u (degree ≤ 8) are proved
       ≥ 0 with exact Bernstein coefficients: t0 ≥ 0; t1 ≤ 1; both slab inequalities for both axes
       at t = t0 and at t = t1; and t1 − t0 ≥ lmin.
     - The slab and [0,1] conditions are linear in t, so they hold on all of [t0, t1].
       Hence [t0, t1] ⊆ Q ∩ σ in the t-parameter, and the length (|d| = 1) is ≥ t1 − t0 ≥ lmin.
       This is the same as "chosen lower ≥ every other lower candidate (including 0), chosen upper
       ≤ every other upper candidate (including 1)", but stated without dividing by M_k, so an axis
       whose d·e_k vanishes in the bin is fine.
   - The vertex candidates are the non-infeasible pairs V_ij of step 5, as for capture. A wrong float
     choice only makes the proof fail. If no choice works on the u-interval, it is halved, up to 3
     times, and each half is proved with its own choice. Each vertex has its own choice. The
     slacks δ handle the sub-interval where the active end switches.
   - **Choice of lmin.** The candidates are tried in order, and the first one that is proved for every
     vertex is used:
     1. 1, if the float minimum length (over the vertices and 9 sample angles) is > 1 − 10⁻⁹;
     2. the float minimum snapped to a fraction with denominator ≤ 1000, if it is within 10⁻⁹;
     3. the float minimum minus 10⁻⁶, rounded down to a multiple of 2⁻²⁰;
     4. half of that.

     Otherwise the segment gets credit 0, which is always sound. Each vertex proof tries the
     slack-free choice (δ0 = δ1 = 0) first. The snap steps are needed for margin-zero certificates,
     where a square stands exactly on a unit segment (length exactly 1, total capture exactly 1).
     Step 3 is a ladder: the float minimum minus 10⁻⁶, 10⁻⁵, 10⁻⁴, 10⁻³ and 10⁻², each rounded down
     to a multiple of 2⁻²⁰, tried in that order. Step 4 is half of the first ladder value.
   - **Joint credit (concavity of the sum).** Summing per-segment minima loses whatever one segment
     gains when another loses (for example, a square shifted along two collinear unit segments).
     The checker therefore also proves a bound on the minimum of the sum:
     - **Lower bounds per vertex.** For each segment i and each vertex candidate v (each pair not
       proved infeasible), it proves c_{i,v} with len_i(V_v(u)) ≥ c_{i,v} for all u in the bin. This
       uses the same exact vertex proof and the same candidate list (snap, ladder, half), started
       above the per-segment credit, so that c_{i,v} ≥ that credit.
     - **The set P.** P is the set of segments with c_{i,v} > 0 at every candidate.
     - **Concavity.** Fix u. The actual extreme points of P_u are among the candidates. So for
       i ∈ P every extreme point has positive length, P_u ⊆ K_i, and g_i is concave on P_u.
       Hence S = Σ_{i∈P} rho_i g_i is concave on P_u, and its minimum is at an extreme point, which
       is some V_v(u).
     - **Credit.** So the credit is J = min_v Σ_{i∈P} rho_i c_{i,v}, plus Σ_{i∉P} rho_i·(per-segment
       credit), which is a constant lower bound valid on the whole box.
     - **Non-vertex candidates.** Some candidates are not extreme points of P_u for some u. Including
       them in the min only makes J smaller (more conservative). The positivity c_{i,v} > 0 is also
       required at them, which may only shrink P. Both effects are sound.
     - **When it runs.** COVER uses points + features + pairs + max(joint credit, sum of
       per-segment credits). The joint computation runs only when the float joint estimate
       (min over candidates of Σ rho_i·(min over samples of the float length)) clears the deficit
       and beats the per-segment credits. It stops early when the proved sum at some candidate is
       already below the deficit. The joint credit is at most that sum, because c_{i,v} ≥ the
       per-segment credit.
   - **COVER** with segments: the sum of individually captured point weights, plus the features and
     Lemma P pairs as before, plus Σ rho·lmin over the segments (or the joint credit above when it
     is larger). Segments are separate mass, so
     there is no double counting with the points. Segment credits are computed only when the float
     estimate of the points, features and pairs is < 1. The float screen counts the better of
     the sum of per-segment float minima and the joint float estimate.
   - `seg_probe.py cert.json` samples random admissible poses in floats and reports the minimum of
     points + Σ rho·length. It is a sanity check only, not a proof.

7. **Coverage of all poses.** The root boxes cover [0, Lx]×[0, Ly] ⊇ T_L, which contains every
   admissible centre; Lx and Ly are rational and checked exactly against L and L√3/2. The root u-bins
   cover [0,1], or [0,U] with D3. Splitting halves one side; the u midpoint is exact in Q(√3).
   Every leaf is EMPTY, COVER or UNCERTIFIED, and the verdict is "verified" only with 0
   UNCERTIFIED leaves.

## Performance notes

- Offsets, pair vertices (X, Y, and their products with E1, E2) and point terms are polynomials in
  u, cached per pair or per point.
- Bernstein vectors are linear in the polynomial. Per u-interval the checker caches the Bernstein
  vectors of the monomials, of D²/2 and of each point term, so a capture test costs only a few
  vector additions.
- Float pre-filters (9 sample angles) discard points and third constraints that cannot work
  before any exact test runs.

## Known limitations

- A margin-zero contact strictly inside a u-bin cannot be certified: it is a double zero. The
  breakpoint must be given (defaults, or `--u-breaks`). `poly.nonneg_on(..., snap=True)` can split at
  an exactly verified rational root, but the box checker does not use this.
- If a dyadic grid line passes very close to a contact vertex at a bin endpoint, the subdivision
  gets deep but stays finite. For n = 2 with `none` and `--root 4`, one corner goes to depth 31.
  Use `--max-depth` ≥ 35 for margin-zero certificates.
- Only the first 200 uncertified boxes are listed in the output; all of them are counted.
- Segments must have length exactly 1. A zero-margin segment credit is only possible when the exact
  minimum is 1 or a fraction with denominator ≤ 1000 (the snap step). Otherwise the credit is at
  most the float minimum minus 10⁻⁶.
- Segment tests are degree-8 polynomials and cost more than point tests. They run only on boxes
  where the points, features and pairs do not already reach 1 (by the float estimate).
