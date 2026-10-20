# Proof that s₄(2) = 2

For R ∈ O(n) write a_ik = |R_ik|, w_i = Σ_j |R_ij| (the ℓ¹ norm of row i, i.e. the width of the cube
R[−½, ½]ⁿ in direction e_i), and

  F_k(R) = Σ_i a_ik (2 − w_i).

F_k depends only on |R|. It is therefore invariant under permutations and sign changes of rows and of columns
(with the column index k moved accordingly), and under R ↦ −R.

**Theorem.** Two unit 4-cubes with disjoint interiors do not fit in a 4-cube of side a < 2. Hence s₄(2) = 2.

The upper bound s₄(2) ≤ 2 is the trivial packing (two cubes side by side in [0, 2]⁴).

## 1. Reduction to Lemma F₄

**Lemma F₄.** F_k(R) ≤ 1 for every R ∈ O(4) and every column k.

**Lemma F₄ implies the theorem.** The argument is the one for n = 3 in `../cubes-in-cube/lemma_f/PROOF.md` and
works in any dimension n.
- Let a < 2 and let C = c + R[−½, ½]ⁿ lie in K_a = [−a/2, a/2]ⁿ. We show that the centre 0 of K_a is in the
  interior of C.
- Suppose not. Since C = {x : ‖Rᵀ(x − c)‖_∞ ≤ ½}, some column u_k of R has |u_k · c| ≥ ½.
- Containment means |c_i| + w_i/2 ≤ a/2 for every i, so a − w_i ≥ 0.
- Hence |u_k · c| ≤ Σ_i a_ik |c_i| ≤ Σ_i a_ik (a − w_i)/2 < Σ_i a_ik (2 − w_i)/2 = F_k/2. The inequality is
  strict because a < 2 and Σ_i a_ik ≥ 1.
- With F_k ≤ 1 this gives |u_k · c| < ½, a contradiction.

So every unit cube in K_a contains the centre in its interior, and two cubes with disjoint interiors cannot both
lie in K_a. ∎

(Conversely, the statement "every unit n-cube in [0, 2]ⁿ contains the centre" is equivalent to F_k ≤ 1 for all
R ∈ O(n) and all k; we only need the direction above.)

By the symmetries, it suffices to prove F_1(R) ≤ 1, and we may assume that the largest |R_e1| is R_11 ≥ 0. Write
u for column 1, c = R_11 = max_e |u_e| = cos θ with 0 ≤ θ < π/2, x = (R_21, R_31, R_41) (so ‖x‖₂ = sin θ), and M
for the lower-right 3 × 3 block of R. The proof splits at c² = 2/3:
- **near region** c² ≥ 2/3: a hand proof (§3), which uses Lemma F in dimension 3;
- **far region** c² ≤ 2/3: two independent computer checks (§4).

## 2. Lemma F in dimension 3

**Lemma F₃.** F_k(Q) ≤ 1 for every Q ∈ O(3) and every column k.

This is Lemma F of `../cubes-in-cube/lemma_f/` (a hand proof near the axes and two independent computer checks
elsewhere). It is stated there for SO(3); since F depends only on |Q|, and −Q ∈ SO(3) when Q ∈ O(3) has
determinant −1, it holds on O(3).

## 3. Near region: if c² ≥ 2/3 then F_1 ≤ 1

The steps (a)–(c) are those of the n = 3 proof (`../cubes-in-cube/lemma_f/PROOF.md` §1) and use only
orthogonality, so they hold in any dimension; we write them for n = 4.

**(a)** Let v_i = w_i − a_i1 (the ℓ¹ norm of row i without its first entry). Then Σ_i a_i1 w_i = Σ_i a_i1² +
Σ_i a_i1 v_i = 1 + Σ_i a_i1 v_i, so

  1 − F_1 = 2 − 2‖u‖₁ + Σ_i a_i1 v_i = 2(1 − c) − 2‖x‖₁ + c·v_1 + Σ_{i=2}^{4} |x_i| ‖M_i‖₁,

where M_i is row i of M (indexed by the rows 2, 3, 4 of R).

**(b)** Columns 1 and j ≥ 2 are orthogonal: c R_1j + (Mᵀx)_j = 0. Hence c·v_1 = ‖Mᵀx‖₁.

**(c)** If θ = 0, then x = 0, row 1 is e_1 (so v_1 = 0), and 1 − F_1 = 0. Otherwise, rows 2–4 of R are
orthonormal, so M Mᵀ = I − x xᵀ. The polar decomposition is M = P Q with

  P = (I − x xᵀ)^{1/2} = I − (1 − c) x̂ x̂ᵀ,  x̂ = x/sin θ,

