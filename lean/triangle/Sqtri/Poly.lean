import Sqtri.Evand

/-!
# Exact arithmetic for the certificates: `ℚ(√3)`, polynomials in `u`, affine forms

* `Q3` — a pair of rationals `(a, b)`, read as the real number `a + b√3` (`Q3.val`).  Addition
  and multiplication are computed on the pairs; `Q3.val_add`, `Q3.val_mul` show they agree with
  the real operations.  `Q3.nonnegB` decides `0 ≤ a + b√3` exactly (comparing `a²` with `3b²`),
  and `Q3.nonnegB_sound` proves it.
* `UPoly` — a list of `Q3` coefficients (lowest degree first), a polynomial in `u`.
* `Aff` — `p₀(u) + pₓ(u)·x + p_y(u)·y`, affine in the centre `(x, y)`.
* `Aff.isZero` — every coefficient is `0`; then the form is identically `0` (`Aff.eval_of_isZero`).

All computation is on rationals, so `decide +kernel` can evaluate it.
-/

namespace SquarePacking.Tri

/-- `a + b√3`. -/
structure Q3 where
  a : ℚ
  b : ℚ
deriving DecidableEq, Repr

namespace Q3

noncomputable def val (q : Q3) : ℝ := (q.a : ℝ) + (q.b : ℝ) * Real.sqrt 3

def zero : Q3 := ⟨0, 0⟩
def one : Q3 := ⟨1, 0⟩
def ofRat (r : ℚ) : Q3 := ⟨r, 0⟩
def add (p q : Q3) : Q3 := ⟨p.a + q.a, p.b + q.b⟩
def neg (p : Q3) : Q3 := ⟨-p.a, -p.b⟩
def sub (p q : Q3) : Q3 := ⟨p.a - q.a, p.b - q.b⟩
def mul (p q : Q3) : Q3 := ⟨p.a * q.a + 3 * (p.b * q.b), p.a * q.b + p.b * q.a⟩

lemma sqrt3_sq : Real.sqrt 3 * Real.sqrt 3 = 3 := Real.mul_self_sqrt (by norm_num)

@[simp] lemma val_zero : zero.val = 0 := by simp [val, zero]
@[simp] lemma val_one : one.val = 1 := by simp [val, one]
@[simp] lemma val_ofRat (r : ℚ) : (ofRat r).val = r := by simp [val, ofRat]
@[simp] lemma val_add (p q : Q3) : (add p q).val = p.val + q.val := by
  simp only [val, add]; push_cast; ring
@[simp] lemma val_neg (p : Q3) : (neg p).val = -p.val := by
  simp only [val, neg]; push_cast; ring
@[simp] lemma val_sub (p q : Q3) : (sub p q).val = p.val - q.val := by
  simp only [val, sub]; push_cast; ring
@[simp] lemma val_mul (p q : Q3) : (mul p q).val = p.val * q.val := by
  simp only [val, mul]; push_cast
  have h := sqrt3_sq
  linear_combination (-(p.b : ℝ) * q.b) * h

/-- Exact test for `0 ≤ a + b√3`. -/
def nonnegB (q : Q3) : Bool :=
  if 0 ≤ q.a then (if 0 ≤ q.b then true else decide (3 * (q.b * q.b) ≤ q.a * q.a))
  else (if 0 ≤ q.b then decide (q.a * q.a ≤ 3 * (q.b * q.b)) else false)

lemma sqrt3_nonneg : (0 : ℝ) ≤ Real.sqrt 3 := Real.sqrt_nonneg 3

