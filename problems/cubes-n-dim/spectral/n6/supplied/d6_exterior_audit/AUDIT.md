# Independent audit: determinant and four-column exterior bounds

Both bounds below are valid for all real orthogonal 6×6 matrices, without row-feasibility assumptions. The audit found no gap. They are sufficient lower bounds on L; they do not by themselves prove the complete dimension-six theorem.

Let U=[x C] with x≥0 and ||x||₂=1. Put p_i=x_i², D=diag(x)C, B=DDᵀ=diag(p)−ppᵀ, s_k=||D_:k||₁ for k=1,...,5, and L=Σs_k. Every column of D has coordinate sum zero. The desired inequality is L≥2(Σsqrt(p_i)−1).

## Root-polytope fact

The zero-sum l1 unit ball in R6 is the convex hull of the oriented roots (e_i−e_j)/2. For a vector on its boundary, split its positive and negative masses (each 1/2) into nonnegative transport weights; doubling the weights gives the required convex combination. The origin handles interior points.

For a fixed number of columns, the norm of their exterior product is convex separately in each column. Maximizing successively over these finite convex combinations therefore reduces to roots. A collection of roots is independent exactly when its undirected edges form a forest. For a tree on r vertices, its unscaled incidence-column Gram determinant is r: Cauchy–Binet sums r squared reduced-incidence determinants, each 1. For a forest, component blocks multiply these factors.

## Universal full determinant bound

For five root columns, independent edges form a tree on six vertices. Their Gram determinant is 6/4⁵. Hence

    det(DᵀD) ≤ (6/4⁵) product_k s_k².

Cauchy–Binet and the cofactors of an orthonormal complement give det(DᵀD)=6 product_i p_i. Equivalently the general identity e_k(B)=(k+1)e_(k+1)(p) at k=5 gives the same result. Thus product s_k≥2⁵ sqrt(product p_i). AM–GM yields

    L ≥ 10 (product p_i)^(1/10).

The proof remains valid when a p_i or an s_k vanishes: both sides of the product inequality are nonnegative and the conclusion follows directly or by continuity. In dimension d the same proof gives L≥2(d−1)(product p_i)^(1/[2(d−1)]).

## Four-column exterior constant

Four independent root columns form a forest with two components on six vertices, including possible isolated vertices. Component sizes are 1+5, 2+4, 3+3; their Gram determinants are respectively 5/4⁴, 8/4⁴, 9/4⁴. Therefore every four-column submatrix satisfies

    ||D_:J's exterior product||₂² ≤ (9/256) product_(j in J) s_j².

Summing over the five four-element column subsets gives

    e4(B) ≤ (9/256) e4(s_1²,...,s_5²).

The constant was independently checked by exact rational enumeration of all 1,365 four-edge subsets of K6. Unscaled Gram determinants/counts:0/285,5/750,8/240,9/90. See `audit.py` and `result.json`.

## Scalar inequality, with all stationary cases

For nonnegative s_1,...,s_5 with Σs_i=L,

    e4(s_i²) ≤ (L/4)^8.

By homogeneity assume L=1. The simplex is compact. On a boundary face with four positive entries, e4 is their squared product, at most 1/4⁸ by AM–GM; with at most three positive entries it is zero.

At an interior stationary point, P=product s_i²>0 and S=Σ1/s_i². The Lagrange equations read

    2P( S/s_i − 1/s_i³ ) = lambda.

Thus each t_i=1/s_i is a positive root of t³−St+lambda/(2P)=0. Its derivative has only one positive critical point, so there are at most two positive roots. All-equal points and two-value multiplicities1:4 or2:3 exhaust the possibilities (exchanging values handles4:1 and3:2).

For 1:4 values, write s=(r,1,1,1,1)/(r+4). The objective is

    f(r)=(1+4r²)/(r+4)^8.

Its positive stationary values occur only at r=1 and r=1/3. The objective values are 1/5⁷ and3⁶/13⁷, respectively, both strictly below 1/4⁸. The comparisons are exact: 65,536<78,125, and4⁸·3⁶=47,775,744<13⁷=62,748,517.

For 2:3 values, write s=(r,r,1,1,1)/(2r+3). The objective is

    g(r)=(2r²+3r⁴)/(2r+3)^8.

The derivative numerator is 12r(1−r)(2r²−r+1). Since the quadratic is positive, the sole positive stationary ratio is r=1, again giving 1/5⁷<1/4⁸. This exhausts all possible interior maxima and proves the scalar inequality.

Combining the inequalities yields the independently audited bound

    L ≥ 4 (256 e4(B)/9)^(1/8).

## Direct polynomial form

For any index subset I, the rank-one determinant formula gives det(B_II)=product_(i in I)p_i · (1−Σ_(i in I)p_i). This identity also holds on coordinate faces by polynomial continuity. Summing over |I|=k counts each (k+1)-fold product (k+1) times, so e_k(B)=(k+1)e_(k+1)(p). In particular,

    L ≥ 4 (1280 e5(p)/9)^(1/8).

This expression requires no eigensolver, making it suitable for rational interval certification. The audit establishes the formula, not that its combination with other bounds covers the remaining simplex.

## Additional completed audits

### Joint positive-weight extension: PASS

`JOINT_BOUND.md` independently verifies pair smoothing, the downward convex-hull interpretation, and the finite exact coefficient polytope. `facets.py` enumerates every five-constraint active set and obtains 31 nonzero integer normals in `facets.json`. This replaces numerical LP dual conversion with exact fixed inequalities.

### Projected and grouped dimension-six bounds: PASS

`PROJECTED_AUDIT.md` independently verifies the sharp projected four-column constant 5/256, the formula e4(B_R)=5prod(p_R)+p_deleted e4(p_R), optimal deletion of a smallest coordinate, matrix-root concavity, and its correct fixed-R use in cell certificates. The original Marcus–Lopes (1957) paper, Theorem 4, p. 311, was checked directly. `projected_audit.py` independently checks all 8,190 deleted-row/root-set combinations with integer determinant arithmetic; results are in `projected_result.json`.

The same document audits the grouped leaf bound L≥8[(p_5+p_6)prod_(i=1)^4 p_i]^(1/8), retaining the original five completion columns. It is valid without frame compression. The merged pair must be fixed over the certified cell; the two smallest coordinates maximize this bound on the ordered simplex.


These analytic bounds require the separate domain certificates for complete dimension-six coverage.
