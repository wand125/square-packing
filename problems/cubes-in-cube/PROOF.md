# Proof that s₃(9) = s₃(10) = 2 + 1/√2

Throughout, s = 2 + 1/√2, so s − 2 = 1/√2, and V = {1, s − 1}³ is a set of 8 points.

A *pose* is a pair (R, c) with R ∈ SO(3) and c ∈ ℝ³. Its cube is Q = {c + R t : ‖t‖_∞ ≤ ½}. The columns
a_0, a_1, a_2 of R are the cube's axes. For a point p, the local coordinates are t_i(p) = a_i · (p − c), and p ∈ Q
iff |t_i(p)| ≤ ½ for i = 0, 1, 2. Write h_w = ½ Σ_j |R_wj|, which is half the ℓ¹ norm of row w of R. Q ⊆ [0, s]³
iff h_w ≤ c_w ≤ s − h_w for every world axis w (support function). Every row is a unit vector, so
½ ≤ h_w ≤ √3/2 < s/2.

## 1. Main lemma and the scaling argument

**Main lemma (8-point lemma).** Every closed unit cube Q ⊆ [0, s]³ contains a point of V. A point on the
boundary of Q counts.

**Theorem.** s₃(9) = s₃(10) = s.

*Proof.* Upper bound: `upper/` gives exact packings of 9 and 10 unit cubes in [0, s]³, written in Q(√2). Each is
checked by two independent exact checkers. They are the packings listed on Erich Friedman's page (§6).

Lower bound: suppose 9 unit cubes with pairwise disjoint interiors fit in [0, L]³ with L < s. Then we can find
9 closed unit cubes in [0, s]³ that are pairwise disjoint, as follows.
- Put λ = L/s < 1.
- Translate each cube by (1/λ − 1)·c_i, where c_i is its centre. The new centre is c_i/λ and the
  orientation is unchanged.
- The translated cube lies in [0, s]³. With h_w the support values of the cube, the original cube satisfies
  h_w ≤ c_{i,w} ≤ L − h_w. Dividing by λ gives
  h_w ≤ h_w/λ ≤ c_{i,w}/λ ≤ (L − h_w)/λ = s − h_w/λ ≤ s − h_w,
  which is the containment condition for the translated cube.
- Two cubes with disjoint interiors have a separating direction u with u·(c_j − c_i) ≥ σ_i(u) + σ_j(u) > 0
  (σ the support values). After the translation the left side is multiplied by 1/λ > 1, so the inequality
  becomes strict and the closed cubes are disjoint.

By the main lemma each of the 9 closed cubes contains a point of V. Since |V| = 8, two of them share a point,
which contradicts disjointness. Hence s₃(9) ≥ s, and s₃(10) ≥ s₃(9) ≥ s. ∎

The rest of this document proves the main lemma. A pose with ‖t‖_∞ ≤ ½ at a point counts as containing it,
and every inequality below is closed. The bound is attained (9 cubes fit at side s), so no strict margin can
be bought; the zero-margin poses are handled exactly by the lemmas below.

## 2. Lemma F (centre lemma)

**Lemma F.** For every R ∈ SO(3) and every column k, F_k(R) := Σ_w |R_wk| (2 − 2h_w) ≤ 1.

This is the inequality behind s₃(2) = 2. The proof is in `lemma_f/PROOF.md`:
- a hand proof when some |R_wk| ≥ 1/√2;
- a computer proof elsewhere, by two independent exact or interval checkers.

**Corollary (centre rule).** If |p_w − c_w| ≤ 1 − h_w for every w, then p ∈ Q.

*Proof.* |t_i(p)| ≤ Σ_w |R_wi| |p_w − c_w| ≤ Σ_w |R_wi|(1 − h_w) = ½F_i(R) ≤ ½. ∎

At the wall p_w = 1 with h_w ≤ c_w ≤ 1, the condition reads 1 − c_w ≤ 1 − h_w, which always holds. The checkers
use the parametrisation c_w = h_w + u_w(s − 2h_w), u_w ∈ [0, 1], which keeps this exact under interval arithmetic.

## 3. Wall lemma

