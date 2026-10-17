# Universal determinant lower bound for weighted orthonormal complements

## Theorem

For every n>=2, nonnegative unit vector x in R^n, and n-by-(n-1) matrix C such that [x C] is orthogonal, put p_i=x_i^2 and

    L=sum_{i,k} x_i |C_ik|.

Then

    L >= 2(n-1)(product_i x_i)^(1/(n-1))
      = 2(n-1)(product_i p_i)^(1/(2(n-1))).             (D)

There is no feasibility/row-l1 hypothesis. This is a proved analytic bound, independently audited by an independent mathematical review.

## Proof

If some x_i=0, the right side is zero and the claim is immediate. Assume all x_i>0. Let Z=diag(x)C and s_k=||Z[:,k]||_1. Orthogonality implies every column of Z has coordinate sum zero. Also every s_k>0.

Fix any row i and delete it. The cofactor formula for the orthogonal matrix U=[x C] gives

    |det(C with row i deleted)|=x_i.

Multiplying each remaining row by its x_j gives

    |det(Z with row i deleted)|=product_j x_j.        (1)

The zero-sum l1 unit ball is the convex hull of the vectors

    (e_a-e_b)/2, a!=b.

Indeed, any zero-sum vector v of l1 norm1 has positive and negative coordinate masses1/2. Transport its positive mass to its negative mass; writing v as a sum of these signed elementary differences with nonnegative coefficients summing1 gives the asserted convex representation.

Normalize the kth column of Z by s_k. Each normalized column belongs to this polytope. Expand the deleted-row determinant multilinearly in these independent convex combinations. Its absolute value is at most the largest absolute determinant obtained by selecting one polytope vertex per column.

Such a vertex matrix, before scaling its columns by1/2, is the reduced incidence matrix of n-1 oriented edges on n labelled vertices. Its determinant is zero unless these edges form a spanning tree; for a spanning tree its determinant is +1 or -1. The latter follows directly by repeatedly removing a leaf and expanding along its row (or by total unimodularity of incidence matrices). Thus every vertex determinant has absolute value at most 2^(-(n-1)).

Applying this to (1) proves

    (product_j x_j)/(product_k s_k) <= 2^(-(n-1)),
    product_k s_k >= 2^(n-1) product_j x_j.

Finally the arithmetic-geometric mean inequality on the n-1 positive numbers s_k yields (D).

## Concavity and exact simplex certification

Define

    D_n(p)=2(n-1)(product_i p_i)^(1/(2(n-1))),
    q_det(p)=D_n(p)-2 sum_i sqrt(p_i)+2.

D_n is concave on the nonnegative orthant for n>=2. One proof regards it as a positive constant times a weighted geometric mean of p_1,...,p_n and the constant1. Each p_i has exponent1/(2(n-1)), and the remaining exponent of1 is1-n/(2(n-1))>=0. Weighted geometric means with total exponent1 are concave.

Therefore on a rational simplex with vertices a^(j), exactly the same chord-loss certificate as the spectral bound applies:

    q_det(p) >= min_j q_det(a^(j))
      -sum_i (sqrt(u_i)-sqrt(l_i))^2/[2(sqrt(u_i)+sqrt(l_i))],

where l_i,u_i are the coordinate extrema on the simplex, and constant zero coordinates contribute zero. A certificate may accept a simplex using either this determinant inequality or another independently valid lower bound; it must not infer concavity of a maximum of lower bounds.

For exact vertex evaluation, the only new operation is a positive integer root of a rational number: for e=2(n-1), precision b, and rational r>=0, find the largest integer k with k^e <= floor(r*2^(b*e)). Then k/2^b and (k+1)/2^b enclose r^(1/e); if equality holds the endpoints coincide. Integer binary search suffices, with no floating-point assumptions.
