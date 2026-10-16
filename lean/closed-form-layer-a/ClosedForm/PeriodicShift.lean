import ClosedForm.Localization

open MeasureTheory
namespace ClosedForm

lemma rowsMeasure_zero_above (ss : List Segment) (dx dy b : ℝ)
    (h : ∀ s ∈ ss, (s.ax : ℝ) + dx ≤ b ∧ (s.bx : ℝ) + dx ≤ b)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, b < p.1) :
    rowsMeasure ss dx dy A = 0 := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    change (segmentMeasure s dx dy + rowsMeasure ss dx dy) A = 0
    rw [Measure.add_apply, ih (fun t ht => h t (by simp [ht])), add_zero]
    rw [segmentMeasure, Measure.smul_apply, smul_eq_mul,
      segMeasure_eq_zero_of_disjoint _ _ A hA, mul_zero]
    intro t ht hp
    have hp' := hAb _ hp
    have hh := h s (by simp)
    change b < (s.ax : ℝ) + dx + t * ((s.bx : ℝ) + dx - ((s.ax : ℝ) + dx)) at hp'
    nlinarith [mul_nonneg (sub_nonneg.mpr ht.2) (sub_nonneg.mpr hh.1),
      mul_nonneg ht.1 (sub_nonneg.mpr hh.2)]

lemma integerWall_positive (f fr : Family) (hs : Structural f fr) (d : ℝ)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, d < p.1) :
    integerWall f d A = (Measure.sum fun n : ℕ => rowsMeasure (profile f) (d + n) 0) A := by
  rw [integerWall, Measure.sum_apply _ hA, Measure.sum_apply _ hA,
    tsum_of_nat_of_neg_add_one ENNReal.summable ENNReal.summable]
  have hz (n : ℕ) : rowsMeasure (profile f) (d + ((-(↑n + 1) : ℤ) : ℝ)) 0 A = 0 := by
    apply rowsMeasure_zero_above _ _ _ d _ A hA hAb
    intro s hsp
    have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 s hsp
    have ha : (s.ax : ℝ) ≤ 1 := by exact_mod_cast (le_max_left _ _).trans hpb.2.1
    have hb : (s.bx : ℝ) ≤ 1 := by exact_mod_cast (le_max_right _ _).trans hpb.2.1
    push_cast
    constructor <;> linarith [Nat.cast_nonneg (α := ℝ) n]
  simp_rw [hz]
  simp only [tsum_zero, add_zero, Int.cast_natCast]

lemma profile_restrict_rectangle (f fr : Family) (hs : Structural f fr) (d : ℝ) :
    (rowsMeasure (profile f) d 0).restrict (rectangle d (d + 1) 0 (9 / 5)) =
      rowsMeasure (profile f) d 0 := by
  apply rowsMeasure_restrict_rectangle
  intro s hsp
  have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 s hsp
  have h0 : (0 : ℝ) ≤ (min s.ax s.bx : ℚ) := by exact_mod_cast hpb.1
  have h1 : ((max s.ax s.bx : ℚ) : ℝ) ≤ 1 := by exact_mod_cast hpb.2.1
  have h2 : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hpb.2.2.1
  have h3 : ((max s.ay s.yb : ℚ) : ℝ) ≤ ((9 / 5 : ℚ) : ℝ) := by exact_mod_cast hpb.2.2.2
  norm_num only [Rat.cast_div, Rat.cast_ofNat] at h3
  apply endpoints_in_rectangle <;> linarith

lemma periodic_local_above (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, 2 < p.2) :
    periodicLocalMeasure f δ A =
      ((integerWall f 2).map Prod.swap + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.1}) A := by
  have hc : cornerMeasure f δ A = 0 := by
    apply measure_zero_of_supported _ _ _ (corner_restrict_rectangle f fr hs δ hδ) hA
    apply Set.disjoint_left.mpr
    intro p hp hrect
    have h := hAb p hp
    exact (not_lt_of_ge hrect.2.2) h
  have hb : (Measure.sum fun n : ℕ => rowsMeasure (profile f) (2 + δ + n) 0) A = 0 := by
    rw [Measure.sum_apply _ hA]
    apply ENNReal.tsum_eq_zero.mpr
    intro n
    apply measure_zero_of_supported _ _ _ (profile_restrict_rectangle f fr hs _) hA
    apply Set.disjoint_left.mpr
    intro p hp hrect
    have h := hAb p hp
    linarith [hrect.2.2]
  have hl : (Measure.sum fun n : ℕ => (rowsMeasure (profile f) (2 + n) 0).map Prod.swap) A =
      ((integerWall f 2).map Prod.swap) A := by
    rw [Measure.sum_apply _ hA, Measure.map_apply measurable_swap hA,
      integerWall_positive f fr hs _ _ (measurable_swap hA) (fun p hp => hAb _ hp),
      Measure.sum_apply _ (measurable_swap hA)]
    apply tsum_congr
    intro n
    rw [Measure.map_apply measurable_swap hA]
  have ha : volume.restrict (localArea f) A =
      volume.restrict {p : Point | (f.UA : ℝ) ≤ p.1} A := by
    rw [Measure.restrict_apply hA, Measure.restrict_apply hA]
    congr 1
    ext p
    simp only [Set.mem_inter_iff, localArea, hs.2.2.2.1, Set.mem_prod, Set.mem_Ici, Set.mem_ofPred_eq]
    constructor
    · rintro ⟨hp, hx, hy⟩; exact ⟨hp, hx⟩
    · rintro ⟨hp, hx⟩
      have h := hAb p hp
      refine ⟨hp, hx, ?_⟩
      rw [hs.2.2.1]
      norm_num
      linarith
  simp only [periodicLocalMeasure,
    show (fun p : Point => (p.2, p.1)) = Prod.swap from rfl, Measure.add_apply, hc, hb, zero_add, add_zero, ha]
  exact congrArg (· + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.1} A) hl

