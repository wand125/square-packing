import ClosedForm.Principle

open MeasureTheory
open scoped ENNReal
namespace ClosedForm

theorem volume_unitSq (z : Point) (θ : ℝ) :
    volume (UnitSquarePacking.unitSq z θ) = 1 := by
  letI : Fact (Module.finrank ℝ ℂ = 2) := ⟨Complex.finrank_real_complex⟩
  have hr : MeasurePreserving (UnitSquarePacking.rot θ) volume volume := by
    have h := Complex.volume_preserving_equiv_real_prod.comp
      ((Complex.orientation.rotation (θ : Real.Angle)).measurePreserving.comp
        Complex.volume_preserving_equiv_real_prod.symm)
    convert h using 1
    all_goals first | rfl |
      (ext p <;> simp [Function.comp_def, UnitSquarePacking.rot,
        Complex.rotation, Circle.coe_exp, Complex.exp_mul_I, Complex.mul_re,
        Complex.mul_im, ← Complex.ofReal_cos, ← Complex.ofReal_sin, add_comm])
  have hp := (measurePreserving_add_left volume z).comp hr
  have hi : Function.Injective (fun p => z + UnitSquarePacking.rot θ p) :=
    (UnitSquarePacking.place z θ).injective
  rw [UnitSquarePacking.unitSq, ← hp.measure_preimage_emb
    (UnitSquarePacking.place z θ).toMeasurableEquiv.measurableEmbedding,
    ]
  change volume ((fun p => z + UnitSquarePacking.rot θ p) ⁻¹'
    (fun p => z + UnitSquarePacking.rot θ p) ''
      (Set.Icc (-1 / 2) (1 / 2) ×ˢ Set.Icc (-1 / 2) (1 / 2))) = 1
  rw [Set.preimage_image_eq _ hi]
  rw [Measure.volume_eq_prod, Measure.prod_prod]
  norm_num [Real.volume_Icc]

theorem sqrt_le_minSide_area (N : ℕ) (hN : 1 ≤ N) :
    Real.sqrt (N : ℝ) ≤ UnitSquarePacking.minSide N := by
  apply le_of_forall_lt_imp_le_of_dense
  intro b hb
  by_cases hneg : b < 0
  · have hz : (0 : ℝ) ≤ UnitSquarePacking.minSide N := by
      apply le_minSide_of_measure 0 volume
      · intro z θ _; rw [volume_unitSq]
      · simpa [UnitSquarePacking.container, Measure.volume_eq_prod,
          Measure.prod_prod, Real.volume_Icc] using (show (0 : ℝ≥0∞) < N by exact_mod_cast hN)
    exact hneg.le.trans hz
  · have hb0 : 0 ≤ b := le_of_not_gt hneg
    apply le_minSide_of_measure b volume
    · intro z θ _; rw [volume_unitSq]
    · have hs : b ^ 2 < (N : ℝ) := (Real.lt_sqrt hb0).mp hb
      simp only [UnitSquarePacking.container, Measure.volume_eq_prod,
        Measure.prod_prod, Real.volume_Icc, sub_zero]
      rw [← ENNReal.ofReal_mul hb0, ← pow_two]
      exact_mod_cast
        (ENNReal.ofReal_lt_ofReal_iff (by positivity : (0 : ℝ) < N)).mpr hs

end ClosedForm
