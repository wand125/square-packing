import ClosedForm.StatementCore

namespace ClosedForm

/-- Only the small endpoint/slope projections are evaluated; β is never evaluated. -/
private lemma interval_bounds (i : Fin 34) :
    0 ≤ ((Data.intervals i).d0 : ℝ) ∧
    ((Data.intervals i).d0 : ℝ) < (Data.intervals i).d1 ∧
    ((Data.intervals i).alpha : ℝ) ≤ 2 := by
  fin_cases i <;>
    norm_num [Data.intervals,
      Data.interval1, Data.interval2, Data.interval3, Data.interval4, Data.interval5,
      Data.interval6, Data.interval7, Data.interval8, Data.interval9, Data.interval10,
      Data.interval11, Data.interval12, Data.interval13, Data.interval14, Data.interval15,
      Data.interval16, Data.interval17, Data.interval18, Data.interval19, Data.interval20,
      Data.interval21, Data.interval22, Data.interval23, Data.interval24, Data.interval25,
      Data.interval26, Data.interval27, Data.interval28, Data.interval29, Data.interval30,
      Data.interval31, Data.interval32, Data.interval33, Data.interval34]

/-- Symbolic monotonicity on the increasing side of the quadratic. -/
lemma quadratic_strictMono (k α β : ℝ) :
    StrictMonoOn (fun δ : ℝ => (k + δ) ^ 2 - 4 * (α * δ + β))
      (Set.Ici (2 * α - k)) := by
  intro x hx y hy hxy
  have hp : 0 < (y - x) * ((k + y - 2 * α) + (k + x - 2 * α)) :=
    mul_pos (sub_pos.mpr hxy) (by simp only [Set.mem_Ici] at hx hy; linarith)
  nlinarith

/-- Strict eligibility guarantees a genuine increasing-side root, even without
any sign assumption on the symbolic intercept β. -/
lemma capped_root_le (k α β n d0 d1 L : ℝ)
    (hends : d0 < d1) (hslope : 2 * α ≤ k + d0)
    (helig : k + d0 < 2 * α + Real.sqrt (4 * α ^ 2 + n + 4 * β - 4 * α * k))
    (hbound : ∀ δ, d0 < δ → δ ≤ d1 →
      (k + δ) ^ 2 - 4 * (α * δ + β) < n → k + δ ≤ L) :
    min (2 * α + Real.sqrt (4 * α ^ 2 + n + 4 * β - 4 * α * k)) (k + d1) ≤ L := by
  let D := 4 * α ^ 2 + n + 4 * β - 4 * α * k
  have hsqrt : 0 < Real.sqrt D := by dsimp [D]; linarith
  have hD : 0 ≤ D := (Real.sqrt_pos.mp hsqrt).le
  have hsq := Real.sq_sqrt hD
  have hroot : (2 * α + Real.sqrt D) ^ 2 -
      4 * (α * ((2 * α + Real.sqrt D) - k) + β) = n := by
    dsimp [D] at hsq ⊢
    nlinarith
  by_contra h
  have hL : L < min (2 * α + Real.sqrt D) (k + d1) := lt_of_not_ge h
  have hleft : k + d0 < min (2 * α + Real.sqrt D) (k + d1) :=
    lt_min helig (by linarith)
  obtain ⟨x, hx, hxc⟩ := exists_between (max_lt hleft hL)
  have hx0 : k + d0 < x := (le_max_left _ _).trans_lt hx
  have hxL : L < x := (le_max_right _ _).trans_lt hx
  have hxr : x < 2 * α + Real.sqrt D := hxc.trans_le (min_le_left _ _)
  have hxd : x < k + d1 := hxc.trans_le (min_le_right _ _)
  have hprod : 0 < ((2 * α + Real.sqrt D) - x) *
      ((2 * α + Real.sqrt D) + x - 4 * α) :=
    mul_pos (by linarith) (by linarith)
  have hmass : (k + (x - k)) ^ 2 - 4 * (α * (x - k) + β) < n := by
    nlinarith [hroot]
  have hb := hbound (x - k) (by linarith) (by linarith) hmass
  linarith

/-- §5: the finite maximum of capped roots follows from the strict mass test.
The sole area-bound dependency is the separately stated `sqrt_le_minSide`.
All intercepts remain symbolic throughout the root argument. -/
theorem a_le_of_bound (N : ℕ) (hN : 49 ≤ N)
    (hbound : ∀ i : Fin 34, ∀ δ ∈ I i,
      ((baseK N : ℝ) + δ) ^ 2 - 4 * certifiedLine i δ < N →
        (baseK N : ℝ) + δ ≤ UnitSquarePacking.minSide N) :
    a N ≤ UnitSquarePacking.minSide N := by
  have hkfloor : (baseK N : ℝ) ≤ Real.sqrt (N : ℝ) :=
    Nat.floor_le (Real.sqrt_nonneg _)
  have hbase : (baseK N : ℝ) ≤ UnitSquarePacking.minSide N :=
    hkfloor.trans (sqrt_le_minSide N (by omega))
  have hk : (7 : ℝ) ≤ baseK N := by
    have hsqrt : (7 : ℝ) ≤ Real.sqrt (N : ℝ) := by
      rw [Real.le_sqrt (by norm_num) (by positivity)]
      exact_mod_cast hN
    have hn : 7 ≤ baseK N := (Nat.le_floor_iff (Real.sqrt_nonneg _)).mpr hsqrt
    exact_mod_cast hn
  classical
  unfold a
  split
  · exact hbase
  · split
    · rename_i hne
      apply Finset.sup'_le
      intro i hi
      have helig : (baseK N : ℝ) + (Data.intervals i).d0 < intervalRoot N i :=
        (Finset.mem_filter.mp hi).2
      obtain ⟨hd0, hends, halpha⟩ := interval_bounds i
      apply capped_root_le (baseK N) (Data.intervals i).alpha (Data.intervals i).beta
        N (Data.intervals i).d0 (Data.intervals i).d1 _ hends (by linarith) helig
      intro δ hleft hright hmass
      apply hbound i δ ?_ hmass
      dsimp only [I]
      split <;> exact ⟨by linarith, hright⟩
    · exact hbase

end ClosedForm
