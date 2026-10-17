# Exact dimension-six central-cap certificate

## The theorem

For every U in O(6), every column j with max_i U_ij^2<=13/20 satisfies F_j(U)<1. No row-width assumption is required.

This is a partial dimension-six result: it does not cover 13/20<max_i U_ij^2<1 by itself.

## Proof ingredients

1. The covariance/nuclear bound and exact spectral-witness method are proved directly in ../../d6_proof_handoff/PROOF.md, Sections 1 and 4.
2. ../EDGE_BOUND.md proves the new global correction L>=sqrt(2)T+R_6(p)/2, where R_6 is the sum of the ten smallest pair products p_i p_j.
3. Sort p decreasingly. The capped ordered simplex p_1<=13/20 has ten vertices: v_k=(1/k repeated k times, then zeros) and w_k=(13/20,7/[20(k-1)] repeated k-1 times, then zeros), k=2,...,6. Order them v2,w2,v3,w3,...,v6,w6, indexed 0 through 9. The standard pulling triangulation is:
   (0,2,4,6,8,1), (2,4,6,8,1,3), (4,6,8,1,3,5), (6,8,1,3,5,7), (8,1,3,5,7,9).
4. For a simplex, use the original exact square-root chord interpolation loss, plus sum_{i<j}Delta_i Delta_j/8 for R_6/2, as proved in ../EDGE_BOUND.md.
5. Bisect exact rational edge midpoints until every leaf has a positive rational lower bound for q+R_6/2.

## Result and reproduction

`certify.py` finished exact-rational acceptance of 1,636,601 tree records, comprising 818,303 accepted leaves and 25,755 unique vertices. Maximum depth 32. Minimum certified leaf slack approximately 8.86324144494e-10, strictly positive. `result.json` supplies the exact fraction. The minimum certified vertex value, .001878222061711159, is not claimed as a lower bound over the entire cap.

`certificate.json` records all vertices, symmetric rational spectral witnesses, initial simplices, and midpoint/leaf tree records. The certificate is about 69 MB uncompressed.

Run `python replay.py` in this directory. It requires only the Python standard library, uses no floating-point eigensolver, checks the supplied square-root witnesses by rational residual bounds, recomputes every rational interpolation acceptance, validates the fixed starting geometry and each midpoint, and checks exhaustion of all five subdivision trees. The generator uses NumPy/mpmath to propose witnesses and splits, but every acceptance is exact.

Generation runtime was530seconds in the current environment. The standard-library exact replay completed successfully, rechecking all25,755 vertices and818,303 leaves in146seconds; its output is in replay.log.
