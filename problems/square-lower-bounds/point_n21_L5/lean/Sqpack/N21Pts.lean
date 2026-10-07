import Sqpack.MixedMeasure
import Sqpack.N21PtsData

/-!
# Point-only `s(21) = 5`, conditional on one computational cover statement

The raw candidate is encoded at coordinate scale 1000 and mass scale 10^12.
All data checks use kernel evaluation. The rational replay itself is external;
its precise interface is `N21PtsCheckerCover` (or the all-pose `N21PtsRegionCover`).
-/

open MeasureTheory Finset
open scoped ENNReal

namespace SquarePacking
namespace N21PtsData

def pentries : Finset (ℕ × ℕ × ℕ) := ptree.toList.toFinset
noncomputable def pt (e : ℕ × ℕ × ℕ) : ℝ × ℝ :=
  ((e.1 : ℝ) / 1000, (e.2.1 : ℝ) / 1000)
noncomputable def pw (e : ℕ × ℕ × ℕ) : ℝ := (e.2.2 : ℝ) / 1000000000000

/-- A point-only cover: both other index types are empty. -/
noncomputable def cover : MixedCover (ℕ × ℕ × ℕ) Empty Empty where
  pts := pentries
  pt := pt
  pw := pw
  segs := ∅
  sa := Empty.elim
  sb := Empty.elim
  sw := Empty.elim
  polys := ∅
  poly := Empty.elim
  gw := Empty.elim

noncomputable def μ : Measure (ℝ × ℝ) := cover.measure
noncomputable def total : ℝ := cover.total

def pX (e : ℕ × ℕ × ℕ) : ℕ × ℕ × ℕ := (5000 - e.1, e.2.1, e.2.2)
def pS (e : ℕ × ℕ × ℕ) : ℕ × ℕ × ℕ := (e.2.1, e.1, e.2.2)

def check : Bool := PTree.chainB ptree.toList &&
  ptree.all (fun e => Nat.ble e.1 5000 && ptree.mem (pX e) && ptree.mem (pS e))

theorem check_ok : check = true := by decide +kernel
theorem pwsum_tree : ptree.wsum = 20998900000168 := by decide +kernel

theorem check_parts : PTree.chainB ptree.toList = true ∧
    ptree.all (fun e => Nat.ble e.1 5000 && ptree.mem (pX e) && ptree.mem (pS e)) = true := by
  have h := check_ok
  simpa only [check, Bool.and_eq_true] using h

theorem pnodup : ptree.toList.Nodup := PTree.nodup_of_chainB _ check_parts.1

theorem card_pentries : pentries.card = 4604 := by
  have hl : ptree.toList.length = 4604 := by decide +kernel
  rw [pentries, List.toFinset_card_of_nodup pnodup, hl]

theorem pentry_ok (e : ℕ × ℕ × ℕ) (he : e ∈ pentries) :
    e.1 ≤ 5000 ∧ pX e ∈ pentries ∧ pS e ∈ pentries := by
  have h := (PTree.all_iff _ ptree).mp check_parts.2 e (List.mem_toFinset.mp he)
  simp only [Bool.and_eq_true, Nat.ble_eq] at h
  exact ⟨h.1.1, List.mem_toFinset.mpr (PTree.mem_sound _ _ h.1.2),
    List.mem_toFinset.mpr (PTree.mem_sound _ _ h.2)⟩

theorem pt_mem_box (e : ℕ × ℕ × ℕ) (he : e ∈ pentries) : pt e ∈ box 5 := by
  have hx := (pentry_ok e he).1
  have hy := (pentry_ok (pS e) (pentry_ok e he).2.2).1
  change e.2.1 ≤ 5000 at hy
  have hx' : (e.1 : ℝ) ≤ 5000 := by exact_mod_cast hx
  have hy' : (e.2.1 : ℝ) ≤ 5000 := by exact_mod_cast hy
  change 0 ≤ (e.1 : ℝ) / 1000 ∧ (e.1 : ℝ) / 1000 ≤ 5 ∧
    0 ≤ (e.2.1 : ℝ) / 1000 ∧ (e.2.1 : ℝ) / 1000 ≤ 5
  exact ⟨by positivity, by linarith, by positivity, by linarith⟩

theorem nonneg : cover.Nonneg :=
  ⟨fun _ _ => by simp only [cover, pw]; positivity,
   fun k => k.elim, fun k => k.elim⟩

/-- Exact mass; the integer sum is proved by `decide +kernel` above. -/
theorem total_eq : total = (2624862500021 : ℝ) / 125000000000 := by
  have hn : ∑ e ∈ pentries, e.2.2 = 20998900000168 := by
    rw [pentries, List.sum_toFinset _ pnodup, ← PTree.wsum_eq, pwsum_tree]
  have hr : ∑ e ∈ pentries, (e.2.2 : ℝ) = 20998900000168 := by
    rw [← Nat.cast_sum, hn]; norm_num
  simp only [total, MixedCover.total, cover, Finset.sum_empty, add_zero, pw]
  rw [← Finset.sum_div, hr]
  norm_num