lemma periodic_local_right (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, 2 + δ < p.1) :
    periodicLocalMeasure f δ A =
      (integerWall f (2 + δ) + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.2}) A := by
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hδ0 := hd0.trans hδ.1
  have hc : cornerMeasure f δ A = 0 := by
    apply measure_zero_of_supported _ _ _ (corner_restrict_rectangle f fr hs δ hδ) hA
    apply Set.disjoint_left.mpr
    intro p hp hrect
    exact (not_lt_of_ge hrect.1.2) (hAb p hp)
  have hl : (Measure.sum fun n : ℕ => (rowsMeasure (profile f) (2 + n) 0).map Prod.swap) A = 0 := by
    rw [Measure.sum_apply _ hA]
    apply ENNReal.tsum_eq_zero.mpr
    intro n
    rw [Measure.map_apply measurable_swap hA]
    apply measure_zero_of_supported _ _ _ (profile_restrict_rectangle f fr hs _)
      (measurable_swap hA)
    apply Set.disjoint_left.mpr
    intro p hp hrect
    have h := hAb _ hp
    change 2 + δ < p.2 at h
    linarith [hrect.2.2]
  have hb := (integerWall_positive f fr hs (2 + δ) A hA hAb).symm
  have ha : volume.restrict (localArea f) A =
      volume.restrict {p : Point | (f.UA : ℝ) ≤ p.2} A := by
    rw [Measure.restrict_apply hA, Measure.restrict_apply hA]
    congr 1
    ext p
    simp only [Set.mem_inter_iff, localArea, hs.2.2.2.1, Set.mem_prod, Set.mem_Ici, Set.mem_ofPred_eq]
    constructor
    · rintro ⟨hp, hx, hy⟩; exact ⟨hp, hy⟩
    · rintro ⟨hp, hy⟩
      refine ⟨hp, ?_, hy⟩
      have h := hAb p hp
      rw [hs.2.2.1]
      norm_num
      linarith
  simp only [periodicLocalMeasure,
    show (fun p : Point => (p.2, p.1)) = Prod.swap from rfl, Measure.add_apply, hc, zero_add, hl, add_zero, hb, ha]

noncomputable def translate (x y : ℝ) (p : Point) : Point := (x + p.1, y + p.2)

lemma translate_measurable (x y : ℝ) : Measurable (translate x y) := by
  unfold translate
  fun_prop

lemma translate_volume (x y : ℝ) : MeasurePreserving (translate x y) volume volume := by
  convert measurePreserving_add_left (volume : Measure Point) (x, y) using 1
  rfl

lemma translate_injective (x y : ℝ) : Function.Injective (translate x y) := by
  rintro ⟨px, py⟩ ⟨qx, qy⟩ hp
  have h : x + px = x + qx ∧ y + py = y + qy := Prod.mk.inj hp
  exact Prod.ext (by linarith [h.1]) (by linarith [h.2])

lemma translate_pose (x y : ℝ) (z : Point) (u : ℝ) :
    translate x y '' poseSquare z u = poseSquare (translate x y z) u := by
  rw [poseSquare, Set.image_image, poseSquare]
  congr 1
  funext p
  ext <;> simp only [translate] <;> ring

