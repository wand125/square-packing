import Sqtri.Poly

/-!
# The certificate checker and its soundness

A pose is a centre `(x, y)` and `u = tan(θ/2)`.  The checker works on regions

  `x ∈ [x0, x1]`, `y ∈ [y0, y1]`, `u ∈ [U0, U1]`, and `f(x, y, u) ≥ 0` for every `f ∈ lins`,

and a list of *hypothesis forms*: the 12 admissibility forms of the container (`admForms`), the 4
sides of the centre rectangle, and `lins`.  All are affine forms in `(x, y)` with polynomial
coefficients in `u`, and all are `≥ 0` on the admissible poses of the region.

**Leaf certificates (Farkas–Bernstein).**  A certificate is a list of entries `(j, d, i, c)` with
`c ≥ 0` in `ℚ(√3)`.  An entry stands for `c · (u − U0)^i (U1 − u)^(d−i) · h_j`, where `h_j` is the
`j`-th hypothesis form, or the constant `1` when `j` is past the end of the list.  Every entry is
therefore `≥ 0` on the region.  The checker verifies a polynomial identity:

* `cover`: for each listed point `p` and each `k < 4`, `Σ entries = target p k`, where
  `target p k ≥ 0` is the `k`-th side condition of `p ∈ sq c θ 1` (times `1 + u²`).
  So `p` is captured.  The listed points are distinct and weigh `≥ 1`.
* `empty`: `Σ entries + 1 = 0`, which is impossible on a non-empty region.

**Splits** at any value of `x`, `y` or `u`, or by the sign of any affine form, cover the region
by their two branches.  Nothing about the splits needs to be checked.

`check_sound`: `check … = true` implies the semantic statement `Cov` on the region.
-/

namespace SquarePacking.Tri

open UPoly

/-! ## Fixed polynomials -/

def q (a b : ℚ) : Q3 := ⟨a, b⟩

/-- `1 + u²`. -/
def Dp : UPoly := [Q3.one, Q3.zero, Q3.one]
/-- `1 − u²`. -/
def C1p : UPoly := [Q3.one, Q3.zero, q (-1) 0]
/-- `2u`. -/
def S1p : UPoly := [Q3.zero, q 2 0]

lemma eval_Dp (u : ℝ) : Dp.eval u = 1 + u ^ 2 := by simp [Dp, Q3.val, Q3.one, Q3.zero]; ring
lemma eval_C1p (u : ℝ) : C1p.eval u = 1 - u ^ 2 := by simp [C1p, q, Q3.val, Q3.one, Q3.zero]; ring
lemma eval_S1p (u : ℝ) : S1p.eval u = 2 * u := by simp [S1p, q, Q3.val, Q3.zero]; ring

/-- `(u − U0)^i (U1 − u)^(d−i)`. -/
def bern (U0 U1 : Q3) (d i : ℕ) : UPoly :=
  mul (pow [Q3.neg U0, Q3.one] i) (pow [U1, q (-1) 0] (d - i))

lemma eval_bern (U0 U1 : Q3) (d i : ℕ) (u : ℝ) :
    (bern U0 U1 d i).eval u = (u - U0.val) ^ i * (U1.val - u) ^ (d - i) := by
  simp [bern, q, Q3.val, Q3.neg, Q3.one]
  congr 1 <;> congr 1 <;> ring

lemma bern_nonneg (U0 U1 : Q3) (d i : ℕ) {u : ℝ} (h0 : U0.val ≤ u) (h1 : u ≤ U1.val) :
    0 ≤ (bern U0 U1 d i).eval u := by
  rw [eval_bern]
  exact mul_nonneg (pow_nonneg (by linarith) _) (pow_nonneg (by linarith) _)

/-! ## Hypothesis forms -/

/-- `(1+u²)·(a·v + b)` for the square vertex `v = c + R_θ (sx, sy)`, with `θ = 2 arctan u`:
the form `≥ 0` says that this vertex lies in the half-plane `a·q + b ≥ 0`. -/
def vform (ax ay b sx sy : Q3) : Aff :=
  let vx := add (scale sx C1p) (scale (Q3.neg sy) S1p)
  let vy := add (scale sx S1p) (scale sy C1p)
  ⟨add (scale b Dp) (add (scale ax vx) (scale ay vy)), scale ax Dp, scale ay Dp⟩

