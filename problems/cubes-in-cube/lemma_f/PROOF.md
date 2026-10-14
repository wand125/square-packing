# Lemma F, and s₃(2) = 2

## Statement
For R ∈ O(3), write a_ik = |R_ik|, w_i = Σ_j |R_ij| (the ℓ¹ norm of row i, i.e. the width of the cube
R[−½, ½]³ in direction e_i) and

  F_k(R) = Σ_i a_ik (2 − w_i).

**Lemma F.** F_k(R) ≤ 1 for every R ∈ SO(3) and every column k.

**Corollary (s₃(2) = 2).** Let a < 2. If a unit cube C = c + R[−½, ½]³ lies in K_a = [−a/2, a/2]³, then the
centre 0 of K_a lies in the interior of C. Hence two unit cubes with disjoint interiors do not fit in a cube of
side a < 2. With monotonicity and the 2×2×2 packing, s₃(n) = 2 for 2 ≤ n ≤ 8.

*Proof of the corollary.*
- Suppose 0 is not in the interior of C. Since C = {x : ‖Rᵀ(x − c)‖_∞ ≤ ½}, some column u_k of R has
  |u_k·c| ≥ ½.
- Containment means |c_i| + w_i/2 ≤ a/2 for every i, so a − w_i ≥ 0.
- Hence |u_k·c| ≤ Σ_i a_ik |c_i| ≤ Σ_i a_ik (a − w_i)/2 < Σ_i a_ik (2 − w_i)/2 = F_k/2. The inequality is
  strict because a < 2 and Σ_i a_ik ≥ 1.
- By Lemma F, |u_k·c| < ½, a contradiction. ∎

Lemma F is symmetric under signs and under permutations of rows and columns, so it may be stated for R ∈ O(3).
The proof below uses only orthogonality.

## 1. Near an axis: if some |R_ik| ≥ 1/√2, then F_k ≤ 1 (hand proof)

By permuting and negating rows and columns, take k = 1, i = 1 and R_11 = cos θ ≥ 1/√2, with 0 ≤ θ ≤ π/4. Let
x = (R_21, R_31) (so ‖x‖₂ = sin θ), let M be the lower-right 2×2 block, and let u be column 1.

(a) Since Σ_i a_i1 w_i = 1 + Σ_i a_i1 v_i with v_i = w_i − a_i1,
  1 − F_1 = 2(1 − cos θ) − 2‖x‖₁ + a_11(|R_12| + |R_13|) + Σ_{i=2,3} |x_i| ‖M_i‖₁.

(b) Columns 1 and j are orthogonal: R_11 R_1j + (Mᵀx)_j = 0. Hence a_11(|R_12| + |R_13|) = ‖Mᵀx‖₁.

(c) Polar decomposition of M.
- Rows 2 and 3 are orthonormal, so M Mᵀ = I − x xᵀ.
- The polar decomposition is M = P Q with P = (I − x xᵀ)^{1/2} = I − (1 − cos θ) x̂ x̂ᵀ, where x̂ = x/sin θ.
  P is invertible because its eigenvalues are 1 and cos θ > 0, so Q = P⁻¹M is orthogonal.
- P x = cos θ · x, so Mᵀx = cos θ · Qᵀx.
- Row i of M is Q_i − (1 − cos θ) x̂_i (x̂ᵀQ). Using Σ_i |x_i||x̂_i| = sin θ, this gives
  Σ_i |x_i| ‖M_i‖₁ ≥ Σ_i |x_i| ‖Q_i‖₁ − (1 − cos θ) ‖Qᵀx‖₁.

(d) Together:
  1 − F_1 ≥ K₂ + 2(1 − cos θ)(1 − ‖Qᵀx‖₁),  where K₂ = ‖Qᵀx‖₁ + Σ_i |x_i| ‖Q_i‖₁ − 2‖x‖₁.

(e) K₂ ≥ 0 (the planar case).
- Every row and column of Q has ℓ¹ norm L = |cos φ| + |sin φ| ∈ [1, √2].
- The ℓ¹ operator norm of Q is its largest column ℓ¹ norm, so ‖x‖₁ = ‖Q(Qᵀx)‖₁ ≤ L‖Qᵀx‖₁.
- Hence K₂ ≥ ‖x‖₁(1/L + L − 2) = ‖x‖₁(L − 1)²/L ≥ 0.

(f) ‖Qᵀx‖₁ ≤ √2 ‖x‖₂ = √2 sin θ ≤ 1, because θ ≤ π/4.

So 1 − F_1 ≥ 2(1 − cos θ)(1 − √2 sin θ) ≥ 0. ∎

Equality F_k = 1 holds at θ = 0, i.e. when the column is a coordinate axis. Away from it the margin grows
quadratically. This zero margin is the reason the near-axis part is proved by hand.

## 2. Far from the axes: if every |R_ik| ≤ 1/√2, then F_k < 1 (computer proof)

Two independent checkers. Each covers SO(3) and, for every box and column, closes the box if either:
- some |R_ik|² > ½ throughout the box (§1 applies), or
- F_k < 1 throughout the box.

Otherwise the box is split.

- `far_bb.py` (first system):
  - Unit quaternions are covered by the four cube faces q_m = 1 (other coordinates in [−1, 1]), which cover
    S³/±1. R = N(q)/|q|².
  - The interval arithmetic is exact rational (Python `Fraction`).
  - Result: `{"boxes": 1567228, "closed": 783616, "max_depth": 21, "ok": true}`.
- `check2/far_check2.py` (second system):
  - It was written without reading `far_bb.py`.
  - Rotations are ZYZ Euler angles over the whole of SO(3), without symmetry reduction.
  - Arithmetic is `mpmath` interval arithmetic at 64 bits, with π enclosed as an interval.
  - Result: `{"ok": true, "boxes": 594431, "leaves": 297216, "max_depth": 22}`.

In floating point (4×10⁷ random rotations), the largest F_k in the far region is about 0.8284 = 2√2 − 2. It occurs
near the boundary |R_ik| = 1/√2, which leaves a margin of about 0.17.

Reproduce: `python3 far_bb.py` and `python3 check2/far_check2.py` (needs `mpmath`).
