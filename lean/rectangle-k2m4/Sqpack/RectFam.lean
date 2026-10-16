import Sqpack.BentzFam
import Sqpack.Conjectures

/-!
# Rectangle families

The proofs adapt the MIT-licensed upstream square-family argument; see `UPSTREAM.md`
and `LICENSE-evand-square-packing`. One-axis lemmas are reused from BentzFam unchanged.
The Boolean orientation is the upstream convention: `false` horizontal, `true` vertical.
-/
open MeasureTheory Finset
open scoped ENNReal
namespace SquarePacking
namespace RectFam
open BentzFam
open Bentz (segA segB idx mem_idx)

def rectangle (A B : ℝ) : Set (ℝ × ℝ) := Set.Icc 0 A ×ˢ Set.Icc 0 B

def wRect (F : Fam) (A B : ℕ) (s : FIx) : ℕ :=
  if s.1.1 then tabW (F.layer s.2) (cellT F.R B s.1.2.2) (lineT F.R A s.1.2.1)
  else tabW (F.layer s.2) (cellT F.R A s.1.2.1) (lineT F.R B s.1.2.2)

def gridRect (A B : ℕ) : Finset FIx := (univ ×ˢ (idx A ×ˢ idx B)) ×ˢ univ

def lebRect (a A B : ℕ) : Set (ℝ × ℝ) :=
  Set.Icc ((a : ℝ) / 5) ((A : ℝ) - a / 5) ×ˢ
    Set.Icc ((a : ℝ) / 5) ((B : ℝ) - a / 5)

noncomputable def famRect (F : Fam) (A B : ℕ) : MixedCover Empty FIx Unit where
  pts := ∅
  pt := fun e => e.elim
  pw := fun e => e.elim
  segs := gridRect A B
  sa := fun s => segA s.1
  sb := fun s => segB s.1
  sw := fun s => (wRect F A B s : ℝ) / F.den
  polys := univ
  poly := fun _ => lebRect F.A A B
  gw := fun _ => ((A : ℝ) - 2 * F.A / 5) * ((B : ℝ) - 2 * F.A / 5)

theorem famRect_diag (F : Fam) (k : ℕ) : famRect F k k = famCover F k := by
  unfold famRect famCover
  simp only [wRect, wN, gridRect, grid, lebRect, lebSq, pow_two]

lemma mem_gridRect {A B : ℕ} {s : FIx} :
    s ∈ gridRect A B ↔ (0 ≤ s.1.2.1 ∧ s.1.2.1 ≤ 5 * (A : ℤ)) ∧
      (0 ≤ s.1.2.2 ∧ s.1.2.2 ≤ 5 * (B : ℤ)) := by
  simp only [gridRect, mem_product, mem_univ, true_and, and_true, mem_idx]

lemma wRect_eq_zero {F : Fam} (hF : OutZero F) {A B : ℕ} {s : FIx}
    (hs : s ∉ gridRect A B) : wRect F A B s = 0 := by
  rw [mem_gridRect, not_and_or] at hs
  obtain ⟨⟨o, i, j⟩, b⟩ := s
  cases o <;> simp only [wRect, Bool.false_eq_true, if_false, if_true] <;> rcases hs with h | h
  · rw [cellT_out h]; exact tabW_out_left hF _ _ (lineT_range _ B j)
  · rw [lineT_out h]; exact tabW_out_right hF _ _ (cellT_range _ A i)
  · rw [lineT_out h]; exact tabW_out_right hF _ _ (cellT_range _ B j)
  · rw [cellT_out h]; exact tabW_out_left hF _ _ (lineT_range _ A i)

