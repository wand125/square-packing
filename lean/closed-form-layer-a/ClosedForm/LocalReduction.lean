import ClosedForm.LocalWindow
import ClosedForm.Rotation

open MeasureTheory
namespace ClosedForm

lemma halfWidth_lt_radius (u : ℝ) : halfWidth u < 7072 / 10000 := by
  have hd : 1 + u ^ 2 ≠ 0 := by positivity
  have hid : poseCos u ^ 2 + poseSin u ^ 2 = 1 := by
    unfold poseCos poseSin
    field_simp
    ring
  have hsq : (poseCos u + |poseSin u|) ^ 2 ≤ 2 := by
    nlinarith [sq_nonneg (poseCos u - |poseSin u|), sq_abs (poseSin u)]
  unfold halfWidth
  by_contra h
  have h' : 7072 / 10000 ≤ (poseCos u + |poseSin u|) / 2 := le_of_not_gt h
  nlinarith

lemma poseSquare_eq_unitSq (z : Point) (u : ℝ) :
    poseSquare z u = UnitSquarePacking.unitSq z (2 * Real.arctan u) := by
  simp only [poseSquare, UnitSquarePacking.unitSq, UnitSquarePacking.rot,
    SquarePacking.cos_two_arctan, SquarePacking.sin_two_arctan, poseCos, poseSin]
  congr 1
  funext p
  ext <;> simp only [Prod.fst_add, Prod.snd_add] <;> ring

lemma poseCos_nonneg {u : ℝ} (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) :
    0 ≤ poseCos u := by
  apply div_nonneg _ (by positivity)
  nlinarith [hu.1, hu.2, sq_nonneg (u - (-13 / 32)),
    mul_nonneg (sub_nonneg.mpr hu.1) (sub_nonneg.mpr hu.2)]

lemma pose_abs_sub_le (z p : Point) (u : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) (hp : p ∈ poseSquare z u) :
    |p.1 - z.1| ≤ halfWidth u ∧ |p.2 - z.2| ≤ halfWidth u := by
  rw [poseSquare_eq_unitSq, unitSq_eq_upstream] at hp
  have h := SquarePacking.abs_sub_le_wid hp
  simp only [SquarePacking.wid, SquarePacking.cos_two_arctan, SquarePacking.sin_two_arctan] at h
  change |p.1 - z.1| ≤ (|poseCos u| + |poseSin u|) / 2 ∧
    |p.2 - z.2| ≤ (|poseCos u| + |poseSin u|) / 2 at h
  simpa only [abs_of_nonneg (poseCos_nonneg hu), halfWidth] using h

lemma poseSquare_subset_record_window (f : Family) (hd1 : f.d1 ≤ 1)
    (r : Region) (z : Point) (hz : z ∈ regionSet f r) (u : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) (ha : Admissible z u) :
    poseSquare z u ⊆ UnitSquarePacking.container (24 / 5) := by
  have hd1' : (f.d1 : ℝ) ≤ 1 := by exact_mod_cast hd1
  have hx : z.1 ≤ 19 / 5 := by
    cases r <;> change (_ ∧ _) ∧ (_ ∧ _) at hz <;> linarith [hz.1.2]
  have hy : z.2 ≤ 19 / 5 := by
    cases r <;> change (_ ∧ _) ∧ (_ ∧ _) at hz <;> linarith [hz.2.2]
  intro p hp
  obtain ⟨hp1, hp2⟩ := pose_abs_sub_le z p u hu hp
  rw [abs_le] at hp1 hp2
  have hw := halfWidth_lt_radius u
  exact ⟨⟨by linarith [ha.1], by linarith⟩, ⟨by linarith [ha.2], by linarith⟩⟩

lemma rowsMeasure_translate (ss : List Segment) (dx dy x y : ℝ) :
    (rowsMeasure ss dx dy).map (fun p : Point => (x + p.1, y + p.2)) =
      rowsMeasure ss (x + dx) (y + dy) := by
  have hm : Measurable (fun p : Point => (x + p.1, y + p.2)) := by fun_prop
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    change (segmentMeasure s dx dy + rowsMeasure ss dx dy).map _ =
      segmentMeasure s (x + dx) (y + dy) + rowsMeasure ss (x + dx) (y + dy)
    rw [Measure.map_add _ _ hm, ih]
    congr 1
    simp only [segmentMeasure]
    rw [Measure.map_smul, map_segMeasure_affine _ hm (by
      intros; ext <;> simp [SquarePacking.segPt] <;> ring)]
    congr 2 <;> ext <;> simp <;> ring

lemma translate_poseSquare (z : Point) (u δ : ℝ) :
    (fun p : Point => (δ + p.1, p.2)) '' poseSquare z u =
      poseSquare (δ + z.1, z.2) u := by
  rw [poseSquare, Set.image_image, poseSquare]
  congr 1
  funext p
  ext <;> ring

