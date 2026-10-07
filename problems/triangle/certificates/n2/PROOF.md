# Two unit squares in an equilateral triangle

**Theorem.** The smallest equilateral triangle containing two non-overlapping unit squares has side
v = 2 + 2/√3 ≈ 3.1547.

Upper bound: two squares side by side on the base; at height 1 the triangle has width v − 2/√3 = 2.

Lower bound: a one-point unavoidable set, the centroid G.

## Lemma

Let T be the equilateral triangle of side v with centroid G. Every closed unit square Q ⊆ T contains G.

*Proof.*

1. Write Q = c + R_θ[−½, ½]². Because both the pair (T, {G}) and the square are symmetric, it is
   enough to take θ ∈ [0, π/12]:
   - the square's angle only matters modulo π/2;
   - the rotation by 2π/3 about G maps θ to θ + π/6 (mod π/2);
   - the reflection in the vertical axis through G maps θ to −θ.
2. T is the intersection of three half-planes {x : n_k·(x − G) ≥ −r}. Here r = v/(2√3) is the inradius
   and the n_k are the inward unit normals, at angles π/2, 7π/6 and 11π/6.
   Q ⊆ T if and only if its centre satisfies n_k·(c − G) ≥ −(r − h_k(θ)) for each k. Here
   h_k(θ) = (|cos(φ_k − θ)| + |sin(φ_k − θ)|)/2 is the support of the unit square in direction n_k.
   So the admissible centres form a triangle D_θ; it is non-empty because Σ(r − h_k) > 0.
   On [0, π/12] the supports have the closed forms
   - h_0 = (cos θ + sin θ)/2
   - h_1 = (cos(π/6 − θ) + sin(π/6 − θ))/2
   - h_2 = (cos(π/6 + θ) + sin(π/6 + θ))/2
   With a_k = r − h_k, the vertices of D_θ relative to G are
   - V01 = ((2a_1 + a_0)/√3, −a_0)
   - V02 = (−(2a_2 + a_0)/√3, −a_0)
   - V12 = ((a_1 − a_2)/√3, a_1 + a_2)
3. G ∈ Q if and only if c − G lies in the square R_θ[−½, ½]². This set is convex, so every admissible
   c qualifies if and only if the three vertices of D_θ do. For each vertex V and each axis
   e ∈ {(cos θ, sin θ), (−sin θ, cos θ)}, this means the twelve functions
   g(θ) = ½ ∓ V(θ)·e(θ) are non-negative on [0, π/12].
4. `check_n2.py` verifies this rigorously; the output is in `check_n2.out`.
   - The exact values g(0) and g′(0) are computed in Q(√3) with sympy.
   - On [0, 1/100] it uses g(θ) ≥ g(0) + g′(0)θ − Mθ²/2, where M is an interval-arithmetic bound on
     |g″| (mpmath `iv`, 40 digits).
   - On [1/100, π/12] it uses interval enclosures on 400 sub-intervals.
   - Two functions vanish at θ = 0, namely V01·e1 and V02·(−e1). These are the two bottom-corner
     squares of the extremal packing. Their derivatives there are (2√3 − 2)/3 and (2 − √3)/3, both
     > 0. All twelve functions pass. ∎

## From the lemma to the theorem

Suppose two unit squares with disjoint interiors lie in an equilateral triangle T_L of side L < v.
Take T_L with the same centroid G as T_v, and put λ = v/L > 1. Translate each square Q_i
(centre c_i) by (λ − 1)(c_i − G). Two things follow.

- **Containment.** For p ∈ Q_i we have p + (λ − 1)(c_i − G) − G = λ[(p − G)/λ + (1 − 1/λ)(c_i − G)].
  The bracket is a convex combination of points of T_L − G, so the translated square lies in
  λ(T_L − G) = T_v − G.
- **Disjointness.** Let u be a direction that separates the interiors. Then
  u·(c_2 − c_1) ≥ h_{Q_1}(u) + h_{Q_2}(u) > 0, and the translation increases this gap by
  (λ − 1)u·(c_2 − c_1) > 0. So the translated closed squares are disjoint.

Both translated squares lie in T_v, so by the lemma both contain G. They are disjoint, which is a
contradiction. Hence s△(2) ≥ v, and with the construction s△(2) = v. ∎

## Context

Friedman's table lists n = 1 and n = 2 as "Trivial". This note does not claim that the value for
n = 2 is new; it writes out one short proof, in the same framework (unavoidable weighted points,
a check at the container itself, and the centre-scaling argument) that is used for n ≥ 3.

## Machine check of the certificate

The one-point certificate `n2_cert.json` (the centroid, weight 1) is also verified at margin zero
by both checkers. `check_n2.py` is a third, stand-alone verification of the lemma above; it needs
Python with sympy and mpmath. Recorded run: Python 3.10.18, sympy 1.14.0, mpmath 1.3.0.

## Status

- Verified by two independently written checkers:
  - `../../checker/` (exact Bernstein bounds over Q(√3));
  - `../../checker2/` (a different method; see its README, including the Independence section).
- Not peer reviewed.
- Not yet formalised in Lean.
