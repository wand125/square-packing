# Independent audit of the six-dimensional central cap

Scope: only target columns with max_i U_ij^2 <= 13/20. This is not a proof of the full dimension-six statement and says nothing by itself about the remaining strip. No row-width hypothesis is used here.

## Mathematical audit

The reduction is valid. After row sign changes and column permutation, write U=[x C], x>=0, p_i=x_i^2. If S=sum x_i and L=sum_ik x_i|C_ik|, then F_j=2S-1-L, and Z=diag(x)C obeys ZZ^T=diag(p)-pp^T. Thus a lower bound on L gives a lower bound on 1-F_j.

The missing-edge lemma in ../EDGE_BOUND.md is correct, including degenerate/zero columns. For every nonzero zero-sum z, keeping one largest positive and one largest negative coordinate gives a coordinate restriction d. If s=||z||_1, t=||z||_2, and rho=||z-d||_1, then rho<=s-2t^2/s. For a pair not selected by any column, all corresponding products from d vanish. The absolute off-diagonal covariance entries are p_i p_j. Summing triangle inequalities over unselected pairs, and then enlarging the sum to all pairs, gives R_6<=sum_k s_k rho_k<=sum_k(s_k^2-2t_k^2). There are 15 pairs and at most five selected distinct pairs, so the ten smallest products give a valid lower bound even if fewer than five distinct pairs were selected. The facts sqrt(2)t_k<=s_k<=1 yield s_k^2-2t_k^2<=2(s_k-sqrt(2)t_k). The nuclear norm triangle inequality completes L>=sqrt(2)Tr sqrt(diag(p)-pp^T)+R_6/2.

The covariance is Loewner-concave in p. Composition with the increasing, concave trace square root makes T(p) concave. For each coordinate the square-root gap above its endpoint chord is (sqrt(u)-sqrt(l))^2/[4(sqrt(u)+sqrt(l))]. Consequently the loss for the -2 sum sqrt(p_i) term is twice this quantity. For a barycentric random vertex V, Cov(V_i,V_j)<=Delta_i Delta_j/4 implies p_i p_j>=E[V_i V_j]-Delta_i Delta_j/4. Minimizing sums over ten-pair subsets yields R_6(p)>=E[R_6(V)]-sum_{i<j}Delta_i Delta_j/4. The factor for R_6/2 is therefore exactly 1/8, with the stated direction. This argument does not presume concavity of R_6.

The ordered simplex has barycentric coordinates k(p_k-p_{k+1}), k=1,...,6, with p_7=0. Since 13/20>1/2, the cut removes only v_1 and crosses precisely the edges v_1-v_k, k>=2, at the listed w_k. The ten listed vertices are therefore correct. Pulling from w_2 cones over the intact opposite facet conv(v_2,...,v_6), and over the truncated facet opposite v_2. Repeating on that facet from w_3, then w_4, w_5, w_6 gives exactly the five listed simplices. This establishes coverage and disjoint interiors without relying on numerical triangulation. Edge-midpoint bisection preserves coverage, including all boundary points.

For a symmetric rational witness A, the residual row-sum norm bounds the spectral norm of B-A^2. Weyl's inequality and the square-root Holder bound give Tr sqrt(B)>=Tr sqrt(A^2)-6 sqrt(delta)>=Tr A-6 sqrt(delta). The coefficient six is correct, and A need not be positive semidefinite. Clipping the trace lower bound at zero before using a lower approximation to sqrt(2) is necessary and is done.

## Independent executable audit

independent_verify.py imports only the Python standard library; neither producer nor original checker is imported. It parses the certificate anew, checks symmetry and every rational spectral residual, checks all domain constraints, verifies the fixed initial geometry, every midpoint, every positive leaf margin, traversal exhaustion, uniqueness and usage of vertices, and the full-binary-forest counting identity.

It uses independent 128-bit square-root enclosures, each checked by exact squaring. For interpolation it bounds the monotone expression g(a,b)=(b-a)^2/[2(a+b)] directly by lower(a), upper(b), rather than repeating the producer's numerator/denominator formula. Its correction loss is evaluated as [(sum Delta)^2-sum Delta^2]/16. All acceptance arithmetic is Fraction arithmetic; conversion to float is only for reporting after verification.

Full execution PASSED, with exit code zero, in 101.99 seconds. It checked 25,755 vertices, 1,636,601 records, and 818,303 leaves, at maximum depth 32. The independent minimum exact margin is recorded in independent_result.json and is approximately 8.863281780797586e-10. This differs slightly from the producer's margin because the independent checker uses tighter 128-bit enclosures and a different safe chord upper bound.

Certificate SHA256: c33aa40033275bf66488a8b781898dcb051aad39459caa6900e0d30413986b82.

Conclusion: the supplied certificate proves q(p)+R_6(p)/2>0 on the entire closed cap max p_i<=13/20, hence F_j(U)<1 for every such column of every real orthogonal 6-by-6 matrix. All the stated counts match the producer. The full dimension-six theorem still requires additional coverage beyond this cap.
