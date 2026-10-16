import ClosedForm.Family

namespace ClosedForm

/-- The variable rows have constant densities, hence an affine total mass. -/
lemma variable_mass_affine (vs : List VariableSegment) (δ : ℝ) :
    (vs.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum =
      (vs.map fun v => (v.rho : ℝ)).sum * δ +
      (vs.map fun v => (v.rho : ℝ) * (2 - v.xl)).sum := by
  induction vs with
  | nil => simp
  | cons v vs ih => simp only [List.map_cons, List.sum_cons, ih]; ring

/-- Stronger than the structural version: the literal saving is affine for every family. -/
theorem saving_affine (f : Family) (δ : ℝ) :
    saving f δ = (9 / 5 - (f.V.map fun v => (v.rho : ℝ)).sum) * δ +
      (99 / 25 - fixedCornerMass f - terminalMass f -
        (f.V.map fun v => (v.rho : ℝ) * (2 - v.xl)).sum) := by
  rw [saving, cornerMass, variable_mass_affine]
  ring

/-- Endpoint domination covers the closed interval, hence also an open left endpoint. -/
theorem saving_le_of_endpoints (f : Family) (α β d0 d1 δ : ℝ)
    (h0 : α * d0 + β ≤ saving f d0) (h1 : α * d1 + β ≤ saving f d1)
    (hδ : δ ∈ Set.Icc d0 d1) : α * δ + β ≤ saving f δ := by
  rw [saving_affine] at h0 h1 ⊢
  rcases le_total α (9 / 5 - (f.V.map fun v => (v.rho : ℝ)).sum) with h | h
  · nlinarith [mul_nonneg (sub_nonneg.mpr h) (sub_nonneg.mpr hδ.1)]
  · nlinarith [mul_nonneg (sub_nonneg.mpr h) (sub_nonneg.mpr hδ.2)]

#print axioms saving_affine
#print axioms saving_le_of_endpoints
end ClosedForm
