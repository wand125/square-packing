import Mathlib

/-!
# Definitions and lemmas copied from evand/square-packing

Copied verbatim (apart from this header and the omission of unused declarations) from
<https://github.com/evand/square-packing>, commit `6e1223c`, directory `s12/lean/Sqpack`:

* `Basic.lean`: `coord`, `sq`, `sqInt`, `unit_subset_interior`, `card_filter_le_one`,
  `packing_le_weight`, `sq_scale`, `sqInt_scale`;
* `ZeroMargin.lean`: `mem_sq_offset`, `gc`, `gval`, `cos_two_arctan`, `sin_two_arctan`,
  `mem_sq_iff_gval`;
* `D4.lean`: `sq_add_pi_div_two`;
* `Cover.lean`: `coverA`, `coverW`, `sum_filter_coverA`, `sum_coverA`.

MIT License, Copyright (c) 2026 Evan Daniel (see `UPSTREAM-LICENSE.txt`).
-/

open Finset
open scoped Classical

namespace SquarePacking

/-- Rotated coordinates of `p` relative to centre `c` and angle `θ`. -/
noncomputable def coord (c : ℝ × ℝ) (θ : ℝ) (p : ℝ × ℝ) : ℝ × ℝ :=
  ((p.1 - c.1) * Real.cos θ + (p.2 - c.2) * Real.sin θ,
   (-(p.1 - c.1)) * Real.sin θ + (p.2 - c.2) * Real.cos θ)

/-- The closed square of side `L`, centre `c`, angle `θ`. -/
def sq (c : ℝ × ℝ) (θ L : ℝ) : Set (ℝ × ℝ) :=
  {p | |(coord c θ p).1| ≤ L/2 ∧ |(coord c θ p).2| ≤ L/2}

/-- The open square (interior) of side `L`, centre `c`, angle `θ`. -/
def sqInt (c : ℝ × ℝ) (θ L : ℝ) : Set (ℝ × ℝ) :=
  {p | |(coord c θ p).1| < L/2 ∧ |(coord c θ p).2| < L/2}

/-- A concentric closed unit square sits in the interior of any concentric square of side
`L > 1`.  This is the step that lets a *closed*-square certificate control a packing. -/
lemma unit_subset_interior {c : ℝ × ℝ} {θ L : ℝ} (hL : 1 < L) :
    sq c θ 1 ⊆ sqInt c θ L := by
  rintro p ⟨h1, h2⟩
  constructor
  · calc |(coord c θ p).1| ≤ 1/2 := h1
      _ < L/2 := by linarith
  · calc |(coord c θ p).2| ≤ 1/2 := h2
      _ < L/2 := by linarith

/-- A point lies in at most one member of a pairwise disjoint family. -/
lemma card_filter_le_one {n : ℕ} (S : Fin n → Set (ℝ × ℝ))
    (hdisj : ∀ i j, i ≠ j → Disjoint (S i) (S j)) (a : ℝ × ℝ) :
    ((univ : Finset (Fin n)).filter (fun i => a ∈ S i)).card ≤ 1 := by
  rw [card_le_one]
  intro i hi j hj
  simp only [mem_filter, mem_univ, true_and] at hi hj
  by_contra hne
  exact (Set.disjoint_left.mp (hdisj i j hne) hi) hj

