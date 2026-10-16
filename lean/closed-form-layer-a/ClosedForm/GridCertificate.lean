import ClosedForm.IntegerMeasureBridge
import ClosedForm.ReflectionBridge
import ClosedForm.CornerBridge
import ClosedForm.Mass

namespace ClosedForm.IntegerStructure
open MeasureTheory

lemma rowValid_spec (r : Row) (hr : rowValid r = true) :
    r.orientation ≤ 1 ∧ r.lo < r.hi ∧ 0 ≤ r.mass ∧ r.density*(r.hi-r.lo)=5*r.mass :=
  of_decide_eq_true hr

lemma decode_valid (D : ℕ) (r : Row) (hr : rowValid r = true) : (decode D r).Valid := by
  have h := rowValid_spec r hr
  have hn : (r.lo:ℚ) ≠ r.hi := by exact_mod_cast ne_of_lt h.2.1
  have hm : 0 ≤ (r.mass:ℚ) / D := div_nonneg (by exact_mod_cast h.2.2.1) (by positivity)
  unfold decode
  split <;> simp_all [Segment.Valid]

/-- Finite integer rectangle test, measured in fifth units. -/
def inBox (x y : ℤ) (r : Row) : Bool :=
  if r.orientation = 0 then decide (0 ≤ r.lo ∧ r.hi ≤ x ∧ 0 ≤ r.line ∧ r.line ≤ y)
  else decide (0 ≤ r.line ∧ r.line ≤ x ∧ 0 ≤ r.lo ∧ r.hi ≤ y)

lemma decode_bounds (D : ℕ) (r : Row) (hr : rowValid r = true) (x y : ℤ)
    (hb : inBox x y r = true) :
    0 ≤ min (decode D r).ax (decode D r).bx ∧ max (decode D r).ax (decode D r).bx ≤ (x:ℚ)/5 ∧
    0 ≤ min (decode D r).ay (decode D r).yb ∧ max (decode D r).ay (decode D r).yb ≤ (y:ℚ)/5 := by
  have hlo : (r.lo:ℚ)/5 ≤ (r.hi:ℚ)/5 := by
    apply div_le_div_of_nonneg_right _ (by norm_num)
    exact_mod_cast (rowValid_spec r hr).2.1.le
  unfold inBox at hb
  unfold decode
  split <;> simp_all only [↓reduceIte, decide_eq_true_eq]
  · obtain ⟨h1,h2,h3,h4⟩ := hb
    simp only [min_eq_left hlo, max_eq_right hlo, min_self, max_self]
    constructor
    · positivity
    constructor
    · exact div_le_div_of_nonneg_right (by exact_mod_cast h2) (by norm_num)
    constructor
    · positivity
    · exact div_le_div_of_nonneg_right (by exact_mod_cast h4) (by norm_num)
  · obtain ⟨h1,h2,h3,h4⟩ := hb
    simp only [min_eq_left hlo, max_eq_right hlo, min_self, max_self]
    constructor
    · positivity
    constructor
    · exact div_le_div_of_nonneg_right (by exact_mod_cast h2) (by norm_num)
    constructor
    · positivity
    · exact div_le_div_of_nonneg_right (by exact_mod_cast h4) (by norm_num)

def shiftRow (k : ℤ) (r : Row) : Row :=
  if r.orientation = 0 then {r with lo := r.lo+k, hi := r.hi+k}
  else {r with line := r.line+k}

def transposeRow (r : Row) : Row := {r with orientation := if r.orientation = 0 then 1 else 0}

def reflectRow (r : Row) : Row :=
  if r.orientation = 0 then {r with lo := 5-r.hi, hi := 5-r.lo}
  else {r with line := if r.line = 0 then 0 else 5-r.line}

lemma decode_shift (D : ℕ) (r : Row) (k : ℤ) :
    decode D (shiftRow k r) = (decode D r).shift ((k:ℚ)/5) 0 := by
  by_cases h : r.orientation = 0 <;>
    simp [decode, shiftRow, h, Segment.shift, Int.cast_add, add_div]

lemma decode_transpose (D : ℕ) (r : Row) :
    decode D (transposeRow r) = (decode D r).transpose := by
  by_cases h : r.orientation = 0 <;> simp [decode, transposeRow, h, Segment.transpose]

def isProfileRow (r : Row) : Bool :=
  if r.orientation = 0 then decide (15 ≤ r.lo ∧ r.hi ≤ 20)
  else decide (15 ≤ r.line ∧ r.line < 20)

def profileRows (xs : List Row) : List Row := (xs.filter isProfileRow).map (shiftRow (-15))
def periodRows (xs : List Row) : List Row :=
  (List.range 7).flatMap fun (j : ℕ) => xs.map (shiftRow (10+5*(j:ℤ)))