/-- The sides of the container `T_L = conv{(0,0), (L,0), (L/2, L√3/2)}`, as `(a_x, a_y, b)` with
`a·q + b ≥ 0` inside. -/
def sides (L : Q3) : List (Q3 × Q3 × Q3) :=
  [(Q3.zero, Q3.one, Q3.zero), (q 0 1, q (-1) 0, Q3.zero), (q 0 (-1), q (-1) 0, Q3.mul (q 0 1) L)]

def halves : List (Q3 × Q3) := [(q (-1/2) 0, q (-1/2) 0), (q (-1/2) 0, q (1/2) 0),
  (q (1/2) 0, q (-1/2) 0), (q (1/2) 0, q (1/2) 0)]

/-- The 12 admissibility forms. -/
def admForms (L : Q3) : List Aff :=
  (sides L).flatMap fun s => halves.map fun h => vform s.1 s.2.1 s.2.2 h.1 h.2

def boxForms (x0 x1 y0 y1 : Q3) : List Aff :=
  [⟨[Q3.neg x0], [Q3.one], []⟩, ⟨[x1], [q (-1) 0], []⟩,
   ⟨[Q3.neg y0], [], [Q3.one]⟩, ⟨[y1], [], [q (-1) 0]⟩]

/-- The coefficients `(α_k(u), β_k(u))` of `G_k = −(1+u²) + α (p_x − x) + β (p_y − y)`. -/
def gab : Fin 4 → UPoly × UPoly
  | 0 => (scale (q 2 0) C1p, [Q3.zero, q 4 0])
  | 1 => (scale (q (-2) 0) C1p, [Q3.zero, q (-4) 0])
  | 2 => ([Q3.zero, q (-4) 0], scale (q 2 0) C1p)
  | 3 => ([Q3.zero, q 4 0], scale (q (-2) 0) C1p)

/-- `(1+u²)·(−G_k)`: `≥ 0` for all `k` iff the point `(px, py)` lies in the square. -/
def target (px py : Q3) (k : Fin 4) : Aff :=
  let al := (gab k).1
  let be := (gab k).2
  Aff.mulU Dp ⟨add Dp (neg (add (scale px al) (scale py be))), al, be⟩

/-! ## Certificates -/

structure Ent where
  j : ℕ
  d : ℕ
  i : ℕ
  c : Q3

/-- The polynomial an entry stands for. -/
def Ent.aff (forms : List Aff) (U0 U1 : Q3) (e : Ent) : Aff :=
  match forms[e.j]? with
  | some f => Aff.mulU (scale e.c (bern U0 U1 e.d e.i)) f
  | none => Aff.const (scale e.c (bern U0 U1 e.d e.i))

def combo (forms : List Aff) (U0 U1 : Q3) (es : List Ent) : Aff :=
  es.foldr (fun e acc => Aff.add (e.aff forms U0 U1) acc) Aff.zero

def certOk (forms : List Aff) (U0 U1 : Q3) (es : List Ent) (tgt : Aff) : Bool :=
  es.all (fun e => e.c.nonnegB) && (Aff.add (combo forms U0 U1 es) (Aff.neg tgt)).isZero

def emptyOk (forms : List Aff) (U0 U1 : Q3) (es : List Ent) : Bool :=
  es.all (fun e => e.c.nonnegB) && (Aff.add (combo forms U0 U1 es) (Aff.const [Q3.one])).isZero

/-- A weighted point: `(x, y, w)`. -/
abbrev Pt := Q3 × Q3 × ℚ

def ptAt (pts : List Pt) (i : ℕ) : Pt := pts.getD i (Q3.zero, Q3.zero, 0)

inductive Tree
  | sx (m : Q3) (lo hi : Tree)
  | sy (m : Q3) (lo hi : Tree)
  | su (m : Q3) (lo hi : Tree)
  | lin (f : Aff) (pos neg : Tree)
  | empty (cert : List Ent)
  | cover (items : List (ℕ × List (List Ent)))