/-- **Main reduction.**  A weighted unavoidable set of total weight `W` bounds the number of
squares of side `L > 1` that can be packed (disjoint interiors) inside `C`. -/
theorem packing_le_weight
    (A : Finset (ℝ × ℝ)) (w : ℝ × ℝ → ℝ) (hw : ∀ a ∈ A, 0 ≤ w a)
    (C : Set (ℝ × ℝ))
    (hcover : ∀ (c : ℝ × ℝ) (θ : ℝ), sq c θ 1 ⊆ C →
        1 ≤ ∑ a ∈ A.filter (fun a => a ∈ sq c θ 1), w a)
    (n : ℕ) (L : ℝ) (hL : 1 < L) (ctr : Fin n → ℝ × ℝ) (ang : Fin n → ℝ)
    (hin : ∀ i, sq (ctr i) (ang i) L ⊆ C)
    (hdisj : ∀ i j, i ≠ j → Disjoint (sqInt (ctr i) (ang i) L) (sqInt (ctr j) (ang j) L)) :
    (n : ℝ) ≤ ∑ a ∈ A, w a := by
  -- the concentric unit squares are inside C, and inside the (disjoint) interiors
  have hIntSub : ∀ (c : ℝ × ℝ) (θ : ℝ), sqInt c θ L ⊆ sq c θ L := by
    rintro c θ p ⟨h1, h2⟩; exact ⟨le_of_lt h1, le_of_lt h2⟩
  have hU : ∀ i, sq (ctr i) (ang i) 1 ⊆ C := fun i =>
    subset_trans (subset_trans (unit_subset_interior hL) (hIntSub _ _)) (hin i)
  set S : Fin n → Set (ℝ × ℝ) := fun i => sq (ctr i) (ang i) 1 with hSdef
  have hSdisj : ∀ i j, i ≠ j → Disjoint (S i) (S j) := by
    intro i j hij
    exact Set.disjoint_of_subset (unit_subset_interior hL) (unit_subset_interior hL) (hdisj i j hij)
  have key : ∀ i : Fin n, (1:ℝ) ≤ ∑ a ∈ A.filter (fun a => a ∈ S i), w a := fun i =>
    hcover (ctr i) (ang i) (hU i)
  have h1 : (n:ℝ) ≤ ∑ i : Fin n, ∑ a ∈ A.filter (fun a => a ∈ S i), w a := by
    calc (n:ℝ) = ∑ _i : Fin n, (1:ℝ) := by simp
      _ ≤ _ := Finset.sum_le_sum fun i _ => key i
  have h2 : ∑ i : Fin n, ∑ a ∈ A.filter (fun a => a ∈ S i), w a
      = ∑ a ∈ A, ∑ i : Fin n, (if a ∈ S i then w a else 0) := by
    simp only [Finset.sum_filter]; exact Finset.sum_comm
  have h3 : ∀ a ∈ A, ∑ i : Fin n, (if a ∈ S i then w a else 0) ≤ w a := by
    intro a ha
    have hcard : (((univ : Finset (Fin n)).filter (fun i => a ∈ S i)).card : ℝ) ≤ 1 := by
      exact_mod_cast card_filter_le_one S hSdisj a
    have hEq : ∑ i : Fin n, (if a ∈ S i then w a else 0)
        = (((univ : Finset (Fin n)).filter (fun i => a ∈ S i)).card : ℝ) * w a := by
      rw [← Finset.sum_filter, Finset.sum_const, nsmul_eq_mul]
    rw [hEq]; nlinarith [hw a ha]
  have h4 : ∑ a ∈ A, ∑ i : Fin n, (if a ∈ S i then w a else 0) ≤ ∑ a ∈ A, w a :=
    Finset.sum_le_sum h3
  linarith [h1, h2 ▸ h1, h4]

/-- Scaling by `μ > 0` turns a unit square into a square of side `μ`. -/
lemma sq_scale (c : ℝ × ℝ) (θ μ : ℝ) (hμ : 0 < μ) (p : ℝ × ℝ) (hp : p ∈ sq c θ 1) :
    (μ * p.1, μ * p.2) ∈ sq (μ * c.1, μ * c.2) θ μ := by
  obtain ⟨h1, h2⟩ := hp
  have e1 : (coord (μ * c.1, μ * c.2) θ (μ * p.1, μ * p.2)).1 = μ * (coord c θ p).1 := by
    simp only [coord]; ring
  have e2 : (coord (μ * c.1, μ * c.2) θ (μ * p.1, μ * p.2)).2 = μ * (coord c θ p).2 := by
    simp only [coord]; ring
  refine ⟨?_, ?_⟩
  · rw [e1, abs_mul, abs_of_pos hμ]; nlinarith [abs_nonneg (coord c θ p).1]
  · rw [e2, abs_mul, abs_of_pos hμ]; nlinarith [abs_nonneg (coord c θ p).2]

/-- Interiors scale the same way. -/
lemma sqInt_scale (c : ℝ × ℝ) (θ μ : ℝ) (hμ : 0 < μ) (p : ℝ × ℝ) (hp : p ∈ sqInt c θ 1) :
    (μ * p.1, μ * p.2) ∈ sqInt (μ * c.1, μ * c.2) θ μ := by
  obtain ⟨h1, h2⟩ := hp
  have e1 : (coord (μ * c.1, μ * c.2) θ (μ * p.1, μ * p.2)).1 = μ * (coord c θ p).1 := by
    simp only [coord]; ring
  have e2 : (coord (μ * c.1, μ * c.2) θ (μ * p.1, μ * p.2)).2 = μ * (coord c θ p).2 := by
    simp only [coord]; ring
  refine ⟨?_, ?_⟩
  · rw [e1, abs_mul, abs_of_pos hμ]; nlinarith [abs_nonneg (coord c θ p).1]
  · rw [e2, abs_mul, abs_of_pos hμ]; nlinarith [abs_nonneg (coord c θ p).2]

