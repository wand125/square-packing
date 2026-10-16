import Mathlib

namespace ClosedForm

abbrev Point := ℝ × ℝ
abbrev QPoint := ℚ × ℚ

/-- SPEC §3.1: total mass, not density. -/
structure Segment where
  ax : ℚ
  ay : ℚ
  bx : ℚ
  yb : ℚ
  mass : ℚ
  deriving DecidableEq, Repr

structure VariableSegment where
  xl : ℚ
  y : ℚ
  rho : ℚ
  deriving DecidableEq, Repr

/-- Metadata is retained as text; it never adds mass. -/
structure Family where
  d0 : ℚ
  d1 : ℚ
  UA : ℚ
  F : List Segment
  T : List Segment
  V : List VariableSegment
  S_d0 : ℚ
  S_d1 : ℚ
  U : Option (List QPoint) := none
  eps : ℚ := 0
  bumps : String := ""
  edge_variant : Option String := none
  deriving Repr

def Segment.shift (s : Segment) (x y : ℚ) : Segment :=
  { s with ax := s.ax + x, ay := s.ay + y, bx := s.bx + x, yb := s.yb + y }

def Segment.transpose (s : Segment) : Segment :=
  ⟨s.ay, s.ax, s.yb, s.bx, s.mass⟩

/-- Canonical unoriented support for axis-parallel input rows. -/
def Segment.support (s : Segment) : QPoint × QPoint :=
  if s.ax + s.ay ≤ s.bx + s.yb then ((s.ax, s.ay), (s.bx, s.yb))
  else ((s.bx, s.yb), (s.ax, s.ay))

def massOn (ss : List Segment) (p : QPoint × QPoint) : ℚ :=
  ((ss.filter (fun s => s.support == p)).map Segment.mass).sum

/-- Combine coincident rows and subtract on each support; no clamping or deduplication of mass.
The structural obligations require the resulting masses to be nonnegative. -/
def subtractRows (xs ys : List Segment) : List Segment :=
  ((((xs ++ ys).map Segment.support).eraseDups).map fun p =>
    (⟨p.1.1, p.1.2, p.2.1, p.2.2, massOn xs p - massOn ys p⟩ : Segment)).filter
      (fun s => s.mass != 0)

/-- SPEC §3.2: period [3,4), translated to [0,1). -/
def profile (f : Family) : List Segment :=
  (f.T.filter fun s =>
    if s.ay == s.yb then 3 ≤ min s.ax s.bx && max s.ax s.bx ≤ 4
    else s.ax == s.bx && 3 ≤ s.ax && s.ax < 4).map (fun s => s.shift (-3) 0)

def periods (f : Family) (n : ℕ) : List Segment :=
  (List.range n).flatMap fun j => (profile f).map fun s => s.shift (2 + j) 0

def cornerF (f : Family) : List Segment :=
  subtractRows f.F ((periods f 7).map Segment.transpose)

def cornerT (f : Family) : List Segment := subtractRows f.T (periods f 7)

/-- Phase zero; placed separately at the last wall endpoint. -/
def terminal (f : Family) : List Segment :=
  (profile f).filter fun s => s.ax == 0 && s.bx == 0

def terminalMass (f : Family) : ℚ := ((terminal f).map Segment.mass).sum

def fixedCornerMass (f : Family) : ℚ :=
  ((cornerF f ++ cornerT f).map Segment.mass).sum

noncomputable def cornerMass (f : Family) (δ : ℝ) : ℝ :=
  (fixedCornerMass f : ℝ) + (f.V.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum

noncomputable def saving (f : Family) (δ : ℝ) : ℝ :=
  99 / 25 + (9 / 5) * δ - cornerMass f δ - terminalMass f

noncomputable def endpointLine (f : Family) (δ : ℝ) : ℝ :=
  f.S_d0 + ((f.S_d1 : ℝ) - f.S_d0) * (δ - f.d0) / ((f.d1 : ℝ) - f.d0)

/-- Basic JSON admissibility, separate from coverage. -/
def Segment.Valid (s : Segment) : Prop :=
  0 ≤ s.mass ∧ (s.ax = s.bx ∨ s.ay = s.yb) ∧
    (s.ax = s.bx ∧ s.ay = s.yb → s.mass = 0)

def Family.Valid (f : Family) : Prop :=
  f.d0 < f.d1 ∧ (∀ s ∈ f.F ++ f.T, s.Valid) ∧
    ∀ v ∈ f.V, 0 ≤ v.rho ∧ v.xl ≤ 2 + f.d0

end ClosedForm
