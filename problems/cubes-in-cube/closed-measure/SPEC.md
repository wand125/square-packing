# SPEC: rigorous checkers for a closed measure (s₃(25) = s₃(26) = 3), two systems

This is the specification both checkers in this folder were written from, as it stood when they ran, lightly edited for
publication (internal file paths, names and the launch logistics are removed; nothing about the method is changed).
"The s₃(9) checkers" means `../checker/` and `../checker2/`, and "PROOF" means `../PROOF.md`.

## 1. Claim

Let μ be the measure in `measure.json` (§2) and σ a rational scale given on the command line (default σ = 27/20).

**Main lemma.** σ·μ(Q) ≥ 1 for every closed unit cube Q ⊆ [0, 3]³. Points, lines and planes on the boundary of Q count.

**Theorem.** Let n_claim = ⌊σ·μ([0,3]³)⌋ + 1. For every n ≥ n_claim, s₃(n) ≥ 3; hence s₃(n) = 3 for n_claim ≤ n ≤ 27
(27 grid cubes give s₃(n) ≤ 3).
For v5b, μ([0,3]³) = 18.45352243946387…, so σ = 27/20 gives σ·μ = 24.9123 < 25 and s₃(25) = s₃(26) = 3.
(s₃(27) = 3 is trivial by volume.)

*Proof of the theorem from the lemma.* Suppose n unit cubes fit in [0, L]³, L < 3. Scaling the centres by 3/L (PROOF §1,
same argument with s = 3) gives n pairwise disjoint closed unit cubes in [0,3]³. μ is a finite Borel measure, so
n ≤ Σ σμ(Q_i) ≤ σμ([0,3]³) < n. ∎

σ is a parameter so that the same checker can later try smaller σ for more n (σ < 25/T gives n ≥ 25, σ < 24/T gives
n ≥ 24, …, T = μ([0,3]³)). The receipt records σ exactly and the theorem is stated from it.

## 2. The measure (input data, checked by the program)

`measure.json` (v5b export, sha256 `565dbf5dd0059aa90929e4151d85fafdeef002a1b9e9aaf83f2e6243b2d393e0`; the published
copy will be a renamed byte-identical file). Fields used: `side` = 3, `closed` = true, `pieces`: a list of
`{type: point|line|plane, bounds: [[lo, hi] × 3], density}`. Only pieces with density > 0 are used.

- **Coordinates.** Every bound is a multiple of 1/10 in [0, 3]. The program converts each bound to an integer number of
  tenths (it must reject the file if `round(10·x)` differs from 10·x by more than 1e-9 or if a value is outside [0, 30]).
  From here on all piece geometry is exact: a coordinate is the rational k/10.
- **Densities.** The JSON number is parsed to the nearest double, and **that double is the exact density** ρ (a dyadic
  rational). Both the Rust parser and the Python validator must use correctly rounded decimal → double parsing (Rust
  `str::parse::<f64>` and Python `float` are correctly rounded); the validator checks that the two agree bit for bit. μ = Σ_pieces ρ_p · H^k restricted to the closed box of piece p (k = 0, 1, 2 its dimension: the number of axes
  with lo < hi). There is no volume piece; the program rejects k = 3 with ρ > 0.
- **Checks the program performs (exact, integer/double comparisons only):**
  1. **Symmetry.** For each of the 48 symmetries g of [0,3]³ (permutations of axes composed with x_w ↦ 30 − x_w in tenths),
     the multiset of (type, bounds, ρ) of the positive pieces is mapped to itself. (Needed by the domain reduction §3.)
  2. **Pair partners (§4.3).** For every positive piece p and every axis w along which p is degenerate (lo_w = hi_w), let
     p + e_w be p translated by +1 (10 tenths) along w. Record the partner if a positive piece with exactly those bounds
     and **the same double ρ** exists. Expected for v5b: planes at x_w = 1 ↔ x_w = 2; lines with a degenerate coordinate 1
     ↔ 2 (the other degenerate coordinate is 1.5, which has no partner); points (1, 1.5, 1.5) ↔ (2, 1.5, 1.5) and
     (0.9, 0.9, 1) ↔ (0.9, 0.9, 2) up to symmetry; points (0.9, 1.5, 1.5) unpaired. The program prints the counts.
     A piece has at most one partner per axis; a positive piece in v5b is paired along at most one axis (the program
     checks this; if not, it uses the axis listed first and says so in the receipt).
  3. **Total.** T = Σ ρ_p · |p| computed with outward-rounded intervals (|p| = product of the free side lengths in tenths
     /10^k), and the program certifies σ·T_hi < n_claim, where n_claim = ⌊σ·T_lo⌋ + 1, both printed in the receipt.
     A small Python validator recomputes T with `fractions.Fraction` (exact) as a cross-check.
  4. **v5b facts used only to choose the rules, not for soundness** (printed, not required): no positive line lies on a
     line with two integer coordinates, and no positive point has three integer coordinates (so no piece sits on an
     edge or vertex of a grid-aligned cube; this is why a second-order form is not needed here).

