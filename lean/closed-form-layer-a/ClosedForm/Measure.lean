import ClosedForm.Family
import Sqpack.MixedMeasure
import Sqpack.Spec

open MeasureTheory
open scoped ENNReal
namespace ClosedForm

noncomputable def segmentMeasure (s : Segment) (dx dy : ℝ) : Measure Point :=
  ENNReal.ofReal (s.mass : ℝ) • SquarePacking.segMeasure
    (s.ax + dx, s.ay + dy) (s.bx + dx, s.yb + dy)

noncomputable def rowsMeasure (ss : List Segment) (dx dy : ℝ) : Measure Point :=
  (ss.map fun s => segmentMeasure s dx dy).sum

noncomputable def variableMeasure (v : VariableSegment) (δ : ℝ) : Measure Point :=
  ENNReal.ofReal ((v.rho : ℝ) * (2 + δ - v.xl)) •
    SquarePacking.segMeasure (v.xl, v.y) (2 + δ, v.y)

noncomputable def cornerMeasure (f : Family) (δ : ℝ) : Measure Point :=
  rowsMeasure (cornerF f) 0 0 + rowsMeasure (cornerT f) δ 0 +
    (f.V.map fun v => variableMeasure v δ).sum

/-- Optional convex polygon; otherwise the actual unbounded quadrant (SPEC §§2.3,3.1). -/
def localArea (f : Family) : Set Point :=
  match f.U with
  | none => Set.Ici (f.UA : ℝ) ×ˢ Set.Ici (f.UA : ℝ)
  | some vs => convexHull ℝ {p | ∃ v ∈ vs, p = ((v.1 : ℝ), (v.2 : ℝ))}

/-- Finite JSON model used by the records; all four checked windows fit within it. -/
noncomputable def localMeasure (f : Family) (δ : ℝ) : Measure Point :=
  rowsMeasure f.F 0 0 + rowsMeasure f.T δ 0 +
    (f.V.map fun v => variableMeasure v δ).sum + volume.restrict (localArea f)

/-- Infinite periodic model for localization, distinguished from the finite JSON window. -/
noncomputable def periodicLocalMeasure (f : Family) (δ : ℝ) : Measure Point :=
  cornerMeasure f δ +
    Measure.sum (fun n : ℕ => rowsMeasure (profile f) (2 + δ + n) 0) +
    Measure.sum (fun n : ℕ =>
      Measure.map (fun p : Point => (p.2, p.1)) (rowsMeasure (profile f) (2 + n) 0)) +
    volume.restrict (localArea f)

noncomputable def rotateC4 (a : ℝ) (p : Point) : Point := (a - p.2, p.1)

noncomputable def wallMeasure (f : Family) (k : ℕ) (δ : ℝ) : Measure Point :=
  ((List.range (k - 4)).map fun n => rowsMeasure (profile f) (2 + δ + n) 0).sum +
    rowsMeasure (terminal f) (2 + δ + (k - 4 : ℕ)) 0

def globalArea (k : ℕ) (δ : ℝ) : Set Point :=
  Set.Icc (9 / 5) ((k : ℝ) + δ - 9 / 5) ×ˢ
    Set.Icc (9 / 5) ((k : ℝ) + δ - 9 / 5)

/-- SPEC §2.1: four rotations, not reflections; the central area occurs just once. -/
noncomputable def globalMeasure (f : Family) (k : ℕ) (δ : ℝ) : Measure Point :=
  ((List.range 4).map fun j =>
    Measure.map ((rotateC4 ((k : ℝ) + δ))^[j])
      (cornerMeasure f δ + wallMeasure f k δ)).sum + volume.restrict (globalArea k δ)

inductive Region | left | straddle | top | right
  deriving DecidableEq, Repr

