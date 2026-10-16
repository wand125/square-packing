import ClosedForm.IntegerStructure
import ClosedForm.MeasureBridge

namespace ClosedForm.IntegerStructure
open MeasureTheory

/-- Evaluation of a signed jump table against an arbitrary real potential. -/
noncomputable def pairing (g : Key → ℝ) (xs : List Entry) : ℝ :=
  (xs.map fun e => (e.weight : ℝ) * g e.key).sum

noncomputable def statePairing (g : Key → ℝ) (s : State) : ℝ :=
  pairing g s.previous.toList + pairing g s.completed

@[simp] theorem pairing_nil (g : Key → ℝ) : pairing g [] = 0 := rfl
@[simp] theorem pairing_cons (g : Key → ℝ) (e : Entry) (xs : List Entry) :
    pairing g (e :: xs) = (e.weight : ℝ) * g e.key + pairing g xs := by
  simp [pairing]

theorem pairing_append (g : Key → ℝ) (xs ys : List Entry) :
    pairing g (xs ++ ys) = pairing g xs + pairing g ys := by
  simp [pairing, List.sum_append]

theorem step_pairing (g : Key → ℝ) (s : State) (e : Entry) :
    statePairing g (step s e) = statePairing g s + (e.weight : ℝ) * g e.key := by
  rcases s with ⟨p, done, ordered⟩
  cases p with
  | none => simp [step, statePairing, add_comm]
  | some p =>
    by_cases h : p.key = e.key
    · simp [step, h, statePairing, Int.cast_add]; ring
    · simp [step, h, statePairing]; ring

theorem run_pairing (g : Key → ℝ) (s : State) (xs : List Entry) :
    statePairing g (run s xs) = statePairing g s + pairing g xs := by
  induction xs generalizing s with
  | nil => simp [run]
  | cons e xs ih =>
    change statePairing g (run (step s e) xs) = _
    rw [ih, step_pairing, pairing_cons, add_assoc]

theorem finish_pairing (g : Key → ℝ) (s : State) :
    pairing g (finish s) = statePairing g s := by
  have hf (xs : List Entry) :
      pairing g (xs.filter fun e => e.weight != 0) = pairing g xs := by
    induction xs with
    | nil => rfl
    | cons e xs ih =>
      by_cases hz : e.weight = 0 <;> simp [hz, ih]
  rw [finish, hf]
  simp [pairing, statePairing, List.map_reverse, List.sum_reverse, List.sum_append, add_comm]

theorem equal_tables_equal_pairings (xs ys : List Entry)
    (h : finish (run {} xs) = finish (run {} ys)) (g : Key → ℝ) :
    pairing g xs = pairing g ys := by
  have he := congrArg (pairing g) h
  rw [finish_pairing, finish_pairing, run_pairing, run_pairing] at he
  simpa [statePairing] using he

theorem pairing_perm {xs ys : List Entry} (h : xs.Perm ys) (g : Key → ℝ) :
    pairing g xs = pairing g ys :=
  (h.map (fun (e : Entry) => (e.weight : ℝ) * g e.key)).sum_eq

/-- Externally sorted lists are useful only together with a checked permutation. -/
theorem equal_sorted_tables_equal_pairings (xs ys sx sy : List Entry)
    (hx : xs.Perm sx) (hy : ys.Perm sy)
    (h : finish (run {} sx) = finish (run {} sy)) (g : Key → ℝ) :
    pairing g xs = pairing g ys := by
  rw [pairing_perm hx, pairing_perm hy]
  exact equal_tables_equal_pairings sx sy h g

/-- Parameterization uses integer coordinates, with fifth-unit scaling here. -/
noncomputable def lineMap (o line : ℤ) (dx dy x : ℝ) : Point :=
  if o = 0 then (x / 5 + dx, (line : ℝ) / 5 + dy)
  else ((line : ℝ) / 5 + dx, x / 5 + dy)

lemma lineMap_measurable (o line : ℤ) (dx dy : ℝ) :
    Measurable (lineMap o line dx dy) := by
  unfold lineMap
  split <;> fun_prop

lemma lineMap_affine (o line : ℤ) (dx dy u v t : ℝ) :
    SquarePacking.segPt (lineMap o line dx dy u) (lineMap o line dx dy v) t =
      lineMap o line dx dy (u + (v-u)*t) := by
  unfold lineMap
  split <;> ext <;> simp [SquarePacking.segPt] <;> ring