Measure summary (v5b): 36 points, 48 lines, 120 planes, 8 distinct densities; lines {x_a ∈ {1,2}, x_b = 1.5} on spans
of [0.5, 0.9], [1, 1.5] (and mirror); planes x_w ∈ {1, 2} on rectangles that are strips of width 0.1 next to the grid
lines (spans [0.9,1]/[2,2.1] × [0.5,0.9], [0.9,1], [1,1.5], …).

## 3. Pose domain

Same parametrisation and coverage arguments as the s₃(9) checkers, with s replaced by 3:
- pose (R, c), Q = {c + R t : ‖t‖_∞ ≤ ½}, t_i(y) = a_i·(y − c) with a_i the columns of R;
- h_w = ½ Σ_j |R_wj|, c_w = h_w + u_w(3 − 2h_w), u ∈ [0,1]³ (exactly the feasible centres; Q ⊆ [0,3]³ holds as a
  mathematical identity of the parametrisation, which §4.2 uses);
- **System 1:** projective quaternion (1, x, y, z), reduction by the 24 cube rotations × 48 container symmetries
  (valid because μ is invariant under the 48, check 1), root box [0, a]² × [−a, a] × [0, ½] × [0, 1]², `outside`
  boxes only by strict inequalities, ties kept. Forked from `../checker/`; only the closing rules are replaced.
- **System 2:** ZYZ Euler angles, 32-fold reduction (8 reflections x_w ↦ 3 − x_w, which preserve μ by check 1, and a
  quarter turn about one cube axis), root [0, 2π] × [0, π] × [0, π/2] × [0, ½]³. Forked from `../checker2/`; only the
  closing rules are replaced. Written from this SPEC without reading system 1's new code (§8).

## 4. The lower bound for a pose box B

For a box B of the parameter domain, the program computes a number L(B) such that **σ·μ(Q) ≥ L(B) for every pose in B**,
and closes B if L(B) ≥ 1 (lower endpoint of an outward-rounded interval). Otherwise B is bisected (as in the s₃(9) checkers). At the
maximum depth B is recorded as unresolved.

### 4.1 Cells
A cell is a closed sub-box of a positive piece obtained by dyadic bisection of the piece's free sides (points: the point;
lines: sub-segments; planes: sub-rectangles). For a cell C and the box B, the program evaluates the predicates below for
all y ∈ C and all poses in B at once, by interval arithmetic in which y ranges over the cell as an interval vector.
Implementation note: every quantity used below is affine in y; evaluate it as (interval coefficient vector)·(y − c) so
that each coordinate of y appears once.

Notation on the box: a_i = column i of R, T_i(y) = a_i·(y − c), d = (R_w0, R_w1, R_w2) (the direction e_w in cube
coordinates, so T(y + s e_w) = T(y) + s d).

### 4.2 Rules for one cell (C counts with ρ|C| if any rule holds)
- **S (inside).** |T_i(y)| ≤ ½ for i = 0, 1, 2.
- **F (centre rule, Lemma F, PROOF §2, already proved there).** |y_w − c_w| ≤ 1 − h_w for every world axis w.
  (Use the collected form of the s₃(9) checkers so that wall contacts keep exact zero slack.)
