import ClosedForm.WallPeriod

open MeasureTheory
namespace ClosedForm

lemma segMeasure_restrict_of_interior (p q : Point) (A : Set Point) (hA : MeasurableSet A)
    (h : ∀ t ∈ Set.Ioo (0 : ℝ) 1, SquarePacking.segPt p q t ∈ A) :
    (SquarePacking.segMeasure p q).restrict A = SquarePacking.segMeasure p q := by
  apply Measure.restrict_eq_self_of_ae_mem
  unfold SquarePacking.segMeasure
  apply (ae_map_iff (SquarePacking.measurable_segPt p q).aemeasurable
    (p := fun x => x ∈ A) (by simpa only [Set.ofPred_mem_eq] using hA)).mpr
  rw [← restrict_Ioo_eq_restrict_Icc]
  exact (ae_restrict_mem measurableSet_Ioo).mono fun t ht => h t ht

lemma segMeasure_restrict_zero_of_interior (p q : Point) (A : Set Point) (hA : MeasurableSet A)
    (h : ∀ t ∈ Set.Ioo (0 : ℝ) 1, SquarePacking.segPt p q t ∉ A) :
    (SquarePacking.segMeasure p q).restrict A = 0 := by
  apply Measure.restrict_eq_zero.mpr
  have hae : ∀ᵐ x ∂SquarePacking.segMeasure p q, x ∉ A := by
    rw [SquarePacking.segMeasure,
      ae_map_iff (SquarePacking.measurable_segPt p q).aemeasurable hA.compl,
      ← restrict_Ioo_eq_restrict_Icc]
    exact (ae_restrict_mem measurableSet_Ioo).mono fun t ht => h t ht
  simpa only [ae_iff, not_not, Set.ofPred_mem_eq] using hae

