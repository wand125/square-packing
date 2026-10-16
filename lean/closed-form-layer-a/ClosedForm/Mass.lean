import ClosedForm.Measure

open MeasureTheory
open scoped ENNReal
namespace ClosedForm

lemma measurableSet_container (a : ℝ) : MeasurableSet (UnitSquarePacking.container a) :=
  measurableSet_Icc.prod measurableSet_Icc

lemma segMeasure_container (a : ℝ) (p q : Point)
    (hp : p ∈ UnitSquarePacking.container a) (hq : q ∈ UnitSquarePacking.container a) :
    SquarePacking.segMeasure p q (UnitSquarePacking.container a) = 1 := by
  rw [SquarePacking.segMeasure_apply p q (measurableSet_container a)]
  have he : SquarePacking.segPt p q ⁻¹' UnitSquarePacking.container a ∩ Set.Icc 0 1 =
      Set.Icc 0 1 := by
    apply Set.inter_eq_right.mpr
    intro t ht
    rcases hp with ⟨hp, hp'⟩
    rcases hq with ⟨hq, hq'⟩
    change (0 ≤ p.1 + t * (q.1 - p.1) ∧ p.1 + t * (q.1 - p.1) ≤ a) ∧
      (0 ≤ p.2 + t * (q.2 - p.2) ∧ p.2 + t * (q.2 - p.2) ≤ a)
    constructor <;> constructor <;> nlinarith [ht.1, ht.2, hp.1, hp.2, hp'.1, hp'.2,
      hq.1, hq.2, hq'.1, hq'.2]
  rw [he, SquarePacking.volume_Icc01]

lemma rowsMeasure_container (ss : List Segment) (dx dy a : ℝ)
    (hv : ∀ s ∈ ss, 0 ≤ s.mass)
    (hs : ∀ s ∈ ss,
      ((s.ax : ℝ) + dx, (s.ay : ℝ) + dy) ∈ UnitSquarePacking.container a ∧
      ((s.bx : ℝ) + dx, (s.yb : ℝ) + dy) ∈ UnitSquarePacking.container a) :
    rowsMeasure ss dx dy (UnitSquarePacking.container a) =
      ENNReal.ofReal (((ss.map Segment.mass).sum : ℚ) : ℝ) := by
  induction ss with
  | nil => simp [rowsMeasure]
  | cons s ss ih =>
    have hm : (0 : ℝ) ≤ s.mass := by exact_mod_cast hv s (by simp)
    have htail : (0 : ℝ) ≤ ((ss.map Segment.mass).sum : ℚ) := by
      exact_mod_cast List.sum_nonneg (fun x hx => by
        obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hx
        exact hv t (by simp [ht]))
    simp only [rowsMeasure, List.map_cons, List.sum_cons, Measure.add_apply,
      segmentMeasure, Measure.smul_apply, smul_eq_mul]
    rw [segMeasure_container a _ _ (hs s (by simp)).1 (hs s (by simp)).2, mul_one]
    change ENNReal.ofReal (s.mass : ℝ) + rowsMeasure ss dx dy _ = _
    rw [ih (fun t ht => hv t (by simp [ht])) (fun t ht => hs t (by simp [ht]))]
    rw [Rat.cast_add, ENNReal.ofReal_add hm htail]

lemma rotateC4_preimage_container (a : ℝ) :
    rotateC4 a ⁻¹' UnitSquarePacking.container a = UnitSquarePacking.container a := by
  ext p
  simp only [Set.mem_preimage, rotateC4, UnitSquarePacking.container,
    Set.mem_prod, Set.mem_Icc]
  constructor <;> rintro ⟨⟨h1, h2⟩, h3, h4⟩ <;> constructor <;> constructor <;> linarith

lemma rotateC4_iterate_preimage_container (a : ℝ) (j : ℕ) :
    (rotateC4 a)^[j] ⁻¹' UnitSquarePacking.container a =
      UnitSquarePacking.container a := by
  induction j with
  | zero => rfl
  | succ j ih =>
    rw [Function.iterate_succ, Set.preimage_comp, ih, rotateC4_preimage_container]

