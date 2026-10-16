import Mathlib

/-!
# The near-region lemma for s_n(2) = 2 (hand part, any dimension)

Notation (see `problems/cubes-n-dim/PROOF.md` §3). An orthogonal matrix of size m + 1 is written in blocks

  R = [ c  r ]
      [ x  M ]

with `c : ℝ`, `r x : Fin m → ℝ` (row 1 without its first entry, column 1 without its first entry) and
`M : Matrix (Fin m) (Fin m) ℝ`. The hypotheses `BlockOrth` record exactly the orthonormality relations used.

  F_1(R) = |c| (2 - |c| - ‖r‖₁) + Σ_i |x_i| (2 - |x_i| - ‖M_i‖₁).

Main results:
* `near_identity`  : 1 - F_1 ≥ K(Q, x) + 2(1 - c)(1 - ‖Qᵀx‖₁) with an explicit orthogonal Q (any m).
* `lemmaK`         : if Q is orthogonal, its rows have ℓ¹ ≤ 2 and its columns have F ≤ 1, then K(Q, x) ≥ 0.
* `near_region`    : for m ≤ 4, assuming Lemma F in dimension m, c > 0 and m·‖x‖₂² ≤ 1 give F_1 ≤ 1.
-/

namespace CubesNd

open Matrix Finset

variable {m : ℕ}

/-- ℓ¹ norm of a vector. -/
noncomputable def l1 (v : Fin m → ℝ) : ℝ := ∑ i, |v i|

/-- Squared Euclidean norm. -/
noncomputable def sq2 (v : Fin m → ℝ) : ℝ := ∑ i, v i ^ 2

/-- Row ℓ¹ norm of a matrix. -/
noncomputable def rowL1 (Q : Matrix (Fin m) (Fin m) ℝ) (i : Fin m) : ℝ := l1 (Q i)

/-- `F_j(Q) = Σ_i |Q_ij| (2 - ‖Q_i‖₁)`. -/
noncomputable def Fcol (Q : Matrix (Fin m) (Fin m) ℝ) (j : Fin m) : ℝ :=
  ∑ i, |Q i j| * (2 - rowL1 Q i)

/-- `F_1(R)` written with the blocks of R. -/
noncomputable def F1 (c : ℝ) (r x : Fin m → ℝ) (M : Matrix (Fin m) (Fin m) ℝ) : ℝ :=
  |c| * (2 - |c| - l1 r) + ∑ i, |x i| * (2 - |x i| - rowL1 M i)

/-- `K(Q, x) = ‖Qᵀx‖₁ + Σ_i |x_i| ‖Q_i‖₁ - 2‖x‖₁`. -/
noncomputable def K (Q : Matrix (Fin m) (Fin m) ℝ) (x : Fin m → ℝ) : ℝ :=
  l1 (Qᵀ *ᵥ x) + ∑ i, |x i| * rowL1 Q i - 2 * l1 x

/-- The orthonormality relations of R = [c r; x M] that are used:
column 1 and row 1 are unit vectors, column 1 is orthogonal to the other columns,
and rows 2..m+1 are orthonormal. -/
structure BlockOrth (c : ℝ) (r x : Fin m → ℝ) (M : Matrix (Fin m) (Fin m) ℝ) : Prop where
  col1 : c ^ 2 + sq2 x = 1
  row1 : c ^ 2 + sq2 r = 1
  col1_perp : ∀ j, c * r j + ∑ i, x i * M i j = 0
  rows : ∀ i k, x i * x k + ∑ j, M i j * M k j = if i = k then 1 else 0

/-- The orthogonal factor `Q = (1 + β x xᵀ) M`, `β = (1/c - 1)/‖x‖₂²`. It is `P⁻¹ M` for the polar
decomposition `M = P Q`, `P = 1 - (1 - c)/‖x‖₂² · x xᵀ`. -/
noncomputable def polarQ (c : ℝ) (x : Fin m → ℝ) (M : Matrix (Fin m) (Fin m) ℝ) :
    Matrix (Fin m) (Fin m) ℝ :=
  (1 + ((1 / c - 1) / sq2 x) • vecMulVec x x) * M

lemma sq2_nonneg (x : Fin m → ℝ) : 0 ≤ sq2 x :=
  Finset.sum_nonneg fun _ _ => sq_nonneg _

lemma l1_nonneg (x : Fin m → ℝ) : 0 ≤ l1 x :=
  Finset.sum_nonneg fun _ _ => abs_nonneg _

lemma block_c_le_one {c : ℝ} {r x : Fin m → ℝ} {M : Matrix (Fin m) (Fin m) ℝ}
    (h : BlockOrth c r x M) (hc : 0 < c) : c ≤ 1 := by
  have := sq2_nonneg x
  nlinarith [h.col1]

