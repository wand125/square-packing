import ClosedForm.PublishedDefs
import ClosedForm.Area
import ClosedForm.Mass
import ClosedForm.Reduction
import ClosedForm.Data.Families
import ClosedForm.Data.Intervals

namespace ClosedForm

/-- Local-build provider for the already cloud-certified structure. The separate
`PublishedStructure.lean` supplies this same declaration for the cloud audit;
review note 9 keeps all 34 certificates outside this machine's default build. -/
theorem published_structure (i : Fin 34) :
    Structural (family i) (familyRight i) ∧
    (family i).d0 = (Data.intervals i).d0 ∧ (family i).d1 = (Data.intervals i).d1 := by
  sorry

/-- Local-build provider only. `PublishedSaving.lean` supplies the proved declaration
from the split integer endpoint certificates. Review note 9 keeps the default
build at I01; `FinalAudit.lean` uses the two proved cloud providers instead. -/
theorem published_saving (i : Fin 34) :
    ∀ δ ∈ I i, certifiedLine i δ ≤ saving (family i) δ := by
  sorry

/-- Published-family version: structural verification is the separate obligation above. -/
theorem covers7_of_local (i : Fin 34) (δ : ℝ) (hδ : δ ∈ I i) :
    LocalCovers (family i) (familyRight i) δ → Covers7 (family i) δ := by
  obtain ⟨hs, h0, h1⟩ := published_structure i
  have hclosed : δ ∈ Set.Icc ((family i).d0 : ℝ) ((family i).d1 : ℝ) := by
    rw [h0, h1]
    dsimp [I] at hδ
    split_ifs at hδ
    · exact ⟨hδ.1.le, hδ.2⟩
    · exact hδ
  have hpos : 0 < δ := by
    have hends : (Data.intervals i).openLeft = true ∨ 0 < (Data.intervals i).d0 := by
      fin_cases i <;> norm_num [Data.intervals,
        Data.interval1, Data.interval2, Data.interval3, Data.interval4, Data.interval5, Data.interval6, Data.interval7, Data.interval8, Data.interval9, Data.interval10, Data.interval11, Data.interval12, Data.interval13, Data.interval14, Data.interval15, Data.interval16, Data.interval17, Data.interval18, Data.interval19, Data.interval20, Data.interval21, Data.interval22, Data.interval23, Data.interval24, Data.interval25, Data.interval26, Data.interval27, Data.interval28, Data.interval29, Data.interval30, Data.interval31, Data.interval32, Data.interval33, Data.interval34]
    rcases hends with hopen | hd0
    · have hnonneg : (0 : ℝ) ≤ (family i).d0 := by exact_mod_cast hs.2.2.2.2.1
      simp only [I, hopen, ↓reduceIte, Set.mem_Ioc] at hδ
      rw [h0] at hnonneg
      exact hnonneg.trans_lt hδ.1
    · have hd0' : (0 : ℝ) < (Data.intervals i).d0 := by exact_mod_cast hd0
      rw [h0] at hclosed
      exact hd0'.trans_le hclosed.1
  exact covers7_of_local_structural _ _ δ hs hclosed hpos