/-- Right-region coordinates are already shifted: z' = (z.x - δ,z.y). -/
def regionSet (f : Family) : Region → Set Point
  | .left => Set.Icc 0 (167 / 100) ×ˢ Set.Icc 0 (19 / 5)
  | .straddle => Set.Icc (167 / 100) (251 / 100 + (f.d1 : ℝ)) ×ˢ Set.Icc 0 (272 / 100)
  | .top => Set.Icc (167 / 100) (251 / 100 + (f.d1 : ℝ)) ×ˢ Set.Icc (272 / 100) (19 / 5)
  | .right => Set.Icc (251 / 100) (19 / 5) ×ˢ Set.Icc 0 (19 / 5)

noncomputable def poseCos (u : ℝ) : ℝ := (1 - u ^ 2) / (1 + u ^ 2)
noncomputable def poseSin (u : ℝ) : ℝ := 2 * u / (1 + u ^ 2)
noncomputable def halfWidth (u : ℝ) : ℝ := (poseCos u + |poseSin u|) / 2

/-- SPEC §4.1, closed square using the rational half-angle parameter. -/
def poseSquare (z : Point) (u : ℝ) : Set Point :=
  (fun p : Point => (z.1 + poseCos u * p.1 - poseSin u * p.2,
    z.2 + poseSin u * p.1 + poseCos u * p.2)) ''
      (Set.Icc (-1 / 2) (1 / 2) ×ˢ Set.Icc (-1 / 2) (1 / 2))

def Admissible (z : Point) (u : ℝ) : Prop := halfWidth u ≤ z.1 ∧ halfWidth u ≤ z.2

/-- Only leaf coverage; structural checks and saving checks are separate. -/
def LocalCovers (fam famR : Family) (δ : ℝ) : Prop :=
  ∀ r : Region, ∀ z ∈ regionSet fam r, ∀ u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16),
    Admissible z u →
      1 ≤ localMeasure (if r = .right then famR else fam) δ (poseSquare z u)

def Covers (fam : Family) (k : ℕ) (δ : ℝ) : Prop :=
  ∀ z θ, UnitSquarePacking.unitSq z θ ⊆ UnitSquarePacking.container ((k : ℝ) + δ) →
    1 ≤ globalMeasure fam k δ (UnitSquarePacking.unitSq z θ)

def Covers7 (fam : Family) (δ : ℝ) : Prop := Covers fam 7 δ

/-- SPEC §§2.1,3.2–3.3: algebraic structure required in addition to leaf coverage.
Support subtraction is checked as a nonnegative decomposition, never assumed silently. -/
def Structural (f fr : Family) : Prop :=
  f.Valid ∧ fr.Valid ∧ f.UA = 9 / 5 ∧ f.U = none ∧
  0 ≤ f.d0 ∧ f.d1 ≤ 1 ∧
  fr.F = f.T ∧ fr.T = [] ∧ fr.V = [] ∧ fr.UA = f.UA ∧ fr.U = none ∧
  fr.d0 = f.d0 ∧ fr.d1 = f.d1 ∧
  ((profile f).map Segment.mass).sum = 9 / 5 ∧
  (∀ s ∈ cornerF f ++ cornerT f, s.Valid) ∧
  (∀ s ∈ cornerF f, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 2 + f.d0 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2) ∧
  (∀ s ∈ cornerT f, s.ax = 2 ∧ s.bx = 2 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2) ∧
  (∀ v ∈ f.V, 0 ≤ v.xl ∧ 0 ≤ v.y ∧ v.y ≤ 2) ∧
  (∀ s ∈ profile f, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 1 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 9 / 5) ∧
  (∀ δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ),
    rowsMeasure f.F 0 0 = rowsMeasure (cornerF f) 0 0 +
      rowsMeasure ((periods f 7).map Segment.transpose) 0 0 ∧
    rowsMeasure f.T δ 0 = rowsMeasure (cornerT f) δ 0 + rowsMeasure (periods f 7) δ 0) ∧
  (let wall := Measure.sum (fun n : ℤ => rowsMeasure (profile f) (n : ℝ) 0)
   Measure.map (fun p : Point => (-p.1, p.2)) wall = wall)

end ClosedForm
