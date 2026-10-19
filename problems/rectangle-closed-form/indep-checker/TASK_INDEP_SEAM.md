# Task: an independent checker for the seam certificates (second system)

Context. The rectangle version of the closed-form bound joins two interval families along each wall by a
"seam": a transition period between two wall profiles. For each of 30 pairs of adjacent families, a seam
family (a family JSON in the closed-form format, see problems/closed-form/SPEC.md §3) was built and every
unit-square pose touching the seam band was proved to have measure ≥ 1 by the first-system 4D checker
(run4d), with records in the closed-form record format (SPEC.md §6). This task is to check those
certificates by an independent implementation, written from the specifications only, without reading the
first-system code (run4d, check_record4d, seam_loop, seam_fix_pieces, split_driver, make_seam_family).
Reusing the published independent closed-form checker (problems/closed-form/indep-checker, "cfcheck") is
allowed and recommended: it already implements every leaf test.

For each pair, check:
1. **Seam family structure.** The local model: periods of profile P on x < S, n = 1 transition period on
   [S, S + 1), periods of profile P' on x ≥ S + 1, Lebesgue density 1 on y ≥ 9/5, with S = 5 and 3 periods
   on each side as pieces F (T and V empty). P and P' are the wall profiles of the two interval families
   (given as their family JSONs with SHA-256). Check that the pieces outside [S, S + 1) are exactly the
   periods of P and P', that all masses are non-negative rationals, and compute the extra mass e of the
   transition period over one period of P (it must equal the recorded value).
2. **Band condition (Lemma R5, d = 2/5).** On the left band [S, S + 2/5) every grid segment of the
   transition has mass ≥ that of P on the same segment; on the right band (S + 3/5, S + 1) ≥ that of P'
   (exact rationals, compared pointwise as line densities on the open half-planes x < S + d and x > S + 1 − d,
   which does not depend on how segments are split; the segment rules are in the spec: vertical lines x ∈ [S, S + d) on the left,
   x ∈ (S + 1 − d, S + 1) on the right; horizontal segments by their left end).
3. **Levels and monotonicity.** A pair may have levels 0..L with families fam_0, fam_1, …; check that each
   fam_{j+1} dominates fam_j segment by segment (same segments present, mass ≥, everything outside F
   identical), so that a pose proved for fam_j holds for fam_{j+1}.
   For two pairs (i005_012 | i012_020_a and i012_020_a | i012_020_b) the final family is fam_r5.json: the last
   level family plus one added segment each (mass 2001/10⁶), because the band condition of item 2 failed on one
   segment of length 2/5 at y = 8/5. Check that fam_r5 dominates every level family and satisfies item 2; the
   recorded e of these two pairs is that of fam_r5.
4. **Root set.** Recompute the R5 root list: the product grid of the window (centers x ∈ [17/4, 27/4],
   y ∈ [0, 13/5], u = tan(θ/2) range as in the record header) restricted to roots that touch the bands
   (z_x upper + w_max ≥ S + d and z_x lower − w_max ≤ S + 1 − d, w_max the maximal half-width over the
   root's θ range). Expected: 11,206 of 17,550.
5. **Coverage.** The pieces passed at all levels (records may split roots into sub-boxes) cover the root
   set exactly: each piece lies in a root, pieces are pairwise interior-disjoint, and volumes add up.
6. **Leaves.** Every leaf of every record is accepted by its named test against the family of its level
   (full replay, not sampled).
7. **Paths.** From the 30 e values and the 4 equal-profile adjacent pairs, recompute for all pairs of the
   34 intervals the minimal-E path, E, r and k₀ = 6 + 3r (7 if r = 0), and compare with paths.json.

Output a per-pair report (PASS/FAIL per item, counts of roots, pieces, leaves) and an overall exit code.
Record machines generically ("a laptop", "a cloud VM with N vCPUs"), times and results as run.
Expected size: about 180,000 leaves per level per pair, 30 pairs. Inputs are delivered as an archive with
SHA256SUMS; the location will be given with the request.
