import ClosedForm.StructureDefs
import ClosedForm.MeasureBridge

namespace ClosedForm.StructuralCheck
open MeasureTheory

def eventKey (e : Event) : ℕ ×ₗ (ℚ ×ₗ ℚ) := toLex (e.orientation, toLex (e.line, e.position))
def lineKey (e : Event) : ℕ ×ₗ ℚ := toLex (e.orientation, e.line)

lemma keyLE_iff (a b : Event) : keyLE a b = true ↔ eventKey a ≤ eventKey b := by
  simp [keyLE, eventKey, Prod.Lex.toLex_le_toLex]

lemma lineKey_le_of_keyLE (a b : Event) (h : keyLE a b = true) : lineKey a ≤ lineKey b := by
  simp only [keyLE_iff, eventKey, Prod.Lex.toLex_le_toLex] at h
  rcases h with h | ⟨h, h'⟩
  · exact Prod.Lex.toLex_le_toLex.mpr (Or.inl h)
  · apply Prod.Lex.toLex_le_toLex.mpr
    exact Or.inr ⟨h, h'.elim le_of_lt (fun h => h.1.le)⟩

lemma sorted_lines (xs : List Event) :
    (xs.mergeSort keyLE).Pairwise (fun a b => lineKey a ≤ lineKey b) := by
  apply (List.pairwise_mergeSort (le := keyLE) ?_ ?_ xs).imp
  · exact fun h => lineKey_le_of_keyLE _ _ h
  · intro a b c hab hbc
    exact keyLE_iff _ _ |>.mpr (le_trans ((keyLE_iff _ _).mp hab) ((keyLE_iff _ _).mp hbc))
  · intro a b
    simp only [Bool.or_eq_true, keyLE_iff]
    exact le_total _ _

noncomputable def eventSum (P : ℕ → ℚ → ℚ → ℝ) (xs : List Event) : ℝ :=
  (xs.map fun e => (e.jump:ℝ) * P e.orientation e.line e.position).sum

noncomputable def cellSum (P : ℕ → ℚ → ℚ → ℝ) (xs : List Cell) : ℝ :=
  (xs.map fun c => (c.density:ℝ) * (P c.orientation c.line c.hi - P c.orientation c.line c.lo)).sum

lemma sameKey_fields {a b : Event} (h : sameKey a b = true) :
    a.orientation = b.orientation ∧ a.line = b.line ∧ a.position = b.position := by
  simpa [sameKey, and_assoc] using h

lemma collect_eventSum (P : ℕ → ℚ → ℚ → ℝ) (xs : List Event) :
    eventSum P (collect xs) = eventSum P xs := by
  induction xs with
  | nil => rfl
  | cons e xs ih =>
    simp only [collect, List.foldr_cons]
    change eventSum P (match collect xs with
      | [] => [e]
      | a::rest => if sameKey e a then {a with jump := e.jump+a.jump}::rest else e::collect xs) = _
    cases he : collect xs with
    | nil => simp [he, eventSum] at ih ⊢; exact ih.symm
    | cons a rest =>
      by_cases h : sameKey e a = true
      · obtain ⟨ho, hl, hp⟩ := sameKey_fields h
        simp only [h, ↓reduceIte, eventSum, List.map_cons, List.sum_cons, Rat.cast_add]
        simp only [he, eventSum, List.map_cons, List.sum_cons] at ih
        rw [ho, hl, hp]
        nlinarith [ih]
      · simp only [h, Bool.false_eq_true, ↓reduceIte, eventSum, List.map_cons, List.sum_cons]
        simp only [he, eventSum, List.map_cons, List.sum_cons] at ih
        rw [ih]

lemma filter_eventSum (P : ℕ → ℚ → ℚ → ℝ) (xs : List Event) :
    eventSum P (xs.filter fun e => e.jump != 0) = eventSum P xs := by
  induction xs with
  | nil => rfl
  | cons e xs ih =>
    by_cases h : e.jump = 0 <;> simp_all [eventSum]

