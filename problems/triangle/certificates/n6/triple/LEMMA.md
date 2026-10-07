# Local lemma for the triple {0, 1, 3} (n = 6, equilateral triangle)

This is the triangle analogue of the local lemma for three squares in a regular hexagon
(`problems/hexagon/n3/local_lemma/` in this repository). The computer checks two things:

- `derive2.py` (sympy) derives the weighted sum S and its exact form;
- `lemma_check.py` (mpmath interval arithmetic) checks the inequality (M) below.

## Setting

- v = 2 + 4/√3. T_L is the triangle with vertices (0,0), (L,0), (L/2, L√3/2).
- d_L(X) = (√3x − y)/2 is the distance of X to the left side. d_R(X) = (√3(L − x) − y)/2 is the distance to
  the right side.
- Squares 0 and 1 are given by their bottom-left corners Q_i = Q_i* + (a_i, b_i) and their tilts φ_i.
  - Q_0* = (1/√3, 0) and Q_1* = (1 + 1/√3, 0).
  - e_i = (cos φ_i, sin φ_i) and f_i = (−sin φ_i, cos φ_i).
- Square 3 is given by its outer lower corner A, the one on the right side, and its tilt φ3 against the right
  side.
  - Its inner edge is D–C, with D = A + f3 and C = D + e3. Here e3 points up along the right side and f3
    points inward.
- P = Q_1 + e_1 + f_1 is the top-right corner of square 1.
- t = (P − D)·e3 is the position of P along the inner edge. At the pinwheel, t = 2/√3 − 1 ≈ 0.1547.

**Lemma.** Suppose the following hold:

- |φ0|, |φ1|, |φ3| ≤ Φ, |a_i| ≤ δ and 0 ≤ b_i ≤ δ (i = 0, 1);
- t ∈ [τ, 1 − τ];
- the three closed squares lie in T_L with pairwise disjoint interiors.

Then L ≥ v. If L = v, then φ0 = φ1 = φ3 = 0 and every contact below is tight. That is the pinwheel, up to
the slide of square 3 along the right side.

The inequality (M) is checked for (Φ, δ, τ) = (0.1, 0.1, 0.08), (0.05, 0.05, 0.05) and (0.05, 0.05, 0.03).
It fails at (0.12, 0.12, 0.1).

## Proof

### Step 1: square 3 becomes a slab

P is not interior to square 3. P lies strictly between the lines of the two short edges, because
0 < t < 1. It also lies on the inner side of the outer edge.

Hence P is beyond the inner-edge line, P = foot + k f3 with k ≥ 0. Therefore

    d_R(P) ≥ d_R(foot) = (1−t) d_R(D) + t d_R(C).

Because d_R is affine, d_R(D) = d_R(A) + cos φ3 and d_R(C) = d_R(B) + cos φ3, where B = A + e3.

- The corners lie in T_L, so d_R(A), d_R(B) ≥ 0.
- Also d_R(B) − d_R(A) = ±sin φ3.

So the larger of the two is at least |sin φ3|, and

    g_R := d_R(P) − cos φ3 − τ|sin φ3| ≥ 0.

The slide of square 3 has disappeared. It enters only through the hypothesis t ∈ [τ, 1−τ].

### Step 2: the other constraints

The following hold:

- g_L := d_L(Q_0 + f_0) ≥ 0, because the top-left corner of square 0 lies in T.
- b_i ≥ 0 and b_i + sin φ_i ≥ 0, because both bottom corners lie in T. So for any β_i ∈ [0, 1],
  g_b,i := b_i + β_i sin φ_i ≥ 0.

Squares 0 and 1 are interior-disjoint, so some axis among e_0, f_0, e_1, f_1 separates them.

- An f-axis cannot separate them. Their f-projections overlap by more than 1 − 0.22, since |b_i| ≤ δ and
  |φ_i| ≤ Φ.
