# Proof that s_n(2) = 2 for n = 3, 4, 5

For U ∈ O(n) write w_i = Σ_k |U_ik| (the ℓ¹ norm of row i, i.e. the width of the cube U[−½, ½]ⁿ in direction e_i), and

  F_j(U) = Σ_i |U_ij| (2 − w_i).

**Lemma F_n.** F_j(U) ≤ 1 for every U ∈ O(n) and every column j.

**Theorem.** For n = 3, 4, 5, two unit n-cubes with disjoint interiors do not fit in an n-cube of side a < 2. Hence
s_n(2) = 2 (the upper bound is the trivial packing of two cubes side by side).

The proof is a chain: Lemma F_2 by hand (§2), and for n = 3, 4, 5 Lemma F_{n−1} implies Lemma F_n (§3 near an axis,
§4–§6 elsewhere). Each step uses only Lemma F in the dimension below, for all orthogonal matrices and all columns.

## 1. Lemma F_n implies the theorem

F_j depends only on |U|, so it is invariant under permutations and sign changes of rows and columns (with the column
index moved accordingly).

Let a < 2 and let C = c + U[−½, ½]ⁿ lie in K_a = [−a/2, a/2]ⁿ. We show that the centre 0 of K_a is in the interior
of C. Suppose not. Since C = {x : ‖Uᵀ(x − c)‖_∞ ≤ ½}, some column u_j of U has |u_j · c| ≥ ½. Containment means
|c_i| + w_i/2 ≤ a/2 for every i, so a − w_i ≥ 0. Hence

  |u_j · c| ≤ Σ_i |U_ij| |c_i| ≤ Σ_i |U_ij| (a − w_i)/2 < Σ_i |U_ij| (2 − w_i)/2 = F_j/2 ≤ ½,

a contradiction. The strict inequality holds because a < 2 and Σ_i |U_ij| ≥ 1. So every unit cube in K_a contains
the centre in its interior, and two cubes with disjoint interiors cannot both lie in K_a. ∎

(Conversely, "every unit n-cube in [0, 2]ⁿ contains the centre" is equivalent to Lemma F_n.)

## 2. Lemma F_2

Up to signs, a 2-by-2 orthogonal matrix has |U| = [[s, t], [t, s]] with s² + t² = 1. Both rows have ℓ¹ norm
w = s + t, so F_j = (s + t)(2 − w) = w(2 − w) = 1 − (1 − w)² ≤ 1. ∎

## 3. Near an axis: Lemma F_m implies F_1 ≤ 1 for columns with c² ≥ 1 − 1/m (m ≤ 4)

Let R ∈ O(m + 1). By the symmetries, take column 1 and assume its largest entry in absolute value is R_11 = c ≥ 0.
Write x = (R_21, …, R_{m+1,1}) (so ‖x‖₂ = sin θ, c = cos θ) and M for the lower-right m-by-m block. Assume
c² ≥ 1 − 1/m.

**(a)** Let v_i = w_i − |R_i1| (the ℓ¹ norm of row i without its first entry). Since Σ_i |R_i1| w_i = 1 + Σ_i |R_i1| v_i,

  1 − F_1 = 2(1 − c) − 2‖x‖₁ + c·v_1 + Σ_{i≥2} |x_i| ‖M_i‖₁,

where M_i is row i of M.

**(b)** Columns 1 and j ≥ 2 are orthogonal: c R_1j + (Mᵀx)_j = 0. Hence c·v_1 = ‖Mᵀx‖₁.

**(c)** If θ = 0, then x = 0, row 1 is e_1 and 1 − F_1 = 0. Otherwise the rows 2, …, m + 1 of R are orthonormal, so
M Mᵀ = I − x xᵀ. The polar decomposition is M = P Q with P = (I − x xᵀ)^{1/2} = I − (1 − c) x̂ x̂ᵀ, x̂ = x/sin θ,
which is invertible (c > 0), so Q = P⁻¹M ∈ O(m). Since P x = c·x, Mᵀx = c·Qᵀx. Row i of M is
M_i = Q_i − (1 − c) x̂_i (x̂ᵀQ), so ‖M_i‖₁ ≥ ‖Q_i‖₁ − (1 − c)|x̂_i| ‖Qᵀx̂‖₁ and

  Σ_i |x_i| ‖M_i‖₁ ≥ Σ_i |x_i| ‖Q_i‖₁ − (1 − c) ‖Qᵀx‖₁.

**(d)** Put y = Qᵀx and K(Q, x) = ‖y‖₁ + Σ_i |x_i| ‖Q_i‖₁ − 2‖x‖₁. Combining (a)–(c),

  1 − F_1 ≥ K(Q, x) + 2(1 − c)(1 − ‖y‖₁).