def coverOk (pts : List Pt) (forms : List Aff) (U0 U1 : Q3) (items : List (ℕ × List (List Ent))) :
    Bool :=
  (items.map Prod.fst).Nodup &&
  decide (1 ≤ (items.map fun it => (ptAt pts it.1).2.2).sum) &&
  items.all fun it =>
    decide (it.1 < pts.length) && decide (it.2.length = 4) &&
    (List.finRange 4).all fun k =>
      certOk forms U0 U1 (it.2.getD k []) (target (ptAt pts it.1).1 (ptAt pts it.1).2.1 k)

def check (L : Q3) (pts : List Pt) :
    Q3 → Q3 → Q3 → Q3 → Q3 → Q3 → List Aff → Tree → Bool
  | x0, x1, y0, y1, U0, U1, lins, .sx m lo hi =>
      check L pts x0 m y0 y1 U0 U1 lins lo && check L pts m x1 y0 y1 U0 U1 lins hi
  | x0, x1, y0, y1, U0, U1, lins, .sy m lo hi =>
      check L pts x0 x1 y0 m U0 U1 lins lo && check L pts x0 x1 m y1 U0 U1 lins hi
  | x0, x1, y0, y1, U0, U1, lins, .su m lo hi =>
      check L pts x0 x1 y0 y1 U0 m lins lo && check L pts x0 x1 y0 y1 m U1 lins hi
  | x0, x1, y0, y1, U0, U1, lins, .lin f pos neg =>
      check L pts x0 x1 y0 y1 U0 U1 (lins ++ [f]) pos &&
      check L pts x0 x1 y0 y1 U0 U1 (lins ++ [Aff.neg f]) neg
  | x0, x1, y0, y1, U0, U1, lins, .empty cert =>
      emptyOk (admForms L ++ boxForms x0 x1 y0 y1 ++ lins) U0 U1 cert
  | x0, x1, y0, y1, U0, U1, lins, .cover items =>
      coverOk pts (admForms L ++ boxForms x0 x1 y0 y1 ++ lins) U0 U1 items

/-! ## Gluing separately checked subtrees -/

theorem check_sx {L : Q3} {pts : List Pt} {x0 x1 y0 y1 U0 U1 m : Q3} {lins : List Aff} {lo hi : Tree}
    (h1 : check L pts x0 m y0 y1 U0 U1 lins lo = true)
    (h2 : check L pts m x1 y0 y1 U0 U1 lins hi = true) :
    check L pts x0 x1 y0 y1 U0 U1 lins (.sx m lo hi) = true := by
  simp [check, h1, h2]

theorem check_sy {L : Q3} {pts : List Pt} {x0 x1 y0 y1 U0 U1 m : Q3} {lins : List Aff} {lo hi : Tree}
    (h1 : check L pts x0 x1 y0 m U0 U1 lins lo = true)
    (h2 : check L pts x0 x1 m y1 U0 U1 lins hi = true) :
    check L pts x0 x1 y0 y1 U0 U1 lins (.sy m lo hi) = true := by
  simp [check, h1, h2]

theorem check_su {L : Q3} {pts : List Pt} {x0 x1 y0 y1 U0 U1 m : Q3} {lins : List Aff} {lo hi : Tree}
    (h1 : check L pts x0 x1 y0 y1 U0 m lins lo = true)
    (h2 : check L pts x0 x1 y0 y1 m U1 lins hi = true) :
    check L pts x0 x1 y0 y1 U0 U1 lins (.su m lo hi) = true := by
  simp [check, h1, h2]

theorem check_lin {L : Q3} {pts : List Pt} {x0 x1 y0 y1 U0 U1 : Q3} {lins : List Aff} {f : Aff}
    {pos neg : Tree}
    (h1 : check L pts x0 x1 y0 y1 U0 U1 (lins ++ [f]) pos = true)
    (h2 : check L pts x0 x1 y0 y1 U0 U1 (lins ++ [Aff.neg f]) neg = true) :
    check L pts x0 x1 y0 y1 U0 U1 lins (.lin f pos neg) = true := by
  simp [check, h1, h2]

/-! ## Semantics and soundness -/

