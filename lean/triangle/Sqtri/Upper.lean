import Sqtri.MinSide

/-!
# Upper bounds: explicit packings with coordinates in `ℚ(√3)`

A square is given by its centre `(cx, cy)` and `(cos θ, sin θ)`, all in `ℚ(√3)`.

* `inTriB` — each of the four vertices satisfies the three side inequalities of `tri L`, decided
  exactly.  `inTriB_sound` shows the whole closed square is then in `tri L`: a linear function is
  `≥ 0` on a square once it is `≥ 0` at the four vertices.
* `sepB` — some edge normal `d` of one of the two squares separates them:
  `d·(c₂ − c₁) ≥ h₁ + h₂`, where `hᵢ = (|d·Rᵢe₁| + |d·Rᵢe₂|)/2` is the half-width of square `i`
  along `d`.  `sepB_sound` shows the open squares are then disjoint.
-/

namespace SquarePacking.Tri

open SquarePacking

/-! ## Two facts about a closed or open square -/

lemma offset_of_coord (c p : ℝ × ℝ) (θ : ℝ) :
    p.1 = c.1 + ((coord c θ p).1 * Real.cos θ - (coord c θ p).2 * Real.sin θ) ∧
    p.2 = c.2 + ((coord c θ p).1 * Real.sin θ + (coord c θ p).2 * Real.cos θ) := by
  have h := Real.cos_sq_add_sin_sq θ
  simp only [coord]
  constructor
  · linear_combination (-(p.1 - c.1)) * h
  · linear_combination (-(p.2 - c.2)) * h

/-- A linear function on a closed square is bounded below by its value at a worst vertex. -/
lemma lin_on_sq (c p : ℝ × ℝ) (θ a1 a2 b : ℝ) (hp : p ∈ sq c θ 1)
    (hv : ∀ sx sy : ℝ, (sx = 1/2 ∨ sx = -1/2) → (sy = 1/2 ∨ sy = -1/2) →
      0 ≤ a1 * (c.1 + (sx * Real.cos θ - sy * Real.sin θ))
        + a2 * (c.2 + (sx * Real.sin θ + sy * Real.cos θ)) + b) :
    0 ≤ a1 * p.1 + a2 * p.2 + b := by
  obtain ⟨e1, e2⟩ := offset_of_coord c p θ
  obtain ⟨hX, hY⟩ := hp
  set X := (coord c θ p).1
  set Y := (coord c θ p).2
  set α := a1 * Real.cos θ + a2 * Real.sin θ
  set β := -(a1 * Real.sin θ) + a2 * Real.cos θ
  have hval : a1 * p.1 + a2 * p.2 + b = (a1 * c.1 + a2 * c.2 + b) + X * α + Y * β := by
    rw [e1, e2]; ring
  have hvert : ∀ sx sy : ℝ, (sx = 1/2 ∨ sx = -1/2) → (sy = 1/2 ∨ sy = -1/2) →
      0 ≤ (a1 * c.1 + a2 * c.2 + b) + sx * α + sy * β := by
    intro sx sy hsx hsy
    have := hv sx sy hsx hsy
    linarith [show a1 * (c.1 + (sx * Real.cos θ - sy * Real.sin θ))
        + a2 * (c.2 + (sx * Real.sin θ + sy * Real.cos θ)) + b
        = (a1 * c.1 + a2 * c.2 + b) + sx * α + sy * β by ring]
  have hXα : X * α ≥ -(|α| / 2) := by
    have := abs_mul X α
    have h1 : |X * α| ≤ |α| / 2 := by rw [abs_mul]; nlinarith [abs_nonneg α, abs_nonneg X]
    linarith [neg_abs_le (X * α)]
  have hYβ : Y * β ≥ -(|β| / 2) := by
    have h1 : |Y * β| ≤ |β| / 2 := by rw [abs_mul]; nlinarith [abs_nonneg β, abs_nonneg Y]
    linarith [neg_abs_le (Y * β)]
  -- the worst vertex takes sx = -sign α / 2, sy = -sign β / 2
  have hw : 0 ≤ (a1 * c.1 + a2 * c.2 + b) - |α| / 2 - |β| / 2 := by
    rcases le_total 0 α with ha | ha <;> rcases le_total 0 β with hb | hb
    · have := hvert (-1/2) (-1/2) (Or.inr rfl) (Or.inr rfl)
      rw [abs_of_nonneg ha, abs_of_nonneg hb]; linarith
    · have := hvert (-1/2) (1/2) (Or.inr rfl) (Or.inl rfl)
      rw [abs_of_nonneg ha, abs_of_nonpos hb]; linarith
    · have := hvert (1/2) (-1/2) (Or.inl rfl) (Or.inr rfl)
      rw [abs_of_nonpos ha, abs_of_nonneg hb]; linarith
    · have := hvert (1/2) (1/2) (Or.inl rfl) (Or.inl rfl)
      rw [abs_of_nonpos ha, abs_of_nonpos hb]; linarith
  linarith