/-- Shifting the right family retains precisely T and a smaller quadrant.
Discarding F and V is a measure inequality, so boundary mass is retained. -/
theorem right_local_le (f fr : Family) (hs : Structural f fr) (δ : ℝ) (hδ : 0 ≤ δ) :
    (localMeasure fr δ).map (fun p : Point => (δ + p.1, p.2)) ≤ localMeasure f δ := by
  rcases hs with ⟨_, _, hua, hu, _, _, hF, hT, hV, hUA, hU, _⟩
  let tr : Point → Point := fun p => (δ + p.1, p.2)
  have hm : Measurable tr := by dsimp [tr]; fun_prop
  have hmp : MeasurePreserving tr volume volume := by
    convert measurePreserving_add_left (volume : Measure Point) (δ, 0) using 1
    ext p <;> simp [tr, Prod.fst_add, Prod.snd_add]
  let shifted : Set Point := Set.Ici ((f.UA : ℝ) + δ) ×ˢ Set.Ici (f.UA : ℝ)
  have hpre : tr ⁻¹' shifted = localArea fr := by
    ext p
    simp only [tr, shifted, localArea, hU, hUA, Set.mem_preimage, Set.mem_prod, Set.mem_Ici]
    constructor <;> rintro ⟨h1, h2⟩ <;> exact ⟨by linarith, h2⟩
  have ha : (volume.restrict (localArea fr)).map tr = volume.restrict shifted := by
    have h := hmp.restrict_preimage (measurableSet_Ici.prod measurableSet_Ici : MeasurableSet shifted)
    change MeasurePreserving tr (volume.restrict (tr ⁻¹' shifted)) (volume.restrict shifted) at h
    rw [hpre] at h
    exact h.map_eq
  have ha_le : volume.restrict shifted ≤ volume.restrict (localArea f) := by
    apply Measure.restrict_mono
    · intro p hp
      change ((f.UA : ℝ) + δ ≤ p.1) ∧ (f.UA : ℝ) ≤ p.2 at hp
      simp only [localArea, hu, Set.mem_prod, Set.mem_Ici]
      exact ⟨by linarith [hp.1], hp.2⟩
    · exact le_rfl
  have hrows : (rowsMeasure f.T 0 0).map tr = rowsMeasure f.T δ 0 := by
    simpa only [zero_add, add_zero] using rowsMeasure_translate f.T 0 0 δ 0
  simp only [localMeasure, hF, hT, hV, rowsMeasure, List.map_nil, List.sum_nil, add_zero]
  change ((rowsMeasure f.T 0 0) + volume.restrict (localArea fr)).map tr ≤ _
  rw [Measure.map_add _ _ hm, hrows, ha]
  apply add_le_add _ ha_le
  exact Measure.le_add_right (Measure.le_add_left le_rfl)

/-- The four record rectangles cover the remaining bounded center window.
In the right rectangle we use the right family in shifted coordinates. -/
theorem localCovers_bounded_window (f fr : Family) (hs : Structural f fr)
    (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) (hc : LocalCovers f fr δ)
    (z : Point) (u : ℝ) (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16))
    (ha : Admissible z u) (hx0 : 0 ≤ z.1) (hy0 : 0 ≤ z.2)
    (hx : z.1 ≤ 19 / 5 + δ) (hy : z.2 ≤ 19 / 5) :
    1 ≤ localMeasure f δ (poseSquare z u) := by
  by_cases hl : z.1 ≤ 167 / 100
  · exact hc .left z ⟨⟨hx0, hl⟩, hy0, hy⟩ u hu ha
  by_cases hm : z.1 ≤ 251 / 100 + (f.d1 : ℝ)
  · by_cases hb : z.2 ≤ 272 / 100
    · exact hc .straddle z ⟨⟨by linarith, hm⟩, hy0, hb⟩ u hu ha
    · exact hc .top z ⟨⟨by linarith, hm⟩, by linarith, hy⟩ u hu ha
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hnonneg : 0 ≤ δ := hd0.trans hδ.1
  have hright := hc .right (z.1 - δ, z.2)
    ⟨⟨by dsimp; linarith [hδ.2], by dsimp; linarith⟩, hy0, hy⟩ u hu
    ⟨by have hw := halfWidth_le_one u; dsimp; linarith [hδ.2], ha.2⟩
  have hle := right_local_le f fr hs δ hnonneg
  have he : (fun p : Point => (δ + p.1, p.2)) ⁻¹' poseSquare z u =
      poseSquare (z.1 - δ, z.2) u := by
    have him := translate_poseSquare (z.1 - δ, z.2) u δ
    simp only [add_sub_cancel] at him
    rw [← him, Set.preimage_image_eq]
    rintro ⟨px, py⟩ ⟨qx, qy⟩ hp
    have hh : δ + px = δ + qx ∧ py = qy := Prod.mk.inj hp
    exact Prod.ext (by linarith [hh.1]) hh.2
  have hmeas : MeasurableSet (poseSquare z u) := by
    rw [poseSquare_eq_unitSq]; exact unitSq_measurable _ _
  have hval := Measure.le_iff.mp hle _ hmeas
  rw [Measure.map_apply (by fun_prop) hmeas, he] at hval
  exact hright.trans hval

end ClosedForm