/-- The point at rotated offset `(x,y)` from the centre lies in the closed unit square. -/
lemma mem_sq_offset (c : ℝ × ℝ) (θ x y : ℝ) (hx : |x| ≤ 1 / 2) (hy : |y| ≤ 1 / 2) :
    (c.1 + (x * Real.cos θ - y * Real.sin θ),
     c.2 + (x * Real.sin θ + y * Real.cos θ)) ∈ sq c θ 1 := by
  have hCS : Real.cos θ ^ 2 + Real.sin θ ^ 2 = 1 := Real.cos_sq_add_sin_sq θ
  have h1 : (coord c θ (c.1 + (x * Real.cos θ - y * Real.sin θ),
      c.2 + (x * Real.sin θ + y * Real.cos θ))).1 = x * (Real.cos θ ^ 2 + Real.sin θ ^ 2) := by
    simp only [coord]; ring
  have h2 : (coord c θ (c.1 + (x * Real.cos θ - y * Real.sin θ),
      c.2 + (x * Real.sin θ + y * Real.cos θ))).2 = y * (Real.cos θ ^ 2 + Real.sin θ ^ 2) := by
    simp only [coord]; ring
  exact ⟨by rw [h1, hCS, mul_one]; exact hx, by rw [h2, hCS, mul_one]; exact hy⟩

/-! ## 3.  The violation polynomials and Lemma E (`RUNG2.md` §6.2, `_gcoef` / `_gmax`) -/

/-- The quadratic coefficients (in `u = tan(θ/2)`) of the four **violation polynomials** at
offsets `a = p_x − c_x`, `b = p_y − c_y`.  This is `_gcoef` of `search/zeromargin.py`:
`G_{p,0} = 2aC + 2bS − N`, `G_{p,1} = −2aC − 2bS − N`, `G_{p,2} = −2aS + 2bC − N`,
`G_{p,3} = 2aS − 2bC − N`, with `C = 1−u²`, `S = 2u`, `N = 1+u²`. -/
def gc : Fin 4 → ℝ → ℝ → ℝ × ℝ × ℝ
  | 0, a, b => (2 * a - 1, 4 * b, -2 * a - 1)
  | 1, a, b => (-2 * a - 1, -4 * b, 2 * a - 1)
  | 2, a, b => (2 * b - 1, -4 * a, -2 * b - 1)
  | 3, a, b => (-2 * b - 1, 4 * a, 2 * b - 1)

/-- The violation polynomial `G_{p,k}` evaluated at `u`. -/
def gval (k : Fin 4) (a b u : ℝ) : ℝ :=
  (gc k a b).1 + (gc k a b).2.1 * u + (gc k a b).2.2 * u ^ 2

lemma cos_two_arctan (u : ℝ) :
    Real.cos (2 * Real.arctan u) = (1 - u ^ 2) / (1 + u ^ 2) := by
  have hpos : (0 : ℝ) < 1 + u ^ 2 := by positivity
  rw [Real.cos_two_mul, Real.cos_sq_arctan]
  field_simp
  ring

lemma sin_two_arctan (u : ℝ) :
    Real.sin (2 * Real.arctan u) = 2 * u / (1 + u ^ 2) := by
  have hpos : (0 : ℝ) < 1 + u ^ 2 := by positivity
  have hsq : Real.sqrt (1 + u ^ 2) ^ 2 = 1 + u ^ 2 := Real.sq_sqrt (le_of_lt hpos)
  have hne : Real.sqrt (1 + u ^ 2) ≠ 0 := by
    intro hc; rw [hc] at hsq; norm_num at hsq; linarith
  rw [Real.sin_two_mul, Real.sin_arctan, Real.cos_arctan]
  field_simp
  rw [hsq]

