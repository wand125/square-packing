import ClosedForm.IntegerMeasureBridge

namespace ClosedForm
open MeasureTheory

lemma nodup_eraseDups_local {α : Type*} [BEq α] [LawfulBEq α] (xs : List α) :
    xs.eraseDups.Nodup := by
  cases xs with
  | nil => simp
  | cons a xs =>
    rw [List.eraseDups_cons, List.nodup_cons]
    constructor
    · simp [List.mem_eraseDups]
    · exact nodup_eraseDups_local _
termination_by xs.length
decreasing_by exact lt_of_le_of_lt (List.length_filter_le _ _) (Nat.lt_succ_self _)

lemma weighted_group {α β : Type*} [DecidableEq β]
    (key : α → β) (w : α → ℝ) (g : β → ℝ) (K : Finset β)
    (xs : List α) (hK : ∀ x ∈ xs, key x ∈ K) :
    (xs.map fun x => w x * g (key x)).sum =
      ∑ k ∈ K, ((xs.filter fun x => key x == k).map w).sum * g k := by
  induction xs with
  | nil => simp
  | cons a xs ih =>
    have ht : ∀ x ∈ xs, key x ∈ K := fun x hx => hK x (by simp [hx])
    simp only [List.map_cons, List.sum_cons, ih ht]
    have he : (∑ k ∈ K, (((a::xs).filter fun x => key x == k).map w).sum * g k) =
        (∑ k ∈ K, (if key a = k then w a * g k else 0)) +
        ∑ k ∈ K, ((xs.filter fun x => key x == k).map w).sum * g k := by
      rw [← Finset.sum_add_distrib]
      apply Finset.sum_congr rfl
      intro k hk
      by_cases h : key a = k <;> simp [h, add_mul]
    rw [he]
    congr 1
    symm
    rw [Finset.sum_eq_single (key a)]
    · simp
    · intro k hk hne; simp [Ne.symm hne]
    · intro hnot; exact (hnot (hK a (by simp))).elim

noncomputable def supportValue (dx dy : ℝ) (A : Set Point) (p : QPoint × QPoint) : ℝ :=
  (SquarePacking.segMeasure (p.1.1 + dx, p.1.2 + dy)
    (p.2.1 + dx, p.2.2 + dy) A).toReal

noncomputable def supportPairing (xs : List Segment) (g : (QPoint × QPoint) → ℝ) : ℝ :=
  (xs.map fun s => (s.mass:ℝ) * g s.support).sum

lemma rowsMeasure_supportPairing (xs : List Segment)
    (hx : ∀ s ∈ xs, 0 ≤ s.mass) (dx dy : ℝ) (A : Set Point) :
    (rowsMeasure xs dx dy A).toReal = supportPairing xs (supportValue dx dy A) := by
  rw [rowsMeasure_toReal]
  apply congrArg List.sum
  apply List.map_congr_left
  intro s hs
  rw [← segmentMeasure_support s dx dy]
  change (ENNReal.ofReal (s.mass:ℝ) * _).toReal = _
  rw [ENNReal.toReal_mul, ENNReal.toReal_ofReal (by exact_mod_cast hx s hs)]
  rfl

lemma supportPairing_group (xs : List Segment) (g : (QPoint × QPoint) → ℝ)
    (K : Finset (QPoint × QPoint)) (hK : ∀ s ∈ xs, s.support ∈ K) :
    supportPairing xs g = ∑ k ∈ K, (massOn xs k : ℝ) * g k := by
  rw [supportPairing, weighted_group Segment.support (fun s => (s.mass:ℝ)) g K xs hK]
  apply Finset.sum_congr rfl
  intro k hk
  simp only [massOn, Rat.cast_list_sum, List.map_map]
  simp only [beq_eq_decide, Function.comp_def]

lemma support_of_mk_support (s : Segment) (m : ℚ) :
    (⟨s.support.1.1, s.support.1.2, s.support.2.1, s.support.2.2, m⟩ : Segment).support =
      s.support := by
  have h : s.support.1.1 + s.support.1.2 ≤ s.support.2.1 + s.support.2.2 := by
    unfold Segment.support
    split <;> simp_all <;> linarith
  change (if s.support.1.1 + s.support.1.2 ≤ s.support.2.1 + s.support.2.2
    then s.support else _) = s.support
  rw [if_pos h]