- **W (wall, chord form).** Let w be an axis with C degenerate along w (lo_w = hi_w = q_w) and q_w ≤ 1 (lower wall)
  or q_w ≥ 2 (upper wall). Suppose for some cube axis k that **d_k ≠ 0 with a fixed sign ς on all of B** (the interval
  of d_k excludes 0), and:
  - **full chord:** |d_k T_j(y) − d_j T_k(y)| + ½|d_j| ≤ ½|d_k| for both j ≠ k;
  - lower wall: ς T_k(y) ≥ −½; upper wall: ς T_k(y) ≤ ½.
  Then y ∈ Q.
  *Proof.* Full chord ⇔ the line y + s e_w meets the planes T_k = ±½ inside the closed faces (multiply T_j + s± d_j by d_k
  with s± = (±½ − T_k)/d_k; the condition for both signs is the stated one). So I = {s : y + s e_w ∈ Q} = [s_min, s_max]
  with s_max − s_min = 1/|d_k| ≥ 1. Lower wall: Q ⊆ {x_w ≥ 0}, so q_w + s_min ≥ 0; ς T_k ≥ −½ ⇔ s_min ≤ 0; then
  s_max ≥ s_min + 1 ≥ 1 − q_w ≥ 0, so 0 ∈ I. Upper wall: mirror. ∎
- **M (wall lemma, generalised).** PROOF §3 with the hypothesis p_w = 1 replaced by y_w ≤ 1 (the proof only uses
  y_w − c_w ≤ 1 − h_w); mirror for y_w ≥ 2. Optional: implement if cheap; it is a second route to the same face points.

### 4.3 Rules for a pair of cells (C on piece p, C + e_w on its partner, same ρ)
- **P (pair, chord form).** For some k with **d_k ≠ 0 and a fixed sign ς on all of B**: full chord at y (as in W) and
  ς T_k(y) ≤ ½ and ς T_k(y + e_w) ≥ −½. Then y ∈ Q or y + e_w ∈ Q.
  *Proof.* As in W, I = [s_min, s_max], length ≥ 1. ς T_k(y) ≤ ½ ⇔ s_max ≥ 0; ς T_k(y + e_w) ≥ −½ ⇔ s_min ≤ 1. A closed
  interval of length ≥ 1 meeting [0,1] contains 0 or 1. ∎
- **P′ (pair, slab form; PROOF §4 with d = e_w).** For some cube axis i and sign ς: |T_j(y)| ≤ ½ and |T_j(y+e_w)| ≤ ½
  for both j ≠ i, ς T_i(y) ≤ ½ and ς T_i(y + e_w) ≥ −½. (|a_i·e_w| ≤ 1 holds since R is orthogonal.)
- **Pair contribution.** If P or P′ holds on C, then μ_p(Q ∩ C) + μ_partner(Q ∩ (C + e_w)) ≥ ρ|C| (for each y one of the two
  translates is in Q, and the two cells have the same ρ). Combined with singles:
  value(C) = max( ρ|C|·([S∨F∨W∨M on C] + [S∨F∨W∨M on C+e_w]), ρ|C|·[P∨P′ on C], Σ_children value(child) ).
  Each pair is counted once: the program iterates over the pairs (p, partner) with p the lower piece (x_w = 1 side), and
  over unpaired pieces separately. No piece takes part in two pairs (check 2).

### 4.4 Assembly and refinement
L(B) = σ · Σ (values of all positive pieces, pairs counted once). The program refines cells adaptively per box: start
with whole pieces, split a cell that is not certified up to `--cell-depth` levels (default 6 per free side; planes split
the longer side first). Stop as soon as the running lower bound reaches 1 (early exit). The cell refinement is part of the
computation of L(B) and does not enter the leaf digest except through the closing rule name and the depth.
Leaf rule names: `bound` (closed by L(B) ≥ 1), `outside`, `unresolved`. The receipt also counts which lemma types
contributed (S, F, W, M, P, P′) summed over closed leaves, for diagnostics only.

## 5. Arithmetic
As in the s₃(9) checkers: every interval operation rounds outward by one representable step; constants (k/10, σ, π, 1/√2 where used)
have interval enclosures; no epsilon in any closing inequality. Densities are exact doubles; ρ|C| and the sum are formed
in outward-rounded intervals.

## 6. Search, receipts, guards
- Deterministic scheduling and the chained leaf digest of the s₃(9) checkers (system 1 and 2 keep their own formats). The leaf record adds
  nothing new except the rule name `bound`.
