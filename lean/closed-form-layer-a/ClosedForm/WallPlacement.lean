import ClosedForm.WallSeam

open MeasureTheory
namespace ClosedForm

noncomputable def finiteWall (f : Family) (m : ℕ) : Measure Point :=
  ((List.range m).map fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0).sum +
    rowsMeasure (terminal f) (m : ℝ) 0

lemma map_list_measures (ms : List (Measure Point)) (g : Point → Point) (hg : Measurable g) :
    ms.sum.map g = (ms.map fun μ => μ.map g).sum := by
  induction ms with
  | nil => simp
  | cons μ ms ih => simp only [List.sum_cons, List.map_cons, Measure.map_add _ _ hg, ih]

lemma finiteWall_translate (f : Family) (m : ℕ) (d : ℝ) :
    (finiteWall f m).map (fun p : Point => (d + p.1, p.2)) =
      ((List.range m).map fun n : ℕ => rowsMeasure (profile f) (d + n) 0).sum +
        rowsMeasure (terminal f) (d + m) 0 := by
  have ht (ss : List Segment) (x : ℝ) :
      (rowsMeasure ss x 0).map (fun p : Point => (d + p.1, p.2)) = rowsMeasure ss (d + x) 0 := by
    simpa only [zero_add] using rowsMeasure_translate ss x 0 d 0
  rw [finiteWall, Measure.map_add _ _ (by fun_prop), map_list_measures _ _ (by fun_prop), ht]
  simp only [List.map_map, Function.comp_def, ht]

lemma wallMeasure_eq_map_finiteWall (f : Family) (k : ℕ) (δ : ℝ) :
    wallMeasure f k δ = (finiteWall f (k - 4)).map (fun p : Point => (2 + δ + p.1, p.2)) := by
  rw [finiteWall_translate]
  simp only [wallMeasure, bind_pure_comp, List.map_eq_map, List.map_map, Function.comp_def]

/-- The upper-left wall rotates to the local transpose. Reversal is proved for
its finite closed strip, including the terminal line at both ends. -/
theorem left_wall_placement (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) :
    (wallMeasure f k δ).map (rotateC4 ((k : ℝ) + δ))^[3] =
      (finiteWall f (k - 4)).map (fun p : Point => (p.2, 2 + p.1)) := by
  have hm : 1 ≤ k - 4 := by omega
  have hn : ((k - 4 : ℕ) : ℝ) = (k : ℝ) - 4 := by
    rw [Nat.cast_sub (by omega : 4 ≤ k)]; norm_num
  have hr := finite_wall_reflection f fr hs (k - 4) hm
  change (finiteWall f (k - 4)).map (fun p : Point => (((k - 4 : ℕ) : ℝ) - p.1, p.2)) =
    finiteWall f (k - 4) at hr
  rw [wallMeasure_eq_map_finiteWall, Measure.map_map ((rotateC4_measurable _).iterate 3) (by fun_prop)]
  have he : (rotateC4 ((k : ℝ) + δ))^[3] ∘ (fun p : Point => (2 + δ + p.1, p.2)) =
      (fun p : Point => (p.2, 2 + p.1)) ∘
        (fun p : Point => (((k - 4 : ℕ) : ℝ) - p.1, p.2)) := by
    funext p
    ext <;> simp [Function.comp_def, rotateC4, hn]
    all_goals ring
  rw [he, ← Measure.map_map (by fun_prop) (by fun_prop), hr]

lemma rowsMeasure_zero_below (ss : List Segment) (dx dy b : ℝ)
    (h : ∀ s ∈ ss, b ≤ (s.ax : ℝ) + dx ∧ b ≤ (s.bx : ℝ) + dx)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, p.1 < b) :
    rowsMeasure ss dx dy A = 0 := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    change (segmentMeasure s dx dy + rowsMeasure ss dx dy) A = 0
    rw [Measure.add_apply, ih (fun t ht => h t (by simp [ht])), add_zero]
    rw [segmentMeasure, Measure.smul_apply, smul_eq_mul,
      segMeasure_eq_zero_of_disjoint _ _ A hA, mul_zero]
    intro t ht hp
    have hp' := hAb _ hp
    have hh := h s (by simp)
    change (s.ax : ℝ) + dx + t * ((s.bx : ℝ) + dx - ((s.ax : ℝ) + dx)) < b at hp'
    nlinarith [mul_nonneg (sub_nonneg.mpr ht.2) (sub_nonneg.mpr hh.1),
      mul_nonneg ht.1 (sub_nonneg.mpr hh.2)]

/-- Below the terminal line a finite wall equals its one-sided extension. -/
theorem finiteWall_window (f fr : Family) (hs : Structural f fr) (m : ℕ)
    (A : Set Point) (hA : MeasurableSet A) (hAb : ∀ p ∈ A, p.1 < m) :
    finiteWall f m A = (Measure.sum fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0) A := by
  have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1
  have hlow (s : Segment) (hsp : s ∈ profile f) : (0 : ℝ) ≤ s.ax ∧ (0 : ℝ) ≤ s.bx := by
    constructor
    · exact_mod_cast (hpb s hsp).1.trans (min_le_left _ _)
    · exact_mod_cast (hpb s hsp).1.trans (min_le_right _ _)
  have hterm : rowsMeasure (terminal f) (m : ℝ) 0 A = 0 := by
    apply rowsMeasure_zero_below _ _ _ m _ A hA hAb
    intro s hsp
    have h := hlow s (List.mem_filter.mp hsp).1
    constructor <;> linarith [h.1, h.2]
  rw [finiteWall, Measure.add_apply, hterm, add_zero, sum_measures_apply,
    List.map_map, Measure.sum_apply _ hA]
  simp only [Function.comp_def]
  rw [tsum_eq_sum (s := Finset.range m) (fun n hn => ?_)]
  · simpa only [List.toFinset_range] using (List.sum_toFinset (fun n : ℕ => rowsMeasure (profile f) (n : ℝ) 0 A)
      List.nodup_range).symm
  · have hnR : (m : ℝ) ≤ n := by exact_mod_cast (show m ≤ n by simpa using hn)
    apply rowsMeasure_zero_below _ _ _ m _ A hA hAb
    intro s hsp
    have h := hlow s hsp
    constructor <;> linarith [h.1, h.2]

end ClosedForm
