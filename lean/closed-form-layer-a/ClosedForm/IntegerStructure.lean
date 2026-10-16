import ClosedForm.Measure

/-! Integer-only building blocks for structural certificates. Concrete decisions
use no rational arithmetic and do not sort. This module does not yet supply the
semantic Structural bridge. -/
namespace ClosedForm.IntegerStructure

abbrev Key := ℤ × ℤ × ℤ

structure Entry where
  key : Key
  weight : ℤ
  deriving DecidableEq, Repr

def keyLE (a b : Key) : Bool :=
  a.1 < b.1 || (a.1 == b.1 &&
    (a.2.1 < b.2.1 || (a.2.1 == b.2.1 && a.2.2 ≤ b.2.2)))

/-- Streaming sortedness and equal-key aggregation. State is carried across blocks. -/
structure State where
  previous : Option Entry := none
  completed : List Entry := []
  ordered : Bool := true
  deriving DecidableEq, Repr

def step (s : State) (e : Entry) : State :=
  match s.previous with
  | none => { s with previous := some e }
  | some p =>
    if p.key == e.key then
      { s with previous := some ⟨p.key, p.weight + e.weight⟩ }
    else
      { previous := some e, completed := p :: s.completed,
        ordered := s.ordered && keyLE p.key e.key }

def run (s : State) (xs : List Entry) : State := xs.foldl step s

def finish (s : State) : List Entry :=
  ((s.previous.toList ++ s.completed).reverse).filter (fun e => e.weight != 0)

/-- A block theorem can be composed without reducing the preceding input again. -/
theorem run_append (s : State) (xs ys : List Entry) :
    run s (xs ++ ys) = run (run s xs) ys := by
  simp [run, List.foldl_append]

theorem run_join (s t u : State) (xs ys : List Entry)
    (h₁ : run s xs = t) (h₂ : run t ys = u) : run s (xs ++ ys) = u := by
  rw [run_append, h₁, h₂]

/-- Integer coefficient at a key. Used only in generic proofs, not the checker. -/
def coefficient (k : Key) (xs : List Entry) : ℤ :=
  (xs.map fun e => if e.key = k then e.weight else 0).sum

def stateCoefficient (k : Key) (s : State) : ℤ :=
  coefficient k s.previous.toList + coefficient k s.completed

@[simp] theorem coefficient_cons (k : Key) (e : Entry) (xs : List Entry) :
    coefficient k (e :: xs) = (if e.key = k then e.weight else 0) + coefficient k xs := by
  simp [coefficient]

@[simp] theorem coefficient_nil (k : Key) : coefficient k [] = 0 := rfl

theorem coefficient_append (k : Key) (xs ys : List Entry) :
    coefficient k (xs ++ ys) = coefficient k xs + coefficient k ys := by
  simp [coefficient, List.sum_append]

theorem step_coefficient (k : Key) (s : State) (e : Entry) :
    stateCoefficient k (step s e) =
      stateCoefficient k s + (if e.key = k then e.weight else 0) := by
  rcases s with ⟨p, done, ordered⟩
  cases p with
  | none => simp [step, stateCoefficient, add_comm]
  | some p =>
    by_cases h : p.key = e.key
    · simp only [step, beq_iff_eq, h, ↓reduceIte]
      by_cases hk : e.key = k
      · simp [stateCoefficient, h, hk, add_assoc, add_comm]
      · simp [stateCoefficient, h, hk]
    · simp [step, h, stateCoefficient, add_comm]

theorem run_coefficient (k : Key) (s : State) (xs : List Entry) :
    stateCoefficient k (run s xs) = stateCoefficient k s + coefficient k xs := by
  induction xs generalizing s with
  | nil => simp [run]
  | cons e xs ih =>
    change stateCoefficient k (run (step s e) xs) = _
    rw [ih, step_coefficient, coefficient_cons]
    exact add_assoc _ _ _

theorem coefficient_reverse (k : Key) (xs : List Entry) :
    coefficient k xs.reverse = coefficient k xs := by
  simp [coefficient, List.map_reverse, List.sum_reverse]

