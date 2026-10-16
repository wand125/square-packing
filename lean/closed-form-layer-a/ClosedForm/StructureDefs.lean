import ClosedForm.Measure

namespace ClosedForm

namespace StructuralCheck

/-- A density jump on a supporting line: orientation 0 = horizontal, 1 = vertical. -/
structure Event where
  orientation : Nat
  line : ℚ
  position : ℚ
  jump : ℚ
  deriving DecidableEq, Repr

/-- A maximal constant-density interval; mass = density * (hi - lo). -/
structure Cell where
  orientation : Nat
  line : ℚ
  lo : ℚ
  hi : ℚ
  density : ℚ
  deriving DecidableEq, Repr

def sameKey (a b : Event) : Bool :=
  a.orientation == b.orientation && a.line == b.line && a.position == b.position

def keyLE (a b : Event) : Bool :=
  a.orientation < b.orientation || (a.orientation == b.orientation &&
    (a.line < b.line || (a.line == b.line && a.position ≤ b.position)))

/-- Valid zero-length rows have zero mass and contribute no events. -/
def events (s : Segment) : List Event :=
  let horizontal := s.ay == s.yb
  let lo := if horizontal then min s.ax s.bx else min s.ay s.yb
  let hi := if horizontal then max s.ax s.bx else max s.ay s.yb
  let o := if horizontal then 0 else 1
  let line := if horizontal then s.ay else s.ax
  if lo == hi then [] else
    let d := s.mass / (hi - lo)
    [⟨o, line, lo, d⟩, ⟨o, line, hi, -d⟩]

/-- Input is sorted. Combine all coincident jumps, including cancellation. -/
def collect (xs : List Event) : List Event :=
  xs.foldr (fun e acc => match acc with
    | [] => [e]
    | a :: rest => if sameKey e a then { a with jump := e.jump + a.jump } :: rest
      else e :: acc) []

/-- Zero jumps are removed before this sweep, so adjacent equal densities are merged. -/
def sweep : List Event → ℚ → List Cell
  | [], _ => []
  | [_], _ => []
  | a :: b :: rest, d =>
    let next := d + a.jump
    if a.orientation == b.orientation && a.line == b.line then
      let tail := sweep (b :: rest) next
      if next == 0 then tail else ⟨a.orientation, a.line, a.position, b.position, next⟩ :: tail
    else sweep (b :: rest) 0

/-- Sorted rational table, independent of proportional subdivision and duplicate rows.
Soundness is asserted only on valid rows: negative masses are not ENNReal-linear. -/
def canonical (ss : List Segment) : List Cell :=
  sweep ((collect ((ss.flatMap events).mergeSort keyLE)).filter (fun e => e.jump != 0)) 0

/-- Reflection modulo integer translation. Phase-zero vertical lines remain at zero;
horizontal intervals reflect about 1/2. Their endpoints carry no atoms. -/
def reflectProfile (s : Segment) : Segment :=
  if s.ay == s.yb then { s with ax := 1 - s.ax, bx := 1 - s.bx }
  else
    let x := if s.ax == 0 then 0 else 1 - s.ax
    { s with ax := x, bx := x }

def valid (s : Segment) : Bool :=
  decide (0 ≤ s.mass) && (s.ax == s.bx || s.ay == s.yb) &&
    (!(s.ax == s.bx && s.ay == s.yb) || s.mass == 0)

/-- Published coordinates lie on the fifth-unit grid; masses need not do so. -/
def grid (x : ℚ) : Bool := (5 * x).den == 1

def rowGrid (s : Segment) : Bool := grid s.ax && grid s.ay && grid s.bx && grid s.yb

def familyValid (f : Family) : Bool :=
  decide (f.d0 < f.d1) && (f.F ++ f.T).all valid &&
    f.V.all (fun v => decide (0 ≤ v.rho ∧ v.xl ≤ 2 + f.d0))

end StructuralCheck

/-- Entirely rational, executable sufficient conditions for `Structural`.
The old semantic predicate remains unchanged for existing clients. -/
def StructuralDec (f fr : Family) : Bool :=
  let p := profile f
  let cf := cornerF f
  let ct := cornerT f
  let ps := periods f 7
  StructuralCheck.familyValid f && StructuralCheck.familyValid fr &&
  decide (f.UA = 9 / 5 ∧ f.U = none ∧ 0 ≤ f.d0 ∧ f.d1 ≤ 1) &&
  decide (fr.F = f.T ∧ fr.T = [] ∧ fr.V = [] ∧ fr.UA = f.UA ∧ fr.U = none ∧
    fr.d0 = f.d0 ∧ fr.d1 = f.d1) &&
  (f.F ++ f.T).all StructuralCheck.rowGrid &&
  f.V.all (fun v => StructuralCheck.grid v.xl && StructuralCheck.grid v.y) &&
  decide ((p.map Segment.mass).sum = 9 / 5) &&
  (cf ++ ct).all StructuralCheck.valid &&
  cf.all (fun s => decide (0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 2 + f.d0 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2)) &&
  ct.all (fun s => decide (s.ax = 2 ∧ s.bx = 2 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2)) &&
  f.V.all (fun v => decide (0 ≤ v.xl ∧ 0 ≤ v.y ∧ v.y ≤ 2)) &&
  p.all (fun s => decide (0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 1 ∧
    0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 9 / 5) &&
    (s.ay == s.yb || decide (s.ax < 1))) &&
  (StructuralCheck.canonical f.F ==
    StructuralCheck.canonical (cf ++ ps.map Segment.transpose)) &&
  (StructuralCheck.canonical f.T == StructuralCheck.canonical (ct ++ ps)) &&
  (StructuralCheck.canonical p == StructuralCheck.canonical (p.map StructuralCheck.reflectProfile))

end ClosedForm