**(e)** ‖y‖₁ ≤ √m ‖y‖₂ = √m sin θ ≤ 1, because sin²θ = 1 − c² ≤ 1/m. So the second term is ≥ 0.

**(f) Lemma K: K(Q, x) ≥ 0.** Write x = Q y, so |x_i| ≤ Σ_j |Q_ij| |y_j|. Every row of Q has ℓ¹ norm
w_i(Q) ≤ √m ≤ 2 (here m ≤ 4 is used), so the factor w_i(Q) − 2 is ≤ 0 and

  K = ‖y‖₁ + Σ_i |x_i| (w_i(Q) − 2) ≥ Σ_j |y_j| (1 − Σ_i |Q_ij| (2 − w_i(Q))) = Σ_j |y_j| (1 − F_j(Q)) ≥ 0

by Lemma F_m, applied to Q and all its columns. Hence F_1 ≤ 1. ∎

For n = m + 1 = 3, 4, 5 the thresholds are max p_i ≥ 1/2, 2/3, 3/4, where p_i = R_i1². Steps (a)–(f) are formalized
in Lean for any m, with Lemma F_m as a hypothesis (`../lean/`). This section is §3 of `../PROOF.md`, written there
for m = 3.

## 4. Elsewhere: the spectral bound

Fix a column, change row signs so that it is x ≥ 0, and write U = [x C], p_i = x_i², S = Σ_i x_i. Orthogonality
gives Σ p_i = 1, xᵀC = 0 and C Cᵀ = I − x xᵀ. Let L = Σ_{i,k} x_i |C_ik|. Since Σ_i x_i w_i = Σ p_i + L = 1 + L,

  F_j = 2S − 1 − L.

For every column y of C, the coordinates of z = diag(x) y sum to zero (xᵀC = 0). If their positive part and their
negative part both have sum a, then ‖z‖₁ = 2a and ‖z‖₂² ≤ 2a², so ‖z‖₁ ≥ √2 ‖z‖₂. Writing Z = diag(x) C as the sum
of the rank-one matrices z_k e_kᵀ and using the triangle inequality for the nuclear norm,

  L = Σ_k ‖z_k‖₁ ≥ √2 Σ_k ‖z_k‖₂ ≥ √2 ‖Z‖_* = √2 Tr √(Z Zᵀ) = √2 Tr √(diag(p) − p pᵀ),

since Z Zᵀ = diag(x)(I − x xᵀ) diag(x) = diag(p) − p pᵀ. Therefore 1 − F_j ≥ q(p), where

  q(p) = √2 T(p) − 2 Σ_i √p_i + 2,  T(p) = Tr √(diag(p) − p pᵀ).

q is symmetric in the coordinates of p. The certificates of §6 prove q(p) > 0 whenever max_i p_i ≤ τ_n = 1 − 1/(n − 1)
(τ = 1/2, 2/3, 3/4 for n = 3, 4, 5). Together with §3 this covers every column, so Lemma F_{n−1} implies Lemma F_n.

q vanishes at a coordinate vector and is negative at some points near it (for example q ≈ −0.025 at
p = (0.96, 0.01, 0.01, 0.01, 0.01)), which is why §3 is needed. For n = 6, q is already negative at the uniform p (√2·5/√6 − 2√6 + 2 ≈ −0.0122), so this route stops at
n = 5.

## 5. The domain and its triangulation

Sort p_1 ≥ … ≥ p_n ≥ 0. The ordered probability simplex has vertices v_k = (1/k, …, 1/k, 0, …, 0) with k nonzero
entries, k = 1, …, n. The cut p_1 ≤ τ removes v_1 (p_1 = 1 > τ ≥ 1/2 ≥ 1/k for k ≥ 2) and creates the points

  w_k = (τ, (1 − τ)/(k − 1), …, (1 − τ)/(k − 1), 0, …, 0), k = 2, …, n,

where the edge from v_1 to v_k meets p_1 = τ. The truncated simplex is the convex hull of v_2, …, v_n, w_2, …, w_n.
It is combinatorially a prism over an (n − 2)-simplex, with bottom v_2 … v_n (the facet p_1 = p_2), top w_2 … w_n (the
facet p_1 = τ), and side facets {v_j, w_j : j ≠ k} for k = 2, …, n. Pulling w_2, then w_3, and so on gives the
staircase triangulation into the n − 1 simplices

  {v_{j+1}, …, v_n, w_2, …, w_{j+1}}, j = 1, …, n − 1.

For n = 3, τ = 1/2 and w_2 = v_2, so the simplex with j = 1 is degenerate and is left out. The checkers verify that
the volumes of the initial simplices add up exactly to the volume of the truncated simplex.

## 6. Certified positivity of q on a simplex