theorem nonnegB_sound (q : Q3) (h : q.nonnegB = true) : 0 ≤ q.val := by
  unfold nonnegB at h
  have s := sqrt3_sq
  have s0 : (0 : ℝ) < Real.sqrt 3 := Real.sqrt_pos.mpr (by norm_num)
  have hb2 : ((q.b : ℝ) * Real.sqrt 3) * ((q.b : ℝ) * Real.sqrt 3) = 3 * ((q.b : ℝ) * q.b) := by
    have : ((q.b : ℝ) * Real.sqrt 3) * ((q.b : ℝ) * Real.sqrt 3)
        = ((q.b : ℝ) * q.b) * (Real.sqrt 3 * Real.sqrt 3) := by ring
    rw [this, s]; ring
  unfold val
  split_ifs at h with ha hb hb
  · have ha' : (0 : ℝ) ≤ q.a := by exact_mod_cast ha
    have hb' : (0 : ℝ) ≤ q.b := by exact_mod_cast hb
    positivity
  · have hq : 3 * (q.b * q.b) ≤ q.a * q.a := of_decide_eq_true h
    have ha' : (0 : ℝ) ≤ q.a := by exact_mod_cast ha
    have hb' : (q.b : ℝ) < 0 := by exact_mod_cast lt_of_not_ge hb
    have hq' : 3 * ((q.b : ℝ) * q.b) ≤ (q.a : ℝ) * q.a := by exact_mod_cast hq
    by_contra hneg
    replace hneg := lt_of_not_ge hneg
    have h1 : 0 < -((q.b : ℝ) * Real.sqrt 3) - q.a := by linarith
    have h2 : 0 < -((q.b : ℝ) * Real.sqrt 3) + q.a := by nlinarith
    have := mul_pos h1 h2
    nlinarith
  · have hq : q.a * q.a ≤ 3 * (q.b * q.b) := of_decide_eq_true h
    have ha' : (q.a : ℝ) < 0 := by exact_mod_cast lt_of_not_ge ha
    have hb' : (0 : ℝ) ≤ q.b := by exact_mod_cast hb
    have hq' : (q.a : ℝ) * q.a ≤ 3 * ((q.b : ℝ) * q.b) := by exact_mod_cast hq
    by_contra hneg
    replace hneg := lt_of_not_ge hneg
    have h1 : 0 < -(q.a : ℝ) - (q.b : ℝ) * Real.sqrt 3 := by linarith
    have h2 : 0 < -(q.a : ℝ) + (q.b : ℝ) * Real.sqrt 3 := by nlinarith
    have := mul_pos h1 h2
    nlinarith

theorem nonnegB_complete (q : Q3) (h : 0 ≤ q.val) : q.nonnegB = true := by
  have s := sqrt3_sq
  have s0 : (0 : ℝ) < Real.sqrt 3 := Real.sqrt_pos.mpr (by norm_num)
  have hb2 : ((q.b : ℝ) * Real.sqrt 3) * ((q.b : ℝ) * Real.sqrt 3) = 3 * ((q.b : ℝ) * q.b) := by
    have : ((q.b : ℝ) * Real.sqrt 3) * ((q.b : ℝ) * Real.sqrt 3)
        = ((q.b : ℝ) * q.b) * (Real.sqrt 3 * Real.sqrt 3) := by ring
    rw [this, s]; ring
  unfold val at h
  unfold nonnegB
  split_ifs with ha hb hb
  · rfl
  · apply decide_eq_true
    have ha' : (0 : ℝ) ≤ q.a := by exact_mod_cast ha
    have hb' : (q.b : ℝ) < 0 := by exact_mod_cast lt_of_not_ge hb
    have h1 : 0 ≤ -((q.b : ℝ) * Real.sqrt 3) := by nlinarith
    have h2 : -((q.b : ℝ) * Real.sqrt 3) ≤ q.a := by linarith
    have : 3 * ((q.b : ℝ) * q.b) ≤ (q.a : ℝ) * q.a := by nlinarith
    exact_mod_cast this
  · apply decide_eq_true
    have ha' : (q.a : ℝ) < 0 := by exact_mod_cast lt_of_not_ge ha
    have hb' : (0 : ℝ) ≤ q.b := by exact_mod_cast hb
    have h1 : 0 ≤ -(q.a : ℝ) := by linarith
    have h2 : -(q.a : ℝ) ≤ (q.b : ℝ) * Real.sqrt 3 := by linarith
    have : (q.a : ℝ) * q.a ≤ 3 * ((q.b : ℝ) * q.b) := by nlinarith
    exact_mod_cast this
  · exfalso
    have ha' : (q.a : ℝ) < 0 := by exact_mod_cast lt_of_not_ge ha
    have hb' : (q.b : ℝ) < 0 := by exact_mod_cast lt_of_not_ge hb
    nlinarith

end Q3

/-! ## Polynomials in `u` -/

abbrev UPoly := List Q3

namespace UPoly

noncomputable def eval : UPoly → ℝ → ℝ
  | [], _ => 0
  | c :: cs, u => c.val + u * eval cs u

def add : UPoly → UPoly → UPoly
  | [], q => q
  | p, [] => p
  | a :: p, b :: q => Q3.add a b :: add p q

def scale (k : Q3) : UPoly → UPoly
  | [] => []
  | a :: p => Q3.mul k a :: scale k p

def neg (p : UPoly) : UPoly := scale ⟨-1, 0⟩ p

def mul : UPoly → UPoly → UPoly
  | [], _ => []
  | a :: p, q => add (scale a q) (Q3.zero :: mul p q)

