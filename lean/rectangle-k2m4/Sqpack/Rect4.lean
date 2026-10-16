import Sqpack.RectFam
import Sqpack.ValidSplit9

/-! The rectangle version of the four-hole bound, conditional on the upstream box-9 validity. -/
open MeasureTheory Finset
open scoped ENNReal
namespace SquarePacking
namespace Rect4
open BentzFam Bentz4 RectFam

theorem hrect_false (m n : ℕ) :
    Hrect fam4 false m n = 42732189097180 + n * 7630891120660 + m * 3569108879340 := by
  have h00 : H00 3 (tabW famTab) = 42732189097180 := by decide +kernel
  have h01 : H01 3 (tabW famTab) = 7630891120660 := by decide +kernel
  have h10 : H10 3 (tabW famTab) = 3569108879340 := by decide +kernel
  have h11 : H11 3 (tabW famTab) = 0 := by decide +kernel
  simp only [Hrect, fam4, Fam.layer, Bool.false_eq_true, if_false, h00, h01, h10, h11]
  ring

theorem hrect_true (m n : ℕ) : Hrect fam4 true m n = 12406391400 := by
  have h00 : H00 3 (tabW famTab2) = 12406391400 := by decide +kernel
  have h01 : H01 3 (tabW famTab2) = 0 := by decide +kernel
  have h10 : H10 3 (tabW famTab2) = 0 := by decide +kernel
  have h11 : H11 3 (tabW famTab2) = 0 := by decide +kernel
  simp only [Hrect, fam4, Fam.layer, if_true, h00, h01, h10, h11]
  ring

/-- Exact total: the deficit is independent of both side lengths. -/
theorem famRect_total4 (m n : ℕ) :
    (famRect fam4 (m + 7) (n + 7)).total =
      ((m + 7 : ℕ) : ℝ) * ((n + 7 : ℕ) : ℝ) - 4 * (214770225571 / 200000000000) := by
  have h := famRect_total fam4 m n
  rw [show m + 2 * fam4.R + 1 = m + 7 from rfl,
    show n + 2 * fam4.R + 1 = n + 7 from rfl,
    hrect_false, hrect_false, hrect_true, hrect_true] at h
  rw [h]
  simp only [fam4]
  push_cast
  ring

theorem valid_rect_of_valid9 (h : Valid9) {A B : ℕ} (hA : 8 ≤ A) (hB : 8 ≤ B)
    (c : ℝ × ℝ) (θ : ℝ) (hS : sq c θ 1 ⊆ rectangle A B) :
    1 ≤ (famRect fam4 A B).measure (sq c θ 1) := by
  obtain ⟨v, hv, hm⟩ := mass_shift_rect fam4 fam4_out (by decide) hA hB c θ hS
  have h9 := h (c - v) θ hv
  rw [box9Cover_measure, MixedCover.measure_apply _ (famCover_nonneg fam4 9)
    (measurableSet_sq _ _ _)] at h9
  have hA' : (8 : ℝ) ≤ A := by exact_mod_cast hA
  have hB' : (8 : ℝ) ≤ B := by exact_mod_cast hB
  rw [MixedCover.measure_apply _ (famRect_nonneg fam4
    (by dsimp [fam4]; linarith) (by dsimp [fam4]; linarith)) (measurableSet_sq _ _ _), hm]
  exact h9

/-- No packing of `A*B - 4` unit squares fits when both dimensions are strictly reduced. -/
theorem rect4_of_valid9 (h : Valid9) :
    ∀ A B : ℕ, 8 ≤ A → 8 ≤ B → ∀ a b : ℝ, a < A → b < B →
      ¬ UnitSquarePacking.Conjectures.PacksRect (A * B - 4) a b := by
  intro A B hA hB a b ha hb
  have hA' : (8 : ℝ) ≤ A := by exact_mod_cast hA
  have hB' : (8 : ℝ) ≤ B := by exact_mod_cast hB
  apply not_packsRect_of_measure A B (by linarith) (by linarith)
    (famRect fam4 A B).measure (valid_rect_of_valid9 h hA hB) (A * B - 4) ?_ ha hb
  have h4 : 4 < A * B := by nlinarith
  have htot : (famRect fam4 A B).total < (A * B - 4 : ℕ) := by
    obtain ⟨m, rfl⟩ : ∃ m, A = m + 7 := ⟨A - 7, by omega⟩
    obtain ⟨n, rfl⟩ : ∃ n, B = n + 7 := ⟨B - 7, by omega⟩
    rw [famRect_total4, Nat.cast_sub h4.le]
    push_cast
    norm_num
  calc
    (famRect fam4 A B).measure (rectangle A B) ≤ (famRect fam4 A B).measure Set.univ :=
      measure_mono (Set.subset_univ _)
    _ ≤ ENNReal.ofReal (famRect fam4 A B).total :=
      (famRect fam4 A B).measure_univ_le (famRect_nonneg fam4
        (by dsimp [fam4]; linarith) (by dsimp [fam4]; linarith))
    _ < ENNReal.ofReal ((A * B - 4 : ℕ) : ℝ) :=
      (ENNReal.ofReal_lt_ofReal_iff
        (by exact_mod_cast Nat.sub_pos_of_lt h4)).mpr htot
    _ = ((A * B - 4 : ℕ) : ℝ≥0∞) := ENNReal.ofReal_natCast _

/-- The same rectangle bound from the tilted-domain hypothesis; the axis lemma is proved upstream. -/
theorem rect4_of_validTilt9 (ht : ValidTilt9) :
    ∀ A B : ℕ, 8 ≤ A → 8 ≤ B → ∀ a b : ℝ, a < A → b < B →
      ¬ UnitSquarePacking.Conjectures.PacksRect (A * B - 4) a b :=
  rect4_of_valid9 (valid9_of_tilt_axis ht validAxis9)

end Rect4
end SquarePacking
