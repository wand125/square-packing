# A fourth-exterior-power bound in dimension six

Let x>=0 be a unit vector in R^6 and [x C] orthogonal. Put p_i=x_i^2, Z=diag(x)C, s_k=||Z[:,k]||_1, and L=sum_k s_k. Then

    L >= 4 ((1280/9) e_5(p))^(1/8),                 (E4)

where e_5(p)=sum_i product_{j!=i}p_j. This remains nonzero on the relative interior of every support-five face.

## 1. Exterior volume of the root polytope

Every zero-sum vector of l1 norm1 is a convex combination of roots (e_i-e_j)/2. For four such vectors v_1,...,v_4, multilinearity of the exterior product and the triangle inequality show that ||v_1 wedge ... wedge v_4|| is bounded by its maximum on four roots.

Four independent roots correspond to a forest of four edges on six vertices, with exactly two connected components, including isolated vertices as components. If their sizes are a,b, then a+b=6 and the squared Euclidean volume of their unscaled incidence columns is ab. Indeed each tree component of size a has incidence-column Gram determinant a, by Cauchy-Binet: there are a nonzero maximal minors, all of absolute value1. Different components are orthogonal. Thus the squared volume of the scaled roots is ab/4^4<=9/256, with equality for component sizes3,3. Dependent edge sets have zero volume.

For each four-element subset K of the five columns, it follows that

    ||wedge_{k in K}Z[:,k]||^2 <= (9/256) product_{k in K}s_k^2.

Summing over K and using Cauchy-Binet gives

    e_4(Z Z^T) <= (9/256)e_4(s_1^2,...,s_5^2).     (1)

## 2. Exact elementary-symmetric inequality

For five nonnegative real numbers s_i with sum S,

    e_4(s_1^2,...,s_5^2) <= (S/4)^8.               (2)

Normalize S=1; S=0 is immediate. The maximum exists on the compact simplex. On its boundary, at least two zeros give e_4=0; exactly one zero gives the product of the other four squares, bounded by1/4^8 by AM-GM.

At an interior stationary point write

    P=product_i s_i^2, H=sum_i s_i^(-2), e_4=P H.

Lagrange multipliers applied to log(PH) give

    2/s_i -2/(H s_i^3)=lambda.

Multiplying by s_i and summing shows lambda=8. Thus all s_i are positive roots of the cubic

    8t^3-2t^2+2/H=0.

This polynomial has at most two positive roots: its derivative is 4t(6t-1), so on the positive half-line it first decreases and then increases. If all coordinates coincide, the value is1/5^7<1/4^8.

If there are two distinct values a,b with multiplicities r,5-r, equating their logarithmic derivatives gives

    H=(a^2+ab+b^2)/(a^2 b^2).

Equating this with r/a^2+(5-r)/b^2 gives

    (r-1)b^2+(4-r)a^2-ab=0.

For r=2 or3 this positive-definite quadratic cannot vanish. For r=1 it gives a=b/3; r=4 is the same solution with the names reversed. Normalization therefore gives the unique nonuniform stationary pattern, up to permutation,

    (1,3,3,3,3)/13.

Its value is 9477/13^8=3^6/13^7<1/4^8. These comparisons are verified as integer inequalities by replay_exterior.py. Thus no interior stationary point exceeds the boundary maximum, proving (2).

## 3. Covariance identity and conclusion

Z Z^T=B=diag(p)-pp^T. For any subset I of k coordinates, the matrix determinant lemma (or polynomial continuity at zero coordinates) gives

    det B[I,I]=(product_{i in I}p_i)(1-sum_{i in I}p_i).

Since sum_i p_i=1, summing these principal minors counts each product of k+1 distinct coordinates exactly k+1 times. Hence

    e_k(B)=(k+1)e_{k+1}(p).

In particular e_4(B)=5e_5(p). Combining this identity with (1) and (2) yields

    5e_5(p) <=(9/256)(L/4)^8,

which is exactly (E4).

## 4. Concavity for simplex certificates

The classical concavity of e_k(p)^(1/k) on the nonnegative orthant implies that e_5(p)^(1/8) is concave: compose e_5^(1/5) with the increasing concave power5/8. Thus the same vertex-concavity plus square-root chord-loss certificate applies to

    q_4(p)=4((1280/9)e_5(p))^(1/8)-2sum_i sqrt(p_i)+2.

For a certificate avoiding this classical concavity theorem, an alternative is direct interval evaluation of the positive polynomial e_5(p) followed by the eighth root; that is valid but typically less sharp on large cells.
