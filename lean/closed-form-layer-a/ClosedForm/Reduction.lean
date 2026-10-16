import ClosedForm.PeriodicShift

open MeasureTheory
namespace ClosedForm

lemma integer_shift_into_period (t L : ℝ) :
    ∃ m : ℤ, L ≤ (m : ℝ) + t ∧ (m : ℝ) + t < L + 1 := by
  refine ⟨-⌊t - L⌋, ?_, ?_⟩
  · have h := Int.floor_le (t - L)
    push_cast; linarith
  · have h := Int.lt_floor_add_one (t - L)
    push_cast; linarith

/-- Two integer shifts suffice, including interior squares: first above the
corner, then beyond its right edge. Each move stays in a periodic wall region. -/
theorem periodic_square_reduction (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) (z : Point) (u : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) (ha : Admissible z u) :
    ∃ z' : Point, Admissible z' u ∧ z'.1 ≤ 371 / 100 + δ ∧ z'.2 ≤ 371 / 100 ∧
      periodicLocalMeasure f δ (poseSquare z' u) = periodicLocalMeasure f δ (poseSquare z u) := by
  have hw := halfWidth_le_one u
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hδ0 := hd0.trans hδ.1
  obtain ⟨z1, ha1, hx1, hy1, hm1⟩ : ∃ z1 : Point,
      Admissible z1 u ∧ z1.1 = z.1 ∧ z1.2 ≤ 371 / 100 ∧
      periodicLocalMeasure f δ (poseSquare z1 u) = periodicLocalMeasure f δ (poseSquare z u) := by
    by_cases hy : z.2 ≤ 371 / 100
    · exact ⟨z, ha, rfl, hy, rfl⟩
    · obtain ⟨m, hm0, hm1⟩ := integer_shift_into_period z.2 (271 / 100)
      refine ⟨translate 0 (m : ℝ) z, ?_, by simp [translate], ?_, ?_⟩
      · exact ⟨by simpa [translate] using ha.1, by dsimp [translate]; linarith⟩
      · dsimp [translate]; linarith
      · exact periodic_pose_shift_y f fr hs δ hδ z u m hu (by linarith) hm0
  by_cases hx : z1.1 ≤ 371 / 100 + δ
  · exact ⟨z1, ha1, hx, hy1, hm1⟩
  · obtain ⟨m, hm0, hm2⟩ := integer_shift_into_period z1.1 (271 / 100 + δ)
    refine ⟨translate (m : ℝ) 0 z1, ?_, ?_, by simpa [translate] using hy1, ?_⟩
    · exact ⟨by dsimp [translate]; linarith, by simpa [translate] using ha1.2⟩
    · dsimp [translate]; linarith
    · exact (periodic_pose_shift_x f fr hs δ hδ z1 u m hu (by linarith) hm0).trans hm1

/-- The k = 7 window has three periods: its terminal phases are at x = 5 + δ
and y = 5. A reduced center is at most 3.71 (+δ horizontally), so its square
stays strictly before those phases because 3.71 + r < 5. This is the geometric
use of `three_periods`, as distinct from the quarter-clearance inequalities. -/
lemma reduced_pose_window (δ : ℝ) (hδ0 : 0 ≤ δ) (z : Point) (u : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) (ha : Admissible z u)
    (hx : z.1 ≤ 371 / 100 + δ) (hy : z.2 ≤ 371 / 100) :
    poseSquare z u ⊆ UnitSquarePacking.container (7 + δ) ∧
      poseSquare z u ⊆ localWindow 7 δ := by
  have hpoint (p : Point) (hp : p ∈ poseSquare z u) :
      (0 ≤ p.1 ∧ p.1 < 5 + δ) ∧ (0 ≤ p.2 ∧ p.2 < 5) := by
    have h := pose_abs_sub_le z p u hu hp
    rw [abs_le, abs_le] at h
    have hw := halfWidth_lt_radius u
    exact ⟨⟨by linarith [ha.1, h.1.1], by linarith [h.1.2]⟩,
      by linarith [ha.2, h.2.1], by linarith [h.2.2]⟩
  constructor
  · intro p hp
    have h := hpoint p hp
    exact ⟨⟨h.1.1, by linarith [h.1.2]⟩, h.2.1, by linarith [h.2.2]⟩
  · intro p hp
    have h := hpoint p hp
    change p.1 < (7 : ℝ) + δ - 2 ∧ p.2 < (7 : ℝ) - 2
    constructor <;> linarith [h.1.2, h.2.2]

lemma quarter_square_localWindow (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (z : Point) (θ : ℝ)
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container ((k : ℝ) + δ))
    (hx : z.1 ≤ ((k : ℝ) + δ) / 2) (hy : z.2 ≤ ((k : ℝ) + δ) / 2) :
    UnitSquarePacking.unitSq z θ ⊆ localWindow k δ := by
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hd1 : (f.d1 : ℝ) ≤ 1 := by exact_mod_cast hs.2.2.2.2.2.1
  have hδ0 := hd0.trans hδ.1
  have hδ1 := hδ.2.trans hd1
  have hgap := (quarter_window_clearance k hk δ hδ0 hδ1).1
  have hbox := unitSq_quarter_window _ z θ hQ hx hy
  intro p hp
  have h := hbox hp
  change p.1 < (k : ℝ) + δ - 2 ∧ p.2 < (k : ℝ) - 2
  constructor <;> linarith [h.1.2, h.2.2]

/-- Transport to k = 7, with the requested inequality and no coverage hypothesis.
C4, closed-window agreement, and integer wall shifts each preserve mass here. -/
theorem unitSq_mass_transport_structural (f fr : Family) (hs : Structural f fr)
    (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (k : ℕ) (hk : 7 ≤ k) (z : Point) (θ : ℝ)
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container ((k : ℝ) + δ)) :
    ∃ z' θ', UnitSquarePacking.unitSq z' θ' ⊆ UnitSquarePacking.container (7 + δ) ∧
      globalMeasure f 7 δ (UnitSquarePacking.unitSq z' θ') ≤
        globalMeasure f k δ (UnitSquarePacking.unitSq z θ) := by
  obtain ⟨c, φ, hQc, hx, hy, hmass⟩ := lower_left_square f k δ z θ hQ
  obtain ⟨u, hu, he⟩ := unitSq_record_orientation c φ
  have hpc : poseSquare c u ⊆ UnitSquarePacking.container ((k : ℝ) + δ) := he.symm ▸ hQc
  have hac := pose_admissible_of_subset c u _ hu hpc
  obtain ⟨c', hac', hx', hy', hm⟩ := periodic_square_reduction f fr hs δ hδ c u hu hac
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  obtain ⟨hQ', hwin'⟩ := reduced_pose_window δ (hd0.trans hδ.1) c' u hu hac' hx' hy'
  refine ⟨c', 2 * Real.arctan u, ?_, ?_⟩
  · simpa only [poseSquare_eq_unitSq] using hQ'
  · rw [← poseSquare_eq_unitSq,
      global_local_window f fr hs 7 (by decide) δ hδ _
        (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _) hwin', hm, he,
      ← global_local_window f fr hs k hk δ hδ _ (unitSq_measurable _ _)
        (quarter_square_localWindow f fr hs k hk δ hδ c φ hQc hx hy), hmass]

lemma localMeasure_le_periodic (f fr : Family) (hs : Structural f fr) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) : localMeasure f δ ≤ periodicLocalMeasure f δ := by
  have hp (dx : ℝ) : rowsMeasure (periods f 7) dx 0 ≤
      Measure.sum (fun n : ℕ => rowsMeasure (profile f) (2 + dx + n) 0) := by
    apply Measure.le_iff.mpr
    intro A hA
    rw [rowsMeasure_periods, sum_measures_apply, List.map_map, Measure.sum_apply _ hA]
    simp only [Function.comp_def]
    have heq := (List.sum_toFinset
      (fun n : ℕ => rowsMeasure (profile f) (2 + dx + n) 0 A)
      (List.nodup_range (n := 7))).symm
    simp only [List.toFinset_range] at heq
    rw [heq]
    exact ENNReal.sum_le_tsum _
  have hl := Measure.map_mono (hp 0) measurable_swap
  rw [← rowsMeasure_transpose, map_measure_sum _ _ measurable_swap] at hl
  simp only [add_zero] at hl
  have hd := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 δ hδ
  unfold localMeasure periodicLocalMeasure cornerMeasure
  rw [hd.1, hd.2]
  have h := add_le_add (add_le_add hl (hp δ))
    (le_rfl : (f.V.map fun v => variableMeasure v δ).sum ≤ _)
  have h' := add_le_add (add_le_add (le_rfl : rowsMeasure (cornerF f) 0 0 ≤ _)
    (le_rfl : rowsMeasure (cornerT f) δ 0 ≤ _)) h
  have h'' := add_le_add h' (le_rfl : volume.restrict (localArea f) ≤ _)
  convert h'' using 1 <;> ac_rfl