/-- The point `i` is captured at the pose `(x, y, u)`: all four side conditions hold. -/
def Captured (pts : List Pt) (i : ℕ) (x y u : ℝ) : Prop :=
  ∀ k : Fin 4, 0 ≤ (target (ptAt pts i).1 (ptAt pts i).2.1 k).eval x y u

/-- The weight captured at `(x, y, u)`. -/
noncomputable def capW (pts : List Pt) (x y u : ℝ) : ℝ :=
  open Classical in
  ∑ i ∈ Finset.range pts.length, if Captured pts i x y u then ((ptAt pts i).2.2 : ℝ) else 0

/-- Every admissible pose of the region captures weight `≥ 1`. -/
def Cov (L : Q3) (pts : List Pt) (x0 x1 y0 y1 U0 U1 : Q3) (lins : List Aff) : Prop :=
  ∀ x y u : ℝ, x0.val ≤ x → x ≤ x1.val → y0.val ≤ y → y ≤ y1.val → U0.val ≤ u → u ≤ U1.val →
    (∀ f ∈ lins, 0 ≤ f.eval x y u) → (∀ f ∈ admForms L, 0 ≤ f.eval x y u) →
    1 ≤ capW pts x y u

lemma eval_combo (forms : List Aff) (U0 U1 : Q3) (es : List Ent) (x y u : ℝ) :
    (combo forms U0 U1 es).eval x y u = (es.map fun e => (e.aff forms U0 U1).eval x y u).sum := by
  induction es with
  | nil => simp [combo]
  | cons e es ih => simp only [combo, List.foldr_cons, Aff.eval_add, List.map_cons, List.sum_cons] at *; rw [ih]