/-- A point of an open square is strictly within the half-width along any nonzero direction. -/
lemma proj_lt_on_sqInt (c p : ℝ × ℝ) (θ d1 d2 : ℝ) (hd : d1 ≠ 0 ∨ d2 ≠ 0) (hp : p ∈ sqInt c θ 1) :
    d1 * (p.1 - c.1) + d2 * (p.2 - c.2) <
      (|d1 * Real.cos θ + d2 * Real.sin θ| + |-(d1 * Real.sin θ) + d2 * Real.cos θ|) / 2 := by
  obtain ⟨e1, e2⟩ := offset_of_coord c p θ
  obtain ⟨hX, hY⟩ := hp
  set X := (coord c θ p).1
  set Y := (coord c θ p).2
  set α := d1 * Real.cos θ + d2 * Real.sin θ
  set β := -(d1 * Real.sin θ) + d2 * Real.cos θ
  have hval : d1 * (p.1 - c.1) + d2 * (p.2 - c.2) = X * α + Y * β := by rw [e1, e2]; ring
  have hcs := Real.cos_sq_add_sin_sq θ
  have hnorm : α ^ 2 + β ^ 2 = d1 ^ 2 + d2 ^ 2 := by
    simp only [α, β]; linear_combination (d1 ^ 2 + d2 ^ 2) * hcs
  have hpos : 0 < α ^ 2 + β ^ 2 := by
    rw [hnorm]; rcases hd with h | h <;> positivity
  rw [hval]
  have hXa : X * α ≤ |X| * |α| := by rw [← abs_mul]; exact le_abs_self _
  have hYb : Y * β ≤ |Y| * |β| := by rw [← abs_mul]; exact le_abs_self _
  rcases eq_or_ne α 0 with ha | ha
  · have hb : β ≠ 0 := by intro hb; rw [ha, hb] at hpos; norm_num at hpos
    have : |Y| * |β| < 1 / 2 * |β| := mul_lt_mul_of_pos_right hY (abs_pos.mpr hb)
    rw [ha] at hXa ⊢; simp at hXa ⊢; nlinarith [abs_nonneg Y]
  · have : |X| * |α| < 1 / 2 * |α| := mul_lt_mul_of_pos_right hX (abs_pos.mpr ha)
    have : |Y| * |β| ≤ 1 / 2 * |β| := mul_le_mul_of_nonneg_right hY.le (abs_nonneg β)
    linarith

theorem disjoint_of_sep (c1 c2 : ℝ × ℝ) (θ1 θ2 d1 d2 : ℝ) (hd : d1 ≠ 0 ∨ d2 ≠ 0)
    (h : (|d1 * Real.cos θ1 + d2 * Real.sin θ1| + |-(d1 * Real.sin θ1) + d2 * Real.cos θ1|) / 2 +
         (|d1 * Real.cos θ2 + d2 * Real.sin θ2| + |-(d1 * Real.sin θ2) + d2 * Real.cos θ2|) / 2
         ≤ d1 * (c2.1 - c1.1) + d2 * (c2.2 - c1.2)) :
    Disjoint (sqInt c1 θ1 1) (sqInt c2 θ2 1) := by
  rw [Set.disjoint_left]
  intro p h1 h2
  have a := proj_lt_on_sqInt c1 p θ1 d1 d2 hd h1
  have b := proj_lt_on_sqInt c2 p θ2 (-d1) (-d2)
    (by rcases hd with h | h; exacts [Or.inl (neg_ne_zero.mpr h), Or.inr (neg_ne_zero.mpr h)]) h2
  have e : ∀ x y : ℝ, |-d1 * x + -d2 * y| = |d1 * x + d2 * y| := fun x y => by
    rw [show -d1 * x + -d2 * y = -(d1 * x + d2 * y) by ring, abs_neg]
  have e' : ∀ x y : ℝ, |-(-d1 * x) + -d2 * y| = |-(d1 * x) + d2 * y| := fun x y => by
    rw [show -(-d1 * x) + -d2 * y = -(-(d1 * x) + d2 * y) by ring, abs_neg]
  rw [e, e'] at b
  linarith

/-! ## Exact decision procedures -/

/-- A square: centre and `(cos θ, sin θ)`, in `ℚ(√3)`. -/
structure Sq where
  cx : Q3
  cy : Q3
  cs : Q3
  sn : Q3

def Q3.abs' (x : Q3) : Q3 := if x.nonnegB then x else Q3.neg x

lemma Q3.val_abs' (x : Q3) : (Q3.abs' x).val = |x.val| := by
  unfold Q3.abs'
  split_ifs with h
  · exact (abs_of_nonneg (Q3.nonnegB_sound x h)).symm
  · rw [Q3.val_neg]
    -- `nonnegB` is exact, so a negative verdict means `x < 0`
    have : x.val < 0 := by
      by_contra hc
      push Not at hc
      exact h (Q3.nonnegB_complete x hc)
    rw [abs_of_neg this]

