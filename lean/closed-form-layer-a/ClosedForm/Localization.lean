import ClosedForm.WallPlacement
import ClosedForm.Orientation

open MeasureTheory
namespace ClosedForm

def rectangle (x0 x1 y0 y1 : ℝ) : Set Point := Set.Icc x0 x1 ×ˢ Set.Icc y0 y1

lemma segMeasure_restrict_rectangle (p q : Point) (x0 x1 y0 y1 : ℝ)
    (hp : p ∈ rectangle x0 x1 y0 y1) (hq : q ∈ rectangle x0 x1 y0 y1) :
    (SquarePacking.segMeasure p q).restrict (rectangle x0 x1 y0 y1) =
      SquarePacking.segMeasure p q := by
  apply segMeasure_restrict_of_interior _ _ _ (measurableSet_Icc.prod measurableSet_Icc)
  intro t ht
  change (x0 ≤ p.1 + t * (q.1 - p.1) ∧ p.1 + t * (q.1 - p.1) ≤ x1) ∧
    (y0 ≤ p.2 + t * (q.2 - p.2) ∧ p.2 + t * (q.2 - p.2) ≤ y1)
  obtain ⟨⟨hp0, hp1⟩, hp2, hp3⟩ := hp
  obtain ⟨⟨hq0, hq1⟩, hq2, hq3⟩ := hq
  constructor <;> constructor <;> nlinarith [ht.1, ht.2]

lemma rowsMeasure_restrict_rectangle (ss : List Segment) (dx dy x0 x1 y0 y1 : ℝ)
    (h : ∀ s ∈ ss,
      ((s.ax : ℝ) + dx, (s.ay : ℝ) + dy) ∈ rectangle x0 x1 y0 y1 ∧
      ((s.bx : ℝ) + dx, (s.yb : ℝ) + dy) ∈ rectangle x0 x1 y0 y1) :
    (rowsMeasure ss dx dy).restrict (rectangle x0 x1 y0 y1) = rowsMeasure ss dx dy := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    change (segmentMeasure s dx dy + rowsMeasure ss dx dy).restrict _ = _
    rw [Measure.restrict_add, ih (fun t ht => h t (by simp [ht]))]
    congr 1
    rw [segmentMeasure, Measure.restrict_smul,
      segMeasure_restrict_rectangle _ _ _ _ _ _ (h s (by simp)).1 (h s (by simp)).2]
    rfl

lemma endpoints_in_rectangle (s : Segment) (dx dy x0 x1 y0 y1 : ℝ)
    (hx0 : x0 ≤ (min s.ax s.bx : ℚ) + dx)
    (hx1 : (max s.ax s.bx : ℚ) + dx ≤ x1)
    (hy0 : y0 ≤ (min s.ay s.yb : ℚ) + dy)
    (hy1 : (max s.ay s.yb : ℚ) + dy ≤ y1) :
    ((s.ax : ℝ) + dx, (s.ay : ℝ) + dy) ∈ rectangle x0 x1 y0 y1 ∧
      ((s.bx : ℝ) + dx, (s.yb : ℝ) + dy) ∈ rectangle x0 x1 y0 y1 := by
  have h1 : (min s.ax s.bx : ℚ) ≤ (s.ax : ℝ) := by exact_mod_cast min_le_left s.ax s.bx
  have h2 : (min s.ax s.bx : ℚ) ≤ (s.bx : ℝ) := by exact_mod_cast min_le_right s.ax s.bx
  have h3 : (s.ax : ℝ) ≤ (max s.ax s.bx : ℚ) := by exact_mod_cast le_max_left s.ax s.bx
  have h4 : (s.bx : ℝ) ≤ (max s.ax s.bx : ℚ) := by exact_mod_cast le_max_right s.ax s.bx
  have h5 : (min s.ay s.yb : ℚ) ≤ (s.ay : ℝ) := by exact_mod_cast min_le_left s.ay s.yb
  have h6 : (min s.ay s.yb : ℚ) ≤ (s.yb : ℝ) := by exact_mod_cast min_le_right s.ay s.yb
  have h7 : (s.ay : ℝ) ≤ (max s.ay s.yb : ℚ) := by exact_mod_cast le_max_left s.ay s.yb
  have h8 : (s.yb : ℝ) ≤ (max s.ay s.yb : ℚ) := by exact_mod_cast le_max_right s.ay s.yb
  exact ⟨⟨⟨by linarith, by linarith⟩, by linarith, by linarith⟩,
    ⟨⟨by linarith, by linarith⟩, by linarith, by linarith⟩⟩

