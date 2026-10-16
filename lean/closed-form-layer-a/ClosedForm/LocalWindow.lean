import ClosedForm.Mass
import ClosedForm.ReflectionBridge

open MeasureTheory
open scoped ENNReal
namespace ClosedForm

lemma halfWidth_le_one (u : ℝ) : halfWidth u ≤ 1 := by
  have hd : 0 < 1 + u ^ 2 := by positivity
  have hc : poseCos u ≤ 1 := by
    unfold poseCos
    apply (div_le_iff₀ hd).2
    nlinarith [sq_nonneg u]
  have hs : |poseSin u| ≤ 1 := by
    rw [poseSin, abs_div, abs_of_pos hd]
    apply (div_le_iff₀ hd).2
    rw [abs_le]
    constructor <;> nlinarith [sq_nonneg (u - 1), sq_nonneg (u + 1)]
  unfold halfWidth
  linarith

/-- The record's side-20 cuts are inactive in all four windows. Right-window
coordinates here are already shifted, exactly as in `regionSet`. -/
theorem record_upper_inactive_of_d1 (f : Family) (hd1 : f.d1 ≤ 1)
    (r : Region) (z : Point) (hz : z ∈ regionSet f r) (u : ℝ) :
    z.1 ≤ 20 - halfWidth u ∧ z.2 ≤ 20 - halfWidth u := by
  have hd1' : (f.d1 : ℝ) ≤ 1 := by exact_mod_cast hd1
  have hw := halfWidth_le_one u
  cases r <;>
    change (_ ∧ _) ∧ (_ ∧ _) at hz <;>
    constructor <;> linarith [hz.1.2, hz.2.2]

/-- First use of k ≥ 7 in SPEC §2.3: opposite corners and endpoints lie
strictly beyond the lower-left quarter enlarged by r = 0.7072. -/
lemma quarter_clearance (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (hδ : δ ≤ 1) :
    (k : ℝ) + δ > 2 * (2 + δ) + 2 * (7072 / 10000 : ℝ) := by
  have hk' : (7 : ℝ) ≤ k := by exact_mod_cast hk
  linarith

/-- Second use of k ≥ 7: three complete wall periods are available. -/
lemma three_periods (k : ℕ) (hk : 7 ≤ k) : 3 ≤ k - 4 := by omega

/-- Third use of k ≥ 7: the quarter window misses both the far wall endpoint
and the upper cut of the area square, throughout the whole δ interval. -/
lemma quarter_window_clearance (k : ℕ) (hk : 7 ≤ k) (δ : ℝ)
    (hδ0 : 0 ≤ δ) (hδ : δ ≤ 1) :
    ((k : ℝ) + δ) / 2 + 7072 / 10000 < (k : ℝ) + δ - (2 + δ) ∧
    ((k : ℝ) + δ) / 2 + 7072 / 10000 < (k : ℝ) + δ - 9 / 5 := by
  have h := quarter_clearance k hk δ hδ
  have hk' : (7 : ℝ) ≤ k := by exact_mod_cast hk
  constructor <;> linarith

lemma rowsMeasure_shift (ss : List Segment) (x y : ℚ) (dx dy : ℝ) :
    rowsMeasure (ss.map fun s => s.shift x y) dx dy =
      rowsMeasure ss ((x : ℝ) + dx) ((y : ℝ) + dy) := by
  unfold rowsMeasure
  simp only [List.map_map, Function.comp_def]
  congr 1
  apply List.map_congr_left
  intro s _
  simp [segmentMeasure, Segment.shift, Rat.cast_add, add_assoc]

lemma rowsMeasure_transpose (ss : List Segment) (dx dy : ℝ) :
    rowsMeasure (ss.map Segment.transpose) dx dy =
      (rowsMeasure ss dy dx).map Prod.swap := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    simp only [rowsMeasure, List.map_cons, List.sum_cons] at ih ⊢
    rw [Measure.map_add _ _ measurable_swap, ← ih]
    congr 1
    simp only [segmentMeasure]
    rw [Measure.map_smul,
      map_segMeasure_affine Prod.swap measurable_swap (by intros; rfl)]
    rfl

lemma rowsMeasure_periods (f : Family) (n : ℕ) (dx dy : ℝ) :
    rowsMeasure (periods f n) dx dy =
      ((List.range n).map fun j : ℕ => rowsMeasure (profile f) (2 + dx + j) dy).sum := by
  unfold periods rowsMeasure
  have hflat (xs : List ℕ) :
      (xs.flatMap fun j => ((profile f).map fun s => segmentMeasure (s.shift (2 + j) 0) dx dy)).sum =
        (xs.map fun j => rowsMeasure ((profile f).map fun s => s.shift (2 + j) 0) dx dy).sum := by
    induction xs with
    | nil => simp [rowsMeasure]
    | cons j xs ih => simp [List.flatMap_cons, List.sum_append, ih, rowsMeasure, List.map_map, Function.comp_def]
  simp only [List.map_flatMap, List.map_map, Function.comp_def]
  rw [hflat]
  apply congrArg List.sum
  apply List.map_congr_left
  intro j _
  rw [rowsMeasure_shift]
  simp only [Rat.cast_add, Rat.cast_ofNat, Rat.cast_natCast, Rat.cast_zero, zero_add]
  congr 1; ring

lemma segMeasure_eq_zero_of_disjoint (p q : Point) (A : Set Point) (hA : MeasurableSet A)
    (h : ∀ t ∈ Set.Icc (0 : ℝ) 1, SquarePacking.segPt p q t ∉ A) :
    SquarePacking.segMeasure p q A = 0 := by
  rw [SquarePacking.segMeasure_apply p q hA]
  have he : SquarePacking.segPt p q ⁻¹' A ∩ Set.Icc 0 1 = ∅ := by
    apply Set.eq_empty_iff_forall_notMem.mpr
    rintro t ⟨ht, hi⟩
    exact h t hi ht
  rw [he, measure_empty]

lemma rowsMeasure_eq_zero_of_left (ss : List Segment) (dx dy b : ℝ)
    (hs : ∀ s ∈ ss, b < (s.ax : ℝ) + dx ∧ b < (s.bx : ℝ) + dx)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, p.1 ≤ b) :
    rowsMeasure ss dx dy A = 0 := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    simp only [rowsMeasure, List.map_cons, List.sum_cons, Measure.add_apply]
    change segmentMeasure s dx dy A + rowsMeasure ss dx dy A = 0
    rw [ih (fun t ht => hs t (by simp [ht])), add_zero]
    rw [segmentMeasure, Measure.smul_apply, smul_eq_mul,
      segMeasure_eq_zero_of_disjoint _ _ A hA, mul_zero]
    intro t ht hp
    have hb := hAb _ hp
    have hh := hs s (by simp)
    change (s.ax : ℝ) + dx + t * ((s.bx : ℝ) + dx - ((s.ax : ℝ) + dx)) ≤ b at hb
    nlinarith [mul_nonneg (sub_nonneg.mpr ht.2) (sub_nonneg.mpr hh.1.le),
      mul_nonneg ht.1 (sub_nonneg.mpr hh.2.le)]