lemma rank_one_square (x : Fin m → ℝ) :
    vecMulVec x x * vecMulVec x x = sq2 x • vecMulVec x x := by
  rw [vecMulVec_mul_vecMulVec, vecMulVec_smul]
  simp [dotProduct, sq2, pow_two]

lemma rank_one_product (x : Fin m → ℝ) (a b : ℝ) :
    (1 + a • vecMulVec x x) * (1 + b • vecMulVec x x) =
      1 + (a + b + a * b * sq2 x) • vecMulVec x x := by
  simp only [add_mul, mul_add, one_mul, mul_one, Matrix.smul_mul, Matrix.mul_smul,
    rank_one_square, smul_smul]
  module

lemma block_mul_transpose {c : ℝ} {r x : Fin m → ℝ}
    {M : Matrix (Fin m) (Fin m) ℝ} (h : BlockOrth c r x M) :
    M * Mᵀ = 1 + (-1 : ℝ) • vecMulVec x x := by
  ext i k
  have := h.rows i k
  simp only [mul_apply, transpose_apply, Matrix.add_apply, Matrix.smul_apply, smul_eq_mul,
    vecMulVec_apply, one_apply]
  linarith

/-- The polar factor is orthogonal (`x ≠ 0`, `c > 0`). -/
theorem polarQ_orth {c : ℝ} {r x : Fin m → ℝ} {M : Matrix (Fin m) (Fin m) ℝ}
    (h : BlockOrth c r x M) (hc : 0 < c) (hx : 0 < sq2 x) :
    polarQ c x M * (polarQ c x M)ᵀ = 1 := by
  let b := (1 / c - 1) / sq2 x
  have hb : (b + -1 + b * -1 * sq2 x) + b +
      (b + -1 + b * -1 * sq2 x) * b * sq2 x = 0 := by
    dsimp [b]
    field_simp [ne_of_gt hc, ne_of_gt hx]
    nlinarith [h.col1]
  unfold polarQ
  change ((1 + b • vecMulVec x x) * M) *
    ((1 + b • vecMulVec x x) * M)ᵀ = 1
  rw [transpose_mul, transpose_add, transpose_one, transpose_smul, transpose_vecMulVec]
  rw [Matrix.mul_assoc, ← Matrix.mul_assoc M, block_mul_transpose h,
    ← Matrix.mul_assoc, rank_one_product, rank_one_product, hb]
  simp

lemma polarQ_entry {c : ℝ} {r x : Fin m → ℝ}
    {M : Matrix (Fin m) (Fin m) ℝ} (h : BlockOrth c r x M)
    (hc : 0 < c) (i j : Fin m) :
    polarQ c x M i j = M i j - ((1 - c) / sq2 x) * x i * r j := by
  have hp : (x ᵥ* M) j = -c * r j := by
    have := h.col1_perp j
    simp only [vecMul, dotProduct]
    linarith
  simp only [polarQ, add_mul, one_mul, Matrix.smul_mul, vecMulVec_mul,
    Matrix.add_apply, Matrix.smul_apply, smul_eq_mul, vecMulVec_apply, hp]
  field_simp [ne_of_gt hc]
  ring

lemma polarQ_transpose_x {c : ℝ} {r x : Fin m → ℝ}
    {M : Matrix (Fin m) (Fin m) ℝ} (h : BlockOrth c r x M)
    (hc : 0 < c) (hx : 0 < sq2 x) : (polarQ c x M)ᵀ *ᵥ x = -r := by
  have ha : ((1 - c) / sq2 x) * sq2 x = 1 - c :=
    div_mul_cancel₀ _ (ne_of_gt hx)
  ext j
  change (∑ i, polarQ c x M i j * x i) = -r j
  simp_rw [polarQ_entry h hc]
  calc
    (∑ i, (M i j - (1 - c) / sq2 x * x i * r j) * x i) =
        (∑ i, x i * M i j) - ((1 - c) / sq2 x) * sq2 x * r j := by
      simp only [sq2, Finset.sum_mul, Finset.mul_sum, ← Finset.sum_sub_distrib]
      apply Finset.sum_congr rfl
      intro i _
      ring
    _ = -r j := by rw [ha]; linarith [h.col1_perp j]

lemma l1_neg (x : Fin m → ℝ) : l1 (-x) = l1 x := by
  simp [l1]