lemma ent_nonneg (forms : List Aff) (U0 U1 : Q3) (e : Ent) (x y u : ℝ)
    (hf : ∀ f ∈ forms, 0 ≤ f.eval x y u) (hu0 : U0.val ≤ u) (hu1 : u ≤ U1.val)
    (hc : e.c.nonnegB = true) : 0 ≤ (e.aff forms U0 U1).eval x y u := by
  have hb := bern_nonneg U0 U1 e.d e.i hu0 hu1
  have hc' := Q3.nonnegB_sound e.c hc
  unfold Ent.aff
  cases h : forms[e.j]? with
  | none => simp only [Aff.eval_const, UPoly.eval_scale]; positivity
  | some f =>
    have hfm : f ∈ forms := List.mem_of_getElem? h
    simp only [Aff.eval_mulU, UPoly.eval_scale]
    exact mul_nonneg (mul_nonneg hc' hb) (hf f hfm)

lemma combo_nonneg (forms : List Aff) (U0 U1 : Q3) (es : List Ent) (x y u : ℝ)
    (hf : ∀ f ∈ forms, 0 ≤ f.eval x y u) (hu0 : U0.val ≤ u) (hu1 : u ≤ U1.val)
    (hc : es.all (fun e => e.c.nonnegB) = true) : 0 ≤ (combo forms U0 U1 es).eval x y u := by
  rw [eval_combo]
  apply List.sum_nonneg
  intro v hv
  obtain ⟨e, he, rfl⟩ := List.mem_map.mp hv
  exact ent_nonneg forms U0 U1 e x y u hf hu0 hu1 (List.all_eq_true.mp hc e he)

theorem certOk_sound {forms : List Aff} {U0 U1 : Q3} {es : List Ent} {tgt : Aff}
    (h : certOk forms U0 U1 es tgt = true) (x y u : ℝ)
    (hf : ∀ f ∈ forms, 0 ≤ f.eval x y u) (hu0 : U0.val ≤ u) (hu1 : u ≤ U1.val) :
    0 ≤ tgt.eval x y u := by
  simp only [certOk, Bool.and_eq_true] at h
  have hz := Aff.eval_of_isZero h.2 x y u
  simp only [Aff.eval_add, Aff.eval_neg] at hz
  have := combo_nonneg forms U0 U1 es x y u hf hu0 hu1 h.1
  linarith

theorem emptyOk_sound {forms : List Aff} {U0 U1 : Q3} {es : List Ent}
    (h : emptyOk forms U0 U1 es = true) (x y u : ℝ)
    (hf : ∀ f ∈ forms, 0 ≤ f.eval x y u) (hu0 : U0.val ≤ u) (hu1 : u ≤ U1.val) : False := by
  simp only [emptyOk, Bool.and_eq_true] at h
  have hz := Aff.eval_of_isZero h.2 x y u
  simp only [Aff.eval_add, Aff.eval_const] at hz
  have := combo_nonneg forms U0 U1 es x y u hf hu0 hu1 h.1
  simp [Q3.val, Q3.one] at hz
  linarith

lemma boxForms_nonneg {x0 x1 y0 y1 : Q3} {x y u : ℝ} (h0 : x0.val ≤ x) (h1 : x ≤ x1.val)
    (h2 : y0.val ≤ y) (h3 : y ≤ y1.val) : ∀ f ∈ boxForms x0 x1 y0 y1, 0 ≤ f.eval x y u := by
  intro f hf
  simp only [boxForms, List.mem_cons, List.not_mem_nil, or_false] at hf
  simp only [Q3.val] at h0 h1 h2 h3
  rcases hf with rfl | rfl | rfl | rfl <;>
    simp [Aff.eval, q, Q3.val, Q3.neg, Q3.one] <;> linarith

/-- All weights are nonnegative. -/
def weightsOk (pts : List Pt) : Bool := pts.all fun p => decide (0 ≤ p.2.2)

lemma weight_nonneg {pts : List Pt} (h : weightsOk pts = true) (i : ℕ) :
    (0 : ℝ) ≤ (ptAt pts i).2.2 := by
  unfold ptAt
  by_cases hi : i < pts.length
  · rw [List.getD_eq_getElem _ _ hi]
    have := List.all_eq_true.mp h _ (List.getElem_mem hi)
    exact_mod_cast of_decide_eq_true this
  · rw [List.getD_eq_default _ _ (by omega)]; simp

lemma sum_le_capW (pts : List Pt) (hW : weightsOk pts = true) (x y u : ℝ) (is : List ℕ)
    (hnd : is.Nodup) (hlt : ∀ i ∈ is, i < pts.length) (hcap : ∀ i ∈ is, Captured pts i x y u) :
    ((is.map fun i => ((ptAt pts i).2.2 : ℝ)).sum) ≤ capW pts x y u := by
  classical
  unfold capW
  rw [← List.sum_toFinset _ hnd]
  calc ∑ i ∈ is.toFinset, ((ptAt pts i).2.2 : ℝ)
      = ∑ i ∈ is.toFinset, (if Captured pts i x y u then ((ptAt pts i).2.2 : ℝ) else 0) := by
        refine Finset.sum_congr rfl fun i hi => ?_
        rw [if_pos (hcap i (List.mem_toFinset.mp hi))]
    _ ≤ ∑ i ∈ Finset.range pts.length, (if Captured pts i x y u then ((ptAt pts i).2.2 : ℝ) else 0) := by
        apply Finset.sum_le_sum_of_subset_of_nonneg
        · intro i hi; exact Finset.mem_range.mpr (hlt i (List.mem_toFinset.mp hi))
        · intro i _ _
          split_ifs
          · exact weight_nonneg hW i
          · exact le_refl 0

theorem coverOk_sound {pts : List Pt} (hW : weightsOk pts = true) {forms : List Aff} {U0 U1 : Q3}
    {items : List (ℕ × List (List Ent))} (h : coverOk pts forms U0 U1 items = true) (x y u : ℝ)
    (hf : ∀ f ∈ forms, 0 ≤ f.eval x y u) (hu0 : U0.val ≤ u) (hu1 : u ≤ U1.val) :
    1 ≤ capW pts x y u := by
  simp only [coverOk, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨hnd, hsum⟩, hall⟩ := h
  have hlt : ∀ i ∈ items.map Prod.fst, i < pts.length := by
    intro i hi
    obtain ⟨it, hit, rfl⟩ := List.mem_map.mp hi
    have := List.all_eq_true.mp hall it hit
    simp only [Bool.and_eq_true, decide_eq_true_eq] at this
    exact this.1.1
  have hcap : ∀ i ∈ items.map Prod.fst, Captured pts i x y u := by
    intro i hi k
    obtain ⟨it, hit, rfl⟩ := List.mem_map.mp hi
    have := List.all_eq_true.mp hall it hit
    simp only [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at this
    exact certOk_sound (this.2 k (List.mem_finRange k)) x y u hf hu0 hu1
  have hle := sum_le_capW pts hW x y u _ hnd hlt hcap
  have hsum' : (1 : ℝ) ≤ ((items.map Prod.fst).map fun i => ((ptAt pts i).2.2 : ℝ)).sum := by
    rw [List.map_map]
    have : ((items.map fun it => (ptAt pts it.1).2.2).sum : ℝ)
        = (items.map ((fun i => ((ptAt pts i).2.2 : ℝ)) ∘ Prod.fst)).sum := by
      rw [Rat.cast_list_sum, List.map_map]; rfl
    rw [← this]; exact_mod_cast hsum
  linarith

theorem check_sound (L : Q3) (pts : List Pt) (hW : weightsOk pts = true) :
    ∀ (t : Tree) (x0 x1 y0 y1 U0 U1 : Q3) (lins : List Aff),
      check L pts x0 x1 y0 y1 U0 U1 lins t = true → Cov L pts x0 x1 y0 y1 U0 U1 lins := by
  intro t
  induction t with
  | sx m lo hi ihl ihh =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check, Bool.and_eq_true] at h
    rcases le_total x m.val with hx | hx
    · exact ihl _ _ _ _ _ _ _ h.1 x y u h0 hx h2 h3 h4 h5 hl ha
    · exact ihh _ _ _ _ _ _ _ h.2 x y u hx h1 h2 h3 h4 h5 hl ha
  | sy m lo hi ihl ihh =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check, Bool.and_eq_true] at h
    rcases le_total y m.val with hy | hy
    · exact ihl _ _ _ _ _ _ _ h.1 x y u h0 h1 h2 hy h4 h5 hl ha
    · exact ihh _ _ _ _ _ _ _ h.2 x y u h0 h1 hy h3 h4 h5 hl ha
  | su m lo hi ihl ihh =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check, Bool.and_eq_true] at h
    rcases le_total u m.val with hu | hu
    · exact ihl _ _ _ _ _ _ _ h.1 x y u h0 h1 h2 h3 h4 hu hl ha
    · exact ihh _ _ _ _ _ _ _ h.2 x y u h0 h1 h2 h3 hu h5 hl ha
  | lin f pos neg ihp ihn =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check, Bool.and_eq_true] at h
    rcases le_total 0 (f.eval x y u) with hf | hf
    · refine ihp _ _ _ _ _ _ _ h.1 x y u h0 h1 h2 h3 h4 h5 ?_ ha
      intro g hg
      rcases List.mem_append.mp hg with hg | hg
      · exact hl g hg
      · simp only [List.mem_singleton] at hg; subst hg; exact hf
    · refine ihn _ _ _ _ _ _ _ h.2 x y u h0 h1 h2 h3 h4 h5 ?_ ha
      intro g hg
      rcases List.mem_append.mp hg with hg | hg
      · exact hl g hg
      · simp only [List.mem_singleton] at hg; subst hg; simp only [Aff.eval_neg]; linarith
  | empty cert =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check] at h
    exfalso
    refine emptyOk_sound h x y u ?_ h4 h5
    intro f hf
    rcases List.mem_append.mp hf with hf | hf
    · rcases List.mem_append.mp hf with hf | hf
      · exact ha f hf
      · exact boxForms_nonneg h0 h1 h2 h3 f hf
    · exact hl f hf
  | cover items =>
    intro x0 x1 y0 y1 U0 U1 lins h x y u h0 h1 h2 h3 h4 h5 hl ha
    simp only [check] at h
    refine coverOk_sound hW h x y u ?_ h4 h5
    intro f hf
    rcases List.mem_append.mp hf with hf | hf
    · rcases List.mem_append.mp hf with hf | hf
      · exact ha f hf
      · exact boxForms_nonneg h0 h1 h2 h3 f hf
    · exact hl f hf

end SquarePacking.Tri