- Checkpoint and `--resume` as before. A per-box `--max-depth` and `--cell-depth` are recorded.
- Receipt fields (both systems): status, pending, unresolved, boxes, max depth, leaves by rule, `leaf_chain`, seconds,
  threads, σ (as p/q), T (interval), n_claim, measure sha256, the check-1/2 results (counts), the sha256 of every source
  file, rustc version, the command line.
- **Diagnostics for the trial:** `--unresolved-list FILE` writes each unresolved box with its L(B) and the per-piece-type
  contributions; `--sample-box JSON` prints L(B) and the contributions for one box (used to compare with the floating
  ideal bound of a floating LP prototype, not included).
- **Mac guard:** on macOS refuse more than 2 threads and more than 1200 seconds unless `--server` (and refuse `--server`
  on macOS), as in `../checker2/`.
- `--output` must be inside the checker's directory.

## 7. Validation (not part of the proof)
1. **Soundness of L(B):** for 20,000 random boxes (a quarter at a wall, a quarter around the aligned coincidence families
   u_w ∈ {0, 0.2, 0.25, 0.45, 0.5}, rotations about each axis), sample 50 poses per box and check
   σ·μ_closed(Q) ≥ L(B) − 1e-12 (the 1e-12 is a tolerance of this floating sanity test only, not part of the
   proof) with an independent floating closed evaluator (semantics: a piece counts with the measure of its intersection with the closed cube). 0 failures required.
2. **Each rule alone:** S, F, W, M, P, P′ on random cells and boxes, checking the conclusion at sampled (pose, y).
3. **Symmetry:** L at a pose and at its 48 images (system 1) / 8 reflections (system 2) agree to 1e-9 on degenerate boxes.
4. **Data checks:** a file with one density changed, one bound moved by 0.1, or a piece removed must be rejected by check 1.
5. Determinism over 1 and 2 threads and over a resume.

## 8. Independence of system 2
System 2 is written from this SPEC and the `../checker2/` base only (a separate implementation run whose input was this
SPEC; it did not read `checker1/`). Differences required: Euler angles, 32-fold reduction, its own interval type and sin/cos (inherited
from `../checker2/`), its own cell scheme: **planes are handled by exact polygon clipping**, not by dyadic cells — for each
rule, the set of y on the piece rectangle where the (affine) conditions hold for all poses of B is approximated from
inside by intersecting half-planes with interval coefficients, taking the inner (pessimistic) side of each; the area of
the resulting convex polygon (for S, W, P) is a valid lower bound. The inner side of an affine inequality a·y ≤ b with
interval coefficients is implemented as the intersection of the half-planes over all corner combinations of the
coefficient intervals ({y : max_a a·y ≤ min b} is exactly that intersection, y ranging over the rectangle); the polygon
area is rounded down. Singles and pairs combine by the same max as in §4.3. Lines likewise by interval clipping of the
segment.


## 9. Amendment 1 (2026-10-15, after the first trials): mean-value enclosures

### Why
Both systems work and validate, but the trees are far too large. Knuth estimates (random probes with each checker's own
split rule, σ = 27/20, a Knuth-style tree-size estimator, not included): system 1 ≈ 3·10⁹ nodes (±2.8·10⁹; ≈ 2.7·10⁴ thread-hours at its batch
speed), system 2 ≈ 1.2·10¹² nodes (median leaf depth 34). A diagnostic script (not included) compares, on random generic poses, system 2's
rigorous L(B) with the sampled ideal pair bound of the same box (angle width w, centre width w/4):

| w | rigorous L(B), 10 poses | ideal (sampled) | value at the box centre |
|---:|---|---|---|
| 0.08 | 0.00–0.06 | 1.37–3.25 | 1.71–3.85 |
| 0.04 | 0.00–1.41 | 1.51–3.44 | |
| 0.02 | 0.05–1.83 | 1.59–3.54 | |
| 0.01 | 0.56–2.83 | 1.65–3.76 | |
| 0.005 | 1.27–3.25 | 1.68–3.82 | |

So the loss is interval overestimation (dependency through R, h and c), not the measure: the ideal closes boxes 8–16
times wider in every angle. The rules of §4 stay exactly as they are; only the enclosure of the quantities changes.

### Change (both systems; each implements it independently)
Every quantity Φ(p; y) used by a rule (T_i(y), T_i(y + e_w), the chord quantity d_k T_j − d_j T_k, d_k, |d_j|, the
centre-rule quantity, the M-rule quantities) is enclosed by

  Φ(p; y) ∈ [ Φ(m; y₀) + Σ_k G_k · [p_k − m_k] + Σ_a A_a · [y_a − y₀_a] ] ∩ naive(Φ),