lemma corner_restrict_rectangle (f fr : Family) (hs : Structural f fr)
    (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) :
    (cornerMeasure f δ).restrict (rectangle 0 (2 + δ) 0 2) = cornerMeasure f δ := by
  rcases hs with ⟨hv, _, _, _, hd0, _, _, _, _, _, _, _, _, _, _, hcf, hct, hvb, _⟩
  have hd0' : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hd0
  have hδ0 := hd0'.trans hδ.1
  have hF : (rowsMeasure (cornerF f) 0 0).restrict (rectangle 0 (2 + δ) 0 2) =
      rowsMeasure (cornerF f) 0 0 := by
    apply rowsMeasure_restrict_rectangle
    intro s hsp
    obtain ⟨hx0, hx1, hy0, hy1⟩ := hcf s hsp
    apply endpoints_in_rectangle
    · simp only [add_zero]; exact_mod_cast hx0
    · have h : ((max s.ax s.bx : ℚ) : ℝ) ≤ 2 + (f.d0 : ℝ) := by exact_mod_cast hx1
      linarith [hδ.1]
    · simp only [add_zero]; exact_mod_cast hy0
    · simp only [add_zero]; exact_mod_cast hy1
  have hT : (rowsMeasure (cornerT f) δ 0).restrict (rectangle 0 (2 + δ) 0 2) =
      rowsMeasure (cornerT f) δ 0 := by
    apply rowsMeasure_restrict_rectangle
    intro s hsp
    obtain ⟨hax, hbx, hy0, hy1⟩ := hct s hsp
    apply endpoints_in_rectangle
    · simp only [hax, hbx, min_self, Rat.cast_ofNat]; linarith
    · simp [hax, hbx]
    · simp only [add_zero]; exact_mod_cast hy0
    · simp only [add_zero]; exact_mod_cast hy1
  have hV (v : VariableSegment) (hvp : v ∈ f.V) :
      (variableMeasure v δ).restrict (rectangle 0 (2 + δ) 0 2) = variableMeasure v δ := by
    obtain ⟨hx, hy0, hy1⟩ := hvb v hvp
    have hx0 : (0 : ℝ) ≤ v.xl := by exact_mod_cast hx
    have hx1 : (v.xl : ℝ) ≤ 2 + (f.d0 : ℝ) := by exact_mod_cast (hv.2.2 v hvp).2
    have hy0' : (0 : ℝ) ≤ v.y := by exact_mod_cast hy0
    have hy1' : (v.y : ℝ) ≤ 2 := by exact_mod_cast hy1
    rw [variableMeasure, Measure.restrict_smul, segMeasure_restrict_rectangle]
    · exact ⟨⟨hx0, by linarith [hδ.1]⟩, hy0', hy1'⟩
    · exact ⟨⟨by linarith, le_rfl⟩, hy0', hy1'⟩
  rw [cornerMeasure, Measure.restrict_add, Measure.restrict_add, hF, hT]
  congr 1
  change (Measure.restrictₗ _) _ = _
  rw [map_list_sum]
  simp only [List.map_map, Function.comp_def, Measure.restrictₗ_apply]
  rw [List.map_congr_left hV]

