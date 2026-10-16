import ClosedForm.Area
import ClosedForm.Mass
import Sqpack.ZeroMargin

open MeasureTheory
namespace ClosedForm

lemma rotateC4_measurable (a : ℝ) : Measurable (rotateC4 a) := by
  unfold rotateC4
  fun_prop

lemma rotateC4_four (a : ℝ) : (rotateC4 a)^[4] = id := by
  funext p
  ext <;> simp [Function.iterate_succ_apply, rotateC4]

lemma rotateC4_volume (a : ℝ) : MeasurePreserving (rotateC4 a) volume volume := by
  let : Fact (Module.finrank ℝ ℂ = 2) := ⟨Complex.finrank_real_complex⟩
  have hr : MeasurePreserving (UnitSquarePacking.rot (Real.pi / 2)) volume volume := by
    have h := Complex.volume_preserving_equiv_real_prod.comp
      ((Complex.orientation.rotation ((Real.pi / 2 : ℝ) : Real.Angle)).measurePreserving.comp
        Complex.volume_preserving_equiv_real_prod.symm)
    convert h using 1
    all_goals first | rfl |
      (ext p <;> simp [Function.comp_def, UnitSquarePacking.rot,
        Complex.rotation, Circle.coe_exp, Complex.exp_mul_I, Complex.mul_re,
        Complex.mul_im, add_comm])
  convert (measurePreserving_add_left volume (a, 0)).comp hr using 1
  ext p <;> simp [UnitSquarePacking.rot, rotateC4, sub_eq_add_neg]

lemma rotateC4_preimage_globalArea (k : ℕ) (δ : ℝ) :
    rotateC4 ((k : ℝ) + δ) ⁻¹' globalArea k δ = globalArea k δ := by
  ext p
  simp only [Set.mem_preimage, globalArea, rotateC4, Set.mem_prod, Set.mem_Icc]
  constructor <;> rintro ⟨⟨h1, h2⟩, h3, h4⟩ <;> constructor <;> constructor <;> linarith