def pow (p : UPoly) : ℕ → UPoly
  | 0 => [Q3.one]
  | n + 1 => mul p (pow p n)

def isZero (p : UPoly) : Bool := p.all fun c => c.a == 0 && c.b == 0

@[simp] lemma eval_nil (u : ℝ) : eval [] u = 0 := rfl
@[simp] lemma eval_cons (c : Q3) (cs : UPoly) (u : ℝ) : eval (c :: cs) u = c.val + u * eval cs u := rfl

@[simp] lemma eval_add (p q : UPoly) (u : ℝ) : eval (add p q) u = eval p u + eval q u := by
  induction p generalizing q with
  | nil => cases q <;> simp [add]
  | cons a p ih => cases q with
    | nil => simp [add]
    | cons b q => simp only [add, eval_cons, Q3.val_add, ih]; ring

@[simp] lemma eval_scale (k : Q3) (p : UPoly) (u : ℝ) : eval (scale k p) u = k.val * eval p u := by
  induction p with
  | nil => simp [scale]
  | cons a p ih => simp only [scale, eval_cons, Q3.val_mul, ih]; ring

@[simp] lemma eval_neg (p : UPoly) (u : ℝ) : eval (neg p) u = -eval p u := by
  simp [neg, Q3.val]

@[simp] lemma eval_mul (p q : UPoly) (u : ℝ) : eval (mul p q) u = eval p u * eval q u := by
  induction p with
  | nil => simp [mul]
  | cons a p ih => simp only [mul, eval_add, eval_scale, eval_cons, Q3.val_zero, ih]; ring

@[simp] lemma eval_pow (p : UPoly) (n : ℕ) (u : ℝ) : eval (pow p n) u = eval p u ^ n := by
  induction n with
  | zero => simp [pow]
  | succ n ih => simp only [pow, eval_mul, ih]; ring

lemma eval_of_isZero {p : UPoly} (h : isZero p = true) (u : ℝ) : eval p u = 0 := by
  induction p with
  | nil => rfl
  | cons c p ih =>
    simp only [isZero, List.all_cons, Bool.and_eq_true, beq_iff_eq] at h
    obtain ⟨⟨ha, hb⟩, hp⟩ := h
    simp only [eval_cons, Q3.val, ha, hb, ih hp]; simp

end UPoly

/-! ## Affine forms in the centre -/

structure Aff where
  c1 : UPoly
  cx : UPoly
  cy : UPoly

namespace Aff

noncomputable def eval (f : Aff) (x y u : ℝ) : ℝ :=
  f.c1.eval u + f.cx.eval u * x + f.cy.eval u * y

def add (f g : Aff) : Aff := ⟨f.c1.add g.c1, f.cx.add g.cx, f.cy.add g.cy⟩
def mulU (p : UPoly) (f : Aff) : Aff := ⟨p.mul f.c1, p.mul f.cx, p.mul f.cy⟩
def neg (f : Aff) : Aff := ⟨f.c1.neg, f.cx.neg, f.cy.neg⟩
def zero : Aff := ⟨[], [], []⟩
def const (p : UPoly) : Aff := ⟨p, [], []⟩
def isZero (f : Aff) : Bool := f.c1.isZero && f.cx.isZero && f.cy.isZero

@[simp] lemma eval_add (f g : Aff) (x y u : ℝ) : (add f g).eval x y u = f.eval x y u + g.eval x y u := by
  simp only [eval, add, UPoly.eval_add]; ring
@[simp] lemma eval_mulU (p : UPoly) (f : Aff) (x y u : ℝ) :
    (mulU p f).eval x y u = p.eval u * f.eval x y u := by
  simp only [eval, mulU, UPoly.eval_mul]; ring
@[simp] lemma eval_neg (f : Aff) (x y u : ℝ) : (neg f).eval x y u = -f.eval x y u := by
  simp only [eval, neg, UPoly.eval_neg]; ring
@[simp] lemma eval_zero (x y u : ℝ) : zero.eval x y u = 0 := by simp [eval, zero]
@[simp] lemma eval_const (p : UPoly) (x y u : ℝ) : (const p).eval x y u = p.eval u := by
  simp [eval, const]

lemma eval_of_isZero {f : Aff} (h : isZero f = true) (x y u : ℝ) : f.eval x y u = 0 := by
  simp only [isZero, Bool.and_eq_true] at h
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  simp [eval, UPoly.eval_of_isZero h1, UPoly.eval_of_isZero h2, UPoly.eval_of_isZero h3]

end Aff

end SquarePacking.Tri
