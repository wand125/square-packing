import Sqtri.Check

/-!
# From the checker's forms to squares in the triangle

* `tri s` — the closed equilateral triangle with vertices `(0,0)`, `(s,0)`, `(s/2, s√3/2)`.
* `adm_nonneg` — if the closed unit square with centre `c` and angle `2 arctan u` lies in
  `tri L`, every admissibility form of the checker is `≥ 0` at `(c, u)`.
* `mem_sq_of_captured` — if the four capture forms of a point are `≥ 0` at `(c, u)`, the point
  lies in that square.
* `unavoidable_of_checks` — three checked trees (one per angle bin `[0, 2−√3]`, `[2−√3, √3/3]`,
  `[√3/3, 1]` in `u = tan(θ/2)`) give: every closed unit square in `tri L`, at any angle, contains
  points of total weight `≥ 1`.
-/

namespace SquarePacking.Tri

open SquarePacking UPoly
open scoped Classical

/-- The closed equilateral triangle of side `s` on the base `[0, s]`. -/
def tri (s : ℝ) : Set (ℝ × ℝ) :=
  {p | 0 ≤ p.2 ∧ 0 ≤ Real.sqrt 3 * p.1 - p.2 ∧ 0 ≤ Real.sqrt 3 * (s - p.1) - p.2}

@[simp] lemma val_q (a b : ℚ) : (q a b).val = a + b * Real.sqrt 3 := rfl

lemma one_add_sq_pos (u : ℝ) : (0 : ℝ) < 1 + u ^ 2 := by positivity

/-! ## Admissibility -/

lemma vform_eval (ax ay b sx sy : Q3) (x y u : ℝ) :
    (vform ax ay b sx sy).eval x y u =
      (1 + u ^ 2) * (ax.val * (x + (sx.val * Real.cos (2 * Real.arctan u)
          - sy.val * Real.sin (2 * Real.arctan u)))
        + ay.val * (y + (sx.val * Real.sin (2 * Real.arctan u)
          + sy.val * Real.cos (2 * Real.arctan u))) + b.val) := by
  rw [cos_two_arctan, sin_two_arctan]
  have hD := (one_add_sq_pos u).ne'
  simp only [vform, Aff.eval, eval_add, eval_scale, eval_Dp, eval_C1p, eval_S1p, Q3.val_neg]
  field_simp
  ring

lemma sides_nonneg (L : Q3) (p : ℝ × ℝ) (hp : p ∈ tri L.val) :
    ∀ s ∈ sides L, 0 ≤ s.1.val * p.1 + s.2.1.val * p.2 + s.2.2.val := by
  obtain ⟨h1, h2, h3⟩ := hp
  intro s hs
  simp only [sides, List.mem_cons, List.not_mem_nil, or_false] at hs
  rcases hs with rfl | rfl | rfl
  · simp [Q3.val, Q3.zero, Q3.one]; linarith
  · simp only [val_q, Q3.val_zero]; push_cast; linarith
  · simp only [val_q, Q3.val_mul]; push_cast; linarith

lemma halves_abs : ∀ h ∈ halves, |h.1.val| ≤ 1 / 2 ∧ |h.2.val| ≤ 1 / 2 := by
  intro h hh
  simp only [halves, List.mem_cons, List.not_mem_nil, or_false] at hh
  rcases hh with rfl | rfl | rfl | rfl <;> norm_num [q, Q3.val, abs_le]

theorem adm_nonneg (L : Q3) (c : ℝ × ℝ) (u : ℝ) (h : sq c (2 * Real.arctan u) 1 ⊆ tri L.val) :
    ∀ f ∈ admForms L, 0 ≤ f.eval c.1 c.2 u := by
  intro f hf
  simp only [admForms, List.mem_flatMap, List.mem_map] at hf
  obtain ⟨s, hs, hh, hhm, rfl⟩ := hf
  obtain ⟨ha1, ha2⟩ := halves_abs hh hhm
  have hv := h (mem_sq_offset c (2 * Real.arctan u) hh.1.val hh.2.val ha1 ha2)
  have := sides_nonneg L _ hv s hs
  rw [vform_eval]
  exact mul_nonneg (one_add_sq_pos u).le (by simpa using this)

