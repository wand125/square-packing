import ClosedForm.GridCertificate
import ClosedForm.Structure

namespace ClosedForm

/-- Exact-support witnesses preserve the original subtraction, including overlaps. -/
lemma subtractRows_mem_of_massOn (xs ys cs : List Segment) (h : ∀ p, massOn xs p = massOn cs p + massOn ys p)
    (hc : ∀ s ∈ cs, 0 ≤ s.mass) (s : Segment) (hs : s ∈ subtractRows xs ys) :
    ∃ t ∈ cs, t.mass ≠ 0 ∧ 0 ≤ s.mass ∧
      s = ⟨t.support.1.1,t.support.1.2,t.support.2.1,t.support.2.2,s.mass⟩ := by
  obtain ⟨hs, hz⟩ := List.mem_filter.mp hs
  obtain ⟨p, hp, rfl⟩ := List.mem_map.mp hs
  have he : massOn xs p - massOn ys p = massOn cs p := by
    rw [h]
    ring
  have hn : massOn cs p ≠ 0 := by simpa [he] using hz
  have hex : ∃ t ∈ cs, t.support = p ∧ t.mass ≠ 0 := by
    by_contra! hnot
    apply hn
    apply List.sum_eq_zero
    intro m hm
    obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hm
    obtain ⟨ht, hp⟩ := List.mem_filter.mp ht
    exact hnot t ht (by simpa using hp)
  obtain ⟨t, ht, htp, htm⟩ := hex
  refine ⟨t, ht, htm, ?_, ?_⟩
  · change 0 ≤ massOn xs p - massOn ys p
    rw [he]
    exact massOn_nonneg cs hc p
  · simp only [htp]

lemma subtractRows_valid_of_massOn (xs ys cs : List Segment) (h : ∀ p, massOn xs p = massOn cs p + massOn ys p)
    (hc : ∀ s ∈ cs, s.Valid) : ∀ s ∈ subtractRows xs ys, s.Valid := by
  intro s hs
  obtain ⟨t, ht, hn, hm, he⟩ := subtractRows_mem_of_massOn xs ys cs h (fun t ht => (hc t ht).1) s hs
  rw [he]
  exact support_row_valid t (hc t ht) hn s.mass hm

lemma subtractRows_bounds_of_massOn (xs ys cs : List Segment) (h : ∀ p, massOn xs p = massOn cs p + massOn ys p)
    (hc : ∀ s ∈ cs, 0 ≤ s.mass) (x y : ℚ)
    (hb : ∀ s ∈ cs, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ x ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ y) :
    ∀ s ∈ subtractRows xs ys, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ x ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ y := by
  intro s hs
  obtain ⟨t, ht, hn, hm, he⟩ := subtractRows_mem_of_massOn xs ys cs h hc s hs
  have hb := hb t ht
  rw [he]
  unfold Segment.support
  split <;> simpa [min_comm, max_comm] using hb

namespace IntegerStructure

def sameSupport (a b : Row) : Bool :=
  decide (a.orientation=b.orientation ∧ a.line=b.line ∧ a.lo=b.lo ∧ a.hi=b.hi)

def addRow (a b : Row) : Row :=
  { a with mass := a.mass+b.mass, density := a.density+b.density }

def mergeHead (a : Row) : List Row → List Row
  | [] => [a]
  | b::bs => if sameSupport a b then addRow a b :: bs else a::b::bs

def mergeRows : List Row → List Row
  | [] => []
  | a::xs => mergeHead a (mergeRows xs)

lemma massOn_cons (a : Segment) (xs : List Segment) (p : QPoint × QPoint) :
    massOn (a::xs) p = (if a.support = p then a.mass else 0) + massOn xs p := by
  simp [massOn, List.filter_cons]
  split <;> simp_all