where p are the six box parameters, m their midpoints (representable), y₀ the cell centre, G_k an interval enclosure of
∂Φ/∂p_k over the whole box × cell, A_a an enclosure of ∂Φ/∂y_a over the box (Φ is affine in y, so A_a is exact
in y), and naive(Φ) the current enclosure. Φ(m; y₀) is evaluated with outward rounding at the point m (a degenerate
interval).
- **Soundness.** Mean value inequality along the segment from (m, y₀) to (p, y): Φ is Lipschitz and piecewise smooth
  in p; where it is not differentiable (only through h_w = ½ Σ_j |R_wj|), use the enclosure ∂|x| ∈ sign(x)·∂x when the
  interval of x excludes 0 and [−1, 1]·∂x otherwise (Clarke generalised gradient; the mean value inequality holds with
  it). Intersecting with the naive enclosure is valid because both contain the true range.
- **Implementation.** A forward-mode interval dual type (value interval + 6 partial-derivative intervals), used twice:
  at the midpoint for the value, and over the box for the derivatives. Rotation derivatives: system 1 from the
  quaternion formula R = N(q)/(1 + |v|²) (quotient rule), system 2 from ∂Rz, ∂Ry (analytic). The centre c_w = h_w +
  u_w(3 − 2h_w) depends on R through h and on u linearly.
- **Optional second-order term** is not added now.
- **Leaf records, digest, receipts:** unchanged in form; the receipt gets `enclosure: "mean-value-1"`. The trial runs
  before this amendment were diagnostics and are discarded; every full run uses the amended version from the start.

### Acceptance (before any full run)
1. All §7 validation tests pass again (0 failures), plus a test that the mean-value enclosure contains 10,000 sampled
   values of each quantity on random boxes.
2. The same diagnostic on the same 10 poses: rigorous L(B) at w = 0.04 should be within about 0.3 of the ideal.
3. New tree-size estimates for both systems.

### Review of amendment 1 (2026-10-15): sound
Φ is locally Lipschitz in p (the only non-smoothness is |R_wj| inside h_w; R is C¹ in p), so Lebourg's mean value
theorem gives Φ(p) − Φ(m) = ⟨ζ, p − m⟩ with ζ ∈ ∂_C Φ(ξ), ξ on the segment; Clarke's chain, sum and product rules (with
inclusion) and the stated enclosure of ∂|x| give G_k ⊇ the k-th components of ∂_C Φ over the box. Φ is affine in y, so
Φ(p; y) = [Φ(m; y₀) + Σ G_k(p_k − m_k)] + Σ_a A_a(p)(y_a − y₀_a); enclosing G over box × cell is a superset. Cautions,
**both required**: (1) keep the naive enclosure in its collected form (§4.2 F note, wall zero slack u_w = 0 ⇒ c_w = h_w)
as the intersection partner, since a midpoint-centred form does not see the exact wall contact; (2) Φ(m; y₀) is computed as
a degenerate interval at a representable midpoint with outward rounding, and [p_k − m_k] as outward-rounded differences.

## 10. Amendment 2 (2026-10-15): system 2 uses all 48 container symmetries, on the centre only

### Why
After amendment 1, Knuth estimates at σ = 27/20: system 1 (cell depth 3) 1.8–2.1·10⁷ nodes (≈ 16–18 thread-hours at
batch speed); system 2 1.3–1.7·10⁹ nodes (≈ 2,500–3,500 thread-hours). System 2 searches a domain 36 times larger
(32-fold reduction against 1,152). Most of that factor can be removed without touching the rotation parametrisation.

### Change (system 2 only)
- The 48 symmetries g of [0,3]³ (axis permutations composed with reflections x_w ↦ 3 − x_w) act on a pose by
  R ↦ G R (G the signed permutation matrix; if det(G R) = −1, negate one column, which changes neither the cube nor any
  h_w) and c ↦ g(c). In the centre parameters they act on u alone, as the symmetries of the unit cube [0,1]³ about its
  centre: permute the coordinates of u, and u_w ↦ 1 − u_w for reflected axes (h is permuted with the rows and is
  unchanged by reflections). μ is invariant under all 48 (check 1), so μ(Q) is constant on orbits.