lemma map_rotateC4_container (a : ℝ) (j : ℕ) (μ : Measure Point) :
    Measure.map ((rotateC4 a)^[j]) μ (UnitSquarePacking.container a) =
      μ (UnitSquarePacking.container a) := by
  have hc : Continuous (rotateC4 a) := by unfold rotateC4; fun_prop
  rw [Measure.map_apply (hc.iterate j).measurable (measurableSet_container a),
    rotateC4_iterate_preimage_container]

lemma profile_valid (f : Family) (hv : f.Valid) :
    ∀ s ∈ profile f, s.Valid := by
  intro s hs
  obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
  have ht' := (List.mem_filter.mp ht).1
  have htval := hv.2.1 t (List.mem_append_right _ ht')
  simpa [Segment.Valid, Segment.shift] using htval

lemma sum_measures_apply (ms : List (Measure Point)) (s : Set Point) :
    ms.sum s = (ms.map fun μ => μ s).sum := by
  induction ms with
  | nil => simp
  | cons μ ms ih => simp [Measure.add_apply, ih]

lemma sum_ofReal (xs : List ℝ) (hx : ∀ x ∈ xs, 0 ≤ x) :
    (xs.map ENNReal.ofReal).sum = ENNReal.ofReal xs.sum := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    rw [List.map_cons, List.sum_cons, List.sum_cons,
      ih (fun y hy => hx y (by simp [hy])),
      ENNReal.ofReal_add (hx x (by simp))
        (List.sum_nonneg (fun y hy => hx y (by simp [hy])))]

lemma endpoints_in_container (s : Segment) (dx dy a : ℝ)
    (hx0 : 0 ≤ (min s.ax s.bx : ℚ) + dx)
    (hx1 : (max s.ax s.bx : ℚ) + dx ≤ a)
    (hy0 : 0 ≤ (min s.ay s.yb : ℚ) + dy)
    (hy1 : (max s.ay s.yb : ℚ) + dy ≤ a) :
    ((s.ax : ℝ) + dx, (s.ay : ℝ) + dy) ∈ UnitSquarePacking.container a ∧
    ((s.bx : ℝ) + dx, (s.yb : ℝ) + dy) ∈ UnitSquarePacking.container a := by
  have h1 : (min s.ax s.bx : ℚ) ≤ (s.ax : ℝ) := by exact_mod_cast min_le_left s.ax s.bx
  have h2 : (min s.ax s.bx : ℚ) ≤ (s.bx : ℝ) := by exact_mod_cast min_le_right s.ax s.bx
  have h3 : (s.ax : ℝ) ≤ (max s.ax s.bx : ℚ) := by exact_mod_cast le_max_left s.ax s.bx
  have h4 : (s.bx : ℝ) ≤ (max s.ax s.bx : ℚ) := by exact_mod_cast le_max_right s.ax s.bx
  have h5 : (min s.ay s.yb : ℚ) ≤ (s.ay : ℝ) := by exact_mod_cast min_le_left s.ay s.yb
  have h6 : (min s.ay s.yb : ℚ) ≤ (s.yb : ℝ) := by exact_mod_cast min_le_right s.ay s.yb
  have h7 : (s.ay : ℝ) ≤ (max s.ay s.yb : ℚ) := by exact_mod_cast le_max_left s.ay s.yb
  have h8 : (s.yb : ℝ) ≤ (max s.ay s.yb : ℚ) := by exact_mod_cast le_max_right s.ay s.yb
  change ((_ ∧ _) ∧ (_ ∧ _)) ∧ ((_ ∧ _) ∧ (_ ∧ _))
  exact ⟨⟨⟨by linarith, by linarith⟩, ⟨by linarith, by linarith⟩⟩,
    ⟨⟨by linarith, by linarith⟩, ⟨by linarith, by linarith⟩⟩⟩

/-- Symbolic mass identity; all boundary segments are counted in full. -/
theorem total_mass_structural (f fr : Family) (h : Structural f fr)
    (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) :
    globalMeasure f k δ (UnitSquarePacking.container ((k : ℝ) + δ)) =
      ENNReal.ofReal (((k : ℝ) + δ) ^ 2 - 4 * saving f δ) := by
  rcases h with ⟨hv, hvr, hua, hu, hd0, hd1, hrest⟩
  rcases hrest with ⟨_, _, _, _, _, _, _, hprof, hcv, hcf, hct, hvb, hpb, _, _⟩
  have hkR : (7 : ℝ) ≤ k := by exact_mod_cast hk
  have hd0R : (0 : ℝ) ≤ f.d0 := by exact_mod_cast hd0
  have hd1R : (f.d1 : ℝ) ≤ 1 := by exact_mod_cast hd1
  have hδ0 : 0 ≤ δ := hd0R.trans hδ.1
  have hδ1 : δ ≤ 1 := hδ.2.trans hd1R
  have hn : ((k - 4 : ℕ) : ℝ) = (k : ℝ) - 4 := by
    rw [Nat.cast_sub (by omega : 4 ≤ k)]; norm_num
  let a : ℝ := (k : ℝ) + δ
  have hF := rowsMeasure_container (cornerF f) 0 0 a
    (fun s hs => (hcv s (List.mem_append_left _ hs)).1) (by
      intro s hs
      rcases hcf s hs with ⟨hx0, hx1, hy0, hy1⟩
      apply endpoints_in_container <;> try dsimp [a]
      all_goals
        have hx0' : (0 : ℝ) ≤ (min s.ax s.bx : ℚ) := by exact_mod_cast hx0
        have hx1' : ((max s.ax s.bx : ℚ) : ℝ) ≤ 2 + (f.d0 : ℝ) := by exact_mod_cast hx1
        have hy0' : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hy0
        have hy1' : ((max s.ay s.yb : ℚ) : ℝ) ≤ 2 := by exact_mod_cast hy1
        linarith [hδ.1])
  have hT := rowsMeasure_container (cornerT f) δ 0 a
    (fun s hs => (hcv s (List.mem_append_right _ hs)).1) (by
      intro s hs
      rcases hct s hs with ⟨hax, hbx, hy0, hy1⟩
      apply endpoints_in_container <;> try dsimp [a]
      all_goals
        have hy0' : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hy0
        have hy1' : ((max s.ay s.yb : ℚ) : ℝ) ≤ 2 := by exact_mod_cast hy1
        try simp only [hax, hbx, min_self, max_self, Rat.cast_ofNat]
        linarith)
  have hVnon : ∀ v ∈ f.V, 0 ≤ (v.rho : ℝ) * (2 + δ - v.xl) := by
    intro v hv'
    obtain ⟨hr, hx⟩ := hv.2.2 v hv'
    have hr' : (0 : ℝ) ≤ v.rho := by exact_mod_cast hr
    have hx' : (v.xl : ℝ) ≤ 2 + (f.d0 : ℝ) := by exact_mod_cast hx
    exact mul_nonneg hr' (by linarith [hδ.1])
  have hV : ((f.V.map fun v => variableMeasure v δ).sum)
      (UnitSquarePacking.container a) =
      ENNReal.ofReal ((f.V.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum) := by
    rw [sum_measures_apply, List.map_map]
    have he : ∀ v ∈ f.V, variableMeasure v δ (UnitSquarePacking.container a) =
        ENNReal.ofReal ((v.rho : ℝ) * (2 + δ - v.xl)) := by
      intro v hv'
      obtain ⟨hx, hy, hy'⟩ := hvb v hv'
      have hxR : (0 : ℝ) ≤ v.xl := by exact_mod_cast hx
      have hyR : (0 : ℝ) ≤ v.y := by exact_mod_cast hy
      have hyR' : (v.y : ℝ) ≤ 2 := by exact_mod_cast hy'
      have hxR' : (v.xl : ℝ) ≤ 2 + (f.d0 : ℝ) := by exact_mod_cast (hv.2.2 v hv').2
      rw [variableMeasure, Measure.smul_apply, smul_eq_mul,
        segMeasure_container a _ _ ?_ ?_, mul_one]
      all_goals change (0 ≤ _ ∧ _ ≤ a) ∧ (0 ≤ _ ∧ _ ≤ a)
      all_goals simp only [a]; exact ⟨⟨by linarith [hδ.1], by linarith [hδ.1]⟩,
        ⟨by linarith, by linarith⟩⟩
    simp only [Function.comp_def]
    rw [List.map_congr_left he]
    rw [show (fun v : VariableSegment => ENNReal.ofReal ((v.rho : ℝ) * (2 + δ - v.xl))) =
      ENNReal.ofReal ∘ (fun v => (v.rho : ℝ) * (2 + δ - v.xl)) from rfl,
      ← List.map_map, sum_ofReal]
    intro x hx
    obtain ⟨v, hv', rfl⟩ := List.mem_map.mp hx
    exact hVnon v hv'
  have hpv := profile_valid f hv
  have hP : ∀ (n : ℕ), n ∈ List.range (k - 4) →
      rowsMeasure (profile f) (2 + δ + n) 0 (UnitSquarePacking.container a) =
        ENNReal.ofReal (9 / 5 : ℝ) := by
    intro n hn'
    rw [rowsMeasure_container _ _ _ _ (fun s hs => (hpv s hs).1), hprof]
    · norm_num
    · intro s hs
      rcases hpb s hs with ⟨hx0, hx1, hy0, hy1⟩
      have hn'R : (n : ℝ) < (k : ℝ) - 4 := by
        rw [← hn]; exact_mod_cast List.mem_range.mp hn'
      apply endpoints_in_container <;> try dsimp [a]
      all_goals
        have hx0' : (0 : ℝ) ≤ (min s.ax s.bx : ℚ) := by exact_mod_cast hx0
        have hx1' : ((max s.ax s.bx : ℚ) : ℝ) ≤ 1 := by exact_mod_cast hx1
        have hy0' : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hy0
        have hy1' : ((max s.ay s.yb : ℚ) : ℝ) ≤ ((9 / 5 : ℚ) : ℝ) := by exact_mod_cast hy1
        norm_num only [Rat.cast_div, Rat.cast_ofNat] at hy1'
        have hn0 : (0 : ℝ) ≤ n := Nat.cast_nonneg n
        linarith
  have hterm : rowsMeasure (terminal f) (2 + δ + (k - 4 : ℕ)) 0
      (UnitSquarePacking.container a) = ENNReal.ofReal (terminalMass f : ℝ) := by
    apply rowsMeasure_container
    · intro s hs; exact (hpv s (List.mem_filter.mp hs).1).1
    · intro s hs
      have hs' := (List.mem_filter.mp hs).1
      have hz := (List.mem_filter.mp hs).2
      simp only [Bool.and_eq_true, beq_iff_eq] at hz
      rcases hpb s hs' with ⟨hx0, hx1, hy0, hy1⟩
      apply endpoints_in_container <;> try dsimp [a]
      all_goals
        have hy0' : (0 : ℝ) ≤ (min s.ay s.yb : ℚ) := by exact_mod_cast hy0
        have hy1' : ((max s.ay s.yb : ℚ) : ℝ) ≤ ((9 / 5 : ℚ) : ℝ) := by exact_mod_cast hy1
        norm_num only [Rat.cast_div, Rat.cast_ofNat] at hy1'
        try simp only [hz.1, hz.2, min_self, max_self, Rat.cast_zero]
        linarith
  have hcorner : cornerMeasure f δ (UnitSquarePacking.container a) =
      ENNReal.ofReal (cornerMass f δ) := by
    rw [cornerMeasure, Measure.add_apply, Measure.add_apply, hF, hT, hV]
    have hcF : (0 : ℝ) ≤ (((cornerF f).map Segment.mass).sum : ℚ) := by
      exact_mod_cast List.sum_nonneg (fun x hx => by
        obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hx
        exact (hcv s (List.mem_append_left _ hs)).1)
    have hcT : (0 : ℝ) ≤ (((cornerT f).map Segment.mass).sum : ℚ) := by
      exact_mod_cast List.sum_nonneg (fun x hx => by
        obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hx
        exact (hcv s (List.mem_append_right _ hs)).1)
    have hcV : 0 ≤ (f.V.map fun v => (v.rho : ℝ) * (2 + δ - v.xl)).sum :=
      List.sum_nonneg (by simpa using hVnon)
    simp only [cornerMass, fixedCornerMass, List.map_append, List.sum_append, Rat.cast_add]
    rw [ENNReal.ofReal_add (add_nonneg hcF hcT) hcV, ENNReal.ofReal_add hcF hcT]
  have ht0 : (0 : ℝ) ≤ terminalMass f := by
    exact_mod_cast List.sum_nonneg (fun x hx => by
      obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hx
      exact (hpv s (List.mem_filter.mp hs).1).1)
  have hw : wallMeasure f k δ (UnitSquarePacking.container a) =
      ENNReal.ofReal (((k : ℝ) - 4) * (9 / 5) + terminalMass f) := by
    rw [wallMeasure, Measure.add_apply, hterm, sum_measures_apply]
    simp only [List.map_map, bind_pure_comp, Function.comp_def]
    change ((List.range (k - 4)).map (fun n : ℕ => (n : ℝ)) |>.map
      (fun x => rowsMeasure (profile f) (2 + δ + x) 0
        (UnitSquarePacking.container a))).sum + _ = _
    rw [List.map_map]
    simp only [Function.comp_def]
    rw [List.map_congr_left hP]
    simp only [List.map_const', List.length_range, List.sum_replicate, nsmul_eq_mul]
    rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), hn,
      ← ENNReal.ofReal_add (by nlinarith : 0 ≤ ((k : ℝ) - 4) * (9 / 5)) ht0]
  have hc0 : 0 ≤ cornerMass f δ := by
    unfold cornerMass fixedCornerMass
    apply add_nonneg
    · exact_mod_cast List.sum_nonneg (fun x hx => by
        obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hx
        exact (hcv s hs).1)
    · exact List.sum_nonneg (by simpa using hVnon)
  have harea : volume.restrict (globalArea k δ) (UnitSquarePacking.container a) =
      ENNReal.ofReal ((a - 18 / 5) ^ 2) := by
    rw [Measure.restrict_apply (measurableSet_container a)]
    have hi : UnitSquarePacking.container a ∩ globalArea k δ = globalArea k δ := by
      apply Set.inter_eq_right.mpr
      rintro p ⟨hp, hq⟩
      change (0 ≤ p.1 ∧ p.1 ≤ a) ∧ (0 ≤ p.2 ∧ p.2 ≤ a)
      exact ⟨⟨by linarith [hp.1], by dsimp [a]; linarith [hp.2]⟩,
        ⟨by linarith [hq.1], by dsimp [a]; linarith [hq.2]⟩⟩
    rw [hi]
    simp only [globalArea, Measure.volume_eq_prod, Measure.prod_prod, Real.volume_Icc]
    rw [← ENNReal.ofReal_mul (by linarith)]
    congr 1
    simp only [a]; ring
  have hw0 : 0 ≤ ((k : ℝ) - 4) * (9 / 5) + (terminalMass f : ℝ) := by nlinarith
  change _ = ENNReal.ofReal (a ^ 2 - 4 * saving f δ)
  rw [globalMeasure, Measure.add_apply, harea, sum_measures_apply, List.map_map]
  simp only [Function.comp_def, map_rotateC4_container, Measure.add_apply]
  change ((List.range 4).map fun _ => cornerMeasure f δ (UnitSquarePacking.container a) +
    wallMeasure f k δ (UnitSquarePacking.container a)).sum + _ = _
  simp only [hcorner, hw]
  rw [← ENNReal.ofReal_add hc0 hw0]
  simp only [List.map_const', List.length_range, List.sum_replicate, nsmul_eq_mul]
  rw [← ENNReal.ofReal_natCast, Nat.cast_ofNat,
    ← ENNReal.ofReal_mul (by norm_num : (0 : ℝ) ≤ 4),
    ← ENNReal.ofReal_add (mul_nonneg (by norm_num) (add_nonneg hc0 hw0)) (sq_nonneg _)]
  congr 1
  dsimp [saving, a]
  ring

end ClosedForm