/-- **The violation polynomials decide containment** (`RUNG2.md` §6.2; checked in floats against
the geometry by `search/zeromargin_stress.py`, "0 disagreements").  With `θ = 2 arctan u`,
`p ∈ sq c θ 1` iff all four `G_{p,k} ≤ 0`. -/
theorem mem_sq_iff_gval (c p : ℝ × ℝ) (u : ℝ) :
    p ∈ sq c (2 * Real.arctan u) 1 ↔ ∀ k : Fin 4, gval k (p.1 - c.1) (p.2 - c.2) u ≤ 0 := by
  have hN : (0 : ℝ) < 1 + u ^ 2 := by positivity
  have hNne : (1 : ℝ) + u ^ 2 ≠ 0 := ne_of_gt hN
  have hX : 2 * (1 + u ^ 2) * (coord c (2 * Real.arctan u) p).1
      = 2 * (p.1 - c.1) * (1 - u ^ 2) + 4 * (p.2 - c.2) * u := by
    simp only [coord, cos_two_arctan, sin_two_arctan]
    field_simp
    ring
  have hY : 2 * (1 + u ^ 2) * (coord c (2 * Real.arctan u) p).2
      = -(4 * (p.1 - c.1) * u) + 2 * (p.2 - c.2) * (1 - u ^ 2) := by
    simp only [coord, cos_two_arctan, sin_two_arctan]
    field_simp
    ring
  constructor
  · rintro ⟨h1, h2⟩ k
    rw [abs_le] at h1 h2
    obtain ⟨h1a, h1b⟩ := h1
    obtain ⟨h2a, h2b⟩ := h2
    fin_cases k <;> simp only [gval, gc] <;> nlinarith [hX, hY, hN, h1a, h1b, h2a, h2b]
  · intro h
    have h0 := h 0
    have h1 := h 1
    have h2 := h 2
    have h3 := h 3
    simp only [gval, gc] at h0 h1 h2 h3
    refine ⟨abs_le.mpr ⟨?_, ?_⟩, abs_le.mpr ⟨?_, ?_⟩⟩
    · nlinarith [hX, hN]
    · nlinarith [hX, hN]
    · nlinarith [hY, hN]
    · nlinarith [hY, hN]

/-- The quarter turn about the centre fixes the axis square, so `θ` matters only mod `π/2`. -/
lemma sq_add_pi_div_two (c : ℝ × ℝ) (θ L : ℝ) : sq c (θ + Real.pi / 2) L = sq c θ L := by
  ext p
  simp only [sq, Set.mem_ofPred_eq]
  have h1 : (coord c (θ + Real.pi / 2) p).1 = (coord c θ p).2 := by
    simp only [coord, Real.cos_add_pi_div_two, Real.sin_add_pi_div_two]; ring
  have h2 : (coord c (θ + Real.pi / 2) p).2 = -(coord c θ p).1 := by
    simp only [coord, Real.cos_add_pi_div_two, Real.sin_add_pi_div_two]; ring
  rw [h1, h2, abs_neg, and_comm]


section family

variable {β : Type*}

/-- The points of a finite family of entries. -/
noncomputable def coverA (E : Finset β) (pt : β → ℝ × ℝ) : Finset (ℝ × ℝ) :=
  open Classical in E.image pt

/-- The aggregated weight: the total weight of the entries at `p`. -/
noncomputable def coverW (E : Finset β) (pt : β → ℝ × ℝ) (wt : β → ℝ) (p : ℝ × ℝ) : ℝ :=
  open Classical in ∑ e ∈ E.filter (fun e => pt e = p), wt e

open Classical in
/-- The weight captured by a set `S` is the total weight of the entries whose point is in `S`. -/
theorem sum_filter_coverA (E : Finset β) (pt : β → ℝ × ℝ) (wt : β → ℝ) (S : Set (ℝ × ℝ)) :
    ∑ a ∈ (coverA E pt).filter (fun a => a ∈ S), coverW E pt wt a
      = ∑ e ∈ E.filter (fun e => pt e ∈ S), wt e := by
  rw [← Finset.sum_fiberwise_of_maps_to (s := E.filter (fun e => pt e ∈ S))
    (t := (coverA E pt).filter (fun a => a ∈ S)) (g := pt)]
  · refine Finset.sum_congr rfl fun a ha => ?_
    simp only [Finset.mem_filter] at ha
    unfold coverW
    rw [Finset.filter_filter]
    congr 1
    ext e
    simp only [Finset.mem_filter]
    constructor
    · rintro ⟨h1, h2⟩; exact ⟨h1, h2 ▸ ha.2, h2⟩
    · rintro ⟨h1, _, h2⟩; exact ⟨h1, h2⟩
  · intro e he
    simp only [Finset.mem_filter] at he ⊢
    exact ⟨Finset.mem_image_of_mem pt he.1, he.2⟩

open Classical in
/-- The total weight of `(coverA, coverW)` is the total weight of the entries. -/
theorem sum_coverA (E : Finset β) (pt : β → ℝ × ℝ) (wt : β → ℝ) :
    ∑ a ∈ coverA E pt, coverW E pt wt a = ∑ e ∈ E, wt e := by
  have h := sum_filter_coverA E pt wt Set.univ
  simp only [Set.mem_univ, Finset.filter_true_of_mem (fun _ _ => trivial)] at h
  exact h


end family

end SquarePacking