/-- Seven stored periods and the infinite wall agree below 24/5. The proof
uses zero segment mass outside the closed window, including all line masses. -/
lemma wall_window (f fr : Family) (hs : Structural f fr) (dx : ℝ) (hdx : 0 ≤ dx)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, p.1 ≤ 24 / 5) :
    rowsMeasure (periods f 7) dx 0 A =
      (Measure.sum fun n : ℕ => rowsMeasure (profile f) (2 + dx + n) 0) A := by
  rcases hs with ⟨_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, hp, _, _⟩
  rw [rowsMeasure_periods, sum_measures_apply, List.map_map, Measure.sum_apply _ hA]
  simp only [Function.comp_def]
  rw [tsum_eq_sum (s := Finset.range 7) (fun n hn => ?_)]
  · exact_mod_cast (List.sum_toFinset _ (List.nodup_range)).symm
  · have hn' : 7 ≤ n := by simpa using hn
    have hnR : (7 : ℝ) ≤ n := by exact_mod_cast hn'
    apply rowsMeasure_eq_zero_of_left _ _ _ (24 / 5) _ A hA hAb
    intro s hsp
    have hmin : (0 : ℝ) ≤ (min s.ax s.bx : ℚ) := by exact_mod_cast (hp s hsp).1
    have ha : (min s.ax s.bx : ℚ) ≤ (s.ax : ℝ) := by exact_mod_cast min_le_left s.ax s.bx
    have hb : (min s.ax s.bx : ℚ) ≤ (s.bx : ℝ) := by exact_mod_cast min_le_right s.ax s.bx
    constructor <;> linarith

theorem finite_periodic_window_structural (f fr : Family) (hs : Structural f fr)
    (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) :
    (localMeasure f δ).restrict (UnitSquarePacking.container (24 / 5)) =
      (periodicLocalMeasure f δ).restrict (UnitSquarePacking.container (24 / 5)) := by
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hδ0 : 0 ≤ δ := hd0.trans hδ.1
  have hdec := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 δ hδ
  ext A hA
  rw [Measure.restrict_apply hA, Measure.restrict_apply hA]
  let B := A ∩ UnitSquarePacking.container (24 / 5)
  have hB : MeasurableSet B := hA.inter (measurableSet_container _)
  have hx : ∀ p ∈ B, p.1 ≤ 24 / 5 := fun p hp => hp.2.1.2
  have hy : ∀ p ∈ B, p.2 ≤ 24 / 5 := fun p hp => hp.2.2.2
  have hbottom := wall_window f fr hs δ hδ0 B hB hx
  have hleft := wall_window f fr hs 0 (by norm_num) (Prod.swap ⁻¹' B)
    (measurable_swap hB) (fun p hp => hy _ hp)
  simp only [add_zero] at hleft
  change localMeasure f δ B = periodicLocalMeasure f δ B
  rw [localMeasure, periodicLocalMeasure, cornerMeasure, hdec.1, hdec.2,
    rowsMeasure_transpose]
  simp only [Measure.add_apply]
  rw [hbottom, Measure.map_apply measurable_swap hB, hleft,
    Measure.sum_apply _ hB, Measure.sum_apply _ (measurable_swap hB)]
  simp only [Measure.sum_apply _ hB,
    show (fun p : Point => (p.2, p.1)) = Prod.swap from rfl,
    Measure.map_apply measurable_swap hB]
  ac_rfl

end ClosedForm
