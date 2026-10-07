# The local lemma in one page (n = 3, regular hexagon)

This is a hand-readable summary of `LOCAL_LEMMA.md`. Only two facts are computer-checked:

- the identity (1) below, in `ll_exact.py`;
- the numerical inequality (A) below, in `ll_radius.py`.

## Setting

- v = (1+√3)/2 and h = v√3/2. The hexagon H has side v and a flat bottom.
- V = (−v/2, −h) is its lower-left vertex.
- n = (−√3/2, −1/2) is the outward normal of the lower-left side. e_y = (0, 1).
- R is the rotation by 2π/3. R(φ) is the rotation by φ.

In frame i (rotate by R^{−i}), square i is

    V + p_i + R(φ_i)[0,1]².

- p_i is the displacement of its lower-left corner from the vertex.
- φ_i is its tilt.
- The pinwheel is p_i = 0, φ_i = 0.

**Lemma.** If |φ_i| ≤ 0.08 and |p_i| ≤ 0.05 for i = 0, 1, 2, the three closed squares cannot lie in H and be
pairwise disjoint.

## Proof

### Step 0: the wedge

The lower-left corner lies in H, so e_y·p_i ≥ 0 and −n·p_i ≥ 0. That is, p_i lies in the 120° wedge W.

On W, (e_y − n)·p ≥ (√3/2)|p|:

- e_y − n = (√3/2, 3/2);
- it gives exactly √3/2 on both unit edge rays of W, (1, 0) and (−1/2, √3/2).

### Step 1: the contacts

Let k_i be the signed distance of the top-right corner of square i beyond the top-edge line of square i+1.

At the pinwheel this corner sits on that edge. Its distances to the other three edges are 0.366, 0.634 and 1.

Under the allowed perturbation these distances change by at most 0.316. So the corner stays strictly inside
those three edges. Therefore disjointness forces k_i > 0.

### Step 2: the identity (1)

Write δ_i = φ_i − φ_{i+1}. Then

    k_i = F_i + (R(φ_{i+1})n)·p_i − (R(φ_{i+1})e_y)·p_{i+1},
    F_i = (1+v)(cos φ_{i+1} − 1) + v(1 − cos δ_i) + (v−1) sin δ_i.

### Step 3: two consequences

Let Φ = max|φ_i| and P = Σ|p_i|.

- On W we have n·p_i ≤ 0 and e_y·p_{i+1} ≥ 0. Also |R(ψ)w − w| ≤ |ψ||w|. Hence

      (i)  0 < k_i ≤ F_i + Φ(|p_i| + |p_{i+1}|).

- In Σk_i the p_i-terms collect to (n − e_y)·p_i + O(Φ)|p_i|. With Step 0,

      (ii) 0 < Σ k_i ≤ Σ F_i − (√3/2 − 2Φ) P.

### Step 4, case A: equal tilts (the flex)

- Σ F_i = 3(1+v)(cos t − 1) ≤ 0.
- But (ii) needs Σ F_i > 0 (or P < 0).
- This is a contradiction.

### Step 5, case B: unequal tilts

Let Δ = max|δ_i| > 0. Since Σδ_i = 0, some δ_j ≤ −Δ/2. Then

- F_j ≤ −(v−1) sin(Δ/2) + vΔ²/2;
- Σ F_i ≤ vΔ² + (v−1)Δ³/2, because Σ sin δ_i = Σ(sin δ_i − δ_i);
- P < Σ F_i/(√3/2 − 2Φ), by (ii).

Put these into (i):

    0 < k_j < Δ [ −(v−1)/2·(1 − Δ²/24) + vΔ/2 + Φ(vΔ + (v−1)Δ²/2)/(√3/2 − 2Φ) ].

The bracket is increasing in Δ ≤ 2Φ ≤ 0.16 and in Φ. At Δ = 0.16, Φ = 0.08 it equals
−0.1828 + 0.1346 < 0. (A)

This is a contradiction. ∎

## Remarks

- The coefficient (v − 1) sin δ is what makes the pinwheel rigid against unequal tilts. It is first order.
- The term (1+v)(cos t − 1) is what makes the flex fail. It is second order, about −1.18 t² per contact.
- The radii 0.08 and 0.05 are limited by Step 1, the contact validity, not by (A). The inequality (A) alone
  would allow tilts up to about 0.1.