- Every u ∈ [0,1]³ has an image in the closed simplex Δ = {0 ≤ u_0 ≤ u_1 ≤ u_2 ≤ ½} (reflect each coordinate into
  [0, ½], then sort). The rotation part is unrestricted (it moves with the group element), so the domain becomes
  {ZYZ angles as now} × Δ, still reduced also by the quarter turn about the cube's third axis (γ ∈ [0, π/2]).
- Root box unchanged ([0, ½]³ for u). New rule `outside`: a box is outside if u_0.lo > u_1.hi or u_1.lo > u_2.hi
  (strict inequalities only; ties kept). Outside leaves are counted in the receipt; closed volume is measured against
  the root box as in system 1.
- System 1 is unchanged (it reduces by sorting the quaternion and u_0 ≤ ½, a different fundamental domain).
- Independence: system 2 still uses different rotation coordinates, a different fundamental domain, its own
  intervals, its own mean-value enclosures and polygon clipping.

### Acceptance
1. Validation as before (0 failures), plus: for 10,000 random poses, the orbit representative computed by the program
   lies in the domain and has the same independent floating μ(Q) as the original to 1e-9 (test tolerance only).
2. A new tree-size estimate for system 2.

### Review of amendment 2 (2026-10-15): sound
A world permutation P sends (R, u) to (PR, Pu) (h is permuted with the rows); a reflection x_w ↦ 3 − x_w sends c_w to
3 − c_w = h_w + (1 − u_w)(3 − 2h_w), so u_w ↦ 1 − u_w with h unchanged (row w negated, |R_wj| unchanged); the determinant
is restored by negating one column, a right action by a cube reflection that leaves Q, c, h and u unchanged. Hence every
pose has an image under the 48 (μ-invariant by check 1) with u ∈ Δ: reflect every coordinate with u_w > ½, then sort.
The quarter turn is a right action R ↦ R·S, which commutes with the left action of the 48 and leaves c, h and u
unchanged, so Δ × {γ ∈ [0, π/2]} is a valid closed fundamental region (ties kept; outside only by the strict
inequalities). **Required:** (1) the §7.3 symmetry test covers the 48 images including the u-sorting map, checking that L
agrees at a pose and at its canonical representative; (2) both receipts state their fundamental domain (system 2:
Δ × γ ∈ [0, π/2]; system 1: sorted quaternion × u_0 ≤ ½).


## 11. Amendment 3 (2026-10-19): splitting a system 2 run into shards (no change to the checker)

### Why
System 2 at σ = 27/20 commits a fixed batch of 4 boxes per round (deterministic leaf chain), so it uses at most 4 cores
whatever `--threads` says (measured 3.4 cores at `--threads 20`). At 2.4 % of the volume per day the run would
take 2 weeks to 2 months. Splitting the pending boxes over several runs is the only speed-up that keeps the checker,
its judging logic and its fingerprint unchanged.

