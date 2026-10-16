import ClosedForm.Measure

/-! Measure identities used by the structural bridge. All translations and
masses below are symbolic; no published rational weights are reduced. -/
namespace ClosedForm

open MeasureTheory

theorem segmentMeasure_reverse (s : Segment) (dx dy : ℝ) :
    segmentMeasure ⟨s.bx, s.yb, s.ax, s.ay, s.mass⟩ dx dy =
      segmentMeasure s dx dy := by
  simp only [segmentMeasure, SquarePacking.segMeasure_comm]

theorem segmentMeasure_add_mass (s : Segment) (a b : ℚ)
    (ha : 0 ≤ a) (hb : 0 ≤ b) (dx dy : ℝ) :
    segmentMeasure { s with mass := a + b } dx dy =
      segmentMeasure { s with mass := a } dx dy +
      segmentMeasure { s with mass := b } dx dy := by
  simp only [segmentMeasure, Rat.cast_add]
  rw [ENNReal.ofReal_add (by exact_mod_cast ha) (by exact_mod_cast hb), add_smul]

/-- The canonical unoriented support represents the same probability measure,
including when both endpoints coincide. -/
theorem segmentMeasure_support (s : Segment) (dx dy : ℝ) :
    segmentMeasure
      ⟨s.support.1.1, s.support.1.2, s.support.2.1, s.support.2.2, s.mass⟩ dx dy =
      segmentMeasure s dx dy := by
  unfold Segment.support
  split
  · rfl
  · exact segmentMeasure_reverse s dx dy

/-- Coincident unoriented supports add with their nonnegative total masses. -/
theorem segmentMeasure_add_same_support (s t : Segment)
    (h : s.support = t.support) (hs : 0 ≤ s.mass) (ht : 0 ≤ t.mass)
    (dx dy : ℝ) :
    segmentMeasure { s with mass := s.mass + t.mass } dx dy =
      segmentMeasure s dx dy + segmentMeasure t dx dy := by
  rw [segmentMeasure_add_mass s s.mass t.mass hs ht]
  congr 1
  rw [← segmentMeasure_support { s with mass := t.mass },
    ← segmentMeasure_support t]
  have he : ({ s with mass := t.mass } : Segment).support = s.support := rfl
  simp only [he, h]

theorem rowsMeasure_append (xs ys : List Segment) (dx dy : ℝ) :
    rowsMeasure (xs ++ ys) dx dy = rowsMeasure xs dx dy + rowsMeasure ys dx dy := by
  simp [rowsMeasure, List.sum_append]

theorem rowsMeasure_perm {xs ys : List Segment} (h : xs.Perm ys) (dx dy : ℝ) :
    rowsMeasure xs dx dy = rowsMeasure ys dx dy := by
  exact (h.map (fun s => segmentMeasure s dx dy)).sum_eq

#print axioms segmentMeasure_reverse
#print axioms segmentMeasure_add_mass
#print axioms segmentMeasure_support
#print axioms segmentMeasure_add_same_support
#print axioms rowsMeasure_append
#print axioms rowsMeasure_perm

lemma scaled_unit_interval (a b : ℝ) (h : a < b) :
    ENNReal.ofReal (b-a) • (volume.restrict (Set.Icc (0:ℝ) 1)).map
      (fun x => a + (b-a)*x) = volume.restrict (Set.Icc a b) := by
  have hp : 0 < b-a := sub_pos.mpr h
  have hm : Measurable (fun x : ℝ => a + (b-a)*x) := by fun_prop
  have he : (fun x : ℝ => a + (b-a)*x) ⁻¹' Set.Icc a b = Set.Icc 0 1 := by
    ext x
    simp only [Set.mem_preimage, Set.mem_Icc]
    constructor
    · intro hx
      constructor <;> nlinarith [hx.1, hx.2]
    · intro hx
      constructor <;> nlinarith [hx.1, hx.2]
  have hv : ENNReal.ofReal (b-a) • volume.map (fun x : ℝ => a + (b-a)*x) = volume := by
    have hc : (fun x : ℝ => a + (b-a)*x) = (fun y => a+y) ∘ (fun x => (b-a)*x) := rfl
    rw [hc, ← Measure.map_map (by fun_prop) (by fun_prop), ← Measure.map_smul]
    rw [show ENNReal.ofReal (b-a) • volume.map (fun x => (b-a)*x) = volume by
      simpa only [abs_of_pos hp] using Real.smul_map_volume_mul_left (ne_of_gt hp)]
    exact map_add_left_eq_self volume a
  rw [← he, ← Measure.restrict_map hm measurableSet_Icc, ← Measure.restrict_smul, hv]