**Wall lemma.** Let p ∈ V with p_w = 1, and assume c_w ≥ h_w (lower wall). Suppose that for an axis i and a sign
σ we have σR_wi > 0 and |R_wj| + |t_j(p)| ≤ ½ for both j ≠ i. Then σ t_i(p) ≤ ½.

*Proof.* Row w of p − c = R t gives Σ_j R_wj t_j = 1 − c_w ≤ 1 − h_w. Put ρ = |R_wi| = σR_wi > 0. Then
ρ·σt_i = R_wi t_i ≤ 1 − h_w + Σ_{j≠i} |R_wj||t_j| = 1 − ½ρ − Σ_{j≠i} |R_wj|(½ − |t_j|).
By hypothesis ½ − |t_j| ≥ |R_wj|, so the last sum is at least Σ_{j≠i} R_wj² = 1 − ρ². Hence
ρ·σt_i ≤ ρ² − ½ρ, so σt_i ≤ ρ − ½ ≤ ½. ∎

The upper wall (p_w = s − 1, c_w ≤ s − h_w) is the mirror image c ↦ s − c.

**Tightening at a wall.** If p_w = 1, c_w ≥ h_w and R_wk ≥ 0, then
R_wk(p_w − c_w) ≤ R_wk(1 − h_w) = ½ − ½(1 − R_wk)² − ½R_wk σ_wk, where σ_wk = Σ_{j≠k} |R_wj|.
The identity follows from 2h_w = R_wk + σ_wk. The bound replaces the w-term of the upper bound of t_k(p) and
avoids interval dependency. The case R_wk ≤ 0 (lower bound) and the upper wall are mirror images.

## 4. Pair lemma

Let p, q ∈ V differ in exactly two coordinates. Then d = q − p has two entries ±1/√2, so |d| = 1, and there are
12 such pairs. We have t_i(q) = t_i(p) + a_i·d, and |a_i·d| ≤ 1.

**Pair lemma.** Suppose that for some axis i and sign σ:
- both points satisfy |t_j| ≤ ½ for both j ≠ i;
- σt_i(p) ≤ ½;
- σt_i(q) ≥ −½.

Then p ∈ Q or q ∈ Q.

*Proof.* If σt_i(p) ≥ −½, then p ∈ Q. Otherwise σt_i(q) ≤ σt_i(p) + 1 < ½, so q ∈ Q. ∎

## 5. Local sign lemma

The checkers do not close one pose by the rules above: the cube rotated 45° about the x axis, touching the wall
x = 0, with centre (½, s/2, s/2). Its four points with x = 1 lie at the midpoints of the edges of its face
x = 1. Near this pose, which of them is contained switches with the sign of two continuous quantities. No box
around the pose can therefore be closed by naming one point. The following lemma names two points and closes a
whole neighbourhood, including the pose itself.

Notation:
- g = (1, s/2, s/2), the centre of the four points with x = 1;
- the four points are q_σ = g + a(0, σ_y, σ_z), with σ ∈ {±1}² and a = s/2 − 1 = 1/(2√2);
- f = c + ½a_0, the centre of the far face;
- e = g − f, p = a_1·e and r = a_2·e;
- ν = (a_0y, a_0z) and d = (s/2 − c_y, s/2 − c_z).

**Lemma L.** Assume all of the following:
- c_x ≥ h_x and a_0x > 0;
- ‖d‖₂ < ½a_0x − a;
- a_1y + a_1z ≥ 0 and a_2z − a_2y ≥ 0;
- |p| ≤ ½ and |r| ≤ ½;
- |r| + a|a_2y + a_2z| ≤ ½ and |p| + a|a_1y − a_1z| ≤ ½;
- t_0(q_σ) ≥ −½ for all four σ.

Put ς_A = −sgn p and ς_B = sgn r (either sign if p = 0 or r = 0). Then A = q_(ς_A, ς_A) or B = q_(ς_B, −ς_B)
lies in Q.

*Proof.* For a point q, q ∈ Q iff t_0(q) ≥ −½ and the following three conditions hold:
- (i) a_0·(q − f) ≤ 0, i.e. t_0(q) ≤ ½;
- (ii) |a_1·(q − f)| ≤ ½;
- (iii) |a_2·(q − f)| ≤ ½.