lemma decode_profile_test (D : ℕ) (r : Row) (hr : rowValid r = true) :
    (if (decode D r).ay == (decode D r).yb then
      3 ≤ min (decode D r).ax (decode D r).bx && max (decode D r).ax (decode D r).bx ≤ 4
     else (decode D r).ax == (decode D r).bx && 3 ≤ (decode D r).ax && (decode D r).ax < 4) =
      isProfileRow r := by
  have hlo : (r.lo:ℚ)/5 ≤ (r.hi:ℚ)/5 := by
    apply div_le_div_of_nonneg_right _ (by norm_num)
    exact_mod_cast (rowValid_spec r hr).2.1.le
  have hne : (r.lo:ℚ) ≠ r.hi := by exact_mod_cast ne_of_lt (rowValid_spec r hr).2.1
  apply Bool.eq_iff_iff.mpr
  by_cases ho : r.orientation = 0
  · simp only [decode, isProfileRow, ho, ↓reduceIte, beq_self_eq_true,
      min_eq_left hlo, max_eq_right hlo, Bool.and_eq_true, decide_eq_true_eq]
    norm_num [le_div_iff₀, div_le_iff₀]
    norm_cast
  · simp only [decode, isProfileRow, ho, ↓reduceIte, beq_iff_eq, div_left_inj' (by norm_num : (5:ℚ)≠0), hne,
      Bool.false_eq_true, ↓reduceIte, beq_self_eq_true, Bool.true_and,
      Bool.and_eq_true, decide_eq_true_eq]
    norm_num [le_div_iff₀, div_lt_iff₀]
    norm_cast

lemma profile_decode (f : Family) (D : ℕ) (xs : List Row)
    (hT : f.T = xs.map (decode D)) (hx : ∀ r ∈ xs, rowValid r = true) :
    profile f = (profileRows xs).map (decode D) := by
  unfold profile profileRows
  rw [hT, List.filter_map]
  have he : xs.filter (fun r =>
      if (decode D r).ay == (decode D r).yb then
        3 ≤ min (decode D r).ax (decode D r).bx && max (decode D r).ax (decode D r).bx ≤ 4
      else (decode D r).ax == (decode D r).bx && 3 ≤ (decode D r).ax && (decode D r).ax < 4) =
      xs.filter isProfileRow := by
    apply List.filter_congr
    intro r hr
    exact decode_profile_test D r (hx r hr)
  simp only [Function.comp_def]
  rw [he]
  simp only [List.map_map]
  apply List.map_congr_left
  intro r hr
  rw [Function.comp_apply, Function.comp_apply, decode_shift]
  norm_num

lemma periods_decode (f : Family) (D : ℕ) (p : List Row)
    (hp : profile f = p.map (decode D)) :
    periods f 7 = (periodRows p).map (decode D) := by
  simp only [periods, periodRows, hp, List.map_flatMap, List.map_map]
  apply List.flatMap_congr
  intro j hj
  apply List.map_congr_left
  intro r hr
  simp only [Function.comp_apply, decode_shift]
  congr 1
  push_cast
  ring