lemma measure_zero_of_supported (μ : Measure Point) (B A : Set Point)
    (hB : μ.restrict B = μ) (hA : MeasurableSet A) (hdis : Disjoint A B) : μ A = 0 := by
  conv_lhs => rw [← hB]
  rw [Measure.restrict_apply hA, Set.disjoint_iff_inter_eq_empty.mp hdis, measure_empty]

lemma wall_restrict_rectangle (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) :
    (wallMeasure f k δ).restrict (rectangle (2 + δ) ((k : ℝ) + δ - 2) 0 (9 / 5)) =
      wallMeasure f k δ := by
  have hpb := hs.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1
  have hn : ((k - 4 : ℕ) : ℝ) = (k : ℝ) - 4 := by
    rw [Nat.cast_sub (by omega : 4 ≤ k)]; norm_num
  have hrow (n : ℕ) (hn' : n < k - 4) :
      (rowsMeasure (profile f) (2 + δ + n) 0).restrict
        (rectangle (2 + δ) ((k : ℝ) + δ - 2) 0 (9 / 5)) =
          rowsMeasure (profile f) (2 + δ + n) 0 := by
    apply rowsMeasure_restrict_rectangle
    intro s hsp
    have hb := hpb s hsp
    have hx0 : (0 : ℝ) ≤ (min s.ax s.bx : ℚ) := by exact_mod_cast hb.1
    have hx1 : ((max s.ax s.bx : ℚ) : ℝ) ≤ 1 := by exact_mod_cast hb.2.1
    have hy0 : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hb.2.2.1
    have hy1 : ((max s.ay s.yb : ℚ) : ℝ) ≤ ((9 / 5 : ℚ) : ℝ) := by exact_mod_cast hb.2.2.2
    norm_num only [Rat.cast_div, Rat.cast_ofNat] at hy1
    have hn1 : (n : ℝ) + 1 ≤ ((k - 4 : ℕ) : ℝ) := by exact_mod_cast Nat.succ_le_of_lt hn'
    apply endpoints_in_rectangle <;> linarith [Nat.cast_nonneg (α := ℝ) n]
  have ht : (rowsMeasure (terminal f) (2 + δ + (k - 4 : ℕ)) 0).restrict
      (rectangle (2 + δ) ((k : ℝ) + δ - 2) 0 (9 / 5)) =
        rowsMeasure (terminal f) (2 + δ + (k - 4 : ℕ)) 0 := by
    apply rowsMeasure_restrict_rectangle
    intro s hsp
    have hb := hpb s (List.mem_filter.mp hsp).1
    have hz := (List.mem_filter.mp hsp).2
    simp only [Bool.and_eq_true, beq_iff_eq] at hz
    have hy0 : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hb.2.2.1
    have hy1 : ((max s.ay s.yb : ℚ) : ℝ) ≤ ((9 / 5 : ℚ) : ℝ) := by exact_mod_cast hb.2.2.2
    norm_num only [Rat.cast_div, Rat.cast_ofNat] at hy1
    have hk' : (7 : ℝ) ≤ k := by exact_mod_cast hk
    apply endpoints_in_rectangle <;> (try simp only [hz.1, hz.2, min_self, max_self, Rat.cast_zero])
    all_goals linarith
  rw [wallMeasure, Measure.restrict_add, ht]
  congr 1
  change (Measure.restrictₗ _) _ = _
  rw [map_list_sum]
  simp only [List.map_map, Function.comp_def, Measure.restrictₗ_apply]
  simp only [bind_pure_comp, List.map_eq_map, List.map_map, Function.comp_def]
  rw [List.map_congr_left (fun n hn => hrow n (List.mem_range.mp hn))]

/-- Window safely below the far corner and wall endpoints. It is deliberately
asymmetric: the bottom wall is offset by δ, the left wall has integer phases. -/
def localWindow (k : ℕ) (δ : ℝ) : Set Point :=
  {p | p.1 < (k : ℝ) + δ - 2 ∧ p.2 < (k : ℝ) - 2}

lemma far_corner_zero (f fr : Family) (hs : Structural f fr) (k : ℕ) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (j : ℕ) (hj0 : 0 < j) (hj4 : j < 4)
    (A : Set Point) (hA : MeasurableSet A) (hwin : A ⊆ localWindow k δ) :
    ((cornerMeasure f δ).map (rotateC4 ((k : ℝ) + δ))^[j]) A = 0 := by
  rw [Measure.map_apply ((rotateC4_measurable _).iterate _) hA]
  apply measure_zero_of_supported _ (rectangle 0 (2 + δ) 0 2) _
    (corner_restrict_rectangle f fr hs δ hδ) (((rotateC4_measurable _).iterate _) hA)
  apply Set.disjoint_left.mpr
  intro p hp hc
  have h := hwin hp
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hδ0 := hd0.trans hδ.1
  obtain ⟨⟨hx0, hx1⟩, hy0, hy1⟩ := hc
  interval_cases j <;>
    simp only [localWindow, Set.mem_ofPred_eq, Function.iterate_succ_apply,
      Function.iterate_zero_apply, rotateC4] at h <;> linarith [h.1, h.2]

lemma far_wall_zero (f fr : Family) (hs : Structural f fr) (k : ℕ) (hk : 7 ≤ k)
    (δ : ℝ) (hδ0 : 0 ≤ δ) (j : ℕ) (hj0 : 0 < j) (hj3 : j < 3)
    (A : Set Point) (hA : MeasurableSet A) (hwin : A ⊆ localWindow k δ) :
    ((wallMeasure f k δ).map (rotateC4 ((k : ℝ) + δ))^[j]) A = 0 := by
  rw [Measure.map_apply ((rotateC4_measurable _).iterate _) hA]
  apply measure_zero_of_supported _ (rectangle (2 + δ) ((k : ℝ) + δ - 2) 0 (9 / 5)) _
    (wall_restrict_rectangle f fr hs k hk δ) (((rotateC4_measurable _).iterate _) hA)
  apply Set.disjoint_left.mpr
  intro p hp hc
  have h := hwin hp
  obtain ⟨⟨hx0, hx1⟩, hy0, hy1⟩ := hc
  interval_cases j <;>
    simp only [localWindow, Set.mem_ofPred_eq, Function.iterate_succ_apply,
      Function.iterate_zero_apply, rotateC4] at h <;> linarith [h.1, h.2]

lemma bottom_wall_local (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (A : Set Point) (hA : MeasurableSet A)
    (hwin : A ⊆ localWindow k δ) :
    wallMeasure f k δ A =
      (Measure.sum fun n : ℕ => rowsMeasure (profile f) (2 + δ + n) 0) A := by
  have hn : ((k - 4 : ℕ) : ℝ) = (k : ℝ) - 4 := by
    rw [Nat.cast_sub (by omega : 4 ≤ k)]; norm_num
  have htr : Measurable (fun p : Point => (2 + δ + p.1, p.2)) := by fun_prop
  rw [wallMeasure_eq_map_finiteWall, Measure.map_apply htr hA,
    finiteWall_window f fr hs _ _ (htr hA) (by
      intro p hp
      have h := (hwin hp).1
      change 2 + δ + p.1 < (k : ℝ) + δ - 2 at h
      rw [hn]; linarith), Measure.sum_apply _ (htr hA), Measure.sum_apply _ hA]
  apply tsum_congr
  intro n
  have hr := rowsMeasure_translate (profile f) (n : ℝ) 0 (2 + δ) 0
  simp only [zero_add] at hr
  rw [← hr, Measure.map_apply htr hA]

lemma left_wall_local (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (A : Set Point) (hA : MeasurableSet A)
    (hwin : A ⊆ localWindow k δ) :
    ((wallMeasure f k δ).map (rotateC4 ((k : ℝ) + δ))^[3]) A =
      (Measure.sum fun n : ℕ =>
        (rowsMeasure (profile f) (2 + n) 0).map Prod.swap) A := by
  have hn : ((k - 4 : ℕ) : ℝ) = (k : ℝ) - 4 := by
    rw [Nat.cast_sub (by omega : 4 ≤ k)]; norm_num
  have htr : Measurable (fun p : Point => (p.2, 2 + p.1)) := by fun_prop
  rw [left_wall_placement f fr hs k hk δ, Measure.map_apply htr hA,
    finiteWall_window f fr hs _ _ (htr hA) (by
      intro p hp
      have h := (hwin hp).2
      change 2 + p.1 < (k : ℝ) - 2 at h
      rw [hn]; linarith), Measure.sum_apply _ (htr hA), Measure.sum_apply _ hA]
  apply tsum_congr
  intro n
  have hr := rowsMeasure_translate (profile f) (n : ℝ) 0 2 0
  simp only [zero_add] at hr
  rw [← hr, Measure.map_map measurable_swap (by fun_prop),
    Measure.map_apply (measurable_swap.comp (by fun_prop)) hA]
  rfl

/-- Closed-set localization, including singular boundary mass. The window is
bounded before the far endpoints, and the finite left wall uses its proved reversal. -/
theorem global_local_window (f fr : Family) (hs : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ)
    (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ))
    (A : Set Point) (hA : MeasurableSet A) (hwin : A ⊆ localWindow k δ) :
    globalMeasure f k δ A = periodicLocalMeasure f δ A := by
  have hd0 : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hs.2.2.2.2.1
  have hδ0 := hd0.trans hδ.1
  have harea : volume.restrict (globalArea k δ) A = volume.restrict (localArea f) A := by
    rw [Measure.restrict_apply hA, Measure.restrict_apply hA]
    congr 1
    ext p
    simp only [Set.mem_inter_iff, globalArea, localArea, hs.2.2.2.1,
      hs.2.2.1, Set.mem_prod, Set.mem_Icc, Set.mem_Ici, Rat.cast_div, Rat.cast_ofNat]
    constructor
    · rintro ⟨hAp, ⟨hx0, hx1⟩, hy0, hy1⟩
      exact ⟨hAp, hx0, hy0⟩
    · rintro ⟨hAp, hx0, hy0⟩
      have h := hwin hAp
      exact ⟨hAp, ⟨hx0, by linarith [h.1]⟩, hy0, by linarith [h.2]⟩
  have hc1 := far_corner_zero f fr hs k δ hδ 1 (by decide) (by decide) A hA hwin
  have hc2 := far_corner_zero f fr hs k δ hδ 2 (by decide) (by decide) A hA hwin
  have hc3 := far_corner_zero f fr hs k δ hδ 3 (by decide) (by decide) A hA hwin
  have hw1 := far_wall_zero f fr hs k hk δ hδ0 1 (by decide) (by decide) A hA hwin
  have hw2 := far_wall_zero f fr hs k hk δ hδ0 2 (by decide) (by decide) A hA hwin
  have hw0 := bottom_wall_local f fr hs k hk δ A hA hwin
  have hw3 := left_wall_local f fr hs k hk δ A hA hwin
  have hmap (j : ℕ) :
      ((cornerMeasure f δ + wallMeasure f k δ).map (rotateC4 ((k : ℝ) + δ))^[j]) A =
        ((cornerMeasure f δ).map (rotateC4 ((k : ℝ) + δ))^[j]) A +
        ((wallMeasure f k δ).map (rotateC4 ((k : ℝ) + δ))^[j]) A := by
    rw [Measure.map_add _ _ ((rotateC4_measurable _).iterate j), Measure.add_apply]
  simp only [globalMeasure, List.range_succ, List.range_zero, List.map_append,
    List.map_cons, List.map_nil, List.sum_append, List.sum_cons, List.sum_nil,
    Measure.add_apply, hmap, Function.iterate_zero, Measure.map_id,
    hc1, hc2, hc3, hw1, hw2, hw0, hw3, harea, add_zero, zero_add]
  simp only [periodicLocalMeasure, Measure.add_apply]
  rfl

end ClosedForm
