# Exact dimension-six remaining-strip certificate

## Goal and current status

The generator checks F_j(U)<1 for every U in O(6) whose chosen column obeys

    13/20 <= max_i |U_ij|^2 <= 159/200.

No row-width assumption is used in this strip. Combined with certificate_cap65, this covers max_i |U_ij|^2<=159/200. A separate near-axis argument is needed above159/200.

Generation completed successfully (exit code 0): 4,001,519 tree records, 2,000,762 accepted leaves, 59,961 vertices, maximum depth 38, and 147 rational tangent witnesses. The minimum exact leaf slack is greater than 1/2,000,000,000 (approximately 8.14359367633e-10). Results are in result.json; the complete certificate is certificate.json. Both exact replay implementations passed with exit code 0 on 2026-10-16: the producer-side standard-library replay in 340.45 seconds and the separately implemented independent replay in 358.60 seconds. Both reproduced the same counts and exact minimum slack. Producer evidence is in replay.log and replay_result.json; independent evidence is in ../../d6_strip_independent/.

## Geometry

Sort p decreasingly. For k=1,...,5 the ten vertices alternate

    (13/20, (7/20)/k repeated k times, remaining zeros),
    (159/200, (41/200)/k repeated k times, remaining zeros).

The ordered tail normalized by1-p_1 ranges over a four-simplex. The projective transformation sending (p_1,p_tail) to (p_1/(1-p_1),p_tail/(1-p_1)) sends this frustum to a product of an interval and that simplex. The usual staircase triangulation of that product pulls back to five simplices:

    (0,2,4,6,8,1)
    (2,4,6,8,1,3)
    (4,6,8,1,3,5)
    (6,8,1,3,5,7)
    (8,1,3,5,7,9).

This covers the whole closed strip. Exact midpoint bisections preserve the cover.

## Accepted leaf bounds

Every leaf uses one of six bounds. All use the same exact square-root chord loss for the target 2 sum sqrt(p_i)-2. Bounds 0 and 1 additionally use the pair-product interpolation loss stated below. Indices of coordinates here are zero-based.

0. The original covariance bound q(p) plus R(p)/2, where R is the sum of the ten smallest pair products. Additional loss: sum_{i<j}Delta_i Delta_j/8.
1. The stronger quadratic missing-edge correction q(p)+(sqrt(1+18R(p))-1)/9. Additional loss: sum_{i<j}Delta_i Delta_j/4.
2. The full determinant bound 10(prod p)^(1/10).
3. The grouped determinant bound 8[((p_4+p_5)prod_{i=0}^3 p_i)]^(1/8). The group is fixed throughout every simplex; sorted coordinates make these the two smallest.
4. The projected fourth-exterior-power bound 4[((256/5)e_4(B_top5))]^(1/8). The deleted coordinate is always the smallest, index 5.
5. A positive rational linear combination of the five full exterior invariants H_k=[(k+1)e_{k+1}(p)/M_k]^(1/(2k)), M=(1/2,1/4,1/8,9/256,6/1024), obtained by a valid rational Young tangent.

The unprojected elementary-symmetric-root concavity is the Marcus–Lopes theorem; composing with the concave powers (k+1)/(2k)<=1 gives concavity of H_k. The grouped determinant is a geometric mean to a concave power. The projected bound follows from the same matrix elementary-symmetric-root concavity and its monotonicity in PSD order, since B_top5(p) is Loewner-concave. These facts extend to boundary points by continuity. Thus each fixed bound 2–5 admits Jensen interpolation directly.

The new edge proofs and their exact interpolation losses are in ../EDGE_BOUND.md. The determinant/exterior proofs are in ../../d6_central/DETERMINANT_BOUND.md, EXTERIOR_FAMILY.md, and JOINT_EXTERIOR_BOUND.md; projected constants were independently audited in ../../d6_exterior_audit/.

## Tangent witness validation

For every facet a, check a_k>=0 and sum_k a_k binom(m,k)/m^(2k)<=1 for every m=1,...,5. Pair smoothing then proves sum_k a_k e_k(s^2/L^2)<=1 for every nonnegative five-vector s with sum L. The exterior bounds give sum_k a_k(H_k/L)^(2k)<=1.

For any recorded rational t_k>=0, define

    D=1+sum_k(2k-1)a_k t_k^(2k),
    c_k=2k a_k t_k^(2k-1)/D.

Convex tangency yields L>=sum_k c_k H_k. The generator rounds each c_k down to a nonnegative rational multiple of 2^-40; this preserves the inequality. The independent checker must verify the recorded coefficient is no greater than this exact c_k.

## Arithmetic and certificate schema

All accepted leaf inequalities use Python Fraction arithmetic. Square-root bounds are exact rational integer-square-root intervals. Other roots use exact integer nth-root bounds at 60 binary fractional bits. Numerical eigendecomposition only proposes the symmetric rational square-root witness used by the original covariance certificate; exact residual arithmetic certifies its trace bound. Numerical calculations only select a subdivision edge or a tangent proposal.

The certificate records all vertices, all spectral witnesses, rational facets and tangent proposals, the initial five simplices, and a complete depth-first tree. A split record supplies two local vertex positions and their exact midpoint index. A leaf record supplies its bound type and tangent index when relevant. Exhaustion of all tree roots is required.

## Reproduction

Run `python replay.py` from this directory. Only the Python standard library is needed for replay; the generator additionally uses NumPy and mpmath. The independent implementation is in `../../d6_strip_independent/verify.py`; run it from that directory with `python verify.py ../d6_spectral/certificate_cap795/certificate.json`.

Raw certificate SHA256: `0bd2317bd8c2fdc87ec9d2350ee6f136680d74430511aa70ca10467862fee149`.
