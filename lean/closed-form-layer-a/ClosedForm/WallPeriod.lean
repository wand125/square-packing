import ClosedForm.LocalReduction

open MeasureTheory
namespace ClosedForm

/-- The complete integer-period wall, used only where the corner is absent. -/
noncomputable def integerWall (f : Family) (d : ℝ) : Measure Point :=
  Measure.sum fun n : ℤ => rowsMeasure (profile f) (d + n) 0

lemma integerWall_translate (f : Family) (d t : ℝ) :
    (integerWall f d).map (fun p : Point => (t + p.1, p.2)) = integerWall f (t + d) := by
  unfold integerWall
  rw [map_measure_sum _ _ (by fun_prop)]
  congr 1
  funext n
  simpa only [zero_add, add_assoc] using rowsMeasure_translate (profile f) (d + n) 0 t 0

lemma integerWall_period (f : Family) (d : ℝ) (m : ℤ) :
    integerWall f (d + m) = integerWall f d := by
  unfold integerWall
  have he := Measure.sum_comp_equiv (Equiv.addLeft m)
    (fun n : ℤ => rowsMeasure (profile f) (d + n) 0)
  convert he using 1
  congr 1
  funext n
  change rowsMeasure (profile f) ((d + m) + n) 0 =
    rowsMeasure (profile f) (d + ((m + n : ℤ) : ℝ)) 0
  rw [Int.cast_add, add_assoc]

/-- Integer translations preserve the full wall measure. -/
theorem integerWall_map_period (f : Family) (d : ℝ) (m : ℤ) :
    (integerWall f d).map (fun p : Point => ((m : ℝ) + p.1, p.2)) = integerWall f d := by
  rw [integerWall_translate, add_comm (m : ℝ) d, integerWall_period]

/-- Structural reversal extends to reflection about every integer wall phase. -/
theorem integerWall_reflect (f fr : Family) (hs : Structural f fr) (m : ℤ) :
    (integerWall f 0).map (fun p : Point => ((m : ℝ) - p.1, p.2)) = integerWall f 0 := by
  have href := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2
  change (Measure.sum fun n : ℤ => rowsMeasure (profile f) (n : ℝ) 0).map reflectX =
    Measure.sum (fun n : ℤ => rowsMeasure (profile f) (n : ℝ) 0) at href
  have hzero : integerWall f 0 = Measure.sum (fun n : ℤ => rowsMeasure (profile f) (n : ℝ) 0) := by
    simp only [integerWall, zero_add]
  have he : (fun p : Point => ((m : ℝ) - p.1, p.2)) =
      (fun p : Point => ((m : ℝ) + p.1, p.2)) ∘ reflectX := by
    funext p; simp [reflectX, sub_eq_add_neg]
  rw [he, ← Measure.map_map (by fun_prop) reflectX_measurable, hzero, href, ← hzero,
    integerWall_map_period]

lemma unitSq_quarter_window (a : ℝ) (z : Point) (θ : ℝ)
    (hQ : UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container a)
    (hx : z.1 ≤ a / 2) (hy : z.2 ≤ a / 2) :
    UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container (a / 2 + 7072 / 10000) := by
  have hw : SquarePacking.wid θ / 2 < 7072 / 10000 := by
    have hi := Real.cos_sq_add_sin_sq θ
    have he : (|Real.cos θ| + |Real.sin θ|) ^ 2 ≤ 2 := by
      nlinarith [sq_nonneg (|Real.cos θ| - |Real.sin θ|),
        sq_abs (Real.cos θ), sq_abs (Real.sin θ)]
    unfold SquarePacking.wid
    by_contra h
    have h' := le_of_not_gt h
    nlinarith
  intro p hp
  have hp0 := hQ hp
  rw [unitSq_eq_upstream] at hp
  have hb := SquarePacking.abs_sub_le_wid hp
  rw [abs_le, abs_le] at hb
  exact ⟨⟨hp0.1.1, by linarith [hb.1.2]⟩, ⟨hp0.2.1, by linarith [hb.2.2]⟩⟩

end ClosedForm
