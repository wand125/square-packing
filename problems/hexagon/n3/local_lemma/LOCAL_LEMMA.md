# Local lemma for three unit squares in the regular hexagon (near the pinwheel)

Checks: `ll_exact.py` (exact sympy identity) and `ll_radius.py` (exact rational check of the radius
conditions, plus a float search for counterexamples).

## Setting

- H is the regular hexagon with side v = (1 + √3)/2, centre 0 and a flat bottom.
- Its apothem is h = v√3/2.
- V = (−v/2, −h) is its lower-left vertex on the bottom side.
- R is the rotation by 2π/3. V_i = R^i V for i = 0, 1, 2.
- n = (−√3/2, −1/2) is the outward normal of the lower-left side. e_y = (0, 1).

The pinwheel P consists of the squares P_i = R^i B, where B = [−v/2, −v/2 + 1] × [−h, −h + 1].

- The lower-left corner of B is the vertex V.
- B has one side on the bottom side of H.
- The top-right corner of P_i lies on the top edge of P_{i+1}, indices mod 3.

Parametrisation of a square near P_i:

- Rotate by R^{−i} ("frame i").
- The square is then the image of [0,1]² under q ↦ V + p_i + R(φ_i) q.
- p_i is the displacement of the lower-left corner from V.
- φ_i is the tilt.

## Lemma

Let ρ = 0.08 and ρ_p = 0.05. There are no three pairwise disjoint closed unit squares Q_0, Q_1, Q_2 in H
such that, for each i, Q_i has a parametrisation in frame i with |φ_i| ≤ ρ and |p_i| ≤ ρ_p.

By the D6 symmetry of H, the same holds near every image of P, including the mirror pinwheel.

## Proof

### 1. Containment

- The lower-left corner of Q_i lies in H.
- In frame i, the two sides of H through V give e_y · p_i ≥ 0 and −n · p_i ≥ 0.
- So p_i lies in the wedge W spanned by r_1 = (1, 0) and r_2 = (−1/2, √3/2).
- On W we have (e_y − n) · p ≥ κ |p| with κ = √3/2.
  - e_y − n = (√3/2, 3/2) takes the value √3/2 on both unit rays r_1 and r_2.
  - Write p = α r_1 + β r_2 with α, β ≥ 0. Then |p| ≤ α + β.

### 2. Contacts

- Let j = i + 1.
- Let k_i be the signed distance of the top-right corner T_i of Q_i beyond the line of the top edge of Q_j.
- The sign is positive on the outside of Q_j.
- In frame i, Q_j is R(V + p_j + R(ψ)(1/2, 1/2)) + rotation, with ψ = φ_j.

Exact identity (`ll_exact.py`):

    k_i = F(φ_i, φ_j) + (R(φ_j) n) · p_i − (R(φ_j) e_y) · p_j,
    F(φ, ψ) = (1+v)(cos ψ − 1) − v (cos(φ − ψ) − 1) + (v − 1) sin(φ − ψ).

Disjointness forces k_i > 0, for the following reason.

- At P, T_i lies on the top edge of P_j.
- Its distances to the three other edge lines of P_j are (√3 − 1)/2 ≈ 0.366, (3 − √3)/2 ≈ 0.634 and 1.
- Under the perturbation, each of these distances changes by at most

      |p_i| + |p_j| + √2 |φ_i| + (|Y_0| + 2ρ_p + √2 ρ) |φ_j|  ≤  0.3154,

  where Y_0 is the vector from the lower-left corner of P_j to T_i, with |Y_0| ≤ 1.065.
- So T_i stays strictly inside those three lines.
- If k_i ≤ 0, then T_i ∈ Q_j ∩ Q_i, which contradicts disjointness.

### 3. Two inequalities

Let Φ = max |φ_i| and Pw = Σ |p_i|.

Since n · p_i ≤ 0 and e_y · p_j ≥ 0 on W, and |R(ψ)w − w| ≤ |ψ| |w|:

    (i)   k_i ≤ F(φ_i, φ_{i+1}) + Φ (|p_i| + |p_{i+1}|) ≤ F_i + Φ Pw.

Summing the identity over i, the coefficient of p_i is R(φ_{i+1}) n − R(φ_i) e_y. This equals
(n − e_y) + O(Φ). With step 1, this gives

    (ii)  0 < Σ k_i ≤ Σ F_i − (κ − 2Φ) Pw.

### 4. Case A: equal tilts

Suppose φ_0 = φ_1 = φ_2 = t. This is the flex.

- Σ F_i = 3(1+v)(cos t − 1) ≤ 0.
- But (ii) needs Σ F_i > (κ − 2Φ) Pw ≥ 0.
- This is a contradiction. The case t = 0, Pw > 0 is included.

### 5. Case B: unequal tilts

- Let δ_i = φ_i − φ_{i+1}. Then Σ δ_i = 0. Let Δ = max |δ_i| > 0, so Δ ≤ 2ρ.
- Some j has δ_j ≤ −Δ/2.
- Then F_j ≤ (v − 1) sin δ_j + v δ_j²/2 ≤ −(v − 1) sin(Δ/2) + v Δ²/2.

Bound on the sum:

- Since Σ δ_i = 0, |Σ sin δ_i| = |Σ (sin δ_i − δ_i)| ≤ Σ|δ_i|³/6 ≤ Δ³/2.
- Also Σ δ_i² ≤ 2Δ².
- Hence Σ F_i ≤ v Δ² + (v − 1) Δ³/2.

Combining:

- By (ii), Pw < Σ F_i / (κ − 2Φ).
- By (i), k_j ≤ F_j + Φ Pw.
- With sin x ≥ x(1 − x²/6), this gives

      k_j < Δ [ −(v−1)/2 (1 − Δ²/24) + vΔ/2 + Φ (vΔ + (v−1)Δ²/2)/(κ − 2Φ) ].

- The bracket increases in Δ and in Φ. At Δ = 2ρ and Φ = ρ it equals −0.18282 + 0.13458 < 0.
- This is checked exactly with rational bounds in `ll_radius.py`.
- So k_j < 0, which contradicts step 2. ∎

## Numerical cross-check

- `ll_radius.py` maximises min_i k_i over the lemma's region, with p_i ∈ W and |p_i| ≤ 0.05.
- It used Nelder–Mead from 3000 starts.
- The maximum found is −1.8·10⁻³. The value 0 is attained only at the pinwheel itself.

## Use in the proof of s(3) = v

The lemma removes this whole neighbourhood of every image of the pinwheel:

- tilts within 0.08 rad (4.6°);
- lower-left corners within 0.05 of their vertices.

What remains for the branch and bound is the part of the stage-1 tube N outside these neighbourhoods. There
the flex already overlaps by at least 1.18 · 0.08² ≈ 0.0076.
