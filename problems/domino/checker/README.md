# Checker 1: exact unavoidability checker for unit squares in a 1:2 rectangle

## What is proved

The input is a side `L`, points `p_i` with rational weights `w_i >= 0`, optional `pairs` and
`wedges` (see below), and a symmetry flag. When the output says `"status": "verified"`, the
following holds:

    every closed unit square Q with Q ⊆ R_L = [0, 2L] x [0, L] (any centre, any angle)
    satisfies  Σ_{p_i ∈ Q} w_i ≥ 1.

Points on ∂Q count.

## How to run

```bash
python check.py ../certificates/n4/n4_cert.json --n 4 --jobs 4 --max-depth 30 \
    --u-breaks "K[-21/37;-11/37;15/37]"
python check.py ../certificates/n4/below/n4_L9651_5000.json --n 4 --jobs 4 --max-depth 44
```

Only the Python standard library is used (Python 3.10+).

The output is a JSON summary with:
- the sha256 of the certificate;
- the exact total weight, and whether it is < n;
- the leaf counts;
- the uncertified boxes (up to 3000 are listed; all are counted);
- the depth and the time.

**Certificate format:**

```
{"L": ..., "symmetry": "D2"|"none", "points": [{"x", "y", "w"}],
 "pairs": [[i, j]], "wedges": [[i, j]]}
```

- Indices refer to the `points` list.
- Numbers are elements of K (below), written as `p/q` or `K[a;b;c]` = a + b·α + c·α².
- Weights are rationals.

Files: `q3.py` (the field K; the class is called `Q3` for historical reasons), `poly.py`
(polynomials and Bernstein tests), `check.py` (CLI and subdivision).

## Why each accepted step is sound

Everything accepted is decided in exact arithmetic. Floats only choose which proof to attempt:
which points, which third constraint, which split. A wrong float guess costs time, never
soundness.

### 1. The field K = Q(α)

α = v4 is the largest real root of f(x) = 5x³ + 8x² − 32x − 4, so α = 1.93028330671426938847…

- **Irreducibility.** f has no rational root: the candidates are ±1, ±2, ±4, ±1/5, ±2/5, ±4/5.
  So f is irreducible, and 1, α, α² is a basis of K. An element is a triple (a, b, c) of
  rationals.
- **Arithmetic.** Products are reduced with α³ = (4 + 32α − 8α²)/5. An inverse is an exact
  3×3 linear solve, checked by multiplying back.
- **Isolating interval.** I0 = [19302833/10⁷, 19302834/10⁷]. At import, the code checks
  exactly that f(lo) < 0 < f(hi). Since f′(x) = 15x² + 16x − 32 > 0 for x ≥ 1.1, α is the unique
  root of f in I0.
- **Sign of a + bα + cα².** If b = c = 0, it is the sign of a. Otherwise:
  - The value is nonzero: a nonzero polynomial of degree ≤ 2 cannot vanish at an algebraic number
    of degree 3.
  - It is evaluated on the current interval [lo, hi] (lo > 0) with exact interval arithmetic:
    bα ∈ [min(b·lo, b·hi), max(b·lo, b·hi)] and cα² ∈ [min(c·lo², c·hi²), max(c·lo², c·hi²)].
  - If the resulting interval excludes 0, its sign is the answer.
  - Otherwise the interval of α is bisected at its rational midpoint m. The half on which f
    changes sign is kept; f(m) ≠ 0, since f has no rational root. Then the evaluation is repeated.
  - This terminates because the value is nonzero and the width halves each time. The interval is
    a module global and only ever shrinks around α.
- **Equality** is equality of the triples.
- Every `<`, `<=` and `== 0` in the checker goes through this. Rationals are the case b = c = 0,
  so certificates with a rational L are checked by the same code.

### 2. Angles

θ = 2 arctan u, so cos θ = (1−u²)/D and sin θ = 2u/D with D = 1 + u² > 0. The square has period
π/2, so u ∈ [0, 1] covers every angle.

With `D2`:

- The checker first verifies exactly that the weighted set is invariant under x ↦ 2L − x and
  y ↦ L − y. These two maps preserve R_L.
- On angles both maps act as θ ↦ −θ (mod π/2). Hence every square is equivalent to one with
  θ ∈ [0, π/4].
- The checker proves θ(U) ≥ π/4 exactly, for the default U = 5/12: with c = (1−U²)/(1+U²), it
  checks c ≤ 0 or c² ≤ 1/2.
- With `D2`, `pairs` are allowed, but features and segments are rejected.

The root u-bins are cut at 0, U, and at any `--u-breaks` (elements of K). Without symmetry the
cuts are 0 and 1, where the sides of R_L are parallel to the square.

### 3. Admissibility as half-planes

Q ⊆ R_L iff its 4 vertices lie in R_L.

- For each side k of R_L (normal (±1, 0) or (0, ±1)) and each vertex σ ∈ {±½}², this gives
  n_k·c ≤ b_k − n_k·R_θσ.
- Multiplied by D, the right-hand side is O(u)/D, where O is a polynomial of degree ≤ 2 over K.
- The box [x0, x1] × [y0, y1] adds 4 more half-planes. So, for each fixed u, the admissible
  centres in the box form a bounded convex polygon P_u.

### 4. Dropping constraints (exact)

A half-plane is dropped only if an exact Bernstein test shows that, for the whole bin, either:

- a parallel constraint is at least as tight, or
- the whole box lies inside it.

A box is **EMPTY** if all 4 corners strictly violate one constraint for every u.

### 5. Vertices

Each extreme point of P_u is the intersection V_ij(u) = (X_ij, Y_ij)/D of two active
constraints (Cramer's rule, exact).

- A pair is discarded only when a third constraint is violated strictly on the whole bin. This is
  proved with all Bernstein coefficients > 0.
- If every pair is discarded, the box is EMPTY.

### 6. Capture

p ∈ Q(c, θ) iff |(p − c)·e_k| ≤ ½ for e1 = (1−u², 2u)/D and e2 = (−2u, 1−u²)/D.

- This set of c is convex. So if every remaining vertex satisfies it for all u in the bin, so
  does all of P_u.
- Multiplied by D², each condition is a polynomial that must be ≥ 0.
- This is proved with exact Bernstein coefficients, with de Casteljau halving up to 12 times.
  The first and last coefficients are the endpoint values, so a margin-zero contact at a bin
  endpoint gives a coefficient that is exactly 0. That is accepted.
- A box is **COVER** when the points proved captured on it have exact total weight ≥ 1.

### 6a. Lemma P (chord pairs)

For points p, q with |q − p| = 1 exactly, a pose whose chord along the line pq crosses two opposite
edges and meets the segment [p, q] contains p or q. The test is the same as in the triangle checker
this code descends from. The certificates in this repository do not use it, except the n = 3 test
below.

### 6b. Wedge lemma (`wedges`, function `wedge_holds`)

**Claim.** Every pose of the box contains p or q.

When it holds, the box is credited min(w_p, w_q). Both points are marked as used, so that no point
is counted twice in the COVER sum.

**Proof.** A closed unit square with centre c misses p iff sgn·e_k·(p − c) > ½ for some side
(k, sgn). Each of the 16 combinations (side for p, side for q) is excluded by (a) or (b):

- **(a)** p is never strictly beyond its side on the box: sgn·e_k·(p − c) ≤ ½ at every vertex of
  P_u, for all u in the bin. The condition is affine in c. The same test applies to q.
- **(b)** The sides are adjacent (k1 ≠ k2), and a Farkas combination with one admissibility line
  n·c ≤ O/D is contradictory:
  - n1 = sgn1·e_k1 and n2 = sgn2·e_k2 are orthonormal. With λ_i = −n·n_i, we get
    λ1·n1 + λ2·n2 + n = 0 and λ1² + λ2² = 1.
  - Adding λ1·(n1·c < n1·p − ½), λ2·(n2·c < n2·q − ½) and (n·c ≤ O/D) gives
    0 < λ1(n1·p − ½) + λ2(n2·q − ½) + O/D. The inequality is strict because λ1 and λ2 are not
    both 0.
  - Multiply by D². If the right-hand side R(u) is ≤ 0, and D·λ1 ≥ 0 and D·λ2 ≥ 0 on the bin,
    the combination is impossible. All three are proved with exact Bernstein coefficients; zero
    coefficients are allowed.
  - Every admissibility line holds for every admissible pose, so each of them may be tried.

**Where it is needed.** In the extremal packing the tilted square L touches three things: the
bottom side, the corner (1, v−1) of the axis-parallel square A, and the centre of the rectangle
(along its edge shared with the other tilted square).

- Take the corner and the centre with the two adjacent sides of L that face them, and the bottom
  side. Then (b) reduces to v ≤ s(β), where
  s(β) = 2(sin β + cos β)(1 + sin β)/((sin β + cos β)² + sin² β).
- This is the formula of the one-parameter family of packings, and v4 = min s(β).
- R has a double root at u* = tan(β*/2). u* is passed as a bin endpoint, so the exact Bernstein
  coefficients are ≥ 0 with zeros at u*.
- The extremal packing is not rigid to first order: the two tilted squares can rotate together,
  with overlap of order t². Near u*, which of the two points a pose captures switches inside every
  box. Box subdivision alone cannot certify that; the wedge lemma does.

### 7. Coverage of all poses

- The root boxes cover [0, Lx] × [0, Ly] ⊇ R_L. Lx and Ly are rationals, checked exactly against
  2L and L.
- The root u-bins cover [0, 1], or [0, U] with D2.
- Splitting halves one side; the midpoints are exact.
- Every leaf is EMPTY, COVER or UNCERTIFIED. The verdict is "verified" only with 0 UNCERTIFIED
  leaves.

## The critical angle

u* = (−21 − 11α + 15α²)/37 ≈ 0.369102 is the root of t³ − 5t² − t + 1 in (0, 1). The identities
u*³ − 5u*² − u* + 1 = 0 and s(u*) = α hold exactly in K; `tests/test_field.py` checks them.
Pass it as `--u-breaks "K[-21/37;-11/37;15/37]"`.

## Tests

```bash
python -m pytest -q tests      # from checker/, needs pytest
```

The tests cover:
- the field against high-precision decimal evaluation;
- the identities for u*;
- a small n = 3 certificate (L = 3/2) that must verify;
- a certificate at L = v4 + 10⁻⁶ that must fail.

## Known limitations

- A margin-zero contact strictly inside a u-bin cannot be certified. The breakpoint must be given
  with `--u-breaks`.
- Without the wedge lemma, the n = 4 certificate at L = v4 fails: boxes near the extremal pose stay
  uncertified at any depth (see `../controls/`).