/-- Coverage from the four finite local record regions. Both record links are
proved separately; the finite local model also lies below its periodic extension. -/
theorem covers7_of_local_structural (fam famR : Family) (δ : ℝ)
    (hstruct : Structural fam famR) (hδ : δ ∈ Set.Icc (fam.d0 : ℝ) (fam.d1 : ℝ))
    (_hpos : 0 < δ) : LocalCovers fam famR δ → Covers7 fam δ := by
  intro hc z θ hQ
  obtain ⟨c, φ, hQc, hx, hy, hmass⟩ := lower_left_square fam 7 δ z θ hQ
  obtain ⟨u, hu, he⟩ := unitSq_record_orientation c φ
  have hac := pose_admissible_of_subset c u _ hu (he.symm ▸ hQc)
  obtain ⟨c', hac', hx', hy', hm⟩ := periodic_square_reduction fam famR hstruct δ hδ c u hu hac
  have hw0 : 0 ≤ halfWidth u := by
    exact div_nonneg (add_nonneg (poseCos_nonneg hu) (abs_nonneg _)) (by norm_num)
  have hc' := localCovers_bounded_window fam famR hstruct δ hδ hc c' u hu hac'
    (hw0.trans hac'.1) (hw0.trans hac'.2) (by linarith) (by linarith)
  have hper := (Measure.le_iff.mp (localMeasure_le_periodic fam famR hstruct δ hδ))
    (poseSquare c' u) (by rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _)
  have hcovered := hc'.trans hper
  rw [hm, he, ← global_local_window fam famR hstruct 7 (by decide) δ hδ _
    (unitSq_measurable _ _) (quarter_square_localWindow fam famR hstruct 7 (by decide) δ hδ
      c φ hQc hx hy), hmass] at hcovered
  exact hcovered

end ClosedForm