lemma segMeasure_split (a b : Point) (t : ℝ) (ht : 0 ≤ t) (ht' : t ≤ 1) :
    SquarePacking.segMeasure a b =
      ENNReal.ofReal t • SquarePacking.segMeasure a (SquarePacking.segPt a b t) +
      ENNReal.ofReal (1-t) • SquarePacking.segMeasure (SquarePacking.segPt a b t) b := by
  rcases eq_or_lt_of_le ht with rfl | ht
  · simp [SquarePacking.segPt]
  rcases eq_or_lt_of_le ht' with he | ht'
  · subst t
    simp [SquarePacking.segPt]
  have hpart : volume.restrict (Set.Icc (0:ℝ) 1) =
      volume.restrict (Set.Icc 0 t) + volume.restrict (Set.Icc t 1) := by
    simp_rw [← restrict_Ioc_eq_restrict_Icc]
    rw [← Measure.restrict_union (Set.Ioc_disjoint_Ioc_of_le le_rfl) measurableSet_Ioc,
      Set.Ioc_union_Ioc_eq_Ioc ht.le ht'.le]
  have hleft : SquarePacking.segPt a (SquarePacking.segPt a b t) =
      SquarePacking.segPt a b ∘ (fun x => 0 + (t-0)*x) := by
    funext x; ext <;> simp [SquarePacking.segPt] <;> ring
  have hright : SquarePacking.segPt (SquarePacking.segPt a b t) b =
      SquarePacking.segPt a b ∘ (fun x => t + (1-t)*x) := by
    funext x; ext <;> simp [SquarePacking.segPt] <;> ring
  have hl := congrArg (fun μ : Measure ℝ => μ.map (SquarePacking.segPt a b))
    (scaled_unit_interval 0 t ht)
  have hr := congrArg (fun μ : Measure ℝ => μ.map (SquarePacking.segPt a b))
    (scaled_unit_interval t 1 ht')
  rw [Measure.map_smul, Measure.map_map (SquarePacking.measurable_segPt a b) (by fun_prop),
    ← hleft] at hl
  rw [Measure.map_smul, Measure.map_map (SquarePacking.measurable_segPt a b) (by fun_prop),
    ← hright] at hr
  simp only [sub_zero] at hl
  rw [SquarePacking.segMeasure, hpart,
    Measure.map_add _ _ (SquarePacking.measurable_segPt a b), ← hl, ← hr]
  rfl

#print axioms segMeasure_split
theorem segmentMeasure_ne_top (s : Segment) (dx dy : ℝ) (A : Set Point) :
    segmentMeasure s dx dy A ≠ ⊤ := by
  exact ENNReal.mul_ne_top ENNReal.ofReal_ne_top (SquarePacking.segMeasure_ne_top _ _ A)

theorem rowsMeasure_ne_top (xs : List Segment) (dx dy : ℝ) (A : Set Point) :
    rowsMeasure xs dx dy A ≠ ⊤ := by
  induction xs with
  | nil => simp [rowsMeasure]
  | cons s xs ih =>
    change (segmentMeasure s dx dy + rowsMeasure xs dx dy) A ≠ ⊤
    rw [Measure.add_apply]
    exact ENNReal.add_ne_top.mpr ⟨segmentMeasure_ne_top s dx dy A, ih⟩

theorem rowsMeasure_toReal (xs : List Segment) (dx dy : ℝ) (A : Set Point) :
    (rowsMeasure xs dx dy A).toReal =
      (xs.map fun s => (segmentMeasure s dx dy A).toReal).sum := by
  induction xs with
  | nil => simp [rowsMeasure]
  | cons s xs ih =>
    change ((segmentMeasure s dx dy + rowsMeasure xs dx dy) A).toReal = _
    rw [Measure.add_apply, ENNReal.toReal_add (segmentMeasure_ne_top s dx dy A)
      (rowsMeasure_ne_top xs dx dy A), ih]
    rfl

/-- Valid point rows disappear before encoding nondegenerate integer rows. -/
theorem segmentMeasure_valid_point (s : Segment) (hv : s.Valid)
    (hx : s.ax = s.bx) (hy : s.ay = s.yb) (dx dy : ℝ) :
    segmentMeasure s dx dy = 0 := by
  simp [segmentMeasure, hv.2.2 ⟨hx, hy⟩]

/-- Zero-mass point rows can be discarded before a nondegenerate integer encoding. -/
theorem rowsMeasure_remove_points (xs : List Segment) (hx : ∀ s ∈ xs, s.Valid)
    (dx dy : ℝ) :
    rowsMeasure (xs.filter fun s => !(s.ax == s.bx && s.ay == s.yb)) dx dy =
      rowsMeasure xs dx dy := by
  induction xs with
  | nil => rfl
  | cons s xs ih =>
    have ht := ih (fun t ht => hx t (by simp [ht]))
    by_cases hp : s.ax = s.bx ∧ s.ay = s.yb
    · have hz := segmentMeasure_valid_point s (hx s (by simp)) hp.1 hp.2 dx dy
      simpa [hp.1, hp.2, rowsMeasure, hz] using ht
    · have hb : (s.ax == s.bx && s.ay == s.yb) = false := by
        simpa using hp
      simp only [List.filter_cons, hb, Bool.not_false, ↓reduceIte]
      change segmentMeasure s dx dy + rowsMeasure _ dx dy =
        segmentMeasure s dx dy + rowsMeasure xs dx dy
      rw [ht]

lemma interval_indicator_integrable {s : Set ℝ} (hs : MeasurableSet s) (a b : ℝ) :
    IntervalIntegrable (s.indicator (fun _ => (1:ℝ))) volume a b := by
  exact ⟨((intervalIntegrable_const : IntervalIntegrable (fun _ => (1:ℝ)) volume a b).1).indicator hs,
    ((intervalIntegrable_const : IntervalIntegrable (fun _ => (1:ℝ)) volume a b).2).indicator hs⟩

lemma interval_volume_primitive {s : Set ℝ} (hs : MeasurableSet s)
    (a b : ℝ) (hab : a ≤ b) :
    (volume (s ∩ Set.Icc a b)).toReal =
      (∫ x in (0:ℝ)..b, s.indicator (fun _ => (1:ℝ)) x) -
      (∫ x in (0:ℝ)..a, s.indicator (fun _ => (1:ℝ)) x) := by
  rw [intervalIntegral.integral_interval_sub_left
    (interval_indicator_integrable hs 0 b) (interval_indicator_integrable hs 0 a),
    intervalIntegral.integral_of_le hab, integral_indicator hs,
    Measure.restrict_restrict hs, setIntegral_const]
  simp only [smul_eq_mul, mul_one]
  congr 1
  exact measure_congr (Filter.EventuallyEq.inter Filter.EventuallyEq.rfl Ioc_ae_eq_Icc).symm

lemma segMeasure_line (g : ℝ → Point) (hg : Measurable g)
    (haff : ∀ u v t, SquarePacking.segPt (g u) (g v) t = g (u + (v-u)*t))
    (a b : ℝ) (hab : a < b) :
    ENNReal.ofReal (b-a) • SquarePacking.segMeasure (g a) (g b) =
      (volume.restrict (Set.Icc a b)).map g := by
  have h := congrArg (fun μ : Measure ℝ => μ.map g) (scaled_unit_interval a b hab)
  rw [Measure.map_smul, Measure.map_map hg (by fun_prop)] at h
  convert h using 2
  unfold SquarePacking.segMeasure
  congr 1
  funext t
  exact haff a b t

lemma segMeasure_density_apply (g : ℝ → Point) (hg : Measurable g)
    (haff : ∀ u v t, SquarePacking.segPt (g u) (g v) t = g (u + (v-u)*t))
    (a b ρ : ℝ) (hab : a < b) (hρ : 0 ≤ ρ)
    {s : Set Point} (hs : MeasurableSet s) :
    ((ENNReal.ofReal (ρ*(b-a)) • SquarePacking.segMeasure (g a) (g b)) s).toReal =
      ρ * ((∫ x in (0:ℝ)..b, (g ⁻¹' s).indicator (fun _ => (1:ℝ)) x) -
        (∫ x in (0:ℝ)..a, (g ⁻¹' s).indicator (fun _ => (1:ℝ)) x)) := by
  rw [ENNReal.ofReal_mul hρ, ← smul_smul, segMeasure_line g hg haff a b hab,
    Measure.smul_apply, smul_eq_mul, ENNReal.toReal_mul, ENNReal.toReal_ofReal hρ,
    Measure.map_apply hg hs, Measure.restrict_apply (hg hs),
    interval_volume_primitive (hg hs) a b hab.le]

#print axioms segMeasure_density_apply
#print axioms rowsMeasure_remove_points
#print axioms segmentMeasure_valid_point
end ClosedForm
