# A dimension-five proof of Lemma F

This combines the previously established dimension-four Lemma F and its near-axis lifting argument with a new exact rational certificate for the remaining columns. The new computation is a finite proof, not a numerical maximization.

## Statement and reduction

For a real orthogonal matrix U, put r_i = sum_k |U_ik| and F_j = sum_i |U_ij|(2-r_i). Assume the dimension-four statement F_j <= 1 for all orthogonal 4-by-4 matrices, as established in the source proof. Then F_j <= 1 for every orthogonal 5-by-5 matrix. In particular this covers the requested case r_i < 2.

Fix a column and change row signs so that it is x >= 0. Write U=[x C], and put p_i=x_i^2 and S=sum_i x_i. Orthogonality gives sum p_i=1, x^T C=0, and CC^T=I-xx^T. Let

L = sum_{i,k} x_i |C_ik|.

Then F_j=2S-1-L. It suffices to prove L >= 2(S-1).

For every column y of C, the coordinates of z=diag(x)y sum to zero. If their positive and negative sums have absolute value a, then ||z||_1=2a and ||z||_2^2<=2a^2. Therefore ||z||_1>=sqrt(2)||z||_2. The triangle inequality for the nuclear norm, applied to the rank-one decomposition by columns, gives

L >= sqrt(2) sum_k ||diag(x)C[:,k]||_2
  >= sqrt(2) ||diag(x)C||_*
  = sqrt(2) Tr sqrt(diag(p)-pp^T).

Define q(p)=sqrt(2) Tr sqrt(diag(p)-pp^T)-2 sum_i sqrt(p_i)+2. Thus 1-F_j >= q(p).

## Near-axis part

Section 3 of the existing proof establishes: dimension-m Lemma F, for m<=4, implies dimension-(m+1) Lemma F for a column whose largest squared entry is at least 1-1/m. Apply m=4. Hence max p_i>=3/4 is already covered.

Source: https://github.com/wand125/square-packing/blob/main/problems/cubes-n-dim/PROOF.md

The new certificate proves q(p)>0 throughout the complementary closed domain max p_i<=3/4. It does not assert this spectral sufficient inequality on the near-axis domain, where it can be false.

## Geometry of the remaining domain

By symmetry sort p_1>=...>=p_5>=0. The ordered probability simplex has vertices v_k=(1/k,...,1/k,0,...,0), with k nonzero entries, k=1,...,5. Indeed its barycentric coefficients are k(p_k-p_{k+1}), setting p_6=0.

Cutting this simplex by p_1<=3/4 removes v_1 and introduces w_k=(3/4,1/[4(k-1)],...,1/[4(k-1)],0,...,0), k=2,...,5. Index v_2,w_2,v_3,w_3,v_4,w_4,v_5,w_5 as 0,...,7. The truncated simplex is covered by these four simplices:

(0,2,4,6,1), (2,4,6,1,3), (4,6,1,3,5), (6,1,3,5,7).

This is the standard pulling triangulation: pull from w_2, taking the cone over the old opposite facet and recursively over the lower-dimensional truncated facet; repeat with w_3 and w_4. The simplices have disjoint interiors and cover the truncated simplex.

## Rigorous simplex acceptance

T(p)=Tr sqrt(diag(p)-pp^T) is concave on the probability simplex. The covariance matrix is Loewner-concave since the difference at a convex combination is theta(1-theta)(p-r)(p-r)^T. The trace square root is increasing in the positive-semidefinite order and concave.

On a simplex with vertices a^(k), write p=sum_k theta_k a^(k). In coordinate i let l_i and u_i be the minimum and maximum vertex coordinates. The largest gap between sqrt(t) and its endpoint chord on [l,u] equals

( sqrt(u)-sqrt(l) )^2 / [4( sqrt(u)+sqrt(l) )],

with zero gap for a constant coordinate. Consequently

q(p) >= min_k q(a^(k)) - sum_i (sqrt(u_i)-sqrt(l_i))^2 / [2(sqrt(u_i)+sqrt(l_i))].

Every accepted leaf in the certificate has a strictly positive exact rational lower bound for this expression. Each non-leaf is bisected along an edge at its exact rational midpoint. These two child simplices cover their parent. The recorded traversal finishes with no unprocessed simplex.

## Exact spectral lower bounds