theorem mu_univ : μ Set.univ = ENNReal.ofReal total :=
  cover.measure_univ_eq nonneg (fun k => k.elim)

open Classical in
theorem mu_sq (c : ℝ × ℝ) (θ : ℝ) :
    μ (sq c θ 1) = ENNReal.ofReal
      (∑ e ∈ pentries.filter (fun e => pt e ∈ sq c θ 1), pw e) := by
  rw [μ, cover.measure_apply nonneg (measurableSet_sq _ _ _)]
  simp only [MixedCover.mass, cover, Finset.sum_empty, add_zero]
  rfl

theorem d4 : D4InvM 5 μ := by
  refine cover.d4InvM 5 (fun k => k.elim) pX pS id id id id ?_
    (fun k => k.elim) (fun k => k.elim) ?_ (fun k => k.elim) (fun k => k.elim)
  · intro e he
    obtain ⟨hx, hpX, _⟩ := pentry_ok e he
    refine ⟨hpX, ?_, rfl, ?_⟩
    · change pt (pX e) = reflX 5 (pt e)
      simp only [pt, pX, reflX, Nat.cast_sub hx]
      ext
      · simp; ring
      · simp
    · obtain ⟨a, b, c⟩ := e
      simp only [pX] at hx ⊢
      ext <;> simp; omega
  · intro e he
    exact ⟨(pentry_ok e he).2.2, rfl, rfl, rfl⟩

/-- The replay's raw capture threshold. -/
noncomputable def q : ℝ := 249987 / 250000

theorem q_pos : 0 < q := by norm_num [q]
theorem margin_eq : 21 * q - total = (999979 : ℝ) / 125000000000 := by
  rw [total_eq]; norm_num [q]

/-- Normalization `μ/q`, represented as scalar multiplication of measures. -/
noncomputable def normalized : Measure (ℝ × ℝ) := ENNReal.ofReal (1 / q) • μ

theorem normalized_apply (s : Set (ℝ × ℝ)) :
    normalized s = ENNReal.ofReal (1 / q) * μ s := by
  simp only [normalized, Measure.smul_apply, smul_eq_mul]

theorem normalized_d4 : D4InvM 5 normalized := by
  intro s hs
  simp only [normalized_apply, (d4 s hs).1, (d4 s hs).2, and_self]

theorem normalized_capture {s : Set (ℝ × ℝ)} (h : ENNReal.ofReal q ≤ μ s) :
    1 ≤ normalized s := by
  rw [normalized_apply]
  have hq : ENNReal.ofReal (1 / q) * ENNReal.ofReal q = 1 := by
    rw [← ENNReal.ofReal_mul (le_of_lt (one_div_pos.mpr q_pos))]
    norm_num [q]
  rw [← hq]
  exact mul_le_mul_right h _

theorem normalized_total_eq : total / q = (2624862500021 : ℝ) / 124993500000 := by
  rw [total_eq]; norm_num [q]

theorem normalized_univ : normalized Set.univ =
    ENNReal.ofReal ((2624862500021 : ℝ) / 124993500000) := by
  rw [normalized_apply, mu_univ, ← ENNReal.ofReal_mul (le_of_lt (one_div_pos.mpr q_pos))]
  congr 1
  calc (1 / q) * total = total / q := by ring
       _ = _ := normalized_total_eq

theorem normalized_box_lt : normalized (box 5) < 21 := by
  have hmass : μ (box 5) ≤ ENNReal.ofReal total :=
    (measure_mono (Set.subset_univ _)).trans (cover.measure_univ_le nonneg)
  have hle : normalized (box 5) ≤ ENNReal.ofReal (total / q) := by
    calc normalized (box 5) = ENNReal.ofReal (1 / q) * μ (box 5) := normalized_apply _
         _ ≤ ENNReal.ofReal (1 / q) * ENNReal.ofReal total := mul_le_mul_right hmass _
         _ = ENNReal.ofReal (total / q) := by
           rw [← ENNReal.ofReal_mul (le_of_lt (one_div_pos.mpr q_pos))]
           congr 1
           ring
  apply hle.trans_lt
  rw [normalized_total_eq]
  norm_num

-- The measure's definition has been checked above. Keep the large data tree out
-- of subsequent unification; this is an elaborator transparency setting only.
attribute [irreducible] μ

end N21PtsData
open N21PtsData

/-- All-pose capture predicate, parameterized to keep certificate data out of reduction. -/
def N21PtsRegionCoverFor (ν : Measure (ℝ × ℝ)) (a : ℝ≥0∞) : Prop :=
  ∀ (c : ℝ × ℝ) (θ : ℝ), sq c θ 1 ⊆ box 5 → a ≤ ν (sq c θ 1)

/-- Checker-domain capture predicate for a measure and threshold. -/
def N21PtsCheckerCoverFor (ν : Measure (ℝ × ℝ)) (a : ℝ≥0∞) : Prop :=
  ∀ (c : ℝ × ℝ) (t : ℝ), c.1 ∈ Set.Icc 0 (5 / 2) → c.2 ∈ Set.Icc 0 (5 / 2) →
    t ∈ Set.Icc 0 (5 / 12) → sq c (2 * Real.arctan t) 1 ⊆ box 5 →
      a ≤ ν (sq c (2 * Real.arctan t) 1)