theorem sq_subset_rectangle_iff (A B : ℝ) (c : ℝ × ℝ) (θ : ℝ) :
    sq c θ 1 ⊆ rectangle A B ↔
      wid θ / 2 ≤ c.1 ∧ c.1 ≤ A - wid θ / 2 ∧
      wid θ / 2 ≤ c.2 ∧ c.2 ≤ B - wid θ / 2 := by
  constructor
  · intro hsub
    -- the four extreme vertices, written with the signs of `cos θ` and `sin θ`
    set sc : ℝ := if 0 ≤ Real.cos θ then 1 else -1 with hsc
    set ss : ℝ := if 0 ≤ Real.sin θ then 1 else -1 with hss
    have hscC : sc * Real.cos θ = |Real.cos θ| := by
      rw [hsc]; split_ifs with h
      · rw [abs_of_nonneg h]; ring
      · rw [abs_of_neg (not_le.mp h)]; ring
    have hssS : ss * Real.sin θ = |Real.sin θ| := by
      rw [hss]; split_ifs with h
      · rw [abs_of_nonneg h]; ring
      · rw [abs_of_neg (not_le.mp h)]; ring
    have habs : ∀ t : ℝ, (t = 1 ∨ t = -1) → |(-t) / 2| ≤ 1 / 2 ∧ |t / 2| ≤ 1 / 2 := by
      rintro t (rfl | rfl) <;> norm_num
    have hsc' : sc = 1 ∨ sc = -1 := by rw [hsc]; split_ifs <;> simp
    have hss' : ss = 1 ∨ ss = -1 := by rw [hss]; split_ifs <;> simp
    have hA := habs sc hsc'
    have hB := habs ss hss'
    refine ⟨?_, ?_, ?_, ?_⟩
    · -- `c_x ≥ w/2`: the vertex at offset `(-sc/2, ss/2)` has `p_x - c_x = -w/2`
      have h := (hsub (mem_sq_offset c θ (-sc / 2) (ss / 2) hA.1 hB.2)).1.1
      simp only [wid] at *
      nlinarith [hscC, hssS, h]
    · have h := (hsub (mem_sq_offset c θ (sc / 2) (-ss / 2) hA.2 hB.1)).1.2
      simp only [wid] at *
      nlinarith [hscC, hssS, h]
    · have h := (hsub (mem_sq_offset c θ (-ss / 2) (-sc / 2) hB.1 hA.1)).2.1
      simp only [wid] at *
      nlinarith [hscC, hssS, h]
    · have h := (hsub (mem_sq_offset c θ (ss / 2) (sc / 2) hB.2 hA.2)).2.2
      simp only [wid] at *
      nlinarith [hscC, hssS, h]
  · rintro ⟨h1, h2, h3, h4⟩ p hp
    obtain ⟨hx, hy⟩ := abs_sub_le_wid hp
    rw [abs_le] at hx hy
    exact ⟨⟨by linarith [hx.1], by linarith [hx.2]⟩, by linarith [hy.1], by linarith [hy.2]⟩

noncomputable def segTermRect (F : Fam) (A B : ℕ) (S : Set (ℝ × ℝ)) (s : FIx) : ℝ :=
  (wRect F A B s : ℝ) / F.den * segFrac (segA s.1) (segB s.1) S