/-! ## Capture -/

lemma target_eval (px py : Q3) (k : Fin 4) (x y u : ℝ) :
    (target px py k).eval x y u = (1 + u ^ 2) * -gval k (px.val - x) (py.val - y) u := by
  fin_cases k <;>
    simp [target, gab, Aff.eval, Aff.mulU, eval_Dp, eval_C1p, gval, gc, q, Q3.val, Q3.zero] <;> ring

theorem mem_sq_of_captured (pts : List Pt) (i : ℕ) (x y u : ℝ) (h : Captured pts i x y u) :
    ((ptAt pts i).1.val, (ptAt pts i).2.1.val) ∈ sq (x, y) (2 * Real.arctan u) 1 := by
  rw [mem_sq_iff_gval]
  intro k
  have hk := h k
  rw [target_eval] at hk
  have hD := one_add_sq_pos u
  have : 0 ≤ -gval k ((ptAt pts i).1.val - x) ((ptAt pts i).2.1.val - y) u := by
    by_contra hc
    push Not at hc
    nlinarith
  simpa using this

/-! ## Angles -/

lemma reduce_angle (c : ℝ × ℝ) (θ : ℝ) :
    ∃ θ' ∈ Set.Ico 0 (Real.pi / 2), sq c θ 1 = sq c θ' 1 := by
  have hpi : 0 < Real.pi / 2 := by positivity
  refine ⟨toIcoMod hpi 0 θ, by simpa using toIcoMod_mem_Ico hpi 0 θ, ?_⟩
  have heq := toIcoMod_add_toIcoDiv_zsmul hpi 0 θ
  have key : ∀ (k : ℤ) (φ : ℝ), sq c (φ + k • (Real.pi / 2)) 1 = sq c φ 1 := by
    intro k
    induction k using Int.induction_on with
    | zero => intro φ; simp
    | succ k ih =>
      intro φ
      have : φ + ((k : ℤ) + 1) • (Real.pi / 2) = (φ + (k : ℤ) • (Real.pi / 2)) + Real.pi / 2 := by
        simp [add_smul]; ring
      rw [this, sq_add_pi_div_two, ih]
    | pred k ih =>
      intro φ
      have : φ + (-(k : ℤ) - 1) • (Real.pi / 2) + Real.pi / 2 = φ + (-(k : ℤ)) • (Real.pi / 2) := by
        simp [sub_smul]; ring
      rw [← sq_add_pi_div_two, this, ih]
  rw [← key (toIcoDiv hpi 0 θ) (toIcoMod hpi 0 θ), heq]

lemma exists_u (θ : ℝ) (hθ : θ ∈ Set.Ico 0 (Real.pi / 2)) :
    ∃ u, 0 ≤ u ∧ u ≤ 1 ∧ 2 * Real.arctan u = θ := by
  obtain ⟨h0, h1⟩ := hθ
  refine ⟨Real.tan (θ / 2), ?_, ?_, ?_⟩
  · exact Real.tan_nonneg_of_nonneg_of_le_pi_div_two (by linarith) (by linarith)
  · have : Real.tan (θ / 2) < Real.tan (Real.pi / 4) :=
      Real.tan_lt_tan_of_nonneg_of_lt_pi_div_two (by linarith) (by linarith) (by linarith)
    rw [Real.tan_pi_div_four] at this; exact this.le
  · rw [Real.arctan_tan (by linarith) (by linarith)]; ring

lemma centre_mem (c : ℝ × ℝ) (θ : ℝ) : c ∈ sq c θ 1 := by
  simp [sq, coord]

/-! ## The unavoidable-set statement -/

/-- Entries of the certificate as real points and weights. -/
noncomputable def ptR (pts : List Pt) (i : ℕ) : ℝ × ℝ := ((ptAt pts i).1.val, (ptAt pts i).2.1.val)
noncomputable def wtR (pts : List Pt) (i : ℕ) : ℝ := (ptAt pts i).2.2

/-- The breakpoints of the angle bins, as elements of `ℚ(√3)`. -/
def B0 : Q3 := q 0 0
def B1 : Q3 := q 2 (-1)
def B2 : Q3 := q 0 (1/3)
def B3 : Q3 := q 1 0