/-- The single computational hypothesis, over all contained closed unit squares. -/
def N21PtsRegionCover : Prop := N21PtsRegionCoverFor μ (ENNReal.ofReal q)

/-- The same capture bound on the actual PL59 checker domain. -/
def N21PtsCheckerCover : Prop := N21PtsCheckerCoverFor μ (ENNReal.ofReal q)

/-- The PL59 bound is sufficient: `tan (π/8) < 5/12`. -/
lemma n21pts_exists_t_of_theta {θ : ℝ} (hθ : θ ∈ Set.Icc 0 (Real.pi / 4)) :
    ∃ t ∈ Set.Icc (0 : ℝ) (5 / 12), 2 * Real.arctan t = θ := by
  obtain ⟨h0, h1⟩ := hθ
  have hpi := Real.pi_pos
  refine ⟨Real.tan (θ / 2), ⟨?_, ?_⟩, ?_⟩
  · apply Real.tan_nonneg_of_nonneg_of_le_pi_div_two <;> linarith
  · set u := Real.tan (θ / 2) with hu
    have he : 2 * Real.arctan u = θ := by
      rw [hu, Real.arctan_tan (by linarith) (by linarith)]; ring
    have hs : Real.sin θ ≤ Real.sin (Real.pi / 4) :=
      Real.sin_le_sin_of_le_of_le_pi_div_two (by linarith) (by linarith) h1
    have hc : Real.cos (Real.pi / 4) ≤ Real.cos θ :=
      Real.cos_le_cos_of_nonneg_of_le_pi h0 (by linarith) h1
    rw [Real.sin_pi_div_four] at hs
    rw [Real.cos_pi_div_four] at hc
    rw [← he, sin_two_arctan, cos_two_arctan] at *
    have hN : (0 : ℝ) < 1 + u ^ 2 := by positivity
    have key : 2 * u ≤ 1 - u ^ 2 := by
      have := le_trans hs hc
      rwa [div_le_div_iff_of_pos_right hN] at this
    by_contra h
    have hl : 5 / 12 < u := lt_of_not_ge h
    have : 25 / 144 < u ^ 2 := by nlinarith [sq_nonneg (u - 5 / 12)]
    nlinarith
  · rw [Real.arctan_tan (by linarith) (by linarith)]; ring

/-- Keep the measure abstract during pose rewriting, so Lean does not unfold the data tree. -/
private theorem n21pts_checker_reduction (ν : Measure (ℝ × ℝ)) (a : ℝ≥0∞)
    (hinv : D4InvM 5 ν)
    (h : N21PtsCheckerCoverFor ν a) : N21PtsRegionCoverFor ν a := by
  let P : ℝ × ℝ → ℝ → Prop := fun c θ => sq c θ 1 ⊆ box 5 → a ≤ ν (sq c θ 1)
  have hP : ∀ c ∈ box 5, ∀ θ, P c θ := by
    refine d4_reduce 5 P ?_ ?_ ?_ ?_
    · intro c θ
      simp only [P, sq_add_pi_div_two]
    · intro c θ hc hsub
      rw [measure_sq_reflX hinv]
      exact hc ((sq_subset_box_reflX_iff 5 c θ).mp hsub)
    · intro c θ hc hsub
      rw [measure_sq_swapXY hinv]
      exact hc ((sq_subset_box_swapXY_iff 5 c θ).mp hsub)
    · intro c θ h1 h2 hθ hsub
      obtain ⟨t, ht, he⟩ := n21pts_exists_t_of_theta hθ
      have hc := h c t h1 h2 ht
      rw [he] at hc
      exact hc hsub
  intro c θ hsub
  exact hP c (hsub (mem_sq_self c θ)) θ hsub

/-- D4 reduction directly at the raw threshold; no extra computational assumption. -/
theorem N21PtsCheckerCover.region (h : N21PtsCheckerCover) : N21PtsRegionCover :=
  n21pts_checker_reduction μ (ENNReal.ofReal q) d4 h

theorem n21pts_not_packs (h : N21PtsRegionCover) {s : ℝ} (hs : s < 5) : ¬ Packs 21 s :=
  not_packs_of_measure 5 normalized
    (fun c θ hsub => normalized_capture (h c θ hsub))
    21 (by exact_mod_cast normalized_box_lt) hs

theorem n21pts_packs : Packs 21 5 := by
  have h := packs_grid 5 21 (by norm_num)
  simpa using h

theorem n21pts_isLeast (h : N21PtsRegionCover) : IsLeast {s | Packs 21 s} 5 :=
  ⟨n21pts_packs, fun _ hs => not_lt.mp fun hlt => n21pts_not_packs h hlt hs⟩

theorem n21pts_eq_five (h : N21PtsRegionCover) : minSide 21 = 5 :=
  (n21pts_isLeast h).csInf_eq

theorem n21pts_eq_five_of_checker (h : N21PtsCheckerCover) : minSide 21 = 5 :=
  n21pts_eq_five h.region

end SquarePacking
