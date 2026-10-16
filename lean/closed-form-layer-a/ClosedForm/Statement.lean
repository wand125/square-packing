import ClosedForm.Algebra

namespace ClosedForm

/-- The local-coverage conditional, assembled using the strict measure deficit. -/
theorem closed_form_of_covers
    (hcov : ∀ i : Fin 34, ∀ δ ∈ I i, LocalCovers (family i) (familyRight i) δ) :
    ∀ N : ℕ, 49 ≤ N → a N ≤ UnitSquarePacking.minSide N := by
  intro N hN
  have hk : 7 ≤ baseK N := by
    apply (Nat.le_floor_iff (Real.sqrt_nonneg _)).mpr
    rw [Real.le_sqrt (by norm_num) (by positivity)]
    exact_mod_cast hN
  apply a_le_of_bound N hN
  intro i δ hδ hmass
  apply le_minSide_of_globalMeasure (family i) (baseK N) N δ _ le_rfl
  · exact covers_k_of_covers7 i δ hδ (covers7_of_local i δ hδ (hcov i δ hδ)) _ hk
  · rw [total_mass i _ hk δ hδ]
    have hs := published_saving i δ hδ
    have hlt : ((baseK N : ℝ) + δ) ^ 2 - 4 * saving (family i) δ < N := by
      linarith
    exact_mod_cast (ENNReal.ofReal_lt_ofReal_iff (by positivity : (0 : ℝ) < N)).mpr hlt

end ClosedForm