noncomputable def potential (D : ℕ) (dx dy : ℝ) (A : Set Point) (k : Key) : ℝ :=
  -(1 / (5 * (D:ℝ))) *
    ∫ x in (0:ℝ)..(k.2.2:ℝ),
      ((lineMap k.1 k.2.1 dx dy) ⁻¹' A).indicator (fun _ => (1:ℝ)) x

lemma row_density_nonneg (r : Row) (hr : rowValid r = true) : 0 ≤ r.density := by
  have h : r.orientation ≤ 1 ∧ r.lo < r.hi ∧ 0 ≤ r.mass ∧
      r.density * (r.hi - r.lo) = 5 * r.mass := of_decide_eq_true hr
  nlinarith [h.2.1, h.2.2.1, h.2.2.2]

lemma decode_apply_pairing (D : ℕ) (hD : 0 < D) (r : Row) (hr : rowValid r = true)
    (dx dy : ℝ) {A : Set Point} (hA : MeasurableSet A) :
    (segmentMeasure (decode D r) dx dy A).toReal =
      pairing (potential D dx dy A) (rowEvents r) := by
  have h : r.orientation ≤ 1 ∧ r.lo < r.hi ∧ 0 ≤ r.mass ∧
      r.density * (r.hi - r.lo) = 5 * r.mass := of_decide_eq_true hr
  have hlen : (r.lo:ℝ) < r.hi := by exact_mod_cast h.2.1
  have hd : 0 < (D:ℝ) := by exact_mod_cast hD
  have hρ : 0 ≤ (r.density:ℝ) / (5 * (D:ℝ)) :=
    div_nonneg (by exact_mod_cast row_density_nonneg r hr) (by positivity)
  have hmass : (r.mass:ℝ) / D =
      ((r.density:ℝ) / (5 * (D:ℝ))) * ((r.hi:ℝ) - r.lo) := by
    have he : (r.density:ℝ) * ((r.hi:ℝ) - r.lo) = 5 * (r.mass:ℝ) := by
      exact_mod_cast h.2.2.2
    field_simp
    nlinarith
  have he : segmentMeasure (decode D r) dx dy =
      ENNReal.ofReal (((r.density:ℝ) / (5 * (D:ℝ))) * ((r.hi:ℝ)-r.lo)) •
        SquarePacking.segMeasure (lineMap r.orientation r.line dx dy r.lo)
          (lineMap r.orientation r.line dx dy r.hi) := by
    rw [← hmass]
    unfold decode lineMap
    split <;> simp_all [segmentMeasure, Rat.cast_div, Rat.cast_intCast]
  rw [he, segMeasure_density_apply _ (lineMap_measurable _ _ _ _)
    (lineMap_affine _ _ _ _) _ _ _ hlen hρ hA]
  simp [pairing, rowEvents, potential]
  ring

lemma rows_apply_pairing (D : ℕ) (hD : 0 < D) (xs : List Row)
    (hx : ∀ r ∈ xs, rowValid r = true) (dx dy : ℝ)
    {A : Set Point} (hA : MeasurableSet A) :
    (rowsMeasure (xs.map (decode D)) dx dy A).toReal =
      pairing (potential D dx dy A) (xs.flatMap rowEvents) := by
  rw [rowsMeasure_toReal]
  induction xs with
  | nil => rfl
  | cons r xs ih =>
    simp only [List.map_cons, List.sum_cons, List.flatMap_cons, pairing_append]
    rw [decode_apply_pairing D hD r (hx r (by simp)) dx dy hA,
      ih (fun r hr => hx r (by simp [hr]))]

/-- Soundness of the integer jump tables, for every common real translation. -/
theorem equal_tables_rowsMeasure (D : ℕ) (xs ys : List Row) (hD : 0 < D)
    (hx : ∀ r ∈ xs, rowValid r = true) (hy : ∀ r ∈ ys, rowValid r = true)
    (h : finish (run {} (xs.flatMap rowEvents)) = finish (run {} (ys.flatMap rowEvents)))
    (dx dy : ℝ) :
    rowsMeasure (xs.map (decode D)) dx dy = rowsMeasure (ys.map (decode D)) dx dy := by
  apply Measure.ext
  intro A hA
  apply (ENNReal.toReal_eq_toReal_iff'
    (rowsMeasure_ne_top _ _ _ _) (rowsMeasure_ne_top _ _ _ _)).mp
  rw [rows_apply_pairing D hD xs hx dx dy hA, rows_apply_pairing D hD ys hy dx dy hA]
  exact equal_tables_equal_pairings _ _ h _

#print axioms equal_tables_rowsMeasure
#print axioms equal_sorted_tables_equal_pairings
end ClosedForm.IntegerStructure