lemma subtractRows_pairing (xs ys : List Segment) (g : (QPoint × QPoint) → ℝ) :
    supportPairing (subtractRows xs ys) g = supportPairing xs g - supportPairing ys g := by
  classical
  let ks := ((xs ++ ys).map Segment.support).eraseDups
  let K := ks.toFinset
  have hK (s : Segment) (hs : s ∈ xs ++ ys) : s.support ∈ K := by
    simp only [K, List.mem_toFinset, ks, List.mem_eraseDups, List.mem_map]
    exact ⟨s, hs, rfl⟩
  rw [supportPairing_group xs g K (fun s hs => hK s (List.mem_append_left _ hs)),
    supportPairing_group ys g K (fun s hs => hK s (List.mem_append_right _ hs)),
    ← Finset.sum_sub_distrib]
  have hsupport (p : QPoint × QPoint) (hp : p ∈ ks) (m : ℚ) :
      (⟨p.1.1, p.1.2, p.2.1, p.2.2, m⟩ : Segment).support = p := by
    simp only [ks, List.mem_eraseDups, List.mem_map] at hp
    obtain ⟨s, hs, rfl⟩ := hp
    exact support_of_mk_support s m
  have hfilter (zs : List Segment) :
      supportPairing (zs.filter fun s => s.mass != 0) g = supportPairing zs g := by
    induction zs with
    | nil => rfl
    | cons s zs ih =>
      by_cases hz : s.mass = 0 <;> simp_all [supportPairing]
  rw [subtractRows, hfilter]
  simp only [supportPairing, List.map_map]
  change (ks.map fun p =>
    ((massOn xs p - massOn ys p : ℚ):ℝ) *
      g (⟨p.1.1, p.1.2, p.2.1, p.2.2, massOn xs p - massOn ys p⟩ : Segment).support).sum = _
  have hh : (ks.map fun p =>
    ((massOn xs p - massOn ys p : ℚ):ℝ) *
      g (⟨p.1.1, p.1.2, p.2.1, p.2.2, massOn xs p - massOn ys p⟩ : Segment).support) =
      ks.map (fun p => (massOn xs p:ℝ)*g p - (massOn ys p:ℝ)*g p) := by
    apply List.map_congr_left
    intro p hp
    rw [hsupport p hp, Rat.cast_sub, sub_mul]
  rw [hh]
  exact (List.sum_toFinset (fun p => (massOn xs p:ℝ)*g p - (massOn ys p:ℝ)*g p) (nodup_eraseDups_local ((xs ++ ys).map Segment.support))).symm

/-- Exact-support subtraction decomposes measures whenever all residual masses
are nonnegative. No change to either corner definition is needed. -/
theorem subtractRows_measure (xs ys : List Segment)
    (hx : ∀ s ∈ xs, 0 ≤ s.mass) (hy : ∀ s ∈ ys, 0 ≤ s.mass)
    (hz : ∀ s ∈ subtractRows xs ys, 0 ≤ s.mass) (dx dy : ℝ) :
    rowsMeasure (subtractRows xs ys) dx dy + rowsMeasure ys dx dy =
      rowsMeasure xs dx dy := by
  ext A hA
  rw [Measure.add_apply]
  apply (ENNReal.toReal_eq_toReal_iff'
    (ENNReal.add_ne_top.mpr ⟨rowsMeasure_ne_top _ _ _ _, rowsMeasure_ne_top _ _ _ _⟩)
    (rowsMeasure_ne_top _ _ _ _)).mp
  rw [ENNReal.toReal_add (rowsMeasure_ne_top _ _ _ _) (rowsMeasure_ne_top _ _ _ _),
    rowsMeasure_supportPairing _ hz, rowsMeasure_supportPairing _ hy,
    rowsMeasure_supportPairing _ hx, subtractRows_pairing]
  ring

lemma massOn_perm {xs ys : List Segment} (h : xs.Perm ys) (p : QPoint × QPoint) :
    massOn xs p = massOn ys p := by
  exact ((h.filter (fun s => s.support == p)).map Segment.mass).sum_eq

