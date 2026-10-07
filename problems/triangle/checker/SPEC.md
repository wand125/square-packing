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
