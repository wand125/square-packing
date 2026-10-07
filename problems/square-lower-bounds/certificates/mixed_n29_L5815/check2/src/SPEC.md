# Fine-net density certificates: specification for the independent check

This specification was written from the certificate data and a prose description of the
certificate, without reading the code that produced the certificates.

## 1. Claim

No n closed unit squares fit with pairwise disjoint interiors in the closed square
container [0, L]². Hence s(n) ≥ L.

## 2. Certificate (`candidate.json`)

| Field | Meaning |
|---|---|
| `n` | number of squares (integer) |
| `L` | container side (rational as a string; a decimal string means the rational it denotes) |
| `B` | core side (rational) |
| `proof_net` | `{step, last}`: the angle net t_j = j·step for j = 0..last, with t = tan(θ/2) |
| `total_mass` | total mass M (rational) |
| `rectangles` | rows `{rectangle: [x0, y0, x1, y1], mass}` with 0 ≤ x0 < x1 ≤ L, 0 ≤ y0 < y1 ≤ L, mass ≥ 0; `mass` is the rectangle's whole mass |
| `points` | rows `{point: [x, y], mass}` (empty in the certificates so far) |

**The measure μ (D4 average).** Each listed rectangle R of mass m is placed, with mass m/8
spread uniformly, on each of its eight images under the symmetry group D4 of the container
(with or without swapping x and y, times with or without x → L − x, times with or without
y → L − y). Each image has density m/(8·area), and overlapping images add. μ is the sum.
The list itself need not be symmetric. Points are not averaged: the listed point measure
itself must be D4-invariant. The total mass is the sum of the listed masses and must equal
`total_mass` exactly.

## 3. Conditions checked (these alone decide validity)

1. **Mass:** M = Σ mass exactly, and 0 < M < n·Γ, with Γ = 1.
2. **Net:** 0 < B < 1, B·(1 + step) < 1, and (1 + last·step)² > 2 (the net reaches past
   tan(π/8) = √2 − 1).
3. **Capture:** for every j = 0..last and every centre c in the range
   C_j = [r(a_j), L − r(a_j)]², the closed square (the core) K with centre c, angle
   θ_j = 2·atan(t_j) and side B has μ(K) ≥ Γ.
   - a_j = max(0, t_j − step/2), r(t) = (cos θ + sin θ)/2 = (1 + 2t − t²)/(2(1 + t²)).
   - cos θ_j = (1 − t_j²)/(1 + t_j²) and sin θ_j = 2t_j/(1 + t_j²) are rational.
4. **Rigour:** every decision is made in exact rationals or in interval arithmetic with
   outward rounding; a floating-point estimate alone never decides.

## 4. Proof (conditions 1 to 3 imply the claim)

- **Orientations.** μ is D4-invariant, so the unit squares' orientations may be restricted
  to θ ∈ [0, π/4] (t ∈ [0, √2 − 1]).
- **Net lemma.** A unit square with orientation t ∈ [t_j − step/2, t_j + step/2] ∩ [0, √2 − 1]
  contains in its interior the core with the same centre, angle θ_j and side B. With
  δ = θ − θ_j, z = tan(|δ|/2) = |t − t_j|/(1 + t·t_j) ≤ step/2. A square of side B with the
  same centre, turned by δ, lies inside the unit square iff B(cos δ + sin δ) ≤ 1, and
  cos δ + sin δ = (1 − z² + 2z)/(1 + z²) ≤ 1 + 2z ≤ 1 + step; B(1 + step) < 1 puts it in the
  interior. The cells cover [0, (last + ½)·step] ⊇ [0, √2 − 1] by condition 2.
- **Centre range.** A unit square with orientation θ inside the container has its centre at
  distance at least r(t) from each wall. r increases on [0, √2 − 1], so its value at the
  cell's lower end a_j is the least, and C_j contains the centres of every orientation the
  cell covers.
- **Contradiction.** If n squares fit, their cores are pairwise disjoint (each lies in the
  open interior of its square). By condition 3 each core has measure at least Γ, so
  n·Γ ≤ μ(container) = M, contradicting condition 1.

## 5. The verifier

- Base: sqverify_fast from jlevy/squares (`packing/sqverify_fast`), a clean-room Rust
  verifier of measure-capture certificates: interval branch and bound with outward rounding
  over centre boxes, and an exact event sweep at direction 0. Its format M has exactly the
  D4-average meaning of §2.
- One change: a format M candidate that declares `proof_net {step, last}` takes the step and
  the direction count last + 1 from it (the original fixes 83/40000 and 201 directions).
  The net premises are checked as before: B(1 + D) < 1, the per-bin tangent form
  B(1 + D/(1 − D²/4)) < 1, the endpoint, and last·step ≤ 1/2. The lemmas of the verifier's
  SOUNDNESS.md (N1 to N3, D) are stated for a general step D.
- The centre range is the verifier's "per-bin" domain (the same formula as a_j in §3).
  Reducing centres by D4 to [L/2, U_j]² is internal to the verifier.

## 6. Hierarchical nets (not supported yet)

Lemma for a t-interval I = [a, b] (a ≥ 0) with representative t_I ∈ I and core side B_I:
if B_I·(1 + 2·z_I) < 1 with z_I = max(t_I − a, b − t_I)/(1 + a·t_I), a unit square with
orientation in I contains in its interior the core with the same centre, angle t_I and
side B_I; its centre range is [r(a), L − r(a)]². A checker would rebuild the interval tree
itself rather than replay a record. Certificates in this form are not checked by the
verifier above.
