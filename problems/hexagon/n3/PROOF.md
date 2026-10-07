# Three unit squares in a regular hexagon

**Theorem (computer-assisted).** The smallest regular hexagon containing three non-overlapping unit squares
has side

    s(3) = v = (1 + √3)/2 ≈ 1.36603.

Status (2026-10-04): a computer-assisted proof. It has not been peer reviewed and it has not been
formalised in Lean.

- The first stage has two independent checks.
- The second stage has two independent implementations (`stage2_checker/`, described in §5, and
  `stage2_checker2/`). Both prove all 742 boxes.

## 1. Upper bound: the pinwheel (Morandi)

Notation:

- H_v is the hexagon with side v, centre 0 and a flat bottom.
- Its apothem is h = v√3/2.
- V = (−v/2, −h) is its lower-left vertex.
- R is the rotation by 2π/3.

The pinwheel consists of the three squares

    B = [−v/2, −v/2 + 1] × [−h, −h + 1],   RB,   R²B.

Facts about this configuration:

- B lies on the bottom side, and its lower-left corner is the vertex V.
- The top-right corner of R^iB lies on the top edge of R^{i+1}B.
- The contact point of B is ((√3 − 3)/4, (1 − √3)/4), at distance (√3 − 1)/2 from the centre.
- The squares have disjoint interiors and lie in H_v.
- All of this is exact in Q(√3) (`local_lemma/ll_exact.py`).

## 2. Reduction to closed disjoint squares in H_v

Suppose three unit squares with disjoint interiors fit in H_L with L < v.

- Push their centres away from the hexagon's centre by the factor v/L.
- The squares become pairwise disjoint *closed* unit squares in H_v. This is the centre-scaling argument of
  the triangle proofs in `squares-in-triangle`.
- Containment only needs convexity and the homothety about the centre. Write k = v/L. If Q ⊆ H_L has
  centre c, then every point of Q + (k−1)c is k·(q/k + (1 − 1/k)c). The point in brackets is a convex
  combination of q ∈ H_L and c ∈ H_L, so it lies in H_L. Hence Q + (k−1)c ⊆ k·H_L = H_v.
- So it suffices to show that H_v contains no three pairwise disjoint closed unit squares.

## 3. Stage 1: one square lies in the flex tube N

Certificate `stage1_cert.json` (sha256 ab0bdfdd…3e623d27):

- 630 weighted points with total weight 749319/250000 < 3;
- 742 *excused boxes* in (centre, u = tan(θ/2)), in the D6-reduced angle range u ∈ [0, 1/7].

Their union, closed under D6, is N. N covers a tube of radius 0.03 around the *flex curve*: the pinwheel
square B rotated about its vertex V by angles in [−0.03, 0.52], together with all its D6 images.

**Claim.** Every closed unit square in H_v whose reduced pose is not excused captures weight ≥ 1.

This claim is verified:

- by the first checker (`stage1_checker/check_hex.py`, depth 32, u-scale 16, 5768 nodes);
- by an independent second checker written from the specification only (`stage1_checker2/`, 58,894 boxes).

A negative control exhibits an admissible pose inside an excused box that captures 495031/500000 < 1. So the
excused boxes are really needed.

**Consequence.** Take three pairwise disjoint closed squares in H_v.

- They capture at most 749319/250000 < 3 in total, so at least one captures less than 1.
- Capture is D6-invariant, so every reduced representative of that square's pose is excused.
- Applying a D6 element (which preserves H_v), we may assume that square 1 has its pose in one excused
  box E_k.

## 4. The local lemma near the pinwheel

Proof: `local_lemma/LOCAL_LEMMA.md`.

Statement: no three pairwise disjoint closed unit squares in H_v have the following form, for each i in
frame i:

- the tilt is within ρ = 0.08 of the pinwheel square P_i;
- the lower-left corner is within ρ_p = 0.05 of its vertex.

The same holds for every D6 image of the pinwheel.

The ingredients:

1. **Containment.** It puts each corner displacement p_i in the 120° wedge W at the vertex.
2. **Exact identity for the contacts** (checked in sympy):

       k_i = F(φ_i, φ_{i+1}) + (R(φ_{i+1})n)·p_i − (R(φ_{i+1})e_y)·p_{i+1}.

3. **Two inequalities**, valid while the contact corners stay strictly inside the other three edge lines of
   the neighbouring square:

       (i)  k_i ≤ F_i + Φ(|p_i| + |p_{i+1}|),
       (ii) Σk ≤ ΣF − (√3/2 − 2Φ) Σ|p|.

4. **Two cases.** If the tilts are equal (the flex), ΣF ≤ 0. If they are not equal, some F_j is negative at
   first order.

The radius conditions are checked in exact rational arithmetic (`local_lemma/ll_radius.py`).

## 5. Stage 2: branch and bound for each excused box

For each excused box E_k, the program `stage2_checker/bb_rig.py` proves that there are no three pairwise disjoint
closed unit squares in H_v with square 1's pose in E_k. Squares 2 and 3 range over all poses: centre in the
bounding rectangle of H_v, angle in [0, π/2].