lemma massOn_append (xs ys : List Segment) (p : QPoint × QPoint) :
    massOn (xs++ys) p = massOn xs p + massOn ys p := by
  simp [massOn, List.filter_append, List.sum_append]

lemma massOn_nonneg (xs : List Segment) (hx : ∀ s ∈ xs, 0 ≤ s.mass) (p : QPoint × QPoint) :
    0 ≤ massOn xs p := by
  apply List.sum_nonneg
  intro m hm
  obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hm
  exact hx s (List.mem_filter.mp hs).1

/-- Each nonzero residual has the support of a nonzero corner witness row. -/
lemma subtractRows_mem_of_perm (xs ys cs : List Segment) (h : xs.Perm (cs++ys))
    (hc : ∀ s ∈ cs, 0 ≤ s.mass) (s : Segment) (hs : s ∈ subtractRows xs ys) :
    ∃ t ∈ cs, t.mass ≠ 0 ∧ 0 ≤ s.mass ∧
      s = ⟨t.support.1.1,t.support.1.2,t.support.2.1,t.support.2.2,s.mass⟩ := by
  obtain ⟨hs, hz⟩ := List.mem_filter.mp hs
  obtain ⟨p, hp, rfl⟩ := List.mem_map.mp hs
  have he : massOn xs p - massOn ys p = massOn cs p := by
    rw [massOn_perm h, massOn_append]
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

lemma support_row_valid (t : Segment) (ht : t.Valid) (hn : t.mass ≠ 0) (m : ℚ) (hm : 0 ≤ m) :
    (⟨t.support.1.1,t.support.1.2,t.support.2.1,t.support.2.2,m⟩:Segment).Valid := by
  have hne : ¬(t.ax=t.bx ∧ t.ay=t.yb) := fun h => hn (ht.2.2 h)
  unfold Segment.support
  split
  · exact ⟨hm, ht.2.1, fun h => (hne h).elim⟩
  · exact ⟨hm, ht.2.1.imp Eq.symm Eq.symm, fun h => (hne ⟨h.1.symm,h.2.symm⟩).elim⟩

lemma subtractRows_valid_of_perm (xs ys cs : List Segment) (h : xs.Perm (cs++ys))
    (hc : ∀ s ∈ cs, s.Valid) : ∀ s ∈ subtractRows xs ys, s.Valid := by
  intro s hs
  obtain ⟨t, ht, hn, hm, he⟩ := subtractRows_mem_of_perm xs ys cs h (fun t ht => (hc t ht).1) s hs
  rw [he]
  exact support_row_valid t (hc t ht) hn s.mass hm

lemma subtractRows_bounds_of_perm (xs ys cs : List Segment) (h : xs.Perm (cs++ys))
    (hc : ∀ s ∈ cs, 0 ≤ s.mass) (x y : ℚ)
    (hb : ∀ s ∈ cs, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ x ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ y) :
    ∀ s ∈ subtractRows xs ys, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ x ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ y := by
  intro s hs
  obtain ⟨t, ht, hn, hm, he⟩ := subtractRows_mem_of_perm xs ys cs h hc s hs
  have hb := hb t ht
  rw [he]
  unfold Segment.support
  split <;> simpa [min_comm, max_comm] using hb

lemma subtractRows_eq_nil_of_perm (xs ys : List Segment) (h : xs.Perm ys) :
    subtractRows xs ys = [] := by
  apply List.filter_eq_nil_iff.mpr
  intro s hs
  obtain ⟨p, hp, rfl⟩ := List.mem_map.mp hs
  simp [massOn_perm h]

namespace IntegerStructure

lemma subtract_pairing (g : Key → ℝ) (xs ys : List Entry) :
    pairing g (subtract xs ys) = pairing g xs - pairing g ys := by
  have hn (zs : List Entry) :
      pairing g (zs.map fun e => ⟨e.key, -e.weight⟩) = -pairing g zs := by
    induction zs with
    | nil => simp
    | cons e zs ih => simp [ih, Int.cast_neg]; ring
  fun_induction subtract xs ys with
  | case1 ys => simp [hn]
  | case2 xs => simp
  | case3 a xs b ys h ih =>
    have he : a.key = b.key := by simpa using h
    simp [pairing_cons, ih, he, Int.cast_sub]; ring
  | case4 a xs b ys h hle ih => simp [pairing_cons, ih]; ring
  | case5 a xs b ys h hle ih => simp [pairing_cons, ih, Int.cast_neg]; ring

