import ClosedForm.CanonicalBridge
import ClosedForm.ReflectionBridge
import ClosedForm.CornerBridge
import ClosedForm.Mass

namespace ClosedForm
open MeasureTheory

lemma StructuralCheck.valid_iff (s : Segment) : StructuralCheck.valid s = true ↔ s.Valid := by
  simp [StructuralCheck.valid, Segment.Valid]
  tauto

lemma StructuralCheck.familyValid_iff (f : Family) :
    StructuralCheck.familyValid f = true ↔ f.Valid := by
  simp [StructuralCheck.familyValid, Family.Valid, List.all_eq_true, StructuralCheck.valid_iff,
    and_assoc]
  aesop

lemma periods_valid (f : Family) (hf : f.Valid) (n : ℕ) :
    ∀ s ∈ periods f n, s.Valid := by
  intro s hs
  obtain ⟨j, hj, hs⟩ := List.mem_flatMap.mp hs
  obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
  have h := profile_valid f hf t ht
  simpa [Segment.Valid, Segment.shift] using h

lemma transpose_valid (s : Segment) (hs : s.Valid) : s.transpose.Valid := by
  simp only [Segment.Valid, Segment.transpose] at *
  tauto

lemma reflectProfile_valid (s : Segment) (hs : s.Valid) :
    (StructuralCheck.reflectProfile s).Valid := by
  by_cases hy : s.ay = s.yb
  · simpa [StructuralCheck.reflectProfile, hy, Segment.Valid] using hs
  · simp [StructuralCheck.reflectProfile, hy, Segment.Valid, hs.1]

/-- Boolean assembly is independent of the concrete family and its rational sizes. -/
theorem structural_of_dec (f fr : Family) (h : StructuralDec f fr = true) :
    Structural f fr := by
  simp only [StructuralDec, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true,
    StructuralCheck.familyValid_iff, beq_iff_eq] at h
  obtain ⟨h, hreflect⟩ := h
  obtain ⟨h, hT⟩ := h
  obtain ⟨h, hF⟩ := h
  obtain ⟨h, hp⟩ := h
  obtain ⟨h, hv⟩ := h
  obtain ⟨h, hct⟩ := h
  obtain ⟨h, hcf⟩ := h
  obtain ⟨h, hcvalid⟩ := h
  obtain ⟨h, hmass⟩ := h
  obtain ⟨h, hvgrid⟩ := h
  obtain ⟨h, hgrid⟩ := h
  obtain ⟨h, hr⟩ := h
  obtain ⟨h, hstd⟩ := h
  obtain ⟨h, hfr⟩ := h
  have hf := h
  have hcv : ∀ s ∈ cornerF f ++ cornerT f, s.Valid := by
    intro s hs
    exact (StructuralCheck.valid_iff s).mp (hcvalid s hs)
  have hpv := profile_valid f hf
  have hper := periods_valid f hf 7
  have htrans : ∀ s ∈ (periods f 7).map Segment.transpose, s.Valid := by
    intro s hs
    obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
    exact transpose_valid t (hper t ht)
  have hcfv : ∀ s ∈ cornerF f, s.Valid := fun s hs => hcv s (List.mem_append_left _ hs)
  have hctv : ∀ s ∈ cornerT f, s.Valid := fun s hs => hcv s (List.mem_append_right _ hs)
  have hrfv : ∀ s ∈ (profile f).map StructuralCheck.reflectProfile, s.Valid := by
    intro s hs
    obtain ⟨t, ht, rfl⟩ := List.mem_map.mp hs
    exact reflectProfile_valid t (hpv t ht)
  rcases hstd with ⟨hua, hu, hd0, hd1⟩
  rcases hr with ⟨hrF, hrT, hrV, hrUA, hrU, hrd0, hrd1⟩
  refine ⟨hf, hfr, hua, hu, hd0, hd1, hrF, hrT, hrV, hrUA, hrU, hrd0, hrd1,
    hmass, hcv, hcf, hct, hv, ?_, ?_, ?_⟩
  · intro s hs
    exact (hp s hs).1
  · intro δ hδ
    constructor
    · exact (subtractRows_measure _ _ (fun s hs => (hf.2.1 s (List.mem_append_left _ hs)).1)
        (fun s hs => (htrans s hs).1) (fun s hs => (hcfv s hs).1) 0 0).symm
    · exact (subtractRows_measure _ _ (fun s hs => (hf.2.1 s (List.mem_append_right _ hs)).1)
        (fun s hs => (hper s hs).1) (fun s hs => (hctv s hs).1) δ 0).symm
  · apply periodic_reflection (profile f) (fun s hs => (hpv s hs).2.1)
    intro dx
    exact StructuralCheck.canonical_rowsMeasure _ _ hpv hrfv hreflect dx 0

#print axioms structural_of_dec
end ClosedForm