which is invertible (eigenvalues 1, 1 and c > 0), so Q = P⁻¹M ∈ O(3). Since P x = c·x, Mᵀx = QᵀP x = c·Qᵀx.
Row i of M is M_i = Q_i − (1 − c) x̂_i (x̂ᵀQ), so ‖M_i‖₁ ≥ ‖Q_i‖₁ − (1 − c)|x̂_i| ‖Qᵀx̂‖₁, and with
Σ_i |x_i||x̂_i| = ‖x‖₂,

  Σ_i |x_i| ‖M_i‖₁ ≥ Σ_i |x_i| ‖Q_i‖₁ − (1 − c) ‖Qᵀx‖₁.

**(d)** Put y = Qᵀx and K(Q, x) = ‖y‖₁ + Σ_i |x_i| ‖Q_i‖₁ − 2‖x‖₁. Combining (a)–(c), with c‖y‖₁ − (1 − c)‖y‖₁ =
‖y‖₁ − 2(1 − c)‖y‖₁,

  1 − F_1 ≥ K(Q, x) + 2(1 − c)(1 − ‖y‖₁).

**(e)** ‖y‖₁ ≤ √3 ‖y‖₂ = √3 ‖x‖₂ = √3 sin θ ≤ 1, because sin²θ = 1 − c² ≤ 1/3. So the second term is ≥ 0.

**(f) Lemma K: K(Q, x) ≥ 0.** Write x = Q y, so |x_i| ≤ Σ_j |Q_ij| |y_j|. For Q ∈ O(3) every row has
w_i(Q) = ‖Q_i‖₁ ≤ √3 < 2, so the factor w_i(Q) − 2 is negative and

  K = ‖y‖₁ + Σ_i |x_i| (w_i(Q) − 2) ≥ Σ_j |y_j| (1 − Σ_i |Q_ij| (2 − w_i(Q))) = Σ_j |y_j| (1 − F_j(Q)) ≥ 0

by Lemma F₃. Hence F_1 ≤ 1 in the near region. ∎

(The same argument proves: if Lemma F holds in dimension m ≤ 4, then in dimension m + 1 every column with
max_e R_e1² ≥ 1 − 1/m satisfies F_1 ≤ 1. The bound w_i ≤ √m ≤ 2 used in (f) fails for m ≥ 5.)

**Lean.** Steps (a)–(f) are formalized in `lean/` for any dimension m, with Lemma F in dimension m as a
hypothesis. `near_identity` is (a)–(d), `polarQ_orth` is the orthogonality of Q in (c), `l1_QTx_le_one` is (e),
and `lemmaK` and `rowL1_le_two` are (f). The conclusion of this section is `near_region` with m = 3. See
`lean/README.md`.

## 4. Far region: if c² ≤ 2/3 then F_1 < 1 (computer-assisted)

**Claim.** For every R ∈ O(4) with max_e R_e1² ≤ 2/3, F_1(R) < 1.

It suffices to check SO(4): if det R = −1, negating column 4 gives a matrix in SO(4) with the same |R|. The claim is
checked by two independent branch-and-bound programs in outward-rounded interval arithmetic. The near and far
regions overlap on c² = 2/3, so their union is all of O(4).

| | first system (`checker/`) | second system (`checker2/`) |
|---|---|---|
| coordinates | column 1 by t = (u_2, u_3, u_4)/u_1; columns 2–4 as N_u S, S ∈ SO(3) by a quaternion | R(p, q) x = p x q̄, two quaternions, each scaled so that a coordinate of largest magnitude is +1, i.e. each on one of the 4 facets {x_i = +1} of [−1, 1]⁴ (this gives R only up to sign; −R ∈ SO(4) and F depends only on |R|, and the symmetry reduction keeps a box unless it excludes both signs) |
| symmetry | sorted column 1 (384) and the Voronoi cell of the binary octahedral group (24) as coordinates | sorted column 1 and row 1 imposed as constraints C1–C3; a box is discarded only if every point violates them, for both R and −R |
| bound on F | mean-value form with interval forward-mode AD, also 2‖u‖₁ − 1 − Σ a_e‖m_e‖₁ and G(u) | mean-value form with interval AD, F's own upper bound only |
| near rule | box inside u_1² ≥ 2/3 | box inside max_e lo(|R_e1|)² ≥ 2/3 |
| tasks | 4,096 | 65,536 |
| boxes | 88,110,984 | 192,488,546 |
| max depth | 22 | 30 |
| unresolved | 0 | 0 |

The coordinates, reductions, closing rules and the runs are described in `checker/README.md` and
`checker2/README.md` (with the specification `checker2/SPEC.md`). The second system was written from its
specification without access to the first system. `verify_logs.py` checks the logs of both runs.

## 5. Notes

- The equality set of F_1 = 1 is not isolated: R = diag(±1, S) with any S ∈ O(n − 1) gives F_1 = 1. Near it,
  1 − F_1 ≳ θ², where θ is the angle between column 1 and the nearest axis. This is why the near region is
  handled by hand and the computer checks only need a strict inequality away from it.
- Numerically, the largest value of F_1 in the far region is about 0.845, attained near the boundary c² = 2/3.
