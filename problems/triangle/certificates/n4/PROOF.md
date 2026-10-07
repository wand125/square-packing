# Four unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing four non-overlapping
unit squares has side v = 3 + 2/√3 ≈ 4.1547.

Upper bound (Friedman, 1997): three squares side by side on the base and one on top. At height 1
the triangle has width v − 2/√3 = 3; at height 2 it has width 3 − 2/√3 > 1.

## Certificate

`n4_cert.json` has three points, each of weight 1, so the total is 3 < 4. They lie on the three
medians at distance 1/√3 from the centroid:

- (1 + 1/√3, 1/3 + 1/√3)
- (2 + 1/√3, 1/3 + 1/√3)
- (3/2 + 1/√3, 1/3 + 5√3/6)

They form an equilateral triangle of side exactly 1. The two lower points lie on the two vertical
edges shared by the squares of the extremal base row.

**Lemma.** Every closed unit square Q ⊆ T_v contains at least one of the three points.

*Proof.* The checker `../../checker/check.py` verified this: exact Q(√3) arithmetic, with the
symmetry D3 (angles θ ∈ [0, θ(1/7)] ⊇ [0, π/12]), 478 nodes, 0 uncertified, 2.6 s on 16 cores
(`check_record.json`, certificate sha256 in that file).

The checker's method:
- **Vertex polygons.** For each bin of u = tan(θ/2), the admissible centres in a box form a convex
  polygon whose vertices are rational functions of u. The capture inequalities are checked at the
  vertices by exact Bernstein bounds.
- **Lemma P.** For each pair of points at unit distance, it can prove "p or q is in Q". This is
  needed because the middle square of the base row holds both lower points on its edges, and which
  one survives a small perturbation depends on the direction.
- The soundness argument is in `../../checker/README.md`.

## From the lemma to the theorem

The argument is the same centre-scaling argument as in `../n2/PROOF.md`. Suppose four unit squares
with disjoint interiors fit in T_L with L < v. Push their centres away from the common centroid by
the factor v/L. The squares become pairwise disjoint closed unit squares in T_v, and together they
capture weight ≥ 4 > 3, a contradiction. Hence s△(4) ≥ v, and with the construction s△(4) = v. ∎

## Independent checks done so far

- **Negative control.** The same construction at L = v + 1/100 does not verify: 63 uncertified
  boxes near the bottom-right corner square.
- **Without Lemma P.** The certificate does not verify at depth 14 and did not finish in 30 minutes
  at depth 40. This is expected, because of the switching family above.
- **Exact random probe.** 20,000 random rational admissible poses over all angles, with no symmetry
  used; minimum exact capture 1 (`../../tools/exact_random.py`).
- **Float probe.** 300,000 random poses; minimum capture 1.

## Status

- Verified by two independently written checkers:
  - `../../checker/` (exact Bernstein bounds over Q(√3));
  - `../../checker2/` (a different method; see its README, including the Independence section).
- Not peer reviewed.
- Not yet formalised in Lean.