**Concavity of T.** C(p) = diag(p) − p pᵀ is Loewner concave: C(θp + (1 − θ)r) − θC(p) − (1 − θ)C(r) =
θ(1 − θ)(p − r)(p − r)ᵀ ⪰ 0. The map X ↦ Tr √X is monotone in the positive-semidefinite order and concave. So for
p = Σ_k θ_k a^(k) in a simplex with vertices a^(k), T(p) ≥ Σ_k θ_k T(a^(k)).

**The square-root terms.** In coordinate i let l_i and u_i be the smallest and largest vertex coordinates. √t lies
above its chord on [l_i, u_i], and the largest gap is (√u − √l)²/(4(√u + √l)) (attained at √t = (√u + √l)/2). Hence
√p_i ≤ Σ_k θ_k √a^(k)_i + (√u_i − √l_i)²/(4(√u_i + √l_i)), and

  q(p) ≥ min_k q(a^(k)) − Σ_i (√u_i − √l_i)²/(2(√u_i + √l_i)).

A simplex is an accepted leaf if an exact rational lower bound of the right-hand side is positive. Otherwise it is
split along an edge at the exact rational midpoint; the two halves cover it.

**Vertex bounds.** At a rational vertex p, C = diag(p) − p pᵀ is rational and positive semidefinite. A witness is any
symmetric rational matrix A. Let δ = max_i Σ_j |C_ij − (A²)_ij|. For a symmetric matrix the spectral norm is at most
the largest absolute row sum, so ‖C − A²‖₂ ≤ δ. By Weyl's inequality the sorted eigenvalues of C and A² differ by at
most δ, and |√s − √t| ≤ √|s − t| for s, t ≥ 0. Hence

  T(p) = Tr √C ≥ Tr √(A²) − n√δ ≥ Tr A − n√δ,

since Tr √(A²) is the sum of the absolute values of the eigenvalues of A. The lower bound is clipped at 0 before it is
multiplied by a lower bound of √2.

**Exact arithmetic.** Square roots are enclosed with integer square roots: at precision b, k = isqrt(⌊x·2^{2b}⌋)
gives √x ∈ [k/2^b, (k + 1)/2^b] (exact if k² = x·2^{2b}). In the loss term the numerator is bounded above using
upper(√u) − lower(√l) and the denominator below using lower(√u) + lower(√l). Everything else is rational
arithmetic, so every acceptance is an exact rational inequality.

## 7. Certificate format

`certificate.json` has four keys.

- `vertices`: exact rationals written as strings `"a/b"`. The first 2(n − 1) entries are v_2, w_2, v_3, w_3, …, v_n,
  w_n (for n = 3 the entries v_2 and w_2 are equal).
- `witnesses`: one symmetric rational n-by-n matrix A for each vertex, with the same index.
- `initial`: the simplices of §5 as lists of vertex indices.
- `records`: the subdivision tree in depth-first order.

The records are read with a stack. The initial simplices are pushed in the listed order, so the last one is
processed first. Each record applies to the simplex popped from the stack:

- `null`: the simplex is an accepted leaf;
- `[a, b, m]`: the simplex is split along the edge between its vertices at positions a and b (0-based). Vertex m is
  the exact midpoint of that edge. The two children are pushed in this order: the simplex with position a replaced
  by m, then the simplex with position b replaced by m.

The certificate is complete when the records are used up exactly as the stack becomes empty.

## 8. The certificates

| n | τ | certificate | leaves | records | vertices | depth | min vertex bound of q | min leaf margin |
|---|---|---|---|---|---|---|---|---|
| 3 | 1/2 | `n3/certificate.json` | 5 | 9 | 8 | 4 | 0.1484 | 2.9 × 10⁻³ |
| 4 | 2/3 | `n4/certificate.json` | 557 | 1,111 | 193 | 14 | 0.0796 | 3.2 × 10⁻⁴ |
| 5 | 3/4 | `n5/supplied/certificate.json` | 21,502 | 43,000 | 2,175 | 25 | 0.0133 | 2.3 × 10⁻⁷ |
| 5 | 3/4 | `n5/certificate.json` (release asset) | 135,255 | 270,506 | 17,904 | 28 | 0.0133 | 4.1 × 10⁻⁷ |

Each certificate is checked by the second-system checker `checkers/check_spectral.py`. The certificates for n = 3, 4
and the second one for n = 5 were made by the first-system generator `checkers/gen_spectral.py`, which checks every
acceptance exactly as well. The first certificate for n = 5 and its two checkers come from the supplied proof in
`n5/supplied/`. The receipts are in `n3/`, `n4/` and `n5/`.

With §2 and §3 this gives Lemma F_3, then F_4, then F_5, and the theorem for n = 3, 4, 5.