lemma F1_expansion {c : ℝ} {r x : Fin m → ℝ}
    {M : Matrix (Fin m) (Fin m) ℝ} (h : BlockOrth c r x M) (hc : 0 < c) :
    1 - F1 c r x M = 2 * (1 - c) - 2 * l1 x + c * l1 r +
      ∑ i, |x i| * rowL1 M i := by
  have he : (∑ i, |x i| * (2 - |x i| - rowL1 M i)) =
      2 * l1 x - sq2 x - ∑ i, |x i| * rowL1 M i := by
    simp only [l1, sq2, Finset.mul_sum, ← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro i _
    nlinarith [sq_abs (x i)]
  rw [F1, abs_of_pos hc, he]
  nlinarith [h.col1]

/-- (a)–(d): the basic inequality, any m. -/
theorem near_identity {c : ℝ} {r x : Fin m → ℝ} {M : Matrix (Fin m) (Fin m) ℝ}
    (h : BlockOrth c r x M) (hc : 0 < c) (hx : 0 < sq2 x) :
    1 - F1 c r x M ≥
      K (polarQ c x M) x + 2 * (1 - c) * (1 - l1 ((polarQ c x M)ᵀ *ᵥ x)) := by
  let a := (1 - c) / sq2 x
  have ha : 0 ≤ a := div_nonneg (sub_nonneg.mpr (block_c_le_one h hc)) (le_of_lt hx)
  have has : a * sq2 x = 1 - c := div_mul_cancel₀ _ (ne_of_gt hx)
  have hr (i : Fin m) : rowL1 (polarQ c x M) i ≤
      rowL1 M i + a * |x i| * l1 r := by
    unfold rowL1 l1
    rw [Finset.mul_sum, ← Finset.sum_add_distrib]
    apply Finset.sum_le_sum
    intro j _
    rw [polarQ_entry h hc]
    change |M i j - a * x i * r j| ≤ |M i j| + a * |x i| * |r j|
    simpa [abs_mul, abs_of_nonneg ha] using abs_sub (M i j) (a * x i * r j)
  have hw := Finset.sum_le_sum (fun i (_ : i ∈ Finset.univ) =>
    mul_le_mul_of_nonneg_left (hr i) (abs_nonneg (x i)))
  have he : (∑ i, |x i| * (rowL1 M i + a * |x i| * l1 r)) =
      (∑ i, |x i| * rowL1 M i) + (1 - c) * l1 r := by
    rw [← has]
    simp only [sq2, Finset.sum_mul, Finset.mul_sum, ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    rw [← sq_abs (x i)]
    ring
  rw [he] at hw
  rw [F1_expansion h hc, K, polarQ_transpose_x h hc hx, l1_neg]
  linarith

lemma l1_sq_le (v : Fin m → ℝ) : (l1 v) ^ 2 ≤ (m : ℝ) * sq2 v := by
  simpa [l1, sq2, sq_abs] using
    (sq_sum_le_card_mul_sum_sq (s := Finset.univ) (f := fun i => |v i|))

lemma sq2_transpose_mulVec {Q : Matrix (Fin m) (Fin m) ℝ}
    (hQ : Q * Qᵀ = 1) (x : Fin m → ℝ) : sq2 (Qᵀ *ᵥ x) = sq2 x := by
  change (∑ i, (Qᵀ *ᵥ x) i ^ 2) = ∑ i, x i ^ 2
  simp only [pow_two]
  change (Qᵀ *ᵥ x) ⬝ᵥ (Qᵀ *ᵥ x) = x ⬝ᵥ x
  rw [dotProduct_transpose_mulVec, mulVec_mulVec, hQ, one_mulVec]

/-- (e): `‖Qᵀx‖₁ ≤ 1` when `Q Qᵀ = 1` and `m ‖x‖₂² ≤ 1`. -/
theorem l1_QTx_le_one {Q : Matrix (Fin m) (Fin m) ℝ} {x : Fin m → ℝ}
    (hQ : Q * Qᵀ = 1) (hs : (m : ℝ) * sq2 x ≤ 1) :
    l1 (Qᵀ *ᵥ x) ≤ 1 := by
  have hb := l1_sq_le (Qᵀ *ᵥ x)
  rw [sq2_transpose_mulVec hQ] at hb
  nlinarith [l1_nonneg (Qᵀ *ᵥ x)]

/-- Lemma K: if `Q Qᵀ = 1`, every row of Q has ℓ¹ norm ≤ 2 and every column has `F ≤ 1`, then `K ≥ 0`. -/
theorem lemmaK {Q : Matrix (Fin m) (Fin m) ℝ} (x : Fin m → ℝ)
    (hQ : Q * Qᵀ = 1) (hw : ∀ i, rowL1 Q i ≤ 2) (hF : ∀ j, Fcol Q j ≤ 1) :
    0 ≤ K Q x := by
  let y := Qᵀ *ᵥ x
  have hxy : Q *ᵥ y = x := by
    dsimp [y]
    rw [mulVec_mulVec, hQ, one_mulVec]
  have hb (i : Fin m) : |x i| ≤ ∑ j, |Q i j| * |y j| := by
    rw [← hxy]
    change |∑ j, Q i j * y j| ≤ ∑ j, |Q i j| * |y j|
    simpa only [abs_mul] using Finset.abs_sum_le_sum_abs (fun j => Q i j * y j) Finset.univ
  have hw' := Finset.sum_le_sum (fun i (_ : i ∈ Finset.univ) =>
    mul_le_mul_of_nonpos_right (hb i) (sub_nonpos.mpr (hw i)))
  have he : (∑ i, (∑ j, |Q i j| * |y j|) * (rowL1 Q i - 2)) =
      ∑ j, |y j| * (-Fcol Q j) := by
    simp only [Fcol, Finset.sum_mul, Finset.mul_sum, ← Finset.sum_neg_distrib,
      mul_neg]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro j _
    apply Finset.sum_congr rfl
    intro i _
    ring
  rw [he] at hw'
  have hn : 0 ≤ l1 y + ∑ j, |y j| * (-Fcol Q j) := by
    unfold l1
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_nonneg
    intro j _
    nlinarith [abs_nonneg (y j), hF j]
  have hk : K Q x = l1 y + ∑ i, |x i| * (rowL1 Q i - 2) := by
    simp only [K, l1, mul_sub, Finset.sum_sub_distrib, Finset.mul_sum]
    dsimp [y]
    simp only [mul_comm (2 : ℝ)]
    ring
  rw [hk]
  linarith

/-- For m ≤ 4 every row of an orthogonal matrix has ℓ¹ norm ≤ 2 (`‖v‖₁ ≤ √m ‖v‖₂`). -/
theorem rowL1_le_two {Q : Matrix (Fin m) (Fin m) ℝ} (hm : m ≤ 4) (hQ : Q * Qᵀ = 1) (i : Fin m) :
    rowL1 Q i ≤ 2 := by
  have hd := congrArg (fun A : Matrix (Fin m) (Fin m) ℝ => A i i) hQ
  have hs : sq2 (Q i) = 1 := by
    simpa [sq2, mul_apply, pow_two] using hd
  have hb := l1_sq_le (Q i)
  rw [hs, mul_one] at hb
  have hm' : (m : ℝ) ≤ 4 := by exact_mod_cast hm
  change l1 (Q i) ≤ 2
  nlinarith [l1_nonneg (Q i)]

/-- Lemma F in dimension m, stated as a hypothesis. -/
def LemmaF (m : ℕ) : Prop :=
  ∀ Q : Matrix (Fin m) (Fin m) ℝ, Q * Qᵀ = 1 → ∀ j, Fcol Q j ≤ 1

lemma eq_zero_of_sq2_eq_zero {x : Fin m → ℝ} (hx : sq2 x = 0) : x = 0 := by
  funext i
  have hi : x i ^ 2 ≤ sq2 x := Finset.single_le_sum
    (fun j _ => sq_nonneg (x j)) (Finset.mem_univ i)
  have : x i = 0 := by nlinarith [sq_nonneg (x i)]
  exact this

/-- **Near region.** For m ≤ 4, Lemma F in dimension m implies `F_1(R) ≤ 1` for every orthogonal R of
size m + 1 with `c = R_11 > 0` and `m (1 - c²) ≤ 1`, i.e. `c² ≥ 1 - 1/m`.
For m = 3 this is the near region of `PROOF.md` §3. -/
theorem near_region (hm : m ≤ 4) (hF : LemmaF m) {c : ℝ} {r x : Fin m → ℝ}
    {M : Matrix (Fin m) (Fin m) ℝ} (h : BlockOrth c r x M) (hc : 0 < c)
    (hs : (m : ℝ) * sq2 x ≤ 1) :
    F1 c r x M ≤ 1 := by
  rcases (sq2_nonneg x).eq_or_lt with hx | hx
  · have hx0 : sq2 x = 0 := hx.symm
    have hc1 : c = 1 := by nlinarith [h.col1]
    have hr0 : sq2 r = 0 := by rw [hc1] at h; nlinarith [h.row1]
    have hxv := eq_zero_of_sq2_eq_zero hx0
    have hrv := eq_zero_of_sq2_eq_zero hr0
    norm_num [F1, hc1, hxv, hrv, l1]
  · have hQ := polarQ_orth h hc hx
    have hk := lemmaK x hQ (rowL1_le_two hm hQ) (hF _ hQ)
    have hy := l1_QTx_le_one hQ hs
    have hp : 0 ≤ 2 * (1 - c) * (1 - l1 ((polarQ c x M)ᵀ *ᵥ x)) :=
      mul_nonneg (mul_nonneg (by norm_num) (sub_nonneg.mpr (block_c_le_one h hc)))
        (sub_nonneg.mpr hy)
    linarith [near_identity h hc hx]

end CubesNd
