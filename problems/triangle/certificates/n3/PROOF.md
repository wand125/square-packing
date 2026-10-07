# Three unit squares in an equilateral triangle

**Theorem (computer-assisted).** The smallest equilateral triangle containing three non-overlapping
unit squares has side v = 3/2 + √3 ≈ 3.2321.

Upper bound (Friedman, 1997): the "pinwheel". Each square has one side on a side of the triangle
and is placed rotationally symmetrically. Each square touches the next one at a single point: a
vertex of one square lies on an edge of the next. Exact check: `../../tools/n3_pinwheel.py`.

## Certificate

`n3_cert.json` has seven points of weight 1/3 each, so the total is 7/3 < 3:

- the centroid G = (3/4 + √3/2, 1/4 + √3/2);
- the six contact points of the pinwheel and of its mirror image. This is the D3-orbit of
  (1 + √3/3, √3/2), which is where a vertex of one pinwheel square touches the edge
  x = 1 + √3/3 of the square standing on the base.

**Lemma.** Every closed unit square Q ⊆ T_v contains points of total weight ≥ 1, i.e. at least
three of the seven points.

*Proof.* The checker `../../checker/check.py` verified this (points only; neither Lemma P nor
threshold features are used). It ran with symmetry D3, 386 nodes, 0 uncertified, maximum depth 30,
0.7 s on 16 cores (`check_record.json`).

The tightest poses are the squares standing on the base in a bottom corner. At θ = 0 they capture
exactly three points: one point lies on the top edge and two on the side edge. The float profile
of the worst margin versus angle (`../../tools/theta_profile.py`) behaves as follows:
- it is 0 at θ = 0, which is a bin endpoint, and grows like θ²;
- it stays about 1e−4 for θ ∈ [3°, 5°].

This is why the subdivision goes to depth 30 there.

## From the lemma to the theorem

The argument is the same centre-scaling argument as in `../n2/PROOF.md`. Three unit squares with
disjoint interiors in T_L with L < v become three pairwise disjoint closed unit squares in T_v.
Together they would capture weight ≥ 3 > 7/3, a contradiction. ∎

## Checks done so far

- **Negative control.** The same construction, scaled about the centroid to
  L = v + 1/100, does not verify: 1177 uncertified boxes at depth 22
  (`../../checker/examples/neg_n3_Lplus.json`).
- **Exact random probe.** 20,000 random rational admissible poses over all angles, with no
  symmetry used; minimum exact capture 1.
- **Float probe.** 200,000 poses; minimum capture 1.

## Status

- Verified by two independently written checkers:
  - `../../checker/` (exact Bernstein bounds over Q(√3));
  - `../../checker2/` (a different method; see its README, including the Independence section).
- Not peer reviewed.
- Not yet formalised in Lean.