lemma sqrt3_bounds : (1.7 : ℝ) < Real.sqrt 3 ∧ Real.sqrt 3 < 1.8 := by
  constructor
  · rw [show (1.7 : ℝ) = Real.sqrt (1.7 ^ 2) by rw [Real.sqrt_sq]; norm_num]
    exact Real.sqrt_lt_sqrt (by norm_num) (by norm_num)
  · rw [show (1.8 : ℝ) = Real.sqrt (1.8 ^ 2) by rw [Real.sqrt_sq]; norm_num]
    exact Real.sqrt_lt_sqrt (by norm_num) (by norm_num)

theorem unavoidable_of_checks (L : Q3) (yTop : Q3) (pts : List Pt)
    (hy : yTop.val = L.val * Real.sqrt 3 / 2) (hW : weightsOk pts = true) (t0 t1 t2 : Tree)
    (h0 : check L pts Q3.zero L Q3.zero yTop B0 B1 [] t0 = true)
    (h1 : check L pts Q3.zero L Q3.zero yTop B1 B2 [] t1 = true)
    (h2 : check L pts Q3.zero L Q3.zero yTop B2 B3 [] t2 = true) :
    ∀ (c : ℝ × ℝ) (θ : ℝ), sq c θ 1 ⊆ tri L.val →
      1 ≤ ∑ a ∈ (coverA (Finset.range pts.length) (ptR pts)).filter (fun a => a ∈ sq c θ 1),
        coverW (Finset.range pts.length) (ptR pts) (wtR pts) a := by
  classical
  intro c θ hsub
  obtain ⟨θ', hθ', hsq⟩ := reduce_angle c θ
  obtain ⟨u, hu0, hu1, rfl⟩ := exists_u θ' hθ'
  rw [hsq] at hsub ⊢
  rw [sum_filter_coverA]
  -- the centre lies in the triangle, so in the root rectangle
  obtain ⟨hc1, hc2, hc3⟩ := hsub (centre_mem c _)
  have s3 := sqrt3_bounds
  have hx0 : Q3.zero.val ≤ c.1 := by simp; nlinarith
  have hx1 : c.1 ≤ L.val := by nlinarith
  have hy0 : Q3.zero.val ≤ c.2 := by simpa using hc1
  have hy1 : c.2 ≤ yTop.val := by rw [hy]; nlinarith
  have hadm := adm_nonneg L c u hsub
  -- the bins cover [0, 1]
  have hcov : 1 ≤ capW pts c.1 c.2 u := by
    have hB0 : B0.val = 0 := by simp [B0]
    have hB3 : B3.val = 1 := by simp [B3]
    rcases le_total u B1.val with hb | hb
    · exact check_sound L pts hW t0 _ _ _ _ _ _ [] h0 c.1 c.2 u hx0 hx1 hy0 hy1
        (by rw [hB0]; exact hu0) hb (by simp) hadm
    · rcases le_total u B2.val with hb' | hb'
      · exact check_sound L pts hW t1 _ _ _ _ _ _ [] h1 c.1 c.2 u hx0 hx1 hy0 hy1 hb hb'
          (by simp) hadm
      · exact check_sound L pts hW t2 _ _ _ _ _ _ [] h2 c.1 c.2 u hx0 hx1 hy0 hy1 hb'
          (by rw [hB3]; exact hu1) (by simp) hadm
  -- captured points lie in the square
  unfold capW at hcov
  calc (1 : ℝ) ≤ _ := hcov
    _ ≤ ∑ e ∈ (Finset.range pts.length).filter (fun e => ptR pts e ∈ sq c (2 * Real.arctan u) 1),
          wtR pts e := by
      rw [Finset.sum_filter]
      refine Finset.sum_le_sum fun i _ => ?_
      by_cases hc : Captured pts i c.1 c.2 u
      · have hm := mem_sq_of_captured pts i c.1 c.2 u hc
        rw [if_pos hc, if_pos (by simpa [ptR] using hm)]; rfl
      · rw [if_neg hc]
        split_ifs
        · exact weight_nonneg hW i
        · exact le_refl 0

end SquarePacking.Tri