lemma addRow_massOn (D : ℕ) (a b : Row) (h : sameSupport a b = true)
    (p : QPoint × QPoint) :
    massOn [decode D (addRow a b)] p = massOn [decode D a, decode D b] p := by
  obtain ⟨ho,hl,hlo,hhi⟩ : a.orientation=b.orientation ∧ a.line=b.line ∧ a.lo=b.lo ∧ a.hi=b.hi := of_decide_eq_true h
  have hs : (decode D b).support = (decode D a).support := by
    by_cases hz : a.orientation = 0 <;> simp [decode, ← ho, ← hl, ← hlo, ← hhi, Segment.support, hz]
  have hs' : (decode D (addRow a b)).support = (decode D a).support := by
    by_cases hz : a.orientation = 0 <;> simp [decode, addRow, Segment.support, hz]
  have hm : (decode D (addRow a b)).mass = (decode D a).mass + (decode D b).mass := by
    by_cases hz : a.orientation = 0 <;> simp [decode, addRow, ← ho, hz, Int.cast_add, add_div]
  simp only [massOn_cons, hs, hs', hm]
  split <;> simp [massOn]

lemma mergeHead_massOn (D : ℕ) (a : Row) (xs : List Row) (p : QPoint × QPoint) :
    massOn ((mergeHead a xs).map (decode D)) p = massOn ((a::xs).map (decode D)) p := by
  cases xs with
  | nil => rfl
  | cons b bs =>
    simp only [mergeHead]
    split
    · have h := addRow_massOn D a b ‹sameSupport a b = true› p
      simpa only [List.map_cons, massOn_cons, show massOn [] p = 0 from rfl, add_zero, add_assoc] using congrArg (fun x => x + massOn (bs.map (decode D)) p) h
    · rfl

lemma mergeRows_massOn (D : ℕ) (xs : List Row) (p : QPoint × QPoint) :
    massOn ((mergeRows xs).map (decode D)) p = massOn (xs.map (decode D)) p := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
    rw [mergeRows, mergeHead_massOn]
    simpa only [List.map_cons, massOn_cons] using congrArg (fun x => (if (decode D a).support=p then (decode D a).mass else 0)+x) ih

lemma merged_massOn (D : ℕ) (xs ys sx sy : List Row)
    (hx : xs.Perm sx) (hy : ys.Perm sy) (h : mergeRows sx = mergeRows sy)
    (p : QPoint × QPoint) : massOn (xs.map (decode D)) p = massOn (ys.map (decode D)) p := by
  rw [massOn_perm (hx.map (decode D)), massOn_perm (hy.map (decode D)),
    ← mergeRows_massOn D sx, ← mergeRows_massOn D sy, h]

lemma source_append (D : ℕ) (xs ys : List Segment) (rs ss : List Row)
    (hx : xs = rs.map (decode D)) (hy : ys = ss.map (decode D)) :
    xs++ys = (rs++ss).map (decode D) := by
  rw [List.map_append, ← hx, ← hy]

end IntegerStructure

/-- Two possibly nonempty corner witnesses, identified by exact support masses. -/
theorem structural_of_massOn_witness (f fr : Family) (cf ct : List Segment)
    (hf : f.Valid) (hfr : fr.Valid)
    (hstd : f.UA = 9/5 ∧ f.U = none ∧ 0 ≤ f.d0 ∧ f.d1 ≤ 1)
    (hr : fr.F=f.T ∧ fr.T=[] ∧ fr.V=[] ∧ fr.UA=f.UA ∧ fr.U=none ∧ fr.d0=f.d0 ∧ fr.d1=f.d1)
    (hpm : ((profile f).map Segment.mass).sum = 9/5)
    (hcf : ∀ s ∈ cf, s.Valid) (hct : ∀ s ∈ ct, s.Valid)
    (hcfb : ∀ s ∈ cf, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 2+f.d0 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2)
    (hctb : ∀ s ∈ ct, s.ax = 2 ∧ s.bx = 2 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2)
    (hv : ∀ v ∈ f.V, 0 ≤ v.xl ∧ 0 ≤ v.y ∧ v.y ≤ 2)
    (hpb : ∀ s ∈ profile f, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 1 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 9/5)
    (hF : ∀ p, massOn f.F p = massOn cf p + massOn ((periods f 7).map Segment.transpose) p)
    (hT : ∀ p, massOn f.T p = massOn ct p + massOn (periods f 7) p)
    (hrefl : ∀ dx : ℝ, rowsMeasure (profile f) dx 0 =
      rowsMeasure ((profile f).map StructuralCheck.reflectProfile) dx 0) : Structural f fr := by
  have hcfv := subtractRows_valid_of_massOn _ _ cf hF hcf
  have hctv := subtractRows_valid_of_massOn _ _ ct hT hct
  have hcfb := subtractRows_bounds_of_massOn _ _ cf hF (fun s hs => (hcf s hs).1) _ _ hcfb
  have hctb : ∀ s ∈ cornerT f, s.ax = 2 ∧ s.bx = 2 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2 := by
    intro s hs
    obtain ⟨t, ht, hn, hm, he⟩ := subtractRows_mem_of_massOn _ _ ct hT
      (fun t ht => (hct t ht).1) s hs
    have hb := hctb t ht
    rw [he]
    unfold Segment.support
    split
    · exact hb
    · exact ⟨hb.2.1, hb.1, by simpa [min_comm, max_comm] using hb.2.2⟩
  have hper := periods_valid f hf 7
  have htrans : ∀ s ∈ (periods f 7).map Segment.transpose, s.Valid := by
    intro s hs
    obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
    exact transpose_valid t (hper t ht)
  rcases hstd with ⟨hua,hu,hd0,hd1⟩
  rcases hr with ⟨hrF,hrT,hrV,hrUA,hrU,hrd0,hrd1⟩
  refine ⟨hf,hfr,hua,hu,hd0,hd1,hrF,hrT,hrV,hrUA,hrU,hrd0,hrd1,hpm,?_,hcfb,hctb,hv,hpb,?_,?_⟩
  · intro s hs
    exact (List.mem_append.mp hs).elim (hcfv s) (hctv s)
  · intro δ hδ
    constructor
    · exact (subtractRows_measure _ _ (fun s hs => (hf.2.1 s (List.mem_append_left _ hs)).1)
        (fun s hs => (htrans s hs).1) (fun s hs => (hcfv s hs).1) 0 0).symm
    · exact (subtractRows_measure _ _ (fun s hs => (hf.2.1 s (List.mem_append_right _ hs)).1)
        (fun s hs => (hper s hs).1) (fun s hs => (hctv s hs).1) δ 0).symm
  · exact periodic_reflection _ (fun s hs => (profile_valid f hf s hs).2.1) hrefl

#print axioms structural_of_massOn_witness
end ClosedForm