theorem coefficient_filter (k : Key) (xs : List Entry) :
    coefficient k (xs.filter fun e => e.weight != 0) = coefficient k xs := by
  induction xs with
  | nil => rfl
  | cons e xs ih =>
    by_cases hz : e.weight = 0
    · simp [hz, ih]
    · simp [hz, ih]

theorem finish_coefficient (k : Key) (s : State) :
    coefficient k (finish s) = stateCoefficient k s := by
  rw [finish, coefficient_filter, coefficient_reverse, coefficient_append]
  rfl

/-- Equal checked integer event tables imply equal jumps at every key. This is
an algebraic fact; the additional measure interpretation is a separate theorem. -/
theorem equal_tables_equal_coefficients (xs ys : List Entry)
    (h : finish (run {} xs) = finish (run {} ys)) (k : Key) :
    coefficient k xs = coefficient k ys := by
  have he := congrArg (coefficient k) h
  rw [finish_coefficient, finish_coefficient, run_coefficient, run_coefficient] at he
  simpa [stateCoefficient] using he

/-- Linear merge/subtraction of sorted tables. It is total even on unsorted
inputs; sortedness is established by separate streamed input certificates. -/
def subtract : List Entry → List Entry → List Entry
  | [], ys => ys.map fun e => ⟨e.key, -e.weight⟩
  | xs, [] => xs
  | a :: xs, b :: ys =>
    if a.key == b.key then
      ⟨a.key, a.weight - b.weight⟩ :: subtract xs ys
    else if keyLE a.key b.key then a :: subtract xs (b :: ys)
    else ⟨b.key, -b.weight⟩ :: subtract (a :: xs) ys
termination_by xs ys => xs.length + ys.length

theorem coefficient_negate (k : Key) (xs : List Entry) :
    coefficient k (xs.map fun e => ⟨e.key, -e.weight⟩) = -coefficient k xs := by
  induction xs with
  | nil => simp
  | cons e xs ih =>
    simp only [List.map_cons, coefficient_cons, ih]
    split <;> simp_all <;> ring

theorem subtract_coefficient (k : Key) (xs ys : List Entry) :
    coefficient k (subtract xs ys) = coefficient k xs - coefficient k ys := by
  fun_induction subtract xs ys with
  | case1 ys => simp [coefficient_negate]
  | case2 xs => simp
  | case3 a xs b ys h ih =>
    have hkey : a.key = b.key := by simpa using h
    simp only [coefficient_cons, ih]
    by_cases hk : b.key = k
    · simp [hkey, hk] <;> ring
    · simp [hkey, hk]
  | case4 a xs b ys h hle ih =>
    simp only [coefficient_cons, ih]
    ring
  | case5 a xs b ys h hle ih =>
    simp only [coefficient_cons, ih]
    split <;> split <;> simp_all <;> ring

/-- A nondegenerate fifth-grid row and its integral density witness. -/
structure Row where
  orientation : ℕ
  line : ℤ
  lo : ℤ
  hi : ℤ
  mass : ℤ
  density : ℤ
  deriving DecidableEq, Repr

def rowValid (r : Row) : Bool :=
  decide (r.orientation ≤ 1 ∧ r.lo < r.hi ∧ 0 ≤ r.mass ∧
    r.density * (r.hi - r.lo) = 5 * r.mass)

def rowEvents (r : Row) : List Entry :=
  [⟨(r.orientation, r.line, r.lo), r.density⟩,
   ⟨(r.orientation, r.line, r.hi), -r.density⟩]

/-- Decoding is symbolic: concrete certificates never evaluate this function. -/
def decode (D : ℕ) (r : Row) : Segment :=
  if r.orientation = 0 then
    ⟨r.lo / 5, r.line / 5, r.hi / 5, r.line / 5, r.mass / D⟩
  else
    ⟨r.line / 5, r.lo / 5, r.line / 5, r.hi / 5, r.mass / D⟩

#print axioms equal_tables_equal_coefficients
#print axioms finish_coefficient
#print axioms subtract_coefficient
#print axioms run_join
#print axioms step_coefficient
#print axioms run_coefficient
end ClosedForm.IntegerStructure
