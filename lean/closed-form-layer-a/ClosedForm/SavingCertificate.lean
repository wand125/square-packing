import ClosedForm.Saving
import ClosedForm.GridCertificate

namespace ClosedForm

lemma subtractRows_mass (xs ys : List Segment) :
    (((subtractRows xs ys).map Segment.mass).sum : ℝ) =
      ((xs.map Segment.mass).sum : ℝ) - ((ys.map Segment.mass).sum : ℝ) := by
  simpa only [supportPairing, mul_one, Rat.cast_list_sum, List.map_map,
    Function.comp_def] using subtractRows_pairing xs ys (fun _ => 1)

lemma periods_mass (f : Family) (n : ℕ) :
    ((periods f n).map Segment.mass).sum = n * ((profile f).map Segment.mass).sum := by
  induction n with
  | zero => simp [periods]
  | succ n ih =>
    simp only [periods, List.range_succ, List.flatMap_append, List.flatMap_cons,
      List.flatMap_nil, List.append_nil, List.map_append, List.sum_append] at *
    simp only [List.map_map, Function.comp_def, Segment.shift] at *
    rw [ih]
    push_cast
    ring

lemma fixedCornerMass_formula (f : Family) :
    (fixedCornerMass f : ℝ) = ((f.F.map Segment.mass).sum : ℝ) +
      ((f.T.map Segment.mass).sum : ℝ) - 14 * (( (profile f).map Segment.mass).sum : ℝ) := by
  simp only [fixedCornerMass, List.map_append, List.sum_append, Rat.cast_add,
    cornerF, cornerT, subtractRows_mass, List.map_map, Function.comp_def, Segment.transpose]
  simp only [periods_mass, Rat.cast_mul, Rat.cast_natCast]
  norm_num only [Nat.cast_ofNat]
  ring

namespace IntegerStructure

def phaseZero (r : Row) : Bool :=
  if r.orientation = 0 then r.lo == 0 && r.hi == 0 else r.line == 0

lemma decode_phaseZero (D : ℕ) (r : Row) :
    ((decode D r).ax == 0 && (decode D r).bx == 0) = phaseZero r := by
  unfold decode phaseZero
  split <;> apply Bool.eq_iff_iff.mpr <;> simp [div_eq_zero_iff]

lemma terminal_decode (f : Family) (D : ℕ) (P : List Row)
    (hp : profile f = P.map (decode D)) :
    (terminalMass f : ℝ) = (((P.filter phaseZero).map Row.mass).sum : ℝ) / D := by
  rw [terminalMass, terminal, hp, List.filter_map]
  simp only [Function.comp_def, decode_phaseZero]
  rw [decode_mass_sum]
  simp only [Rat.cast_div, Rat.cast_intCast, Rat.cast_natCast]

/-- Only xl and rho affect the variable mass. Coordinates use the established fifth grid. -/
def decodeVariable (D : ℕ) (r : ℤ × ℤ) : VariableSegment :=
  ⟨(r.1 : ℚ) / 5, 0, (r.2 : ℚ) / D⟩

def variablePairs (vs : List VariableSegment) : List (ℚ × ℚ) :=
  vs.map fun v => (v.xl, v.rho)

def variableSource (qs : List ((ℤ × ℤ) × (ℤ × ℤ))) : List (ℚ × ℚ) :=
  qs.map fun q => (decodeFraction q.1, decodeFraction q.2)

def variablesMatch (D : ℕ) : List ((ℤ × ℤ) × (ℤ × ℤ)) → List (ℤ × ℤ) → Bool
  | [], [] => true
  | q :: qs, v :: vs => fractionMatches q.1 v.1 5 &&
      fractionMatches q.2 v.2 D && variablesMatch D qs vs
  | _, _ => false

lemma variablesMatch_sound (D : ℕ) (qs : List ((ℤ × ℤ) × (ℤ × ℤ)))
    (vs : List (ℤ × ℤ)) (h : variablesMatch D qs vs = true) :
    variableSource qs = variablePairs (vs.map (decodeVariable D)) := by
  induction qs generalizing vs with
  | nil => cases vs <;> simp_all [variablesMatch, variableSource, variablePairs]
  | cons q qs ih =>
    cases vs with
    | nil => simp [variablesMatch] at h
    | cons v vs =>
      simp only [variablesMatch, Bool.and_eq_true] at h
      have hx := fractionMatches_sound _ _ _ h.1.1
      have hr := fractionMatches_sound _ _ _ h.1.2
      have ht := ih vs h.2
      simpa only [variableSource, variablePairs, List.map_cons, decodeVariable,
        List.map_map, Int.cast_ofNat, Int.cast_natCast, hx, hr] using
        congrArg (List.cons ((v.1 : ℚ)/5, (v.2 : ℚ)/D)) ht