lemma decode_reflect_measure (D : ℕ) (r : Row) (hr : rowValid r = true) (dx dy : ℝ) :
    segmentMeasure (decode D (reflectRow r)) dx dy =
      segmentMeasure (StructuralCheck.reflectProfile (decode D r)) dx dy := by
  have hne : (r.lo:ℚ) ≠ r.hi := by exact_mod_cast ne_of_lt (rowValid_spec r hr).2.1
  by_cases ho : r.orientation = 0
  · simp only [reflectRow, decode, ho, ↓reduceIte, StructuralCheck.reflectProfile,
      beq_self_eq_true]
    have he : (5-(r.hi:ℚ))/5 = 1-(r.hi:ℚ)/5 := by ring
    have he' : (5-(r.lo:ℚ))/5 = 1-(r.lo:ℚ)/5 := by ring
    simp only [Int.cast_sub, Int.cast_ofNat, he, he']
    exact segmentMeasure_reverse
      ⟨1-(r.lo:ℚ)/5,(r.line:ℚ)/5,1-(r.hi:ℚ)/5,(r.line:ℚ)/5,(r.mass:ℚ)/D⟩ dx dy
  · simp only [reflectRow, decode, ho, ↓reduceIte, StructuralCheck.reflectProfile,
      beq_iff_eq, div_left_inj' (by norm_num : (5:ℚ)≠0), hne, ↓reduceIte]
    by_cases hz : r.line = 0
    · simp [hz]
    · have hz' : (r.line:ℚ) ≠ 0 := by exact_mod_cast hz
      simp [hz, hz', Int.cast_sub, sub_div]

/-- Source fractions are linked to decoded integer data by cross products.
Only integer witnesses are evaluated by concrete kernel checks. -/
lemma fraction_link (a b c d : ℤ) (hb : b ≠ 0) (hd : d ≠ 0) (h : a*d=c*b) :
    (a:ℚ)/(b:ℚ) = (c:ℚ)/(d:ℚ) := by
  apply (div_eq_div_iff (by exact_mod_cast hb) (by exact_mod_cast hd)).mpr
  exact_mod_cast h

structure SourceRow where
  ax : ℤ × ℤ
  ay : ℤ × ℤ
  bx : ℤ × ℤ
  yb : ℤ × ℤ
  mass : ℤ × ℤ
  deriving DecidableEq, Repr

def decodeFraction (q : ℤ × ℤ) : ℚ := (q.1:ℚ)/(q.2:ℚ)
def decodeSource (q : SourceRow) : Segment :=
  ⟨decodeFraction q.ax,decodeFraction q.ay,decodeFraction q.bx,decodeFraction q.yb,decodeFraction q.mass⟩

def fractionMatches (q : ℤ × ℤ) (n d : ℤ) : Bool :=
  decide (q.2 ≠ 0 ∧ d ≠ 0 ∧ q.1*d=n*q.2)

lemma fractionMatches_sound (q : ℤ × ℤ) (n d : ℤ) (h : fractionMatches q n d = true) :
    decodeFraction q = (n:ℚ)/(d:ℚ) := by
  obtain ⟨h1,h2,h3⟩ : q.2 ≠ 0 ∧ d ≠ 0 ∧ q.1*d=n*q.2 := of_decide_eq_true h
  exact fraction_link _ _ _ _ h1 h2 h3

def sourceMatches (D : ℕ) (q : SourceRow) (r : Row) : Bool :=
  (if r.orientation = 0 then
    fractionMatches q.ax r.lo 5 && fractionMatches q.ay r.line 5 &&
    fractionMatches q.bx r.hi 5 && fractionMatches q.yb r.line 5
   else fractionMatches q.ax r.line 5 && fractionMatches q.ay r.lo 5 &&
    fractionMatches q.bx r.line 5 && fractionMatches q.yb r.hi 5) &&
  fractionMatches q.mass r.mass D

lemma sourceMatches_sound (D : ℕ) (q : SourceRow) (r : Row)
    (h : sourceMatches D q r = true) : decodeSource q = decode D r := by
  unfold sourceMatches at h
  by_cases ho : r.orientation = 0 <;> simp only [ho, ↓reduceIte, Bool.and_eq_true] at h
  all_goals
    obtain ⟨⟨⟨⟨h1,h2⟩,h3⟩,h4⟩,h5⟩ := h
    simp only [decodeSource, decode, ho, ↓reduceIte]
    congr 1
    · exact fractionMatches_sound _ _ _ h1
    · exact fractionMatches_sound _ _ _ h2
    · exact fractionMatches_sound _ _ _ h3
    · exact fractionMatches_sound _ _ _ h4
    · simpa only [Int.cast_natCast] using fractionMatches_sound _ _ _ h5

def rowsMatch (D : ℕ) : List SourceRow → List Row → Bool
  | [], [] => true
  | q::qs, r::rs => sourceMatches D q r && rowsMatch D qs rs
  | _, _ => false

lemma rowsMatch_sound (D : ℕ) (qs : List SourceRow) (rs : List Row)
    (h : rowsMatch D qs rs = true) : qs.map decodeSource = rs.map (decode D) := by
  induction qs generalizing rs with
  | nil => cases rs <;> simp_all [rowsMatch]
  | cons q qs ih =>
    cases rs with
    | nil => simp [rowsMatch] at h
    | cons r rs =>
      simp only [rowsMatch, Bool.and_eq_true] at h
      obtain ⟨h1,h2⟩ := h
      simp only [List.map_cons]
      rw [sourceMatches_sound D q r h1, ih rs h2]

lemma all_append_checked {α : Type*} (p : α → Bool) (xs ys : List α)
    (hx : xs.all p = true) (hy : ys.all p = true) : (xs++ys).all p = true := by
  simp [hx, hy]

theorem sorted_tables_rowsMeasure (D : ℕ) (xs ys : List Row) (sx sy : List Entry)
    (hD : 0 < D) (hx : ∀ r ∈ xs, rowValid r = true) (hy : ∀ r ∈ ys, rowValid r = true)
    (hpx : (xs.flatMap rowEvents).Perm sx) (hpy : (ys.flatMap rowEvents).Perm sy)
    (h : finish (run {} sx) = finish (run {} sy)) (dx dy : ℝ) :
    rowsMeasure (xs.map (decode D)) dx dy = rowsMeasure (ys.map (decode D)) dx dy := by
  ext A hA
  apply (ENNReal.toReal_eq_toReal_iff' (rowsMeasure_ne_top _ _ _ _) (rowsMeasure_ne_top _ _ _ _)).mp
  rw [rows_apply_pairing D hD xs hx dx dy hA, rows_apply_pairing D hD ys hy dx dy hA]
  exact equal_sorted_tables_equal_pairings _ _ sx sy hpx hpy h _

lemma reflected_rows_measure (D : ℕ) (xs : List Row) (hx : ∀ r ∈ xs, rowValid r = true)
    (dx dy : ℝ) :
    rowsMeasure ((xs.map reflectRow).map (decode D)) dx dy =
      rowsMeasure ((xs.map (decode D)).map StructuralCheck.reflectProfile) dx dy := by
  unfold rowsMeasure
  simp only [List.map_map]
  apply congrArg List.sum
  apply List.map_congr_left
  intro r hr
  exact decode_reflect_measure D r (hx r hr) dx dy

lemma decode_mass_sum (D : ℕ) (xs : List Row) :
    (((xs.map (decode D)).map Segment.mass).sum : ℚ) =
      (((xs.map Row.mass).sum:ℤ):ℚ) / D := by
  induction xs with
  | nil => simp
  | cons r xs ih =>
    simp only [List.map_cons, List.sum_cons, Int.cast_add, add_div, ih]
    unfold decode
    split <;> rfl

end IntegerStructure

/-- Assembly from checked row witnesses. The corner support obligations refer to
the original `subtractRows` definitions, including duplicate supports. -/
theorem structural_of_witness (f fr : Family) (cs : List Segment)
    (hf : f.Valid) (hfr : fr.Valid)
    (hstd : f.UA = 9/5 ∧ f.U = none ∧ 0 ≤ f.d0 ∧ f.d1 ≤ 1)
    (hr : fr.F=f.T ∧ fr.T=[] ∧ fr.V=[] ∧ fr.UA=f.UA ∧ fr.U=none ∧ fr.d0=f.d0 ∧ fr.d1=f.d1)
    (hpm : ((profile f).map Segment.mass).sum = 9/5)
    (hc : ∀ s ∈ cs, s.Valid)
    (hcb : ∀ s ∈ cs, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 2+f.d0 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 2)
    (hv : ∀ v ∈ f.V, 0 ≤ v.xl ∧ 0 ≤ v.y ∧ v.y ≤ 2)
    (hpb : ∀ s ∈ profile f, 0 ≤ min s.ax s.bx ∧ max s.ax s.bx ≤ 1 ∧
      0 ≤ min s.ay s.yb ∧ max s.ay s.yb ≤ 9/5)
    (hF : f.F.Perm (cs ++ (periods f 7).map Segment.transpose))
    (hT : f.T.Perm (periods f 7))
    (hrefl : ∀ dx : ℝ, rowsMeasure (profile f) dx 0 =
      rowsMeasure ((profile f).map StructuralCheck.reflectProfile) dx 0) : Structural f fr := by
  have hct : cornerT f = [] := subtractRows_eq_nil_of_perm _ _ hT
  have hcfv : ∀ s ∈ cornerF f, s.Valid := subtractRows_valid_of_perm _ _ cs hF hc
  have hcfb := subtractRows_bounds_of_perm _ _ cs hF (fun s hs => (hc s hs).1) _ _ hcb
  have hper : ∀ s ∈ periods f 7, s.Valid := by
    intro s hs
    have := hf.2.1 s (List.mem_append_right _ (hT.mem_iff.mpr hs))
    exact this
  have htrans : ∀ s ∈ (periods f 7).map Segment.transpose, s.Valid := by
    intro s hs
    obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
    have h := hper t ht
    simp only [Segment.Valid, Segment.transpose] at *
    tauto
  rcases hstd with ⟨hua, hu, hd0, hd1⟩
  rcases hr with ⟨hrF,hrT,hrV,hrUA,hrU,hrd0,hrd1⟩
  refine ⟨hf,hfr,hua,hu,hd0,hd1,hrF,hrT,hrV,hrUA,hrU,hrd0,hrd1,hpm,?_,hcfb,?_,hv,hpb,?_,?_⟩
  · simpa [hct] using hcfv
  · simp [hct]
  · intro δ hδ
    constructor
    · exact (subtractRows_measure _ _ (fun s hs => (hf.2.1 s (List.mem_append_left _ hs)).1)
        (fun s hs => (htrans s hs).1) (fun s hs => (hcfv s hs).1) 0 0).symm
    · rw [hct]
      simpa [rowsMeasure] using rowsMeasure_perm hT δ 0
  · exact periodic_reflection _ (fun s hs => (profile_valid f hf s hs).2.1) hrefl

end ClosedForm