At a rational vertex p, C=diag(p)-pp^T is exact rational. A witness is an arbitrary symmetric rational matrix A. Define

delta=max_i sum_j |C_ij-(A^2)_ij|.

Symmetry gives ||C-A^2||_2<=delta. Weyl's eigenvalue inequality and |sqrt(s)-sqrt(t)|<=sqrt(|s-t|) for s,t>=0 imply

Tr sqrt(C) >= Tr sqrt(A^2)-5sqrt(delta) >= Tr A-5sqrt(delta).

No numerical eigenvalue claim or positive-semidefiniteness claim about A is required. Numerical eigendecomposition only proposes A; the residual inequality is checked exactly. A lower bound is clipped at zero before multiplication by a lower bound for sqrt(2).

All square-root intervals are proved by integer arithmetic. At precision b, k=floor(sqrt(x)*2^b) is computed as isqrt(floor(x*2^(2b))); k/2^b and (k+1)/2^b are certified endpoints. The upper endpoint equals the lower endpoint when its square is exactly x. All other arithmetic is Python Fraction arithmetic.

For the simplex loss, the numerator is bounded upward using upper(sqrt(u))-lower(sqrt(l)); the denominator is bounded downward using lower(sqrt(u))+lower(sqrt(l)). Constant coordinates contribute zero. Thus every final acceptance is an exact rational inequality.

## Certificate format

`certificate.json` has four keys.

- `vertices`: exact rationals written as strings `"a/b"`. Entries 0–7 are v_2, w_2, v_3, w_3, v_4, w_4, v_5, w_5.
- `witnesses`: one symmetric rational 5-by-5 matrix A for each vertex, with the same index.
- `initial`: the four simplices of the triangulation above, as lists of vertex indices.
- `records`: the subdivision tree in depth-first order.

The records are read with a stack. The four initial simplices are pushed in the listed order, so the last one is
processed first. Each record applies to the simplex popped from the stack:

- `null`: the simplex is an accepted leaf.
- `[a, b, m]`: the simplex is split along the edge between its vertices at positions a and b (0-based). Vertex m is
  the exact midpoint of that edge. Two children are pushed in this order: the simplex with position a replaced by m,
  then the simplex with position b replaced by m.

The certificate is complete when the records are used up exactly as the stack becomes empty.

## Reproduction and result

Run `python replay.py` from this directory. Replay requires only the Python standard library. It checks the supplied rational spectral witnesses, the fixed initial geometry, every exact midpoint, every leaf inequality, and exhaustion of the subdivision tree. It does not use a numerical eigensolver.

The checked certificate has 2,175 vertices, 43,000 tree records, and 21,502 accepted leaves. The smallest certified leaf slack is approximately 2.277398269734683e-7, strictly greater than 1/5,000,000. The smallest certified vertex q lower bound is approximately 0.0132625610923975. The former, not the latter, is a lower bound for the entire domain.

`certificate.json` contains the exact rational vertices, rational symmetric spectral witnesses, four initial simplices, and complete subdivision tree. `replay.py` performs the exact replay. `spectral_bound.py` implements the residual bound. `certify.py` regenerates the certificate using NumPy and mpmath only to choose subdivisions and propose witnesses; acceptance is still exact rational arithmetic. `result.json` records the generation result.

Therefore q(p)>0 whenever max p_i<=3/4. Combined with the dimension-four near-axis lifting result, this proves dimension-five Lemma F.

## Packing corollary

Let a<2 and let a unit five-cube c+U[-1/2,1/2]^5 be contained in [-a/2,a/2]^5. Coordinatewise containment gives |c_i|<=(a-r_i)/2. If the origin were not in the interior of this unit cube, some column u_j of U would satisfy |u_j dot c|>=1/2. But

|u_j dot c| <= (1/2) sum_i |U_ij|(a-r_i)
             < (1/2) sum_i |U_ij|(2-r_i)
             = F_j/2 <= 1/2,

a contradiction. The strict inequality uses a<2 and the nonzero column. Thus every unit five-cube inside a five-cube of side a<2 contains the enclosing cube's center in its interior. Two such unit cubes cannot have disjoint interiors. Side length 2 is attained by placing two axis-aligned unit cubes side by side. Hence s_5(2)=2, under the same established dimension-four premise.