- Square 1 cannot lie on the low side of e_0 or e_1, because e·(Q_1 − Q_0) ≥ 1 − O(δ).

So one of two cases holds:

- **S1** (axis e_1): e_1·Q_1 ≥ e_1·X for X = Q_0 + e_0 + f_0 and X = Q_0 + e_0. For any α ∈ [0, 1],
  g_sep := e_1·Q_1 − e_1·(α(Q_0+e_0+f_0) + (1−α)(Q_0+e_0)) ≥ 0.
- **S0** (axis e_0): e_0·Y ≥ e_0·Q_0 + 1 for Y = Q_1 + f_1 and Y = Q_1. For any α ∈ [0, 1],
  g_sep := α e_0·(Q_1+f_1) + (1−α) e_0·Q_1 − e_0·Q_0 − 1 ≥ 0.

### Step 3: the weighted sum

Define

    S := g_L + g_R + (√3/2) g_sep + (g_b,0 + g_b,1)/2  ≥  0.

S is evaluated with L = v in g_R. For a configuration in T_L, each constraint g_R(·, L) ≥ 0 gives
g_R(·, v) ≥ (√3/2)(v − L). So

    S ≥ (√3/2)(v − L).                                    (1)

The weights √3/2, 1 and 1/2 are the KKT multipliers of the reduced problem. S is affine in (a, b), and
`derive2.py` prints it exactly:

    S = F_case(φ; α, β, τ) + (√3/2)(1 − cos ψ)(a_0 − a_1) + (√3/2) sin ψ (b_1 − b_0),

- ψ = φ1 in case S1 and ψ = φ0 in case S0;
- F_case(0) = 0;
- ∇F at 0 is ( (√3α + β0 − √3)/2, (−√3α + β1 + √3 − 1)/2, −τ sgn φ3 ). It is the same in both cases.

### Step 4: choosing the weights by orthant

The weights are chosen by the signs of (φ0, φ1):

| signs | α | β0 | β1 | gradient terms |
|---|---|---|---|---|
| (+,+) | 1 − 1/(2√3) | 0 | 0 | −¼\|φ0\| − ¼\|φ1\| |
| (−,−) | 1 − 1/(2√3) | 1 | 1 | −¼\|φ0\| − ¼\|φ1\| |
| (+,−) | 0 | 0 | 1 | −(√3/2)(\|φ0\| + \|φ1\|) |
| (−,+) | 1 | 1 | 0 | −½(\|φ0\| + \|φ1\|) |

Taylor's theorem with the interval Hessian over the orthant box, plus the p-terms bounded by |a_0 − a_1| ≤ 2δ
and |b_1 − b_0| ≤ δ, gives

    S ≤ −c (|φ0| + |φ1| + |φ3|),   c > 0.                  (M)

`lemma_check.py` checks (M) for all 2 cases × 8 orthants. The worst coefficient is −0.0296 at
(0.1, 0.1, 0.08) and −0.0249 at (0.05, 0.05, 0.05).

### Step 5: conclusion

(1) and (M) give 0 ≤ (√3/2)(v − L) ≤ S ≤ −c‖φ‖₁. Hence L ≥ v. If L = v, then φ = 0 and S = 0, so every
weighted constraint is tight. ∎

## How it is used

The lemma closes the leaves of the localization tree in `../PROOF.md`. A leaf is closed when two things hold:

1. the boxes of squares 0, 1 and 3 lie inside the lemma's (Φ, δ) range, measured from a pinwheel image;
2. an interval enclosure of t lies in [τ, 1−τ].

`validity_box.py` checks both on the final boxes. The binding hypothesis is (2), not (M): the slack of t is
only 0.1547.

Without the hypothesis the lemma is false. If square 3 slides up by more than 0.155, squares 0 and 1 are free
to move right, and the triple alone is not rigid. So the localization must bound the slide of square 3. In the
full packing, squares 2, 4 and 5 bound it.