lemma horizontal_model_period (f : Family) (δ : ℝ) (m : ℤ) :
    (integerWall f (2 + δ) + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.2}).map
      (translate m 0) = integerWall f (2 + δ) + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.2} := by
  have hm := translate_measurable (m : ℝ) 0
  rw [Measure.map_add _ _ hm]
  have hw : (integerWall f (2 + δ)).map (translate m 0) = integerWall f (2 + δ) := by
    have he : translate (m : ℝ) 0 = (fun p : Point => ((m : ℝ) + p.1, p.2)) := by
      funext p; simp [translate]
    rw [he]
    exact integerWall_map_period f (2 + δ) m
  rw [hw]
  congr 1
  have h := (translate_volume (m : ℝ) 0).restrict_preimage
    (show MeasurableSet {p : Point | (f.UA : ℝ) ≤ p.2} by measurability)
  have he : translate (m : ℝ) 0 ⁻¹' {p : Point | (f.UA : ℝ) ≤ p.2} =
      {p : Point | (f.UA : ℝ) ≤ p.2} := by ext p; simp [translate]
  rw [he] at h
  exact h.map_eq

lemma vertical_model_period (f : Family) (m : ℤ) :
    ((integerWall f 2).map Prod.swap + volume.restrict {p : Point | (f.UA : ℝ) ≤ p.1}).map
      (translate 0 m) = (integerWall f 2).map Prod.swap +
        volume.restrict {p : Point | (f.UA : ℝ) ≤ p.1} := by
  have hm := translate_measurable 0 (m : ℝ)
  rw [Measure.map_add _ _ hm]
  have hw : ((integerWall f 2).map Prod.swap).map (translate 0 m) =
      (integerWall f 2).map Prod.swap := by
    rw [Measure.map_map hm measurable_swap]
    have he : translate 0 (m : ℝ) ∘ Prod.swap =
        Prod.swap ∘ (fun p : Point => ((m : ℝ) + p.1, p.2)) := by
      funext p; simp [translate]
    rw [he, ← Measure.map_map measurable_swap (by fun_prop), integerWall_map_period]
  rw [hw]
  congr 1
  have h := (translate_volume 0 (m : ℝ)).restrict_preimage
    (show MeasurableSet {p : Point | (f.UA : ℝ) ≤ p.1} by measurability)
  have he : translate 0 (m : ℝ) ⁻¹' {p : Point | (f.UA : ℝ) ≤ p.1} =
      {p : Point | (f.UA : ℝ) ≤ p.1} := by ext p; simp [translate]
  rw [he] at h
  exact h.map_eq

lemma invariant_pose_mass (μ : Measure Point) (x y : ℝ)
    (hμ : μ.map (translate x y) = μ) (z : Point) (u : ℝ) :
    μ (poseSquare (translate x y z) u) = μ (poseSquare z u) := by
  conv_lhs => rw [← hμ]
  rw [Measure.map_apply (translate_measurable _ _)
    (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _), ← translate_pose,
    Set.preimage_image_eq _ (translate_injective _ _)]

lemma periodic_pose_shift_y (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) (z : Point) (u : ℝ) (m : ℤ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16))
    (hz : 271 / 100 ≤ z.2) (hz' : 271 / 100 ≤ (translate 0 (m : ℝ) z).2) :
    periodicLocalMeasure f δ (poseSquare (translate 0 (m : ℝ) z) u) =
      periodicLocalMeasure f δ (poseSquare z u) := by
  have hhigh (c : Point) (hc : 271 / 100 ≤ c.2) :
      ∀ p ∈ poseSquare c u, 2 < p.2 := by
    intro p hp
    have h := (pose_abs_sub_le c p u hu hp).2
    rw [abs_le] at h
    have hw := halfWidth_lt_radius u
    linarith [h.1]
  rw [periodic_local_above f fr hs δ hδ _
    (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _) (hhigh _ hz'),
    periodic_local_above f fr hs δ hδ _
    (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _) (hhigh _ hz)]
  exact invariant_pose_mass _ 0 (m : ℝ) (vertical_model_period f m) z u

lemma periodic_pose_shift_x (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) (z : Point) (u : ℝ) (m : ℤ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16))
    (hz : 271 / 100 + δ ≤ z.1) (hz' : 271 / 100 + δ ≤ (translate (m : ℝ) 0 z).1) :
    periodicLocalMeasure f δ (poseSquare (translate (m : ℝ) 0 z) u) =
      periodicLocalMeasure f δ (poseSquare z u) := by
  have hhigh (c : Point) (hc : 271 / 100 + δ ≤ c.1) :
      ∀ p ∈ poseSquare c u, 2 + δ < p.1 := by
    intro p hp
    have h := (pose_abs_sub_le c p u hu hp).1
    rw [abs_le] at h
    have hw := halfWidth_lt_radius u
    linarith [h.1]
  rw [periodic_local_right f fr hs δ hδ _
    (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _) (hhigh _ hz'),
    periodic_local_right f fr hs δ hδ _
    (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _) (hhigh _ hz)]
  exact invariant_pose_mass _ (m : ℝ) 0 (horizontal_model_period f δ m) z u

end ClosedForm
