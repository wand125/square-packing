import ClosedForm.Measure

/-!
The square specialization of the scaling reduction in
`../rect-k2m4-lean/Sqpack/RectFam.lean` (Evan Daniel, MIT).
The scaling/disjointness proof is reused unchanged through upstream
`SquarePacking.not_packs_of_measure`, which uses `packing_le_measure`.
No symmetry assumption is needed, and the container side is real.
-/
open MeasureTheory
open scoped ENNReal
namespace ClosedForm

private lemma box_eq_container (s : ℝ) :
    SquarePacking.box s = UnitSquarePacking.container s := by
  ext p
  simp only [SquarePacking.box, UnitSquarePacking.container, Set.mem_prod,
    Set.mem_Icc, Set.mem_setOf_eq]
  tauto

private lemma packs_iff (N : ℕ) (s : ℝ) :
    SquarePacking.Packs N s ↔ UnitSquarePacking.Packs N s := by
  simp only [SquarePacking.Packs, UnitSquarePacking.Packs,
    UnitSquarePacking.interior_unitSq]
  simp only [UnitSquarePacking.unitSq_eq_setOf,
    SquarePacking.sq, SquarePacking.sqInt, SquarePacking.coord, ← box_eq_container]
  rfl

/-- A strict mass deficit at real side `b` excludes every smaller packing.
Finiteness on the container suffices; global finiteness is unnecessary. -/
theorem not_packs_of_measure (b : ℝ) (μ : Measure Point)
    (hcover : ∀ z θ, UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container b →
      1 ≤ μ (UnitSquarePacking.unitSq z θ))
    (N : ℕ) (hmass : μ (UnitSquarePacking.container b) < N)
    {s : ℝ} (hs : s < b) : ¬ UnitSquarePacking.Packs N s := by
  intro hp
  apply SquarePacking.not_packs_of_measure b μ ?_ N ?_ hs ((packs_iff N s).mpr hp)
  · intro z θ hz
    have heq : SquarePacking.sq z θ 1 = UnitSquarePacking.unitSq z θ := by
      rw [UnitSquarePacking.unitSq_eq_setOf]; rfl
    rw [heq]
    apply hcover
    simpa only [heq, box_eq_container] using hz
  · simpa only [box_eq_container] using hmass

/-- The measure principle in the common `minSide` specification. -/
theorem le_minSide_of_measure (b : ℝ) (μ : Measure Point)
    (hcover : ∀ z θ, UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container b →
      1 ≤ μ (UnitSquarePacking.unitSq z θ))
    (N : ℕ) (hmass : μ (UnitSquarePacking.container b) < N) :
    b ≤ UnitSquarePacking.minSide N := by
  apply le_csInf
  · refine ⟨N, (packs_iff N N).mp (SquarePacking.packs_grid N N ?_)⟩
    exact Nat.le_mul_self N
  · intro s hp
    exact le_of_not_gt fun hs => not_packs_of_measure b μ hcover N hmass hs hp

/-- Form used with the closed-form total at the larger side `k + δ`.
In particular any claimed `c < k + δ` is bounded by `minSide N`. -/
theorem le_minSide_of_globalMeasure (f : Family) (k N : ℕ) (δ c : ℝ)
    (hc : c ≤ (k : ℝ) + δ) (hcover : Covers f k δ)
    (hmass : globalMeasure f k δ (UnitSquarePacking.container ((k : ℝ) + δ)) < N) :
    c ≤ UnitSquarePacking.minSide N :=
  hc.trans (le_minSide_of_measure _ _ hcover N hmass)

end ClosedForm