/-- A profile cannot have a positive-mass vertical row at phase one. The
half-open extraction convention, rather than just the support box, is essential. -/
lemma profile_vertical_lt_one (f : Family) (hv : f.Valid) (s : Segment)
    (hs : s ∈ profile f) (hx : s.ax = s.bx) (hm : s.mass ≠ 0) : s.ax < 1 := by
  obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
  have hv' := hv.2.1 t (List.mem_append_right _ (List.mem_filter.mp ht).1)
  have hx' : t.ax = t.bx := by simpa [Segment.shift] using hx
  have hm' : t.mass ≠ 0 := hm
  have hy : t.ay ≠ t.yb := by
    intro hy
    exact hm' (hv'.2.2 ⟨hx', hy⟩)
  have ht' := (List.mem_filter.mp ht).2
  simp only [beq_iff_eq, hy, ↓reduceIte, Bool.and_eq_true, decide_eq_true_eq] at ht'
  change t.ax + (-3) < 1
  linarith [ht'.2]

/-- Endpoint lines carry only vertical rows; a horizontal row's endpoint has
zero segment mass. This is a one-dimensional argument, not planar a.e. equality. -/
theorem profile_phase_zero (f fr : Family) (hs : Structural f fr) :
    (rowsMeasure (profile f) 0 0).restrict {p : Point | p.1 = 0} =
      rowsMeasure (terminal f) 0 0 := by
  have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1
  have hv := profile_valid f hs.1
  have hA : MeasurableSet {p : Point | p.1 = 0} := by measurability
  have hone (s : Segment) (hsp : s ∈ profile f) :
      (segmentMeasure s 0 0).restrict {p : Point | p.1 = 0} =
        if s.ax = 0 ∧ s.bx = 0 then segmentMeasure s 0 0 else 0 := by
    have ha : (0 : ℝ) ≤ s.ax := by exact_mod_cast (hpb s hsp).1.trans (min_le_left _ _)
    have hb : (0 : ℝ) ≤ s.bx := by exact_mod_cast (hpb s hsp).1.trans (min_le_right _ _)
    by_cases hz : s.ax = 0 ∧ s.bx = 0
    · rw [if_pos hz, segmentMeasure, Measure.restrict_smul,
        segMeasure_restrict_of_interior _ _ _ hA]
      intro t ht
      simp [SquarePacking.segPt, hz.1, hz.2]
    · rw [if_neg hz, segmentMeasure, Measure.restrict_smul,
        segMeasure_restrict_zero_of_interior _ _ _ hA, smul_zero]
      intro t ht hp
      have hax : (s.ax : ℝ) ≠ 0 ∨ (s.bx : ℝ) ≠ 0 := by exact_mod_cast (not_and_or.mp hz)
      change (s.ax : ℝ) + 0 + t * ((s.bx : ℝ) + 0 - ((s.ax : ℝ) + 0)) = 0 at hp
      rcases hax with ha' | hb'
      · have ha' := lt_of_le_of_ne ha (Ne.symm ha')
        nlinarith [mul_pos (sub_pos.mpr ht.2) ha', mul_nonneg ht.1.le hb]
      · have hb' := lt_of_le_of_ne hb (Ne.symm hb')
        nlinarith [mul_pos ht.1 hb', mul_nonneg (sub_nonneg.mpr ht.2.le) ha]
  change (rowsMeasure (profile f) 0 0).restrict _ =
    rowsMeasure ((profile f).filter fun s => s.ax == 0 && s.bx == 0) 0 0
  have hlist (ss : List Segment)
      (he : ∀ s ∈ ss, (segmentMeasure s 0 0).restrict {p : Point | p.1 = 0} =
        if s.ax = 0 ∧ s.bx = 0 then segmentMeasure s 0 0 else 0) :
      (rowsMeasure ss 0 0).restrict {p : Point | p.1 = 0} =
        rowsMeasure (ss.filter fun s => s.ax == 0 && s.bx == 0) 0 0 := by
    induction ss with
    | nil => simp [rowsMeasure]
    | cons s ss ih =>
      have ht := ih (fun t ht => he t (by simp [ht]))
      simp only [rowsMeasure, List.map_cons, List.sum_cons, Measure.restrict_add]
      rw [he s (by simp)]
      by_cases hz : s.ax = 0 ∧ s.bx = 0
      · simpa [rowsMeasure, List.filter_cons, hz] using congrArg (segmentMeasure s 0 0 + ·) ht
      · simpa [rowsMeasure, List.filter_cons, hz] using ht
  exact hlist (profile f) hone

/-- Closed longitudinal strip; both terminal phases are included. -/
def wallStrip (m : ℕ) : Set Point := {p | 0 ≤ p.1 ∧ p.1 ≤ m}

lemma measurableSet_wallStrip (m : ℕ) : MeasurableSet (wallStrip m) := by
  unfold wallStrip
  measurability

lemma segment_integer_strip (f fr : Family) (hs : Structural f fr) (m : ℕ) (_hm : 1 ≤ m)
    (n : ℤ) (s : Segment) (hsp : s ∈ profile f) :
    (segmentMeasure s (n : ℝ) 0).restrict (wallStrip m) =
      if 0 ≤ n ∧ n < m then segmentMeasure s (n : ℝ) 0
      else if n = m ∧ s.ax = 0 ∧ s.bx = 0 then segmentMeasure s (n : ℝ) 0 else 0 := by
  have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 s hsp
  have ha0 : (0 : ℝ) ≤ s.ax := by exact_mod_cast hpb.1.trans (min_le_left _ _)
  have hb0 : (0 : ℝ) ≤ s.bx := by exact_mod_cast hpb.1.trans (min_le_right _ _)
  have ha1 : (s.ax : ℝ) ≤ 1 := by exact_mod_cast (le_max_left _ _).trans hpb.2.1
  have hb1 : (s.bx : ℝ) ≤ 1 := by exact_mod_cast (le_max_right _ _).trans hpb.2.1
  have hm0 : (0 : ℝ) ≤ m := Nat.cast_nonneg m
  by_cases hz : s.mass = 0
  · simp [segmentMeasure, hz]
  have hphase : (s.ax : ℝ) < 1 ∨ (s.bx : ℝ) < 1 := by
    by_contra h
    push Not at h
    have ha : s.ax = 1 := by exact_mod_cast le_antisymm ha1 h.1
    have hb : s.bx = 1 := by exact_mod_cast le_antisymm hb1 h.2
    have hv := profile_vertical_lt_one f hs.1 s hsp (ha.trans hb.symm) hz
    rw [ha] at hv
    exact (lt_irrefl _ hv)
  by_cases hi : 0 ≤ n ∧ n < m
  · rw [if_pos hi, segmentMeasure, Measure.restrict_smul,
      segMeasure_restrict_of_interior _ _ _ (measurableSet_wallStrip m)]
    intro t ht
    have hn0 : (0 : ℝ) ≤ n := by exact_mod_cast hi.1
    have hn1 : (n : ℝ) + 1 ≤ m := by exact_mod_cast (show n + 1 ≤ (m : ℤ) by omega)
    change 0 ≤ (s.ax : ℝ) + n + t * ((s.bx : ℝ) + n - ((s.ax : ℝ) + n)) ∧
      (s.ax : ℝ) + n + t * ((s.bx : ℝ) + n - ((s.ax : ℝ) + n)) ≤ m
    constructor <;> nlinarith [mul_nonneg ht.1.le hb0,
      mul_nonneg (sub_nonneg.mpr ht.2.le) ha0,
      mul_nonneg ht.1.le (sub_nonneg.mpr hb1),
      mul_nonneg (sub_nonneg.mpr ht.2.le) (sub_nonneg.mpr ha1)]
  rw [if_neg hi]
  by_cases he : n = m ∧ s.ax = 0 ∧ s.bx = 0
  · rw [if_pos he, segmentMeasure, Measure.restrict_smul,
      segMeasure_restrict_of_interior _ _ _ (measurableSet_wallStrip m)]
    intro t ht
    simp [wallStrip, SquarePacking.segPt, he.1, he.2.1, he.2.2]
  rw [if_neg he, segmentMeasure, Measure.restrict_smul,
    segMeasure_restrict_zero_of_interior _ _ _ (measurableSet_wallStrip m), smul_zero]
  intro t ht hp
  change 0 ≤ (s.ax : ℝ) + n + t * ((s.bx : ℝ) + n - ((s.ax : ℝ) + n)) ∧
      (s.ax : ℝ) + n + t * ((s.bx : ℝ) + n - ((s.ax : ℝ) + n)) ≤ m at hp
  by_cases hn : n < 0
  · have hn1 : (n : ℝ) ≤ -1 := by exact_mod_cast (show n ≤ -1 by omega)
    rcases hphase with ha | hb
    · nlinarith [mul_pos (sub_pos.mpr ht.2) (sub_pos.mpr ha),
        mul_nonneg ht.1.le (sub_nonneg.mpr hb1)]
    · nlinarith [mul_pos ht.1 (sub_pos.mpr hb),
        mul_nonneg (sub_nonneg.mpr ht.2.le) (sub_nonneg.mpr ha1)]
  · have hnge : (m : ℤ) ≤ n := by omega
    by_cases hnm : n = m
    · have hax : (s.ax : ℝ) ≠ 0 ∨ (s.bx : ℝ) ≠ 0 := by
        have hh : ¬(s.ax = 0 ∧ s.bx = 0) := fun h => he ⟨hnm, h⟩
        exact_mod_cast not_and_or.mp hh
      have hnR : (n : ℝ) = m := by exact_mod_cast hnm
      rw [hnR] at hp
      rcases hax with ha | hb
      · have ha := lt_of_le_of_ne ha0 (Ne.symm ha)
        nlinarith [mul_pos (sub_pos.mpr ht.2) ha, mul_nonneg ht.1.le hb0]
      · have hb := lt_of_le_of_ne hb0 (Ne.symm hb)
        nlinarith [mul_pos ht.1 hb, mul_nonneg (sub_nonneg.mpr ht.2.le) ha0]
    · have hnR : (m : ℝ) < n := by exact_mod_cast (lt_of_le_of_ne hnge (Ne.symm hnm))
      nlinarith [mul_nonneg (sub_nonneg.mpr ht.2.le) ha0, mul_nonneg ht.1.le hb0]

lemma rows_integer_strip (f fr : Family) (hs : Structural f fr) (m : ℕ) (hm : 1 ≤ m)
    (n : ℤ) :
    (rowsMeasure (profile f) (n : ℝ) 0).restrict (wallStrip m) =
      if 0 ≤ n ∧ n < m then rowsMeasure (profile f) (n : ℝ) 0
      else if n = m then rowsMeasure (terminal f) (n : ℝ) 0 else 0 := by
  have he := segment_integer_strip f fr hs m hm n
  unfold rowsMeasure
  change (Measure.restrictₗ (wallStrip m)) _ = _
  rw [map_list_sum]
  simp only [List.map_map, Function.comp_def, Measure.restrictₗ_apply]
  rw [List.map_congr_left he]
  by_cases hi : 0 ≤ n ∧ n < m
  · simp only [if_pos hi]
  · simp only [if_neg hi]
    by_cases hn : n = m
    · simp only [hn, true_and, ↓reduceIte]
      rw [List.sum_map_ite]
      simp only [List.map_const', List.sum_replicate, nsmul_zero, add_zero]
      congr 2
      apply List.filter_congr
      intro s _
      apply Bool.eq_iff_iff.mpr
      simp only [Bool.and_eq_true, beq_iff_eq, decide_eq_true_eq]
    · simp [hn]

/-- A finite wall includes one terminal phase-zero line in addition to its
whole periods. This identity is on the closed strip, including both seams. -/
theorem integerWall_restrict_strip (f fr : Family) (hs : Structural f fr)
    (m : ℕ) (hm : 1 ≤ m) :
    (integerWall f 0).restrict (wallStrip m) =
      ((List.range m).map fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0).sum +
        rowsMeasure (terminal f) (m : ℝ) 0 := by
  ext A hA
  rw [integerWall, Measure.restrict_sum _ (measurableSet_wallStrip m)]
  simp only [zero_add, Measure.sum_apply _ hA]
  simp_rw [rows_integer_strip f fr hs m hm]
  rw [tsum_of_nat_of_neg_add_one ENNReal.summable ENNReal.summable]
  have hneg (n : ℕ) :
      ((if 0 ≤ -(↑n + 1 : ℤ) ∧ -(↑n + 1 : ℤ) < m then
        rowsMeasure (profile f) ((-(↑n + 1 : ℤ) : ℤ) : ℝ) 0 else
        if -(↑n + 1 : ℤ) = m then rowsMeasure (terminal f) ((-(↑n + 1 : ℤ) : ℤ) : ℝ) 0
        else 0) : Measure Point) A = 0 := by
    have h0 : ¬(0 ≤ -(↑n + 1 : ℤ)) := by omega
    have he : -(↑n + 1 : ℤ) ≠ m := by omega
    simp only [h0, false_and, ↓reduceIte, he]
    rfl
  simp_rw [hneg]
  rw [tsum_zero, add_zero]
  rw [tsum_eq_sum (s := Finset.range (m + 1)) (fun n hn => ?_)]
  · rw [Finset.sum_range_succ, Measure.add_apply, sum_measures_apply, List.map_map]
    simp only [lt_self_iff_false, and_false, ↓reduceIte, Int.cast_natCast]
    congr 1
    trans ∑ n ∈ Finset.range m, rowsMeasure (profile f) (n : ℝ) 0 A
    · apply Finset.sum_congr rfl
      intro n hn
      have hi : (0 : ℤ) ≤ n ∧ (n : ℤ) < m :=
        ⟨by omega, by exact_mod_cast Finset.mem_range.mp hn⟩
      simp only [if_pos hi]
    · simpa only [List.toFinset_range, Function.comp_def] using
        List.sum_toFinset (fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0 A)
          (List.nodup_range (n := m))
  · have hi : ¬((0 : ℤ) ≤ n ∧ (n : ℤ) < m) := by
      simp only [Finset.mem_range, not_lt] at hn
      omega
    have he : (n : ℤ) ≠ m := by
      simp only [Finset.mem_range, not_lt] at hn
      omega
    simp only [if_neg hi, if_neg he]
    rfl

/-- Reversing a finite wall swaps its two closed terminal phases. -/
theorem finite_wall_reflection (f fr : Family) (hs : Structural f fr)
    (m : ℕ) (hm : 1 ≤ m) :
    ((((List.range m).map fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0).sum +
      rowsMeasure (terminal f) (m : ℝ) 0).map (fun p : Point => ((m : ℝ) - p.1, p.2))) =
      ((List.range m).map fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0).sum +
        rowsMeasure (terminal f) (m : ℝ) 0 := by
  rw [← integerWall_restrict_strip f fr hs m hm]
  have hpre : (fun p : Point => ((m : ℝ) - p.1, p.2)) ⁻¹' wallStrip m = wallStrip m := by
    ext p
    change (0 ≤ (m : ℝ) - p.1 ∧ (m : ℝ) - p.1 ≤ m) ↔ (0 ≤ p.1 ∧ p.1 ≤ m)
    constructor <;> rintro ⟨h1, h2⟩ <;> constructor <;> linarith
  have h := Measure.restrict_map (μ := integerWall f 0)
    (f := fun p : Point => ((m : ℝ) - p.1, p.2)) (by fun_prop) (measurableSet_wallStrip m)
  rw [hpre] at h
  rw [← h]
  have hr := integerWall_reflect f fr hs (m : ℤ)
  simp only [Int.cast_natCast] at hr
  rw [hr]

end ClosedForm
