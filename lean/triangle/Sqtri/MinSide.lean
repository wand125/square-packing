import Sqtri.Geom

/-!
# Packings in the triangle and the lower-bound argument

* `PacksTri n s` — `n` closed unit squares (any centres, any angles) lie in `tri s` and have
  pairwise disjoint interiors.
* `minSideTri n = sInf {s | PacksTri n s}` — the side of the smallest equilateral triangle that
  holds `n` unit squares.
* `le_of_unavoidable` — a weighted set of total weight `< n` that meets every closed unit square
  in `tri v` with weight `≥ 1` shows `v ≤ s` for every `s` with `PacksTri n s`.

  If `s < v`, scaling the whole picture by `μ = v/s > 1` turns the packing into `n` squares of
  side `μ` in `tri v` with disjoint interiors.  `packing_le_weight` then gives `n ≤ W < n`.
-/

namespace SquarePacking.Tri

open SquarePacking
open scoped Classical

def PacksTri (n : ℕ) (s : ℝ) : Prop :=
  ∃ (ctr : Fin n → ℝ × ℝ) (ang : Fin n → ℝ), (∀ i, sq (ctr i) (ang i) 1 ⊆ tri s) ∧
    ∀ i j, i ≠ j → Disjoint (sqInt (ctr i) (ang i) 1) (sqInt (ctr j) (ang j) 1)

noncomputable def minSideTri (n : ℕ) : ℝ := sInf {s | PacksTri n s}

lemma coord_scale (c : ℝ × ℝ) (θ μ : ℝ) (hμ : μ ≠ 0) (p : ℝ × ℝ) :
    coord (μ * c.1, μ * c.2) θ p = (μ * (coord c θ (p.1 / μ, p.2 / μ)).1,
      μ * (coord c θ (p.1 / μ, p.2 / μ)).2) := by
  simp only [coord, Prod.mk.injEq]
  constructor <;> field_simp