/-- Support keys may be supplied by an integer certificate. Coordinates are
symbolic; only the total masses are decoded from the common denominator. -/
def decodeSupport (D : ℕ) (support : Key → Segment) (e : Entry) : Segment :=
  { support e.key with mass := (e.weight:ℚ) / D }

lemma decodeSupport_nonneg (D : ℕ) (support : Key → Segment) (es : List Entry)
    (he : ∀ e ∈ es, 0 ≤ e.weight) :
    ∀ s ∈ es.map (decodeSupport D support), 0 ≤ s.mass := by
  intro s hs
  obtain ⟨e, he', rfl⟩ := List.mem_map.mp hs
  exact div_nonneg (by exact_mod_cast he e he') (by exact_mod_cast Nat.zero_le D)

lemma decodeSupport_pairing (D : ℕ) (support : Key → Segment) (es : List Entry)
    (he : ∀ e ∈ es, 0 ≤ e.weight) (dx dy : ℝ) (A : Set Point) :
    (rowsMeasure (es.map (decodeSupport D support)) dx dy A).toReal =
      pairing (fun k => (1/(D:ℝ)) *
        (SquarePacking.segMeasure ((support k).ax + dx, (support k).ay + dy)
          ((support k).bx + dx, (support k).yb + dy) A).toReal) es := by
  rw [rowsMeasure_toReal]
  simp only [pairing, List.map_map]
  apply congrArg List.sum
  apply List.map_congr_left
  intro e he'
  simp only [Function.comp_def, decodeSupport, segmentMeasure, Measure.smul_apply, smul_eq_mul,
    ENNReal.toReal_mul, Rat.cast_div, Rat.cast_intCast, Rat.cast_natCast]
  rw [ENNReal.toReal_ofReal (div_nonneg (by exact_mod_cast he e he') (by positivity))]
  ring

/-- Linear merge subtraction agrees with the original exact-support corner
subtraction as a measure. Duplicate keys and differently ordered inputs are
allowed; the hypotheses explicitly require nonnegative residual masses. -/
theorem merge_subtractRows_agreement (D : ℕ) (support : Key → Segment)
    (xs ys : List Entry)
    (hx : ∀ e ∈ xs, 0 ≤ e.weight) (hy : ∀ e ∈ ys, 0 ≤ e.weight)
    (hz : ∀ e ∈ subtract xs ys, 0 ≤ e.weight)
    (hold : ∀ s ∈ subtractRows (xs.map (decodeSupport D support))
      (ys.map (decodeSupport D support)), 0 ≤ s.mass) (dx dy : ℝ) :
    rowsMeasure ((subtract xs ys).map (decodeSupport D support)) dx dy =
      rowsMeasure (subtractRows (xs.map (decodeSupport D support))
        (ys.map (decodeSupport D support))) dx dy := by
  ext A hA
  apply (ENNReal.toReal_eq_toReal_iff' (rowsMeasure_ne_top _ _ _ _)
    (rowsMeasure_ne_top _ _ _ _)).mp
  have ho := congrArg (fun μ : Measure Point => (μ A).toReal)
    (subtractRows_measure _ _ (decodeSupport_nonneg D support xs hx)
      (decodeSupport_nonneg D support ys hy) hold dx dy)
  rw [Measure.add_apply, ENNReal.toReal_add (rowsMeasure_ne_top _ _ _ _)
    (rowsMeasure_ne_top _ _ _ _), decodeSupport_pairing D support ys hy,
    decodeSupport_pairing D support xs hx] at ho
  rw [decodeSupport_pairing D support _ hz, subtract_pairing]
  linarith

#print axioms merge_subtractRows_agreement
end IntegerStructure

#print axioms subtractRows_measure
end ClosedForm
