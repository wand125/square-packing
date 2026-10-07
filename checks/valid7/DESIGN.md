# Independent checker for Valid7 (draft design)

**Claim to check (Valid7).** For the mixed cover `mu` in `L4_k02_box7.txt` (s = 7), every closed unit square
`Q(c, t) = c + R_t [-1/2, 1/2]^2 ⊆ [0, 7]^2` has `mu(Q) >= 1`.

**Scope choices.** No D4 reduction of the cover (the whole centre domain and every angle are checked). Only the
square's own period `pi/2` is used: `t ∈ [-53.13°, 53.13°]` (more than one period), parametrised by
`u = tan(t/2) ∈ [-1/2, 1/2]`, so that the zero-margin angle `t = 0` is interior and the far end of the range has
margin (with `u ∈ [0, 1]` the end `t = 90°` is again zero-margin). The admissible width is `|cos t| + |sin t|`, `cos t = (1 - u^2)/(1 + u^2)`, `sin t = 2u/(1 + u^2)` (all rational at rational `u`).

## Step 0: structure of the cover (checked, `src/cover.py`)
800 segments, each of length 1/5, on 60 lines of the 1/5 grid (30 vertical, 30 horizontal); one polygon
`S = [9/5, 26/5]^2` with density 1 (Lebesgue). Exact total `5701378693611/125000000000 < 46`; D4-invariant as a
measure. No segment meets the open interior of `S`.

## Step 1: the angle 0 (and pi/2) by closure, not by enumeration
For `t ∈ (0, pi/2)` no segment is parallel to an edge of `Q`, so `mu(Q(c,t))` is **continuous** in `(c, t)`.
The set `{(c, t, p): p ∈ Q(c, t)}` is closed, so `mu(Q)` is upper semicontinuous everywhere. Every admissible pose
at `t = 0` is a limit of admissible poses with `t > 0` (the admissible centre set `[w/2, 7 - w/2]^2`,
`w = cos t + sin t`, varies continuously). Hence `mu >= 1` for `t ∈ (0, pi/2)` implies it at `t = 0`. An independent
exact enumeration at `t = 0` is kept only as a cross-check.

## Step 2: fixed angle = piecewise quadratic in the centre (`src/solver.py`)
**Lemma F1.** For `t` not a multiple of `pi/2`, `c -> mu(Q(c, t))` is continuous and is a polynomial of degree
<= 2 on every face of the arrangement of the lines (a) a vertex of `Q` on a line of the cover geometry (mass line,
polygon edge line) and (b) an edge of `Q` through a breakpoint (density change on a mass line, polygon vertex).
After multiplying by `1 + u^2` their coefficients are polynomials in `u` of degree <= 2.

**Lemma F2 (no interior minima).** On a face, the polygon term `g(c) = area(Q(c) ∩ S)` is identically 0 or
positive, and `sqrt(g)` is concave where positive (Brunn-Minkowski for the translates of two convex bodies). So
`Hess g = 2 ∇h ∇h^T + 2h Hess h` (`h = sqrt g`) has at most one positive eigenvalue; the segment part is affine.
A quadratic with at most one positive eigenvalue attains its minimum over a closed convex face on the boundary.
Hence the minimum over a centre box is at a vertex of the arrangement (box sides and the admissibility lines
included) or at the 1-D critical point of an edge between consecutive vertices. No face enumeration is needed.

The same code runs on `u` a `Fraction` (exact fixed-angle solver) or `u` an `RF` (Step 3, Tier B).

## Step 3: two tiers over (centre, u)
- **Tier A (`src/tier_a.py`, `src/run_a.py`): box core bound.** Every square of a pose box contains the core
  (Lemma A1: inner rational polygon of the angular core, edges at both ends plus the chord through the tangency
  points; Lemma A2: erosion by the centre box), so `mu(Q) >= mu(core)` computed exactly. Lemma A3: for a density-1
  polygon `S`, also `area(Q ∩ S) >= 1 - area(O minus S)` with `O` a rational outer hull (vertex arcs enclosed by
  tangent triangles, plus the centre box); without it every pose with `Q ⊆ S` (mass exactly 1 on a 3-dimensional
  set) would fail. Boxes may contain `u = 0`: away from the tight set the core is close to the open square and the
  margin is large (0.16-0.43 on test boxes with `u ∈ [0, 1/64]`).