### Change (outside the checker: `checker2/shard.py`)
- **Split.** Input: a copy of a checker2 `checkpoint.json` (the unsplit run continues; the copy is the proof's parent).
  Check volume conservation exactly (integers in units of 2⁻²⁵⁶ of the root, a box of depth d counts 2^(256−d)):
  Σ_d hist[d]·2^(256−d) + Σ_pending 2^(256−depth) = 2²⁵⁶ (for a re-split shard: = the shard's volume). Refuse if the parent
  has unresolved boxes. Distribute the pending boxes (their JSON text copied byte for byte) over N shards, largest
  volume first into the lightest shard. Each shard gets a checkpoint with the parent's fingerprint, depth cap and cell
  depth, its boxes, zeroed counters and an initial leaf chain sha256(parent chain | shard | name | sha256(boxes)); a copy
  is kept as `shard_init.json`. `manifest.json` records the parent's sha256, volume, fingerprint, caps, σ, chain, and per
  shard its box count, exact volume, sha256 of its boxes and of its initial checkpoint.
- **Run.** Each shard is an ordinary run of the unchanged binary with `--resume --output <shard dir>` (inside checker2).
  The fingerprint check of `--resume` makes a shard load only under the same sources and measure metadata (σ included).
- **Re-split.** A running shard may be stopped and its checkpoint split again (`<shard>/split/`); the merge then uses the
  sub-tree in place of that shard's own receipt.
- **Merge** (all must hold, else the merge fails and names the check):
  1. the parent checkpoint and every `shard_init.json` match the manifest hashes; fingerprints and caps agree everywhere;
  2. **partition:** the shards' initial box lists, as texts, are exactly the parent's pending list: no box twice, none
     missing, none foreign (multiset equality); no shard directory outside the manifest;
  3. each shard's final checkpoint has the manifest fingerprint and caps, and every box left in it lies inside one of the
     shard's initial boxes (catches a checkpoint copied from another shard);
  4. **volume:** for every node, closed leaves + pending = its initial volume, exactly; for the tree,
     parent leaves + Σ shard leaves = 2²⁵⁶;
  5. without `--partial`: every shard receipt is `complete` with pending 0 and unresolved 0, agrees with the final
     checkpoint (chain, boxes, histogram), states the manifest's σ, depth cap and cell depth, and its command line is a
     `--resume` run whose `--output` is that shard's directory; the top manifest's parent is the root.
  Output `merged_receipt.json`: summed counts, the exact closed volume, the list of chains (parent, then each shard) and
  their combined sha256, the tool's sha256.

### What the merge relies on
The same as one run: the binary's split of a box into two halves that are disjoint up to a shared face and cover it
(the histogram measure then adds up), and its leaf records. The merge adds no geometric judgement. As with one run without
`--keep-leaves`, the leaf chain of a shard is reported but cannot be replayed.

### Assumptions taken as for a single run (reviewed 2026-10-19: sound, with conditions 1–3, applied)
- The proof is item 4 of the merge: the root's volume is exhausted by leaves the checker closed, with nothing pending
  and nothing unresolved. The leaf chain is a mark of the run's integrity, not part of the proof; a shard's chain covers
  its own leaves, the parent's chain covers the leaves up to the checkpoint copy. That a shard starts from the parent's
  checkpoint is checked by item 2 and by the hashes of `shard_init.json`.
- The parent is a checkpoint of the unsplit run; trusting that run's internal state up to the checkpoint is the
  same trust as in any single run (system 2's independence is from system 1). Its writing binary is identified by the
  fingerprint (item 1), and the merge checks its volume conservation at that point (item 4).
- **Condition 1 (tree):** `merged_receipt.json` records the tree: the parent checkpoint's sha256 → each shard's
  `shard_init.json` sha256 → that shard's final checkpoint and receipt sha256 (or its own sub-tree). The parent
  checkpoint copies and every `shard_init.json` are kept in the bundle (they are small).
- **Condition 2 (binding to the parent):** a shard's initial leaf chain is sha256(parent checkpoint sha256 | parent chain |
  shard | name | sha256(boxes)), so the chain each shard receipt carries starts from its own parent and its own boxes;
  the merge recomputes it from the manifest. Negative controls: a shard from a split of another parent, as is, and with
  its start rewritten to claim this parent (then the partition check fails).
- **Condition 3 (provenance):** the merged receipt states "leaves up to the checkpoint X (sha256, its box count) are from
  the unsplit run that wrote it; after it, N shard runs of the same binary (fingerprint)".

### Acceptance (`checker2/test_shard.py`, log `checker2/test_shard.log`)
1. Positive: the deepest 12 pending boxes of a real σ = 27/20 checkpoint as a node, split into 3, one shard stopped after
   2 rounds and re-split into 2, all run to `complete` with the unchanged binary; merge (sub-tree mode) passes; the same
   merge without the test flag fails (not the root).
2. Real data: a checkpoint copy of the unsplit run (2026-10-19, 56 pending, 2.73 % closed) splits into 16 shards; partial merge passes; a
   shard loads and runs under the unchanged binary.
3. Negative controls, each must fail: a shard dropped; a stray shard directory; a box in two shards; a foreign box; an
   edited `shard_init.json`; an extra leaf claimed in the parent histogram; a changed fingerprint; a checkpoint and
   receipt swapped between shards; a checkpoint copied from another shard (partial); a receipt with unresolved 1; a
   receipt with another σ; a leaf removed from a completed shard (checkpoint and receipt edited to agree); a receipt
   without `--resume`; a shard of another parent (as is, and with its start rewritten to claim this parent).

