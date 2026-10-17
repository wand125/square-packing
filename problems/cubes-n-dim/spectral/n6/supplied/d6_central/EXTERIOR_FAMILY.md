# A universal hierarchy of exterior-power lower bounds

Let n>=2, x>=0 with ||x||_2=1, [x C] orthogonal, p_i=x_i^2, and L=sum_{i,j}x_i|C_ij|. For each k=1,...,n-1 define

    c=n-k, q=floor(n/c), r=n-qc,
    P_(n,k)=q^(c-r)(q+1)^r,
    D_(N,k)=max_{m=k,...,N} binom(m,k)/m^(2k), N=n-1.

Then

    L >= [(k+1)4^k e_(k+1)(p)/(P_(n,k) D_(n-1,k))]^(1/(2k)).   (H_k)

All constants P,D are exact integers/rationals. This result needs no row-l1 feasibility assumption. The endpoint k=n-1 recovers the determinant bound. The proof below also proves the finite scalar optimization exactly, rather than relying on a numerical search.

## Root-polytope exterior bound

Put Z=diag(x)C, s_j=||Z[:,j]||_1. Each column has coordinate sum zero. A normalized column is in the convex hull of roots (e_i-e_j)/2. The norm of a wedge of k normalized columns is at most its largest value on k such roots, by multilinearity and the triangle inequality.

An independent collection of k roots corresponds to a forest on n vertices with c=n-k components. If the component sizes are a_1,...,a_c, its unscaled incidence-column Gram determinant is product a_i: for a tree on a vertices the determinant is a by Cauchy-Binet and its a unit-magnitude maximal minors. Scaling k columns by1/2 divides the squared volume by4^k.

The largest product of c positive integers with sum n is attained by balanced sizes q and q+1, and equals P_(n,k). Indeed replacing a pair a>=b+2 by a-1,b+1 increases their product. Thus every k-column wedge satisfies

    ||wedge_(j in J) Z_j||^2 <= P_(n,k)/4^k product_(j in J)s_j^2.

Summing over J gives

    e_k(Z Z^T) <= P_(n,k)/4^k e_k(s_1^2,...,s_N^2).             (1)

Zero columns cause no difficulty: their wedge products vanish and normalization is omitted for them.

## Exact scalar optimization by pair smoothing

For any N nonnegative numbers s_j with total S and 1<=k<=N,

    e_k(s_1^2,...,s_N^2) <= D_(N,k) S^(2k).                    (2)

Normalize S=1; the case S=0 is immediate. The continuous expression attains a maximum on the compact simplex. Its maximum is positive, so any maximizer has at least k positive entries. If k=1, sum s_j^2<=1 and D_(N,1)=1, proving the assertion.

Suppose k>=2 and a maximizer has two unequal positive coordinates a,b. Hold their sum a+b and all other coordinates fixed; write t=ab. Expanding the elementary symmetric polynomial with respect to these coordinates gives

    e_k(s^2)=alpha t^2 + beta[(a+b)^2-2t]+gamma,
    alpha=e_(k-2)(other coordinates squared)>0,
    beta=e_(k-1)(other coordinates squared)>=0.

The strict positivity of alpha follows because the maximizer has at least k positive coordinates, leaving at least k-2 outside the chosen pair. Therefore this is a strictly convex quadratic in t on [0,(a+b)^2/4]. Since a,b are positive and unequal, t is strictly interior. One of the endpoint replacements, namely (a+b,0) or ((a+b)/2,(a+b)/2), strictly increases the objective, contradicting maximality.

Consequently all positive coordinates of a maximizer are equal. If their number is m, each equals1/m and the value is binom(m,k)/m^(2k). Maximizing over the finitely many integers k<=m<=N proves (2).

## Covariance identity

As Z Z^T=diag(p)-pp^T, its principal minor on a k-element coordinate set I is

    (product_(i in I)p_i)(1-sum_(i in I)p_i).

Using sum_i p_i=1 and summing over I gives

    e_k(Z Z^T)=(k+1)e_(k+1)(p).                               (3)

This formula also holds when some coordinates vanish, by polynomial continuity. Combining (1), (2), and (3) gives (H_k).

## Explicit dimension-six formulas

The maximizing m is k for each k=1,...,5 when N=5. Exact comparison of the rational constants is in exterior_bounds.py. The resulting five bounds are

    k=1: L >= 2 sqrt(e_2(p)),
    k=2: L >= 2 (12 e_3(p))^(1/4),
    k=3: L >= 3 (32 e_4(p))^(1/6),
    k=4: L >= 4 ((1280/9)e_5(p))^(1/8),
    k=5: L >= 10 (e_6(p))^(1/10).

## Concavity and exact replay

For each k>=1, e_(k+1)(p)^(1/(k+1)) is concave on the nonnegative orthant, the standard elementary-symmetric mean concavity theorem. Since (k+1)/(2k)<=1, composing with this increasing concave power proves concavity of each right-hand side of (H_k).

Thus each member of the hierarchy can separately be used in the existing simplex chord-loss certificate for L-2(sum sqrt(p)-1). For every leaf, choose any one bound whose exact vertex values minus the square-root chord loss are positive. The maximum of the bounds need not itself be concave, and should not be treated as concave.

All vertex calculations require only exact polynomial evaluation, rational constants, and a positive integer root of order2k. A complete certificate can use the same integer-root interval construction described in DETERMINANT_BOUND.md.

### Primary source for elementary-symmetric-root concavity

The concavity fact used above is the Marcus–Lopes inequality: Marcus and Lopes (1957), Theorem 2, DOI https://doi.org/10.4153/CJM-1957-037-9. The theorem gives the superadditivity of the degree-one homogeneous function e_j^(1/j) on the nonnegative orthant; combining superadditivity with homogeneity gives concavity, with boundary points obtained by continuity.