### Nodes and pruning

A node is a triple of pose boxes. It is discarded when one of the following is proved.

- **Outside.** Some square sticks out of H_v for every pose in its box.
  - Let d be the half-diagonal of the box's centre rectangle plus √(1/2) times its angular half-width,
    padded by 1e-14 for the rounding of the midpoint.
  - Every point of every pose's square is within d of the corresponding point of the mid-pose square
    (a chord is shorter than its arc).
  - So it suffices that a corner of the mid-pose square is beyond a side by more than d.
  - The side normals are unit vectors, enclosed with a relative pad of 1e-12.
- **Overlap.** Two squares intersect for every pair of poses.
  - Each pose's square contains the mid-pose square shrunk to side 1 − 2d. The reason: the boundary moves
    by at most d, and a winding-number argument gives the containment.
  - It suffices that the two shrunk squares have positive overlap depth on all four separating axes.
- **Lemma inequalities.** For a D6 image of the pinwheel and an assignment of the three boxes to its
  squares:
  - images of boxes are enclosed in outward-rounded bounding boxes, which contain the true images;
  - the tilts φ_i and the bounds on |p_i| are computed;
  - the contact-validity bound is checked on the whole node;
  - inequality (i) or (ii) of §4 shows that some contact k_i ≤ 0, which disjointness forbids.
- **Lemma neighbourhood.** All three boxes lie in the neighbourhood of §4.

Otherwise the largest box is halved.

### Arithmetic

- Every operation uses intervals rounded outward by one ulp (`np.nextafter`).
- cos, sin and atan are widened by 1e-15.
- √3 and π are enclosed by adjacent doubles. The pinwheel angles 2πi/3 are intervals.
- The excused boxes are read from the exact rationals of the certificate.

### Result

All 742 boxes are proved with ε = 0.004:

- 5.75·10^9 nodes in total; the largest box needed 1.6·10^7 nodes;
- every box ends with 0 leaves and an empty stack;
- about 54 core-hours on a c2d-highcpu-16;
- results in `stage2_checker/results/rig_results.jsonl` (sha256 840df154…).
- Box #86, which contains the pinwheel square, gives identical node counts on arm64 macOS and on x86-64 Linux.

## 6. Conclusion

- By §3, any three pairwise disjoint closed unit squares in H_v have one square in some excused box E_k.
- By §5, that is impossible for every k.
- Hence H_v contains no such triple.
- By §2, s(3) ≥ v. With §1, s(3) = v. ∎

## Checks and controls

- **Soundness fuzz test** (`stage2_checker/fuzz_rig.py`). Over 20,000 random nodes around the pinwheel, its flex and
  its D6 images, each pruning test's own claim was checked on samples:
  - outside: every pose sticks out;
  - overlap: every pair of poses intersects;
  - lemma: every contained configuration has an intersecting pair.
  - Violations: 0. In the recorded run (`stage2_checker/results/fuzz_rig.out`) 783 nodes were pruned by
    the lemma tests and 4,202 contained samples in them were checked.
- **Negative controls** (`stage2_checker/controls/`, a copy of the program with options; not used for the proof):
  - **NC1.** Without the lemma tests, box #86 is not proved at side v.
    - After 10^7 nodes, 293,399 leaves remain (`controls/records/nc1_side1.00_nolemma.out`).
    - The first 100 leaves lie within max-norm distance 0.033–0.041 (centre coordinates and angle) of
      the pinwheel (`controls/leafdist.py`). So the lemma is what closes the problem near the pinwheel.
  - **NC3.** At side 1.01·v, the pinwheel scaled by 1.01 from the centre is a genuine packing of three
    disjoint squares.
    - On nodes of half-width 10^-4 to 4·10^-3 around it, neither the outside test nor the overlap test fires
      (`controls/nc3_pinwheel.py`).
    - Without the lemma, box #86 is not proved at 1.01·v either (65,443 leaves after 10^7 nodes,
      `controls/records/nc3_side1.01_nolemma.out`).
- **Second implementation of §5** (`stage2_checker2/`, Rust, written from `SPEC_stage2.md` only, without
  reading `stage2_checker/`, this document's §5 or the first implementation's design notes):
  - all 742 boxes PROVED with 0 unproved leaves (4.37·10^9 nodes, about 6.1 core-hours);
  - its own pruning: support-function containment, separating-axis overlap, the Q2/Q3 swap symmetry and
    the local lemma (tilt and corner radii compared conservatively);
  - its recorded negative control (`del11_run/neg.jsonl`): at side 1.01·v without the lemma, box 1 is not
    proved (7.7·10^5 unproved leaves after 6.9·10^6 nodes);
  - results `stage2_checker2/del11_run/full.jsonl` (sha256 a569c0ba…); `SHA256SUMS` also covers its sources
    and the stage-1 certificate;
  - the local lemma was re-derived independently (identity, constants and the final inequality) while
    writing this implementation.