- **Tier B, general form (`src/tier_b.py`, `src/rf.py`): symbolic execution in `u`.** Near the zero-margin germs. The solver of
  Step 2 runs with `u` a rational function carrying a rational sample `s`; every comparison is decided at `s` and its
  polynomial logged as a guard (a comparison that is exactly 0 at `s` but not identically forces a new sample).
  **Lemma B1.** If no guard has a root in an open interval `J ∋ s`, every branch is identical for all `u ∈ J`, so
  `min_c mu = min_i R_i(u)` on `J` with the returned rational functions `R_i = N_i/D_i`; it suffices that
  `(N_i - D_i) D_i >= 0` on the closure of `J`, checked exactly (Taylor-bound fast path, else Sturm sequences and
  sign samples between isolated roots). Tight zeros are allowed. **Lemma B2.** For `u != 0`, `m(u) = min_c mu` is
  continuous, so open components that cover `(a, b)` up to finitely many points prove `m >= 1` on `(a, b)`.
  Components are chained from left to right; their ends are guard roots kept as exact isolating intervals and
  compared exactly (gcd test for equality).  An algebraic number is kept as (squarefree polynomial, open
  isolating interval) whose ends are not roots of the polynomial (enforced at construction by exact Sturm counts).
- **Tier B as used in the run (`src/tier_b2.py`): per candidate.** Lemmas B1-B2 applied to the whole solver re-run
  everything at every event; the run uses a per-candidate form instead.
  **Lemma B3 (vertices).** Fix `J = (a, b)` not containing 0 and a centre box `X`.  Let `L` be a set of lines
  (coefficients rational in `u`) containing every line of type (a), (b) that meets `X` for some `u` in `J` (a line
  is left out only if its values at the four corners of `X` have one strict sign on all of `[a, b]`, proved
  exactly), plus the eight lines bounding the admissible centres `R(u) = X ∩ [lo, 7 - lo]^2`.  Every vertex of the
  arrangement in `R(u)` is `p_ij(u) = L_i ∩ L_j` for a pair with `p_ij(u) ∈ R(u)`.  For each pair, the set of `u`
  in `J` where `p_ij(u) ∈ R(u)` is cut out exactly by the real roots of nine polynomials (eight membership tests and
  the determinant); on each piece the mass at `p_ij(u)` is obtained by symbolic execution of the point-mass
  evaluator (Lemma B1, guards per piece; pieces are split at guard roots) and `(N - D) D >= 0` is proved on the open
  piece (odd-multiplicity roots excluded, exact comparison with the algebraic ends).
  **Lemma B4 (edges, only when a square of `X` can meet the Lebesgue square).** For each line `L_i` separately, its
  breakpoints are its intersections with the other lines of `L` that lie in `R(u)`; between consecutive ones the
  mass is one quadratic along the line (Lemma F1).  The segment part is affine there, so the second difference
  `A` is computed from the polygon term alone; where `A > 0` and the critical parameter lies inside, its value is a
  candidate.  Each line is certified by Lemmas B1-B2 on its own (an event on one line re-runs only that line).
  The finitely many `u` where a piece or component changes are covered by continuity for `u != 0` (Lemma B2).
  Tier B requires a cover without point masses (with them the mass is not continuous in the centre).

## Step 4: coverage record
Every leaf (centre box x u-interval, kind) is written to a record; `src/check_record.py` re-checks, independently
of the driver's control flow, that the roots are exactly the product grid of `[0, 7]^2 x [-1/2, 1/2]` (each once,
across all record files), that the leaves of every root form a bisection partition of it, EMPTY leaves exactly,
and that no Tier B leaf contains `u = 0`; `--recheck N` / `--recheck-b N` re-certify random CORE / TIERB2 leaves.

## Implementation
Python with exact `fractions.Fraction`; Tier B uses `python-flint` (`fmpq_poly`) for polynomial arithmetic, with
our own Sturm-based root isolation (no floating point in any decision). Deliberately different
from the first checker: no D4, angle 0 by closure, different leaf primitives.