lemma mem_sq_scale {c : ℝ × ℝ} {θ μ : ℝ} (hμ : 0 < μ) {p : ℝ × ℝ}
    (hp : p ∈ sq (μ * c.1, μ * c.2) θ μ) : (p.1 / μ, p.2 / μ) ∈ sq c θ 1 := by
  obtain ⟨h1, h2⟩ := hp
  rw [coord_scale c θ μ hμ.ne'] at h1 h2
  simp only [abs_mul, abs_of_pos hμ] at h1 h2
  exact ⟨by nlinarith [abs_nonneg (coord c θ (p.1 / μ, p.2 / μ)).1],
    by nlinarith [abs_nonneg (coord c θ (p.1 / μ, p.2 / μ)).2]⟩

lemma mem_sqInt_scale {c : ℝ × ℝ} {θ μ : ℝ} (hμ : 0 < μ) {p : ℝ × ℝ}
    (hp : p ∈ sqInt (μ * c.1, μ * c.2) θ μ) : (p.1 / μ, p.2 / μ) ∈ sqInt c θ 1 := by
  obtain ⟨h1, h2⟩ := hp
  rw [coord_scale c θ μ hμ.ne'] at h1 h2
  simp only [abs_mul, abs_of_pos hμ] at h1 h2
  exact ⟨by nlinarith [abs_nonneg (coord c θ (p.1 / μ, p.2 / μ)).1],
    by nlinarith [abs_nonneg (coord c θ (p.1 / μ, p.2 / μ)).2]⟩

lemma tri_scale {s μ : ℝ} (hμ : 0 < μ) {p : ℝ × ℝ} (hp : (p.1 / μ, p.2 / μ) ∈ tri s) :
    p ∈ tri (μ * s) := by
  obtain ⟨h1, h2, h3⟩ := hp
  simp only at h1 h2 h3
  refine ⟨?_, ?_, ?_⟩
  · have := mul_nonneg hμ.le h1; rwa [mul_div_cancel₀ _ hμ.ne'] at this
  · have := mul_nonneg hμ.le h2
    have e : μ * (Real.sqrt 3 * (p.1 / μ) - p.2 / μ) = Real.sqrt 3 * p.1 - p.2 := by
      field_simp
    linarith
  · have := mul_nonneg hμ.le h3
    have e : μ * (Real.sqrt 3 * (s - p.1 / μ) - p.2 / μ) = Real.sqrt 3 * (μ * s - p.1) - p.2 := by
      field_simp
    linarith

lemma tri_x_bounds {s : ℝ} {p : ℝ × ℝ} (hp : p ∈ tri s) : 0 ≤ p.1 ∧ p.1 ≤ s := by
  obtain ⟨h1, h2, h3⟩ := hp
  have s3 : 0 < Real.sqrt 3 := Real.sqrt_pos.mpr (by norm_num)
  constructor
  · by_contra h; push Not at h; nlinarith
  · by_contra h; push Not at h; nlinarith

/-- A unit square fits only in a triangle of positive side. -/
lemma side_pos_of_sq {s : ℝ} {c : ℝ × ℝ} {θ : ℝ} (h : sq c θ 1 ⊆ tri s) : 0 < s := by
  have hm := fun (x y : ℝ) (hx : |x| ≤ 1 / 2) (hy : |y| ≤ 1 / 2) =>
    tri_x_bounds (h (mem_sq_offset c θ x y hx hy))
  have a := hm (1/2) 0 (by norm_num [abs_of_pos]) (by norm_num)
  have b := hm (-1/2) 0 (by norm_num [abs_of_neg]) (by norm_num)
  have c' := hm 0 (1/2) (by norm_num) (by norm_num [abs_of_pos])
  have d := hm 0 (-1/2) (by norm_num) (by norm_num [abs_of_neg])
  simp only at a b c' d
  have hcs := Real.cos_sq_add_sin_sq θ
  by_contra hs
  push Not at hs
  have hc0 : Real.cos θ = 0 := by nlinarith
  have hs0 : Real.sin θ = 0 := by nlinarith
  rw [hc0, hs0] at hcs; norm_num at hcs

theorem le_of_unavoidable (n : ℕ) (v : ℝ) (A : Finset (ℝ × ℝ)) (w : ℝ × ℝ → ℝ)
    (hw : ∀ a ∈ A, 0 ≤ w a)
    (hcover : ∀ (c : ℝ × ℝ) (θ : ℝ), sq c θ 1 ⊆ tri v →
        1 ≤ ∑ a ∈ A.filter (fun a => a ∈ sq c θ 1), w a)
    (hW : ∑ a ∈ A, w a < n) (s : ℝ) (hs : PacksTri n s) : v ≤ s := by
  obtain ⟨ctr, ang, hin, hdisj⟩ := hs
  have hW0 : 0 ≤ ∑ a ∈ A, w a := Finset.sum_nonneg hw
  have hn : 0 < n := by
    rcases Nat.eq_zero_or_pos n with h | h
    · subst h; simp at hW; linarith
    · exact h
  have hs0 : 0 < s := side_pos_of_sq (hin ⟨0, hn⟩)
  by_contra hlt
  push Not at hlt
  set μ := v / s with hμdef
  have hμ : 1 < μ := by rw [hμdef, lt_div_iff₀ hs0]; linarith
  have hμ0 : 0 < μ := by linarith
  have hμs : μ * s = v := by rw [hμdef]; field_simp
  have key := packing_le_weight A w hw (tri v) hcover n μ hμ
    (fun i => (μ * (ctr i).1, μ * (ctr i).2)) ang
    (fun i p hp => by
      have := hin i (mem_sq_scale hμ0 hp)
      rw [← hμs]; exact tri_scale hμ0 this)
    (fun i j hij => by
      rw [Set.disjoint_left]
      intro p hpi hpj
      exact Set.disjoint_left.mp (hdisj i j hij) (mem_sqInt_scale hμ0 hpi) (mem_sqInt_scale hμ0 hpj))
  linarith

theorem minSideTri_eq (n : ℕ) (v : ℝ) (hup : PacksTri n v) (hlow : ∀ s, PacksTri n s → v ≤ s) :
    minSideTri n = v :=
  IsLeast.csInf_eq ⟨hup, hlow⟩

lemma sum_range_wtR (pts : List Pt) :
    ∑ e ∈ Finset.range pts.length, wtR pts e = (((pts.map fun p => p.2.2).sum : ℚ) : ℝ) := by
  induction pts with
  | nil => simp
  | cons a l ih =>
    rw [List.length_cons, Finset.sum_range_succ']
    simp only [wtR, ptAt, List.getD_cons_succ, List.getD_cons_zero] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.sum_cons]
    ring

/-- The lower bound from a checked certificate. -/
theorem le_of_checks (n : ℕ) (L yTop : Q3) (pts : List Pt)
    (hy : yTop.val = L.val * Real.sqrt 3 / 2) (hW : weightsOk pts = true)
    (hsum : (pts.map fun p => p.2.2).sum < n) (t0 t1 t2 : Tree)
    (h0 : check L pts Q3.zero L Q3.zero yTop B0 B1 [] t0 = true)
    (h1 : check L pts Q3.zero L Q3.zero yTop B1 B2 [] t1 = true)
    (h2 : check L pts Q3.zero L Q3.zero yTop B2 B3 [] t2 = true) :
    ∀ s, PacksTri n s → L.val ≤ s := by
  classical
  apply le_of_unavoidable n L.val (coverA (Finset.range pts.length) (ptR pts))
    (coverW (Finset.range pts.length) (ptR pts) (wtR pts))
  · intro a _
    unfold coverW
    exact Finset.sum_nonneg fun i _ => weight_nonneg hW i
  · exact unavoidable_of_checks L yTop pts hy hW t0 t1 t2 h0 h1 h2
  · rw [sum_coverA]
    rw [sum_range_wtR]; exact_mod_cast hsum

end SquarePacking.Tri