/-- The vertex `c + R(sx, sy)` of the square. -/
def Sq.vx (s : Sq) (sx sy : Q3) : Q3 := Q3.add s.cx (Q3.sub (Q3.mul sx s.cs) (Q3.mul sy s.sn))
def Sq.vy (s : Sq) (sx sy : Q3) : Q3 := Q3.add s.cy (Q3.add (Q3.mul sx s.sn) (Q3.mul sy s.cs))

def inTriB (L : Q3) (s : Sq) : Bool :=
  (sides L).all fun t => halves.all fun h =>
    (Q3.add (Q3.add (Q3.mul t.1 (s.vx h.1 h.2)) (Q3.mul t.2.1 (s.vy h.1 h.2))) t.2.2).nonnegB

/-- Half-width of a square along `d`. -/
def Sq.hw (s : Sq) (d1 d2 : Q3) : Q3 :=
  Q3.mul (q (1/2) 0) (Q3.add (Q3.abs' (Q3.add (Q3.mul d1 s.cs) (Q3.mul d2 s.sn)))
    (Q3.abs' (Q3.add (Q3.neg (Q3.mul d1 s.sn)) (Q3.mul d2 s.cs))))

def sepDir (a b : Sq) (d1 d2 : Q3) : Bool :=
  (Q3.sub (Q3.add (Q3.mul d1 (Q3.sub b.cx a.cx)) (Q3.mul d2 (Q3.sub b.cy a.cy)))
    (Q3.add (a.hw d1 d2) (b.hw d1 d2))).nonnegB

/-- Try the edge normals of both squares, in both orientations. -/
def sepB (a b : Sq) : Bool :=
  [(a.cs, a.sn), (Q3.neg a.sn, a.cs), (b.cs, b.sn), (Q3.neg b.sn, b.cs)].any fun d =>
    sepDir a b d.1 d.2 || sepDir a b (Q3.neg d.1) (Q3.neg d.2)

/-- `s` stands for the real square with centre `(cx, cy)` and angle `θ`. -/
def Sq.Rep (s : Sq) (θ : ℝ) : Prop := s.cs.val = Real.cos θ ∧ s.sn.val = Real.sin θ

noncomputable def Sq.c (s : Sq) : ℝ × ℝ := (s.cx.val, s.cy.val)

theorem inTriB_sound (L : Q3) (s : Sq) (θ : ℝ) (hr : s.Rep θ) (h : inTriB L s = true) :
    sq s.c θ 1 ⊆ tri L.val := by
  intro p hp
  have key : ∀ t ∈ sides L, 0 ≤ t.1.val * p.1 + t.2.1.val * p.2 + t.2.2.val := by
    intro t ht
    apply lin_on_sq s.c p θ _ _ _ hp
    intro sx sy hsx hsy
    have hall := List.all_eq_true.mp (List.all_eq_true.mp h t ht)
    obtain ⟨hx, hy⟩ := hr
    have hmem : ∀ a b : ℚ, ((a : ℝ) = 1/2 ∨ (a : ℝ) = -1/2) → ((b : ℝ) = 1/2 ∨ (b : ℝ) = -1/2) →
        (q a 0, q b 0) ∈ halves := by
      intro a b ha hb
      have ha' : a = 1/2 ∨ a = -1/2 := by
        rcases ha with h | h
        · left; exact_mod_cast (by linarith : (a : ℝ) = ((1/2 : ℚ) : ℝ))
        · right; exact_mod_cast (by push_cast; linarith : (a : ℝ) = ((-1/2 : ℚ) : ℝ))
      have hb' : b = 1/2 ∨ b = -1/2 := by
        rcases hb with h | h
        · left; exact_mod_cast (by linarith : (b : ℝ) = ((1/2 : ℚ) : ℝ))
        · right; exact_mod_cast (by push_cast; linarith : (b : ℝ) = ((-1/2 : ℚ) : ℝ))
      rcases ha' with rfl | rfl <;> rcases hb' with rfl | rfl <;> simp [halves, q] <;> norm_num
    -- write sx, sy as rationals
    have hsxq : ∃ a : ℚ, (a : ℝ) = sx ∧ ((a : ℝ) = 1/2 ∨ (a : ℝ) = -1/2) := by
      rcases hsx with rfl | rfl
      · exact ⟨1/2, by push_cast; ring, Or.inl (by push_cast; ring)⟩
      · exact ⟨-1/2, by push_cast; ring, Or.inr (by push_cast; ring)⟩
    have hsyq : ∃ b : ℚ, (b : ℝ) = sy ∧ ((b : ℝ) = 1/2 ∨ (b : ℝ) = -1/2) := by
      rcases hsy with rfl | rfl
      · exact ⟨1/2, by push_cast; ring, Or.inl (by push_cast; ring)⟩
      · exact ⟨-1/2, by push_cast; ring, Or.inr (by push_cast; ring)⟩
    obtain ⟨a, rfl, ha⟩ := hsxq
    obtain ⟨b, rfl, hb⟩ := hsyq
    have := Q3.nonnegB_sound _ (hall _ (hmem a b ha hb))
    simp only [Q3.val_add, Q3.val_mul, Sq.vx, Sq.vy, Q3.val_sub, val_q] at this
    simp only [Sq.c]
    rw [← hx, ← hy]
    simpa using this
  have h0 := key (Q3.zero, Q3.one, Q3.zero) (by simp [sides])
  have h1 := key (q 0 1, q (-1) 0, Q3.zero) (by simp [sides])
  have h2 := key (q 0 (-1), q (-1) 0, Q3.mul (q 0 1) L) (by simp [sides])
  simp [Q3.val, Q3.zero, Q3.one, Q3.mul, q] at h0 h1 h2
  refine ⟨by linarith, by linarith, ?_⟩
  have e : Real.sqrt 3 * L.val = 3 * (L.b : ℝ) + (L.a : ℝ) * Real.sqrt 3 := by
    simp only [Q3.val]; linear_combination (L.b : ℝ) * Q3.sqrt3_sq
  have e2 : Real.sqrt 3 * (L.val - p.1) = Real.sqrt 3 * L.val - Real.sqrt 3 * p.1 := by ring
  push_cast at h2
  linarith

theorem sepDir_sound (a b : Sq) (θa θb : ℝ) (ha : a.Rep θa) (hb : b.Rep θb) (d1 d2 : Q3)
    (hd : d1.val ≠ 0 ∨ d2.val ≠ 0) (h : sepDir a b d1 d2 = true) :
    Disjoint (sqInt a.c θa 1) (sqInt b.c θb 1) := by
  apply disjoint_of_sep a.c b.c θa θb d1.val d2.val hd
  have := Q3.nonnegB_sound _ h
  obtain ⟨hac, has⟩ := ha
  obtain ⟨hbc, hbs⟩ := hb
  simp only [Sq.hw, Q3.val_sub, Q3.val_add, Q3.val_mul, Q3.val_neg, Q3.val_abs', val_q]
    at this
  simp only [Sq.c]
  rw [hac, has, hbc, hbs] at this
  push_cast at this
  linarith

lemma Sq.ne_zero (s : Sq) (θ : ℝ) (h : s.Rep θ) : s.cs.val ≠ 0 ∨ s.sn.val ≠ 0 := by
  by_contra hc
  push Not at hc
  have := Real.cos_sq_add_sin_sq θ
  rw [← h.1, ← h.2, hc.1, hc.2] at this
  norm_num at this

theorem sepB_sound (a b : Sq) (θa θb : ℝ) (ha : a.Rep θa) (hb : b.Rep θb) (h : sepB a b = true) :
    Disjoint (sqInt a.c θa 1) (sqInt b.c θb 1) := by
  have na := Sq.ne_zero a θa ha
  have nb := Sq.ne_zero b θb hb
  have neg' : ∀ x y : Q3, x.val ≠ 0 ∨ y.val ≠ 0 → (Q3.neg x).val ≠ 0 ∨ (Q3.neg y).val ≠ 0 := by
    intro x y hxy; simp only [Q3.val_neg, neg_ne_zero]; exact hxy
  have swap' : ∀ x y : Q3, x.val ≠ 0 ∨ y.val ≠ 0 → (Q3.neg y).val ≠ 0 ∨ x.val ≠ 0 := by
    intro x y hxy; simp only [Q3.val_neg, neg_ne_zero]; exact hxy.symm
  obtain ⟨d, hd, h⟩ := List.any_eq_true.mp h
  have hdn : d.1.val ≠ 0 ∨ d.2.val ≠ 0 := by
    simp only [List.mem_cons, List.not_mem_nil, or_false] at hd
    rcases hd with rfl | rfl | rfl | rfl
    exacts [na, swap' _ _ na, nb, swap' _ _ nb]
  rcases Bool.or_eq_true_iff.mp h with h | h
  · exact sepDir_sound a b θa θb ha hb _ _ hdn h
  · exact sepDir_sound a b θa θb ha hb _ _ (neg' _ _ hdn) h

/-! ## Helpers shared by the main theorems -/

lemma sqrt3_ne : Real.sqrt 3 ≠ 0 := (Real.sqrt_pos.mpr (by norm_num)).ne'

lemma two_div_sqrt3 : 2 / Real.sqrt 3 = 2 / 3 * Real.sqrt 3 := by
  field_simp
  rw [Real.sq_sqrt (by norm_num : (0 : ℝ) ≤ 3)]

lemma yTop_val {L y : Q3} (h : y = Q3.mul L (q 0 (1/2))) : y.val = L.val * Real.sqrt 3 / 2 := by
  subst h; simp [Q3.val_mul]; ring

lemma rep0 (cx cy : Q3) : (Sq.mk cx cy (q 1 0) (q 0 0)).Rep 0 := by
  constructor <;> simp

lemma rep6 (cx cy : Q3) : (Sq.mk cx cy (q 0 (1/2)) (q (1/2) 0)).Rep (Real.pi / 6) := by
  constructor
  · simp [Real.cos_pi_div_six]; ring
  · simp [Real.sin_pi_div_six]

lemma rep3 (cx cy : Q3) : (Sq.mk cx cy (q (1/2) 0) (q 0 (1/2))).Rep (Real.pi / 3) := by
  constructor
  · simp [Real.cos_pi_div_three]
  · simp [Real.sin_pi_div_three]; ring

/-- A packing from a list of exactly checked squares. -/
theorem packs_of_squares (n : ℕ) (L : Q3) (s : Fin n → Sq) (θ : Fin n → ℝ)
    (hr : ∀ i, (s i).Rep (θ i)) (hin : ∀ i, inTriB L (s i) = true)
    (hsep : ∀ i j, i < j → sepB (s i) (s j) = true) : PacksTri n L.val := by
  refine ⟨fun i => (s i).c, θ, fun i => inTriB_sound L (s i) (θ i) (hr i) (hin i), ?_⟩
  intro i j hij
  rcases lt_or_gt_of_ne hij with h | h
  · exact sepB_sound _ _ _ _ (hr i) (hr j) (hsep i j h)
  · exact (sepB_sound _ _ _ _ (hr j) (hr i) (hsep j i h)).symm

/-- All squares axis-parallel, inside `tri L`, and pairwise separated: one Boolean test. -/
def axisPackB (n : ℕ) (L : Q3) (s : Fin n → Sq) : Bool :=
  (List.finRange n).all (fun i => decide ((s i).cs = q 1 0) && decide ((s i).sn = q 0 0) &&
    inTriB L (s i)) &&
  (List.finRange n).all (fun i => (List.finRange n).all (fun j => !(decide (i < j)) || sepB (s i) (s j)))

theorem packs_of_axisPackB (n : ℕ) (L : Q3) (s : Fin n → Sq) (h : axisPackB n L s = true) :
    PacksTri n L.val := by
  simp only [axisPackB, Bool.and_eq_true, List.all_eq_true, List.mem_finRange, true_implies,
    decide_eq_true_eq] at h
  obtain ⟨h1, h2⟩ := h
  refine packs_of_squares n L s (fun _ => 0) (fun i => ?_) (fun i => (h1 i).2) (fun i j hij => ?_)
  · have := (h1 i).1
    constructor
    · rw [this.1]; simp
    · rw [this.2]; simp
  · have := h2 i j
    simp only [Bool.or_eq_true, Bool.not_eq_true', decide_eq_false_iff_not, not_lt] at this
    rcases this with h | h
    · exact absurd hij (not_lt.mpr h)
    · exact h

end SquarePacking.Tri