lemma collect_line_mem (xs : List Event) (e : Event) (he : e ∈ collect xs) :
    ∃ a ∈ xs, lineKey e = lineKey a := by
  induction xs generalizing e with
  | nil => simp [collect] at he
  | cons a xs ih =>
    simp only [collect, List.foldr_cons] at he
    change e ∈ (match collect xs with
      | [] => [a]
      | b::rest => if sameKey a b then {b with jump := a.jump+b.jump}::rest else a::collect xs) at he
    cases hc : collect xs with
    | nil => simp only [hc, List.mem_singleton] at he; subst e; exact ⟨a, by simp, rfl⟩
    | cons b rest =>
      by_cases hab : sameKey a b = true
      · simp only [hc, hab, ↓reduceIte, List.mem_cons] at he
        rcases he with rfl | he
        · obtain ⟨c, hc', hbc⟩ := ih b (by simp [hc])
          exact ⟨c, by simp [hc'], hbc⟩
        · obtain ⟨c, hc', hec⟩ := ih e (by simp [hc, he])
          exact ⟨c, by simp [hc'], hec⟩
      · simp only [hc, hab, Bool.false_eq_true, ↓reduceIte, List.mem_cons] at he
        rcases he with he | he
        · subst e; exact ⟨a, by simp, rfl⟩
        · obtain ⟨c, hc', hec⟩ := ih e (by simpa [hc] using he)
          exact ⟨c, by simp [hc'], hec⟩

lemma collect_sorted_lines (xs : List Event)
    (hs : xs.Pairwise (fun a b => lineKey a ≤ lineKey b)) :
    (collect xs).Pairwise (fun a b => lineKey a ≤ lineKey b) := by
  induction xs with
  | nil => simp [collect]
  | cons a xs ih =>
    obtain ⟨ha, hs⟩ := List.pairwise_cons.mp hs
    have ht := ih hs
    change (match collect xs with
      | [] => [a]
      | b::rest => if sameKey a b then {b with jump := a.jump+b.jump}::rest else a::collect xs).Pairwise _
    cases hc : collect xs with
    | nil => simp
    | cons b rest =>
      by_cases hab : sameKey a b = true
      · simpa [hab, hc, List.pairwise_cons, lineKey] using ht
      · simp only [hab, Bool.false_eq_true, ↓reduceIte, List.pairwise_cons]
        refine ⟨?_, by simpa [hc] using ht⟩
        intro e he
        obtain ⟨c, hcx, hec⟩ := collect_line_mem xs e (by simpa [hc] using he)
        rw [hec]
        exact ha c hcx

noncomputable def lineSum (xs : List Event) (k : ℕ ×ₗ ℚ) : ℝ :=
  eventSum (fun o l _ => if toLex (o,l) = k then 1 else 0) xs

lemma lineSum_cons (e : Event) (xs : List Event) (k : ℕ ×ₗ ℚ) :
    lineSum (e::xs) k = (if lineKey e = k then (e.jump:ℝ) else 0) + lineSum xs k := by
  simp only [lineSum, eventSum, List.map_cons, List.sum_cons, lineKey]
  split <;> simp_all

lemma events_balanced (s : Segment) (k : ℕ ×ₗ ℚ) : lineSum (events s) k = 0 := by
  unfold events
  dsimp only
  split <;> simp [lineSum, eventSum] <;> split <;> simp <;> split <;> simp_all

lemma inputs_balanced (xs : List Segment) (k : ℕ ×ₗ ℚ) :
    lineSum (xs.flatMap events) k = 0 := by
  induction xs with
  | nil => rfl
  | cons s xs ih =>
    change lineSum (events s ++ xs.flatMap events) k = 0
    have ha (es fs : List Event) : lineSum (es++fs) k = lineSum es k + lineSum fs k := by
      simp [lineSum, eventSum, List.sum_append]
    rw [ha, events_balanced, ih, add_zero]

lemma lineSum_absent (xs : List Event) (k : ℕ ×ₗ ℚ)
    (h : ∀ e ∈ xs, lineKey e ≠ k) : lineSum xs k = 0 := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
    rw [lineSum_cons, if_neg (h a (by simp)), ih (fun e he => h e (by simp [he])), add_zero]

lemma sweep_eventSum (P : ℕ → ℚ → ℚ → ℝ) (a : Event) (xs : List Event) (d : ℚ)
    (hs : (a::xs).Pairwise (fun a b => lineKey a ≤ lineKey b))
    (hb : ∀ k, lineSum (a::xs) k = if lineKey a = k then -(d:ℝ) else 0) :
    eventSum P (a::xs) + cellSum P (sweep (a::xs) d) =
      -(d:ℝ) * P a.orientation a.line a.position := by
  induction xs generalizing a d with
  | nil =>
    have h := hb (lineKey a)
    simp [lineSum, eventSum, lineKey] at h
    simp [sweep, eventSum, cellSum, h]
  | cons b xs ih =>
    obtain ⟨ha, htail⟩ := List.pairwise_cons.mp hs
    by_cases hl : lineKey a = lineKey b
    · have hfields : a.orientation = b.orientation ∧ a.line = b.line := by
        exact Prod.mk.inj (congrArg ofLex hl)
      have hbool : (a.orientation == b.orientation && a.line == b.line) = true := by
        simp [hfields.1, hfields.2]
      have hb' : ∀ k, lineSum (b::xs) k =
          if lineKey b = k then -((d+a.jump:ℚ):ℝ) else 0 := by
        intro k
        have h := hb k
        rw [lineSum_cons] at h
        by_cases hk : lineKey b = k <;> simp [hl, hk, Rat.cast_add] at h ⊢ <;> linarith
      have hi := ih b (d+a.jump) htail hb'
      simp only [sweep, hbool, ↓reduceIte]
      by_cases hz : d+a.jump = 0
      · simp only [hz, beq_self_eq_true, ↓reduceIte]
        have hc : (d:ℝ)+(a.jump:ℝ) = 0 := by exact_mod_cast hz
        simp only [hz, Rat.cast_zero, neg_zero, zero_mul] at hi
        simp only [eventSum, List.map_cons, List.sum_cons] at hi ⊢
        rw [hfields.1, hfields.2]
        linear_combination hi + P b.orientation b.line a.position * hc
      · simp only [beq_iff_eq, hz, ↓reduceIte, cellSum, eventSum,
          List.map_cons, List.sum_cons, Rat.cast_add] at hi ⊢
        rw [hfields.1, hfields.2]
        nlinarith [hi]
    · have hbool : (a.orientation == b.orientation && a.line == b.line) = false := by
        simp only [Bool.and_eq_false_iff, beq_eq_false_iff_ne]
        by_contra h
        push Not at h
        apply hl
        simp [lineKey, h.1, h.2]
      have hab : lineKey a ≤ lineKey b := ha b (by simp)
      have hnone : ∀ e ∈ b::xs, lineKey e ≠ lineKey a := by
        intro e he heq
        have hbe : lineKey b ≤ lineKey e := by
          rcases List.mem_cons.mp he with rfl | he
          · exact le_rfl
          · exact (List.pairwise_cons.mp htail).1 e he
        exact hl (le_antisymm hab (heq ▸ hbe))
      have hz : (d:ℝ)+(a.jump:ℝ) = 0 := by
        have h := hb (lineKey a)
        rw [lineSum_cons, if_pos rfl, lineSum_absent _ _ hnone] at h
        simp at h
        linarith
      have hb' : ∀ k, lineSum (b::xs) k = if lineKey b = k then -((0:ℚ):ℝ) else 0 := by
        intro k
        have h := hb k
        rw [lineSum_cons] at h
        by_cases hk : lineKey a = k <;> simp [hk] at h <;> simp <;> linarith
      have hi := ih b 0 htail hb'
      simp only [sweep, hbool, Bool.false_eq_true, ↓reduceIte]
      simp only [eventSum, List.map_cons, List.sum_cons, Rat.cast_zero, neg_zero, zero_mul] at hi ⊢
      linear_combination hi + P a.orientation a.line a.position * hz

lemma canonical_eventSum (P : ℕ → ℚ → ℚ → ℝ) (xs : List Segment) :
    eventSum P (xs.flatMap events) = -cellSum P (canonical xs) := by
  let es := ((collect ((xs.flatMap events).mergeSort keyLE)).filter fun e => e.jump != 0)
  have hpres (Q : ℕ → ℚ → ℚ → ℝ) : eventSum Q es = eventSum Q (xs.flatMap events) := by
    rw [filter_eventSum, collect_eventSum]
    exact ((List.mergeSort_perm _ _).map
      (fun (e : Event) => (e.jump:ℝ) * Q e.orientation e.line e.position)).sum_eq
  have hbal (k : ℕ ×ₗ ℚ) : lineSum es k = 0 := by
    rw [lineSum, hpres]
    exact inputs_balanced xs k
  have hsort : es.Pairwise (fun a b => lineKey a ≤ lineKey b) :=
    (collect_sorted_lines _ (sorted_lines _)).filter _
  change eventSum P (xs.flatMap events) = -cellSum P (sweep es 0)
  rw [← hpres]
  cases he : es with
  | nil => simp [eventSum, sweep, cellSum]
  | cons a rest =>
    have hb : ∀ k, lineSum (a::rest) k = if lineKey a = k then -((0:ℚ):ℝ) else 0 := by
      intro k
      simpa [he] using hbal k
    have hh := sweep_eventSum P a rest 0 (by simpa [he] using hsort) hb
    simp only [Rat.cast_zero, neg_zero, zero_mul] at hh
    linarith

noncomputable def rationalLine (o : ℕ) (l : ℚ) (dx dy x : ℝ) : Point :=
  if o = 0 then (x+dx, (l:ℝ)+dy) else ((l:ℝ)+dx, x+dy)

lemma rationalLine_measurable (o : ℕ) (l : ℚ) (dx dy : ℝ) :
    Measurable (rationalLine o l dx dy) := by
  unfold rationalLine
  split <;> fun_prop

lemma rationalLine_affine (o : ℕ) (l : ℚ) (dx dy u v t : ℝ) :
    SquarePacking.segPt (rationalLine o l dx dy u) (rationalLine o l dx dy v) t =
      rationalLine o l dx dy (u+(v-u)*t) := by
  unfold rationalLine
  split <;> ext <;> simp [SquarePacking.segPt] <;> ring

noncomputable def rationalPotential (dx dy : ℝ) (A : Set Point)
    (o : ℕ) (l x : ℚ) : ℝ :=
  ∫ t in (0:ℝ)..(x:ℝ), ((rationalLine o l dx dy) ⁻¹' A).indicator (fun _ => (1:ℝ)) t

def lineSegment (o : ℕ) (l a b m : ℚ) : Segment :=
  if o = 0 then ⟨a,l,b,l,m⟩ else ⟨l,a,l,b,m⟩

lemma lineSegment_apply (o : ℕ) (l a b m : ℚ) (hab : a < b) (hm : 0 ≤ m)
    (dx dy : ℝ) {A : Set Point} (hA : MeasurableSet A) :
    (segmentMeasure (lineSegment o l a b m) dx dy A).toReal =
      (m / (b-a):ℚ) * (rationalPotential dx dy A o l b - rationalPotential dx dy A o l a) := by
  have hlen : (a:ℝ) < b := by exact_mod_cast hab
  have hm' : 0 ≤ (m:ℝ) := by exact_mod_cast hm
  have hρ : 0 ≤ (m:ℝ) / ((b:ℝ)-a) := div_nonneg hm' (sub_pos.mpr hlen).le
  have he := segMeasure_density_apply (rationalLine o l dx dy)
    (rationalLine_measurable _ _ _ _) (rationalLine_affine _ _ _ _)
    a b ((m:ℝ)/((b:ℝ)-a)) hlen hρ hA
  rw [div_mul_cancel₀ _ (ne_of_gt (sub_pos.mpr hlen))] at he
  by_cases ho : o = 0 <;>
    simpa [rationalPotential, lineSegment, rationalLine, segmentMeasure, ho] using he

lemma segment_eventSum (s : Segment) (hv : s.Valid) (dx dy : ℝ)
    {A : Set Point} (hA : MeasurableSet A) :
    (segmentMeasure s dx dy A).toReal = -eventSum (rationalPotential dx dy A) (events s) := by
  by_cases hy : s.ay = s.yb
  · rcases lt_trichotomy s.ax s.bx with hx | hx | hx
    · have he := lineSegment_apply 0 s.ay s.ax s.bx s.mass hx hv.1 dx dy hA
      have hs : lineSegment 0 s.ay s.ax s.bx s.mass = s := by
        cases s; simp_all [lineSegment]
      rw [hs] at he
      rw [he]
      simp [events, hy, min_eq_left hx.le, max_eq_right hx.le, ne_of_lt hx,
        eventSum, mul_sub]
      ring
    · rw [segmentMeasure_valid_point s hv hx hy]
      simp [events, hy, hx, eventSum]
    · have he := lineSegment_apply 0 s.ay s.bx s.ax s.mass hx hv.1 dx dy hA
      have hs : lineSegment 0 s.ay s.bx s.ax s.mass =
          (⟨s.bx,s.yb,s.ax,s.ay,s.mass⟩:Segment) := by simp [lineSegment, hy]
      rw [hs, segmentMeasure_reverse] at he
      rw [he]
      simp [events, hy, min_eq_right hx.le, max_eq_left hx.le, ne_of_lt hx,
        eventSum, mul_sub]
      ring
  · have hx := hv.2.1.resolve_right hy
    rcases lt_or_gt_of_ne hy with hy' | hy'
    · have he := lineSegment_apply 1 s.ax s.ay s.yb s.mass hy' hv.1 dx dy hA
      have hs : lineSegment 1 s.ax s.ay s.yb s.mass = s := by
        cases s; simp_all [lineSegment]
      rw [hs] at he
      rw [he]
      simp [events, hy, min_eq_left hy'.le, max_eq_right hy'.le, eventSum, mul_sub]
      ring
    · have he := lineSegment_apply 1 s.ax s.yb s.ay s.mass hy' hv.1 dx dy hA
      have hs : lineSegment 1 s.ax s.yb s.ay s.mass =
          (⟨s.bx,s.yb,s.ax,s.ay,s.mass⟩:Segment) := by simp [lineSegment, hx]
      rw [hs, segmentMeasure_reverse] at he
      rw [he]
      simp [events, hy, min_eq_right hy'.le, max_eq_left hy'.le, Ne.symm hy, eventSum, mul_sub]
      ring

lemma rows_eventSum (xs : List Segment) (hx : ∀ s ∈ xs, s.Valid) (dx dy : ℝ)
    {A : Set Point} (hA : MeasurableSet A) :
    (rowsMeasure xs dx dy A).toReal = -eventSum (rationalPotential dx dy A) (xs.flatMap events) := by
  rw [rowsMeasure_toReal]
  induction xs with
  | nil => simp [eventSum]
  | cons s xs ih =>
    simp only [List.map_cons, List.sum_cons, List.flatMap_cons]
    rw [segment_eventSum s (hx s (by simp)) dx dy hA, ih (fun s hs => hx s (by simp [hs]))]
    simp [eventSum, List.sum_append, add_comm]

/-- Soundness of the unchanged rational canonicalizer, including zero-mass point rows. -/
theorem canonical_rowsMeasure (xs ys : List Segment)
    (hx : ∀ s ∈ xs, s.Valid) (hy : ∀ s ∈ ys, s.Valid)
    (h : canonical xs = canonical ys) (dx dy : ℝ) :
    rowsMeasure xs dx dy = rowsMeasure ys dx dy := by
  ext A hA
  apply (ENNReal.toReal_eq_toReal_iff' (rowsMeasure_ne_top _ _ _ _)
    (rowsMeasure_ne_top _ _ _ _)).mp
  rw [rows_eventSum xs hx dx dy hA, rows_eventSum ys hy dx dy hA,
    canonical_eventSum, canonical_eventSum, h]

#print axioms canonical_rowsMeasure
end ClosedForm.StructuralCheck
