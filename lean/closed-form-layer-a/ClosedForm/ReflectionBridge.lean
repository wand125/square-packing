import ClosedForm.StructureDefs
import ClosedForm.MeasureBridge

namespace ClosedForm
open MeasureTheory

noncomputable def reflectX (p : Point) : Point := (-p.1, p.2)
lemma reflectX_measurable : Measurable reflectX := by unfold reflectX; fun_prop

lemma map_segMeasure_affine (g : Point → Point) (hg : Measurable g)
    (haff : ∀ a b t, g (SquarePacking.segPt a b t) =
      SquarePacking.segPt (g a) (g b) t) (a b : Point) :
    (SquarePacking.segMeasure a b).map g = SquarePacking.segMeasure (g a) (g b) := by
  rw [SquarePacking.segMeasure, Measure.map_map hg (SquarePacking.measurable_segPt a b)]
  unfold SquarePacking.segMeasure
  congr 1
  funext t
  exact haff a b t

lemma reflectX_affine (a b : Point) (t : ℝ) :
    reflectX (SquarePacking.segPt a b t) =
      SquarePacking.segPt (reflectX a) (reflectX b) t := by
  ext <;> simp [reflectX, SquarePacking.segPt] <;> ring

/-- Horizontal and nonzero-phase rows use -n-1; phase-zero vertical rows use -n. -/
def reflectionIndex (s : Segment) : ℤ :=
  if s.ay = s.yb then 1 else if s.ax = 0 then 0 else 1

def reflectionEquiv (c : ℤ) : ℤ ≃ ℤ where
  toFun n := -n-c
  invFun n := -n-c
  left_inv n := by ring
  right_inv n := by ring

lemma reflect_segment_period (s : Segment) (haxis : s.ax = s.bx ∨ s.ay = s.yb)
    (n : ℤ) :
    (segmentMeasure s (n:ℝ) 0).map reflectX =
      segmentMeasure (StructuralCheck.reflectProfile s)
        ((reflectionEquiv (reflectionIndex s) n : ℤ):ℝ) 0 := by
  rw [segmentMeasure, Measure.map_smul,
    map_segMeasure_affine reflectX reflectX_measurable reflectX_affine]
  by_cases hy : s.ay = s.yb
  · simp [StructuralCheck.reflectProfile, reflectionIndex, reflectionEquiv, hy,
      segmentMeasure, reflectX, Rat.cast_sub]
    congr 2
  · have hx : s.ax = s.bx := haxis.resolve_right hy
    by_cases hz : s.ax = 0
    · simp [StructuralCheck.reflectProfile, reflectionIndex, reflectionEquiv, hy, hz,
        segmentMeasure, reflectX, ← hx]
    · simp [StructuralCheck.reflectProfile, reflectionIndex, reflectionEquiv, hy, hz,
        segmentMeasure, reflectX, Rat.cast_sub, ← hx]
      congr 2

lemma map_measure_sum {ι : Type*} (μ : ι → Measure Point)
    (g : Point → Point) (hg : Measurable g) :
    (Measure.sum μ).map g = Measure.sum (fun i => (μ i).map g) := by
  ext A hA
  simp only [Measure.map_apply hg hA, Measure.sum_apply _ hA, Measure.sum_apply _ (hg hA)]

lemma reflect_single_wall (s : Segment) (haxis : s.ax = s.bx ∨ s.ay = s.yb) :
    (Measure.sum fun n : ℤ => segmentMeasure s (n:ℝ) 0).map reflectX =
      Measure.sum fun n : ℤ => segmentMeasure (StructuralCheck.reflectProfile s) (n:ℝ) 0 := by
  rw [map_measure_sum _ _ reflectX_measurable]
  simp_rw [reflect_segment_period s haxis]
  exact Measure.sum_comp_equiv (reflectionEquiv (reflectionIndex s))
    (fun n : ℤ => segmentMeasure (StructuralCheck.reflectProfile s) (n:ℝ) 0)

lemma reflect_rows_wall (xs : List Segment)
    (hx : ∀ s ∈ xs, s.ax = s.bx ∨ s.ay = s.yb) :
    (Measure.sum fun n : ℤ => rowsMeasure xs (n:ℝ) 0).map reflectX =
      Measure.sum fun n : ℤ => rowsMeasure (xs.map StructuralCheck.reflectProfile) (n:ℝ) 0 := by
  induction xs with
  | nil => simp [rowsMeasure, Measure.sum_zero]
  | cons s xs ih =>
    have hc (s : Segment) (xs : List Segment) (x : ℝ) :
        rowsMeasure (s::xs) x 0 = segmentMeasure s x 0 + rowsMeasure xs x 0 := rfl
    simp only [List.map_cons, hc, ← Measure.sum_add_sum,
      Measure.map_add _ _ reflectX_measurable]
    rw [reflect_single_wall s (hx s (by simp)), ih (fun s hs => hx s (by simp [hs]))]

/-- The finite reflected-profile identity implies the required full integer-wall symmetry. -/
theorem periodic_reflection (xs : List Segment)
    (hx : ∀ s ∈ xs, s.ax = s.bx ∨ s.ay = s.yb)
    (heq : ∀ dx : ℝ, rowsMeasure xs dx 0 =
      rowsMeasure (xs.map StructuralCheck.reflectProfile) dx 0) :
    (Measure.sum fun n : ℤ => rowsMeasure xs (n:ℝ) 0).map
      (fun p : Point => (-p.1, p.2)) =
      Measure.sum fun n : ℤ => rowsMeasure xs (n:ℝ) 0 := by
  change (Measure.sum fun n : ℤ => rowsMeasure xs (n:ℝ) 0).map reflectX = _
  rw [reflect_rows_wall xs hx]
  simp_rw [← heq]

#print axioms periodic_reflection
end ClosedForm
