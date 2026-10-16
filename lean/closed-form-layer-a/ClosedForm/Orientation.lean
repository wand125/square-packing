import ClosedForm.LocalReduction

namespace ClosedForm

/-- The asymmetric rational u interval contains a complete quarter-turn of
square orientations. This uses square periodicity, not a reflection of the measure. -/
lemma record_angle_width :
    2 * Real.arctan (-13 / 32 : ℝ) + Real.pi / 2 ≤ 2 * Real.arctan (7 / 16 : ℝ) := by
  have h : Real.pi / 4 ≤ Real.arctan (13 / 32 : ℝ) + Real.arctan (7 / 16 : ℝ) := by
    rw [Real.arctan_add (by norm_num), ← Real.arctan_one]
    apply Real.arctan_mono
    norm_num
  rw [show (-13 / 32 : ℝ) = -(13 / 32) by ring, Real.arctan_neg]
  linarith

lemma unitSq_record_orientation (z : Point) (θ : ℝ) :
    ∃ u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16), poseSquare z u = UnitSquarePacking.unitSq z θ := by
  have hp : 0 < Real.pi / 2 := by positivity
  let L := 2 * Real.arctan (-13 / 32 : ℝ)
  let θ' := toIcoMod hp L θ
  have hθ' : L ≤ θ' ∧ θ' < L + Real.pi / 2 := toIcoMod_mem_Ico hp L θ
  have hupp : θ' ≤ 2 * Real.arctan (7 / 16 : ℝ) :=
    hθ'.2.le.trans record_angle_width
  have hlow : -(Real.pi / 2) < θ' / 2 := by
    have h := (Real.arctan_mem_Ioo (-13 / 32 : ℝ)).1
    dsimp [L] at hθ'
    linarith [hθ'.1]
  have hhigh : θ' / 2 < Real.pi / 2 := by
    have h := Real.arctan_lt_pi_div_two (7 / 16 : ℝ)
    linarith
  let u := Real.tan (θ' / 2)
  have hat : Real.arctan u = θ' / 2 := Real.arctan_tan hlow hhigh
  have hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16) := by
    constructor
    · apply Real.arctan_le_arctan_iff.mp
      rw [hat]
      dsimp [L] at hθ'
      linarith [hθ'.1]
    · apply Real.arctan_le_arctan_iff.mp
      rw [hat]
      linarith
  refine ⟨u, hu, ?_⟩
  rw [poseSquare_eq_unitSq, hat, show 2 * (θ' / 2) = θ' by ring]
  have hper : Function.Periodic (UnitSquarePacking.unitSq z) (Real.pi / 2) := by
    intro t
    rw [unitSq_eq_upstream, unitSq_eq_upstream, SquarePacking.sq_add_pi_div_two]
  have he := hper.zsmul (toIcoDiv hp L θ) θ'
  rw [toIcoMod_add_toIcoDiv_zsmul hp L θ] at he
  exact he.symm

lemma pose_admissible_of_subset (z : Point) (u a : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16))
    (hQ : poseSquare z u ⊆ UnitSquarePacking.container a) : Admissible z u := by
  rw [poseSquare_eq_unitSq, unitSq_eq_upstream] at hQ
  have hbox : SquarePacking.sq z (2 * Real.arctan u) 1 ⊆ SquarePacking.box a := by
    intro p hp
    obtain ⟨hx, hy⟩ := hQ hp
    exact ⟨hx.1, hx.2, hy.1, hy.2⟩
  have h := (SquarePacking.sq_subset_box_iff a z (2 * Real.arctan u)).mp hbox
  have hw : SquarePacking.wid (2 * Real.arctan u) / 2 = halfWidth u := by
    simp only [SquarePacking.wid, SquarePacking.cos_two_arctan, SquarePacking.sin_two_arctan]
    change (|poseCos u| + |poseSin u|) / 2 = halfWidth u
    rw [abs_of_nonneg (poseCos_nonneg hu)]
    rfl
  exact ⟨hw ▸ h.1, hw ▸ h.2.2.1⟩

end ClosedForm