/-- The coverage consequence of square-mass transport by an inequality. -/
theorem covers_k_of_covers7_structural (f fr : Family) (hs : Structural f fr)
    (δ : ℝ) (hδ : δ ∈ Set.Icc (f.d0 : ℝ) (f.d1 : ℝ)) :
    Covers7 f δ → ∀ k : ℕ, 7 ≤ k → Covers f k δ := by
  intro hc k hk z θ hQ
  obtain ⟨z', θ', hQ', hm⟩ := unitSq_mass_transport_structural f fr hs δ hδ k hk z θ hQ
  exact le_trans (hc z' θ' (by simpa using hQ')) hm

theorem covers_k_of_covers7 (i : Fin 34) (δ : ℝ) (hδ : δ ∈ I i) :
    Covers7 (family i) δ → ∀ k : ℕ, 7 ≤ k → Covers (family i) k δ := by
  obtain ⟨hs, h0, h1⟩ := published_structure i
  apply covers_k_of_covers7_structural (family i) (familyRight i) hs δ
  rw [h0, h1]
  dsimp [I] at hδ
  split_ifs at hδ
  · exact ⟨hδ.1.le, hδ.2⟩
  · exact hδ

/-- SPEC §1.3; includes the terminal phase-zero mass. -/
theorem total_mass (i : Fin 34) (k : ℕ) (hk : 7 ≤ k) (δ : ℝ) (hδ : δ ∈ I i) :
    globalMeasure (family i) k δ (UnitSquarePacking.container ((k : ℝ) + δ)) =
      ENNReal.ofReal (((k : ℝ) + δ) ^ 2 - 4 * saving (family i) δ) := by
  obtain ⟨hs, h0, h1⟩ := published_structure i
  apply total_mass_structural (family i) (familyRight i) hs k hk δ
  rw [h0, h1]
  dsimp [I] at hδ
  split_ifs at hδ
  · exact ⟨hδ.1.le, hδ.2⟩
  · exact hδ

noncomputable def baseK (N : ℕ) : ℕ := ⌊Real.sqrt (N : ℝ)⌋₊

noncomputable def intervalRoot (N : ℕ) (i : Fin 34) : ℝ :=
  let α : ℝ := (Data.intervals i).alpha
  let β : ℝ := (Data.intervals i).beta
  2 * α + Real.sqrt (4 * α ^ 2 + N + 4 * β - 4 * α * baseK N)

noncomputable def eligible (N : ℕ) : Finset (Fin 34) := by
  classical
  exact Finset.univ.filter fun i => (baseK N : ℝ) + (Data.intervals i).d0 < intervalRoot N i

/-- Supremum endpoint: equality at a root is included in the bound even though the
mass test is strict. No exclusion is made at an open left endpoint of the interval. -/
noncomputable def branchValue (N : ℕ) (i : Fin 34) : ℝ :=
  min (intervalRoot N i) ((baseK N : ℝ) + (Data.intervals i).d1)

/-- SPEC §1.1. Squares use the area bound. The empty-maximum fallback is k,
so the definition is total also for N < 49, where no claim is made. -/
noncomputable def a (N : ℕ) : ℝ := by
  classical
  exact if N = baseK N ^ 2 then (baseK N : ℝ)
    else if h : (eligible N).Nonempty then (eligible N).sup' h (branchValue N)
    else (baseK N : ℝ)

/-- Area lower bound: not found in the available upstream library. -/
theorem sqrt_le_minSide (N : ℕ) (hN : 1 ≤ N) :
    Real.sqrt (N : ℝ) ≤ UnitSquarePacking.minSide N :=
  sqrt_le_minSide_area N hN

/-- The finite JSON window and periodic extension coincide on the checked window. -/
theorem finite_periodic_window (i : Fin 34) (δ : ℝ) (hδ : δ ∈ I i) :
    (localMeasure (family i) δ).restrict (UnitSquarePacking.container (24 / 5)) =
      (periodicLocalMeasure (family i) δ).restrict
        (UnitSquarePacking.container (24 / 5)) := by
  obtain ⟨hs, h0, h1⟩ := published_structure i
  apply finite_periodic_window_structural (family i) (familyRight i) hs δ
  rw [h0, h1]
  dsimp [I] at hδ
  split_ifs at hδ
  · exact ⟨hδ.1.le, hδ.2⟩
  · exact hδ

/-- Record upper-container constraints are inactive, including shifted right coordinates. -/
theorem record_upper_inactive (i : Fin 34) (r : Region) (z : Point)
    (hz : z ∈ regionSet (family i) r) (u : ℝ)
    (hu : u ∈ Set.Icc (-13 / 32 : ℝ) (7 / 16)) (ha : Admissible z u) :
    z.1 ≤ 20 - halfWidth u ∧ z.2 ≤ 20 - halfWidth u := by
  clear hu ha
  exact record_upper_inactive_of_d1 (family i)
    (published_structure i).1.2.2.2.2.2.1 r z hz u

end ClosedForm