The first condition, t_0(q) ≥ −½, is a hypothesis.

1. *(ii) and (iii) by signs.*
   - a_1·(A − f) = p + ς_A a(a_1y + a_1z). Here a|a_1y + a_1z| ≤ a√2 = ½, and the two terms have opposite signs,
     so |a_1·(A − f)| ≤ max(|p|, ½) ≤ ½.
   - |a_2·(A − f)| ≤ |r| + a|a_2y + a_2z| ≤ ½.
   - For B in the same way: a_2·(B − f) = r − ς_B a(a_2z − a_2y), whose two terms have opposite signs, and
     |a_1·(B − f)| ≤ |p| + a|a_1y − a_1z| ≤ ½.
2. *(i) from the wall.*
   - a_0·e = a_0x(1 − c_x) + ν·d − ½.
   - From c_x ≥ h_x and the identity a_0x(1 − h_x) = ½ − ½(1 − a_0x)² − ½a_0xσ_x, with σ_x = |a_1x| + |a_2x|, we
     get a_0·e ≤ ν·d − ½a_0xσ_x − ½(1 − a_0x)².
   - Row x and column 0 of R are unit vectors, so a_1x² + a_2x² = 1 − a_0x² = ‖ν‖², and hence σ_x ≥ ‖ν‖.
   - Since a_0·(q_σ − f) = a_0·e + a ν·σ, condition (i) for q_σ follows from ν·d + aν·σ ≤ ½a_0x‖ν‖.
3. *A and B cannot both fail (i).*
   - We have ν·σ_A = ς_A(ν_y + ν_z) and ν·σ_B = ς_B(ν_y − ν_z).
   - If both fail, then ν·d + a·min(|ν_y + ν_z|, |ν_y − ν_z|) > ½a_0x‖ν‖. The minimum is at most
     √(((ν_y + ν_z)² + (ν_y − ν_z)²)/2) = ‖ν‖, so ν·d > (½a_0x − a)‖ν‖.
   - But ν·d ≤ ‖ν‖‖d‖ < (½a_0x − a)‖ν‖, a contradiction when ν ≠ 0.
   - If ν = 0, then a_0x = 1 and σ_x = 0, so (i) holds for every σ. ∎

*Remarks.*
- The proof uses only that (a_0, a_1, a_2) is an orthonormal frame with Q = {c + Σ t_k a_k : |t_k| ≤ ½}.
  Orientation is never used, so the lemma applies to any signed permutation of the columns of R.
- The images of the lemma under the symmetries of the container that fix V (coordinate permutations and
  reflections c ↦ s − c) hold as well.
- At the pose itself, p = r = 0, A lies on an edge of Q and (i) holds with equality. Since Q is closed, A ∈ Q.

## 6. Computer part and sources

The main lemma is reduced to finitely many interval inequalities over a 6-parameter domain (rotation and
centre). Two independent checkers cover the whole domain, using §2 to §5 as closing rules. Each box is closed by
one rule, or split. See `checker/README.md` and `checker2/README.md` for:
- the parametrisations and symmetry reductions;
- the arithmetic;
- receipts with chained SHA-256 digests over the leaf stream;
- reproduction commands.

Sources, in three layers:
- **Classical.** The point-set method is the standard lower-bound technique for packing unit squares in squares,
  described in Erich Friedman's survey "Packing unit squares in squares: a survey and new results" (Electronic
  Journal of Combinatorics, Dynamic Survey DS7).

  The packings of 9 and 10 cubes at side 2 + 1/√2 are listed on Erich Friedman's Packing Center page
  "Cubes in Cubes" (https://erich-friedman.github.io/packing/cubincub/). As far as we found, no proof of their
  optimality has been published.
- **Our earlier lemmas.** These come from our work on s₃(2) = 2 and on s₃(k³ − 1) = k:
  - Lemma F (§2);
  - the wall lemma (§3);
  - the pair lemma (§4).
- **New here.** The 8-point main lemma, the local sign lemma (§5), and the two checkers.