/-- Re-indexing the segment sums by a shift that matches the terms. -/
lemma sum_segTermRect_shift {F : Fam} (hF : OutZero F) {A B K : ℕ} (S S' : Set (ℝ × ℝ)) (nx ny : ℤ)
    (hterm : ∀ s, segTermRect F A B S s = segTermRect F K K S' (shiftF nx ny s)) :
    ∑ s ∈ gridRect A B, segTermRect F A B S s = ∑ s ∈ gridRect K K, segTermRect F K K S' s := by
  set τ := shiftF nx ny with hτ
  set τ' := shiftF (-nx) (-ny) with hτ'
  have h1 : ∀ s, τ' (τ s) = s := fun s => by
    obtain ⟨⟨o, i, j⟩, b⟩ := s; simp [hτ, hτ', shiftF, Bentz.shiftIx]
  have h2 : ∀ s, τ (τ' s) = s := fun s => by
    obtain ⟨⟨o, i, j⟩, b⟩ := s; simp [hτ, hτ', shiftF, Bentz.shiftIx]
  have hinj : Set.InjOn τ (gridRect A B : Set FIx) := fun a _ b _ h => by
    rw [← h1 a, h, h1 b]
  rw [Finset.sum_congr rfl fun s _ => hterm s, ← Finset.sum_image hinj]
  have hzK : ∀ s, s ∉ gridRect K K → segTermRect F K K S' s = 0 := fun s hs => by
    simp [segTermRect, wRect_eq_zero hF hs]
  have hzk : ∀ s ∈ gridRect K K, s ∉ (gridRect A B).image τ →
      segTermRect F K K S' s = 0 := fun s _ hs => by
    have hn : τ' s ∉ gridRect A B := fun hm => hs (mem_image.mpr ⟨τ' s, hm, h2 s⟩)
    rw [← h2 s, ← hterm]
    simp [segTermRect, wRect_eq_zero hF hn]
  have e1 : ∑ s ∈ (gridRect A B).image τ, segTermRect F K K S' s
      = ∑ s ∈ (gridRect A B).image τ ∪ gridRect K K, segTermRect F K K S' s :=
    Finset.sum_subset Finset.subset_union_left
      (fun s hs hns => hzk s ((mem_union.mp hs).resolve_left hns) hns)
  have e2 : ∑ s ∈ gridRect K K, segTermRect F K K S' s
      = ∑ s ∈ (gridRect A B).image τ ∪ gridRect K K, segTermRect F K K S' s :=
    Finset.sum_subset Finset.subset_union_right (fun s _ hns => hzK s hns)
  rw [e1, e2]

lemma volume_lebRect {a A B : ℕ} (hA : 2 * (a : ℝ) / 5 ≤ A) :
    volume (lebRect a A B) =
      ENNReal.ofReal (((A : ℝ) - 2 * a / 5) * ((B : ℝ) - 2 * a / 5)) := by
  rw [lebRect, Measure.volume_eq_prod, Measure.prod_prod, Real.volume_Icc,
    Real.volume_Icc, ← ENNReal.ofReal_mul (by linarith)]
  congr 1; ring

lemma polyTermRect {a A B : ℕ} (hA : 2 * (a : ℝ) / 5 < A)
    (hB : 2 * (a : ℝ) / 5 < B) (S : Set (ℝ × ℝ)) :
    ((A : ℝ) - 2 * a / 5) * ((B : ℝ) - 2 * a / 5) * areaFrac (lebRect a A B) S =
      (volume (S ∩ lebRect a A B)).toReal := by
  have hpos : 0 < ((A : ℝ) - 2 * a / 5) * ((B : ℝ) - 2 * a / 5) :=
    mul_pos (by linarith) (by linarith)
  rw [areaFrac, volume_lebRect hA.le, ENNReal.toReal_mul, ENNReal.toReal_inv,
    ENNReal.toReal_ofReal hpos.le, ← mul_assoc, mul_inv_cancel₀ hpos.ne', one_mul]

/-- Localize to the original square family, with independent shifts on the two axes. -/
theorem mass_shift_rect (F : Fam) (hF : OutZero F) (hA : F.A ≤ 5 * F.R)
    {A B : ℕ} (hAx : 2 * F.R + 2 ≤ A) (hBy : 2 * F.R + 2 ≤ B)
    (c : ℝ × ℝ) (θ : ℝ) (hS : sq c θ 1 ⊆ rectangle A B) :
    ∃ v : ℝ × ℝ, sq (c - v) θ 1 ⊆ box ((2 * F.R + 3 : ℕ) : ℝ) ∧
      (famRect F A B).mass (sq c θ 1) =
        (famCover F (2 * F.R + 3)).mass (sq (c - v) θ 1) := by
  rw [← famRect_diag F (2 * F.R + 3)]
  have hA' : (F.A : ℝ) / 5 ≤ F.R := by
    have : (F.A : ℝ) ≤ 5 * F.R := by exact_mod_cast hA
    linarith
  have hAx' : 2 * (F.R : ℝ) + 2 ≤ A := by exact_mod_cast hAx
  have hBy' : 2 * (F.R : ℝ) + 2 ≤ B := by exact_mod_cast hBy
  obtain ⟨ha1, ha2, ha3, ha4⟩ := (sq_subset_rectangle_iff A B c θ).mp hS
  have hw := Bentz.wid_lt_two θ
  obtain ⟨nx, hgx⟩ := exists_good hAx (x₀ := c.1 - wid θ / 2) (x₁ := c.1 + wid θ / 2) (by linarith)
  obtain ⟨ny, hgy⟩ := exists_good hBy (x₀ := c.2 - wid θ / 2) (x₁ := c.2 + wid θ / 2) (by linarith)
  have hx0 : 0 ≤ c.1 - wid θ / 2 := by linarith
  have hx1 : c.1 + wid θ / 2 ≤ A := by linarith
  have hy0 : 0 ≤ c.2 - wid θ / 2 := by linarith
  have hy1 : c.2 + wid θ / 2 ≤ B := by linarith
  set v : ℝ × ℝ := ((nx : ℝ), (ny : ℝ)) with hv
  refine ⟨v, ?_, ?_⟩
  · obtain ⟨b1, b2⟩ := good_box hgx hx0 hx1
    obtain ⟨b3, b4⟩ := good_box hgy hy0 hy1
    refine (sq_subset_box_iff _ (c - v) θ).mpr ⟨?_, ?_, ?_, ?_⟩ <;>
      simp only [hv, Prod.fst_sub, Prod.snd_sub] <;> linarith
  -- the bounding box of the square
  have hbox : ∀ p ∈ sq c θ 1, (c.1 - wid θ / 2 ≤ p.1 ∧ p.1 ≤ c.1 + wid θ / 2) ∧
      (c.2 - wid θ / 2 ≤ p.2 ∧ p.2 ≤ c.2 + wid θ / 2) := fun p hp => by
    obtain ⟨h1, h2⟩ := abs_sub_le_wid hp
    rw [abs_le] at h1 h2
    exact ⟨⟨by linarith, by linarith⟩, by linarith, by linarith⟩
  unfold MixedCover.mass
  refine congrArg₂ (· + ·) (congrArg₂ (· + ·) ?_ ?_) ?_
  · have h : ∀ (T : Finset Empty) (f : Empty → ℝ), ∑ e ∈ T, f e = 0 := fun T f => by
      simp [Finset.eq_empty_of_isEmpty T]
    rw [h, h]
  · -- the segments
    change ∑ s ∈ gridRect A B, segTermRect F A B (sq c θ 1) s
      = ∑ s ∈ gridRect (2 * F.R + 3) (2 * F.R + 3),
        segTermRect F (2 * F.R + 3) (2 * F.R + 3) (sq (c - v) θ 1) s
    refine sum_segTermRect_shift hF _ _ nx ny fun s => ?_
    simp only [segTermRect, shiftF]
    rw [Bentz.segFrac_shift]
    by_cases h0 : segFrac (segA s.1) (segB s.1) (sq c θ 1) = 0
    · rw [h0]; simp
    obtain ⟨t, ⟨t0, t1⟩, ht⟩ := Bentz.exists_of_segFrac_ne h0
    obtain ⟨⟨p1, p2⟩, p3, p4⟩ := hbox _ ht
    obtain ⟨⟨o, i, j⟩, b⟩ := s
    congr 3
    cases o
    · simp only [segPt, segA, segB, Bool.false_eq_true, if_false] at p1 p2 p3 p4
      simp only [wRect, Bentz.shiftIx, Bool.false_eq_true, if_false]
      rw [good_cell hgx hx0 hx1 (i := i) (by nlinarith) (by nlinarith),
        good_line hgy hy0 hy1 (j := j) (by nlinarith) (by nlinarith)]
    · simp only [segPt, segA, segB, if_true] at p1 p2 p3 p4
      simp only [wRect, Bentz.shiftIx, if_true]
      rw [good_cell hgy hy0 hy1 (i := j) (by nlinarith) (by nlinarith),
        good_line hgx hx0 hx1 (j := i) (by nlinarith) (by nlinarith)]
  · -- the Lebesgue square
    simp only [famRect, Finset.sum_const, Finset.card_univ, Fintype.card_unit, one_smul]
    have hK : 2 * (F.A : ℝ) / 5 < ((2 * F.R + 3 : ℕ) : ℝ) := by push_cast; linarith
    rw [polyTermRect (by linarith) (by linarith), polyTermRect hK hK]
    congr 1
    have hset : sq (c - v) θ 1 ∩ lebRect F.A (2 * F.R + 3) (2 * F.R + 3)
        = (fun p => p + v) ⁻¹' (sq c θ 1 ∩ lebRect F.A A B) := by
      ext p
      simp only [Set.mem_inter_iff, Set.mem_preimage, Bentz.mem_sq_sub]
      refine and_congr_right fun hp => ?_
      obtain ⟨⟨p1, p2⟩, p3, p4⟩ := hbox _ hp
      simp only [Prod.fst_add, Prod.snd_add, hv] at p1 p2 p3 p4
      simp only [lebRect, Set.mem_prod, Set.mem_Icc, Prod.fst_add, Prod.snd_add, hv]
      rw [good_leb hA' hgx p1 p2, good_leb hA' hgy p3 p4]
      simp only [add_sub_cancel_right]
    rw [hset, measure_preimage_add_right]

lemma famRect_nonneg (F : Fam) {A B : ℕ}
    (hA : 2 * (F.A : ℝ) / 5 ≤ A) (hB : 2 * (F.A : ℝ) / 5 ≤ B) :
    (famRect F A B).Nonneg :=
  ⟨fun e => e.elim, fun _ _ => by simp only [famRect]; positivity,
    fun _ _ => mul_nonneg (by linarith) (by linarith)⟩

lemma sum_cell_line_rect (R m n : ℕ) (T : ℤ → ℤ → ℕ) :
    ∑ i ∈ idx (m + 2 * R + 1), ∑ j ∈ idx (n + 2 * R + 1),
        T (cellT R (m + 2 * R + 1) i) (lineT R (n + 2 * R + 1) j)
      = H00 R T + n * H01 R T + m * H10 R T + m * n * H11 R T := by
  rw [sum_congr rfl fun i _ => sum_lineT R n (T (cellT R (m + 2 * R + 1) i))]
  rw [sum_cellT R m (fun c => L0 R (T c) + n * L1 R (T c))]
  have lin0 : ∀ a b : ℤ → ℕ, C0 R (fun c => a c + n * b c) = C0 R a + n * C0 R b := by
    intro a b; simp only [C0, sum_add_distrib, ← mul_sum]; ring
  have lin1 : ∀ a b : ℤ → ℕ, C1 R (fun c => a c + n * b c) = C1 R a + n * C1 R b := by
    intro a b; simp only [C1, sum_add_distrib, ← mul_sum]
  rw [lin0, lin1]
  unfold H00 H01 H10 H11
  ring

/-- Horizontal contribution with independent cell and line lengths. -/
def Hrect (F : Fam) (b : Bool) (m n : ℕ) : ℕ :=
  H00 F.R (tabW (F.layer b)) + n * H01 F.R (tabW (F.layer b)) +
    m * H10 F.R (tabW (F.layer b)) + m * n * H11 F.R (tabW (F.layer b))

theorem seg_total_rect (F : Fam) (m n : ℕ) :
    ∑ s ∈ gridRect (m + 2 * F.R + 1) (n + 2 * F.R + 1),
      wRect F (m + 2 * F.R + 1) (n + 2 * F.R + 1) s =
      Hrect F false m n + Hrect F false n m + Hrect F true m n + Hrect F true n m := by
  have hb : ∀ b : Bool,
      ∑ seg ∈ univ ×ˢ (idx (m + 2 * F.R + 1) ×ˢ idx (n + 2 * F.R + 1)),
        wRect F (m + 2 * F.R + 1) (n + 2 * F.R + 1) (seg, b) =
          Hrect F b m n + Hrect F b n m := by
    intro b
    rw [sum_product, Fintype.sum_bool]
    simp only [sum_product, wRect, if_true, Bool.false_eq_true, if_false]
    rw [sum_comm (s := idx (m + 2 * F.R + 1)) (t := idx (n + 2 * F.R + 1))
      (f := fun i j => tabW (F.layer b) (cellT F.R (n + 2 * F.R + 1) j)
        (lineT F.R (m + 2 * F.R + 1) i))]
    rw [sum_cell_line_rect, sum_cell_line_rect]
    unfold Hrect
    ring
  rw [gridRect, sum_product, sum_comm, Fintype.sum_bool, hb, hb]
  ring

theorem famRect_total (F : Fam) (m n : ℕ) :
    (famRect F (m + 2 * F.R + 1) (n + 2 * F.R + 1)).total =
      ((Hrect F false m n + Hrect F false n m + Hrect F true m n + Hrect F true n m : ℕ) : ℝ) /
        F.den + (((m + 2 * F.R + 1 : ℕ) : ℝ) - 2 * F.A / 5) *
          (((n + 2 * F.R + 1 : ℕ) : ℝ) - 2 * F.A / 5) := by
  have hs : ∑ s ∈ gridRect (m + 2 * F.R + 1) (n + 2 * F.R + 1),
      (wRect F (m + 2 * F.R + 1) (n + 2 * F.R + 1) s : ℝ) / F.den =
      ((Hrect F false m n + Hrect F false n m + Hrect F true m n + Hrect F true n m : ℕ) : ℝ) /
        F.den := by
    rw [← sum_div, ← Nat.cast_sum, seg_total_rect]
  simp only [MixedCover.total, famRect, sum_empty, hs, sum_const, card_univ,
    Fintype.card_unit, one_smul, zero_add]

/-- A measure cover excludes a packing in any rectangle strictly shorter in both axes. -/
theorem not_packsRect_of_measure (A B : ℝ) (hA : 0 < A) (hB : 0 < B)
    (μ : Measure (ℝ × ℝ))
    (hcover : ∀ (c : ℝ × ℝ) (θ : ℝ), sq c θ 1 ⊆ rectangle A B → 1 ≤ μ (sq c θ 1))
    (n : ℕ) (htot : μ (rectangle A B) < n) {a b : ℝ} (ha : a < A) (hb : b < B) :
    ¬ UnitSquarePacking.Conjectures.PacksRect n a b := by
  rintro ⟨ctr, ang, hin, hdisj⟩
  have hin' : ∀ i, sq (ctr i) (ang i) 1 ⊆ rectangle a b := by
    intro i
    simpa only [UnitSquarePacking.unitSq_eq_setOf, sq, coord, rectangle] using hin i
  have hdisj' : ∀ i j, i ≠ j →
      Disjoint (sqInt (ctr i) (ang i) 1) (sqInt (ctr j) (ang j) 1) := by
    intro i j hij
    simpa only [UnitSquarePacking.interior_unitSq, sqInt, coord] using hdisj hij
  rcases Nat.eq_zero_or_pos n with rfl | hn
  · simp at htot
  have hab := (sq_subset_rectangle_iff a b _ _).mp (hin' ⟨0, hn⟩)
  have hw := one_le_wid (ang ⟨0, hn⟩)
  have ha0 : 0 < a := by linarith [hab.1, hab.2.1]
  have hb0 : 0 < b := by linarith [hab.2.2.1, hab.2.2.2]
  set t : ℝ := max (a / A) (b / B) with ht
  have ht0 : 0 < t := lt_of_lt_of_le (div_pos ha0 hA) (le_max_left _ _)
  have ht1 : t < 1 := max_lt ((div_lt_one hA).mpr ha) ((div_lt_one hB).mpr hb)
  set k : ℝ := 1 / t with hkdef
  have hk : 1 < k := (one_lt_div ht0).mpr ht1
  have hk0 : 0 < k := by linarith
  have hka : k * a ≤ A := by
    have h := (div_le_iff₀ hA).mp (le_max_left (a / A) (b / B))
    rw [hkdef, one_div, ← div_eq_inv_mul]
    exact (div_le_iff₀ ht0).mpr (by simpa only [ht, mul_comm] using h)
  have hkb : k * b ≤ B := by
    have h := (div_le_iff₀ hB).mp (le_max_right (a / A) (b / B))
    rw [hkdef, one_div, ← div_eq_inv_mul]
    exact (div_le_iff₀ ht0).mpr (by simpa only [ht, mul_comm] using h)
  have h := packing_le_measure μ (rectangle A B) hcover n k hk
    (fun i => (k * (ctr i).1, k * (ctr i).2)) ang ?_ ?_
  · exact absurd h (not_le.mpr htot)
  · intro i q hq
    rw [mem_sq_scale_iff hk0] at hq
    obtain ⟨⟨h1, h2⟩, h3, h4⟩ := hin' i hq
    have e1 : q.1 = k * (q.1 / k) := by field_simp
    have e2 : q.2 = k * (q.2 / k) := by field_simp
    refine ⟨⟨?_, ?_⟩, ?_, ?_⟩
    · rw [e1]; positivity
    · rw [e1]; exact (mul_le_mul_of_nonneg_left h2 hk0.le).trans hka
    · rw [e2]; positivity
    · rw [e2]; exact (mul_le_mul_of_nonneg_left h4 hk0.le).trans hkb
  · intro i j hij
    rw [Set.disjoint_left]
    intro q hqi hqj
    rw [mem_sqInt_scale_iff hk0] at hqi hqj
    exact Set.disjoint_left.mp (hdisj' i j hij) hqi hqj

end RectFam
end SquarePacking