lemma variable_mass_pairs (vs ws : List VariableSegment)
    (h : variablePairs vs = variablePairs ws) (δ : ℝ) :
    (vs.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum =
    (ws.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum := by
  have := congrArg (fun ps : List (ℚ × ℚ) =>
    (ps.map fun p => (p.2 : ℝ) * (2 + δ - p.1)).sum) h
  simpa only [variablePairs, List.map_map, Function.comp_def] using this

lemma variable_decode (D : ℕ) (vs : List (ℤ × ℤ)) (δ : ℝ) :
    ((vs.map (decodeVariable D)).map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum =
      (((vs.map fun r => r.2 * (10 - r.1)).sum : ℤ) : ℝ) / (5 * D) +
      (((vs.map Prod.snd).sum : ℤ) : ℝ) / D * δ := by
  induction vs with
  | nil => simp
  | cons r vs ih =>
    simp only [List.map_cons, List.sum_cons, ih, decodeVariable,
      Rat.cast_div, Rat.cast_intCast, Rat.cast_ofNat, Rat.cast_natCast,
      Int.cast_add, Int.cast_mul, Int.cast_sub, Int.cast_ofNat]
    ring

/-- Integer row sums identify the affine saving; all rational operations are symbolic. -/
lemma saving_from_integer_sums (f : Family) (D : ℕ) (F T P : List Row)
    (vs : List (ℤ × ℤ)) (fm tm pm vm vx : ℤ)
    (hf : f.F = F.map (decode D)) (ht : f.T = T.map (decode D))
    (hp : profile f = P.map (decode D))
    (hv : variablePairs f.V = variablePairs (vs.map (decodeVariable D)))
    (hfm : (F.map Row.mass).sum + (T.map Row.mass).sum = fm)
    (hpm : (P.map Row.mass).sum = pm)
    (htm : ((P.filter phaseZero).map Row.mass).sum = tm)
    (hvm : (vs.map Prod.snd).sum = vm)
    (hvx : (vs.map fun r => r.2 * (10-r.1)).sum = vx) (δ : ℝ) :
    saving f δ = 99/25 + (9/5)*δ - (fm : ℝ)/D + 14*(pm : ℝ)/D -
      (vx : ℝ)/(5*D) - (vm : ℝ)/D*δ - (tm : ℝ)/D := by
  rw [saving, cornerMass, fixedCornerMass_formula, hf, ht, hp,
    decode_mass_sum, decode_mass_sum, decode_mass_sum,
    terminal_decode f D P hp, variable_mass_pairs _ _ hv, variable_decode,
    hpm, htm, hvm, hvx]
  simp only [Rat.cast_div, Rat.cast_intCast, Rat.cast_natCast]
  have hfm' : (((F.map Row.mass).sum : ℤ) : ℝ) +
    (((T.map Row.mass).sum : ℤ) : ℝ) = (fm : ℝ) := by exact_mod_cast hfm
  rw [← hfm']
  ring

/-- One integer inequality after clearing every positive denominator. -/
lemma endpoint_integer (D : ℕ) (an ad bn bd dn dd fm tm pm vm vx : ℤ)
    (hD : 0 < D) (ha : 0 < ad) (hb : 0 < bd) (hd : 0 < dd)
    (h : 25 * (an * dn * bd + bn * ad * dd) * (D : ℤ) ≤
      (99 * dd * (D : ℤ) + 45 * dn * (D : ℤ) - 25 * fm * dd +
        350 * pm * dd - 5 * vx * dd - 25 * vm * dn - 25 * tm * dd) * ad * bd) :
    ((an : ℝ)/ad) * ((dn : ℝ)/dd) + (bn : ℝ)/bd ≤
      99/25 + (9/5)*((dn : ℝ)/dd) - (fm : ℝ)/D + 14*(pm : ℝ)/D -
      (vx : ℝ)/(5*D) - (vm : ℝ)/D*((dn : ℝ)/dd) - (tm : ℝ)/D := by
  have hD' : (0 : ℝ) < D := by exact_mod_cast hD
  have ha' : (0 : ℝ) < ad := by exact_mod_cast ha
  have hb' : (0 : ℝ) < bd := by exact_mod_cast hb
  have hd' : (0 : ℝ) < dd := by exact_mod_cast hd
  apply (mul_le_mul_iff_left₀ (show (0 : ℝ) < 25 * ad * bd * dd * D by positivity)).mp
  convert (show (25 : ℝ) * (an * dn * bd + bn * ad * dd) * D ≤
    (99 * dd * D + 45 * dn * D - 25 * fm * dd + 350 * pm * dd -
      5 * vx * dd - 25 * vm * dn - 25 * tm * dd) * ad * bd by exact_mod_cast h) using 1 <;>
    (try field_simp [ne_of_gt hD', ne_of_gt ha', ne_of_gt hb', ne_of_gt hd']) <;>
    first | rfl | ring

#print axioms saving_from_integer_sums
#print axioms endpoint_integer
end IntegerStructure
end ClosedForm