/-- C4 invariance follows from the four placements; no reflection of corner
pieces is assumed. The central area occurs once and is itself C4 invariant. -/
theorem globalMeasure_rotateC4 (f : Family) (k : ℕ) (δ : ℝ) :
    (globalMeasure f k δ).map (rotateC4 ((k : ℝ) + δ)) = globalMeasure f k δ := by
  let a := (k : ℝ) + δ
  have hm := rotateC4_measurable a
  have harea : (volume.restrict (globalArea k δ)).map (rotateC4 a) =
      volume.restrict (globalArea k δ) := by
    have h := (rotateC4_volume a).restrict_preimage
      (measurableSet_Icc.prod measurableSet_Icc : MeasurableSet (globalArea k δ))
    change MeasurePreserving (rotateC4 ((k : ℝ) + δ))
      (volume.restrict (rotateC4 ((k : ℝ) + δ) ⁻¹' globalArea k δ))
      (volume.restrict (globalArea k δ)) at h
    rw [rotateC4_preimage_globalArea] at h
    exact h.map_eq
  let μ := cornerMeasure f δ + wallMeasure f k δ
  change ((List.map (fun j => μ.map (rotateC4 a)^[j]) (List.range 4)).sum +
    volume.restrict (globalArea k δ)).map (rotateC4 a) = _
  rw [Measure.map_add _ _ hm, harea]
  have hiter (j : ℕ) : Measurable (rotateC4 a)^[j] := hm.iterate j
  have hmap (j : ℕ) : (μ.map (rotateC4 a)^[j]).map (rotateC4 a) =
      μ.map (rotateC4 a)^[j+1] := by
    rw [Measure.map_map hm (hiter j), Function.iterate_succ']
  change _ = (List.map (fun j => μ.map (rotateC4 a)^[j]) (List.range 4)).sum +
    volume.restrict (globalArea k δ)
  congr 1
  norm_num only [List.range_succ, List.range_zero, List.map_append, List.map_cons,
    List.map_nil, List.sum_append, List.sum_cons, List.sum_nil, add_zero]
  simp only [Measure.map_add _ _ hm, hmap]
  rw [rotateC4_four]
  simp only [Function.iterate_zero, Measure.map_id, Measure.map_zero, zero_add]
  ac_rfl

lemma unitSq_measurable (z : Point) (θ : ℝ) : MeasurableSet (UnitSquarePacking.unitSq z θ) :=
  (UnitSquarePacking.place z θ).toMeasurableEquiv.measurableEmbedding.measurableSet_image.mpr
    (measurableSet_Icc.prod measurableSet_Icc)

lemma rotateC4_unitSq (a : ℝ) (z : Point) (θ : ℝ) :
    rotateC4 a '' UnitSquarePacking.unitSq z θ =
      UnitSquarePacking.unitSq (rotateC4 a z) (θ + Real.pi / 2) := by
  rw [UnitSquarePacking.unitSq, Set.image_image, UnitSquarePacking.unitSq]
  congr 1
  funext p
  ext <;> simp only [rotateC4, UnitSquarePacking.rot,
    Prod.fst_add, Prod.snd_add, Real.cos_add_pi_div_two, Real.sin_add_pi_div_two] <;> ring

lemma rotateC4_injective (a : ℝ) : Function.Injective (rotateC4 a) := by
  intro p q h
  have hx := congrArg Prod.snd h
  have hy := congrArg Prod.fst h
  dsimp [rotateC4] at hx hy
  ext <;> linarith

lemma unitSq_rotate_mass (f : Family) (k : ℕ) (δ : ℝ) (z : Point) (θ : ℝ) :
    globalMeasure f k δ
      (UnitSquarePacking.unitSq (rotateC4 ((k : ℝ) + δ) z) (θ + Real.pi / 2)) =
        globalMeasure f k δ (UnitSquarePacking.unitSq z θ) := by
  conv_lhs => rw [← globalMeasure_rotateC4 f k δ]
  rw [Measure.map_apply (rotateC4_measurable _) (unitSq_measurable _ _),
    ← rotateC4_unitSq, Set.preimage_image_eq _ (rotateC4_injective _)]

lemma unitSq_eq_upstream (z : Point) (θ : ℝ) :
    UnitSquarePacking.unitSq z θ = SquarePacking.sq z θ 1 := by
  rw [UnitSquarePacking.unitSq_eq_setOf]
  rfl

lemma unitSq_center_mem {a : ℝ} {z : Point} {θ : ℝ}
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container a) :
    z ∈ UnitSquarePacking.container a := by
  apply hQ
  rw [UnitSquarePacking.unitSq]
  refine ⟨(0,0), by norm_num, ?_⟩
  simp [UnitSquarePacking.rot]

lemma unitSq_rotated_subset {a : ℝ} {z : Point} {θ : ℝ}
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container a) :
    UnitSquarePacking.unitSq (rotateC4 a z) (θ + Real.pi / 2) ⊆
      UnitSquarePacking.container a := by
  rw [← rotateC4_unitSq]
  rintro p ⟨q, hq, rfl⟩
  exact show q ∈ rotateC4 a ⁻¹' UnitSquarePacking.container a from
    (rotateC4_preimage_container a).symm ▸ hQ hq

/-- The four closed quarters are covered by C4, even on either midline. -/
theorem lower_left_square (f : Family) (k : ℕ) (δ : ℝ) (z : Point) (θ : ℝ)
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container ((k : ℝ) + δ)) :
    ∃ z' θ', UnitSquarePacking.unitSq z' θ' ⊆ UnitSquarePacking.container ((k : ℝ) + δ) ∧
      z'.1 ≤ ((k : ℝ) + δ) / 2 ∧ z'.2 ≤ ((k : ℝ) + δ) / 2 ∧
      globalMeasure f k δ (UnitSquarePacking.unitSq z' θ') =
        globalMeasure f k δ (UnitSquarePacking.unitSq z θ) := by
  let a := (k : ℝ) + δ
  by_cases hx : z.1 ≤ a / 2
  · by_cases hy : z.2 ≤ a / 2
    · exact ⟨z, θ, hQ, hx, hy, rfl⟩
    · refine ⟨rotateC4 a z, θ + Real.pi / 2, unitSq_rotated_subset hQ, ?_, hx,
        unitSq_rotate_mass f k δ z θ⟩
      dsimp [rotateC4]; linarith
  · by_cases hy : z.2 ≤ a / 2
    · refine ⟨rotateC4 a (rotateC4 a (rotateC4 a z)),
        ((θ + Real.pi / 2) + Real.pi / 2) + Real.pi / 2,
        unitSq_rotated_subset (unitSq_rotated_subset (unitSq_rotated_subset hQ)), ?_, ?_, ?_⟩
      · dsimp [rotateC4]; linarith
      · dsimp [rotateC4]; linarith
      · rw [unitSq_rotate_mass, unitSq_rotate_mass, unitSq_rotate_mass]
    · refine ⟨rotateC4 a (rotateC4 a z), (θ + Real.pi / 2) + Real.pi / 2,
        unitSq_rotated_subset (unitSq_rotated_subset hQ), ?_, ?_, ?_⟩
      · dsimp [rotateC4]; linarith
      · dsimp [rotateC4]; linarith
      · rw [unitSq_rotate_mass, unitSq_rotate_mass]

end ClosedForm
