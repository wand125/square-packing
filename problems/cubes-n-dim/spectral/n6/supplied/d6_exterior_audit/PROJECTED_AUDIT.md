# Independent audit of the projected and grouped dimension-six bounds

The projected bound and its concavity argument pass independently. Let Z=diag(x)C, s_j=||Z_:j||₁ using the original full six-coordinate norms, L=Σs_j, and B=ZZᵀ=diag(p)−ppᵀ.

## Projected four-column constant

Delete coordinate h and retain R, a set of five coordinates. Normalize each original zero-sum column by its original norm s_j. It is a convex combination of roots (e_i−e_j)/2. After projection, roots touching h become signed unit vectors divided by two. Thus any four extreme columns form a reduced incidence matrix of four edges on six vertices with the h row deleted.

A cyclic set has dependent columns. An independent set is a forest with two components. The grounded component's reduced incidence Gram determinant is one; the other component's determinant is its number of vertices, at most five. This includes an isolated ground vertex, which attains five. Dividing by4⁴ gives the sharp constant 5/256.

The full six-coordinate column norms must be retained in this argument. A claim using arbitrary projected-column norms and the same root polytope would need a separate justification.

Independent integer enumeration in `projected_audit.py` checks all1,365 edge subsets for each of six deleted rows, totaling8,190 cases. For every deleted row, the unscaled Gram determinants0,1,2,3,4,5 have counts285,625,160,90,80,125. Results are in `projected_result.json`. This checker uses the determinant permutation formula, separately from the elimination-based unprojected checker.

Consequently

    e4(B_R) ≤ (5/256)e4(s_1²,...,s_5²) ≤ (5/256)(L/4)^8,
    L ≥ 4[(256/5)e4(B_R)]^(1/8).

The scalar inequality was independently audited in AUDIT.md and also follows from JOINT_BOUND.md.

## Exact polynomial and optimal deleted coordinate

The principal-minor formula gives

    e4(B_R)=5 product_(i in R)p_i + p_h e4(p_R).

For distinct deleted indices i,j, the difference is

    e4(B_without_i)−e4(B_without_j)
      =4(p_j−p_i) product_(k not in {i,j})p_k.

Therefore deleting a smallest probability maximizes this projected invariant, including boundary points by the polynomial identity. On the ordered simplex p_1≥...≥p_6, deleting coordinate6 is valid throughout every cell.

## Concavity: verified source and composition

Marcus and Lopes, “Inequalities for Symmetric Functions and Hermitian Matrices,” Canadian Journal of Mathematics9 (1957), pp305–312, Theorem 4 on p. 311, establishes the Minkowski-type inequality for elementary-symmetric characteristic coefficients of nonnegative Hermitian matrices. Homogeneity gives concavity of A↦e_k(A)^(1/k). The primary PDF was checked directly: [original article](https://doi.org/10.4153/CJM-1957-037-9).

Loewner monotonicity follows because ordered eigenvalues increase under PSD addition, and e_k on nonnegative eigenvalues is coordinatewise increasing. Also, for p=θa+(1−θ)b,

    B_R(p)−θB_R(a)−(1−θ)B_R(b)
      =θ(1−θ)(a_R−b_R)(a_R−b_R)ᵀ ≥0.

Hence p↦e4(B_R(p))^(1/4) is concave. Composing with the increasing concave square root proves concavity of e4(B_R(p))^(1/8), and thus of the projected lower bound. Continuity covers singular covariance matrices and coordinate faces.

Important: the maximum over different R is not automatically concave. A simplex certificate must use one fixed R over the cell, or prove the cell separately for a chosen R. It cannot choose different maximizing deleted rows at different vertices and then invoke Jensen. Ordered-simplex certification avoids this issue by always deleting its smallest coordinate.

If G(p) is this fixed-R lower bound, vertex interpolation and the existing square-root chord-error estimate give

    L−2(Σsqrt(p_i)−1)
      ≥min_vertex [G(v)−2(Σsqrt(v_i)−1)]−chord_loss.

Thus the generator's projected leaf test is mathematically justified.

## Grouped determinant bound used in leaf type3

Merge any two rows of Z by adding them. Let q be the resulting five group masses, e.g.

    q=(p_1,p_2,p_3,p_4,p_5+p_6).

The resulting5×5 matrix Z' has zero-sum columns and covariance Z'Z'ᵀ=diag(q)−qqᵀ. Its column l1 norms s'_j are at most s_j. Crucially, there are still five columns; no replacement by a square orthogonal completion is assumed.

In five ambient rows, the four-root forest constant is5/256. Therefore

    5 product q=e4(Z'Z'ᵀ)
      ≤(5/256)e4((s'_j)²)≤(5/256)(L/4)^8,
    L≥8(product q)^(1/8).

This is exactly the leaf-type3 expression. It is concave in p: product q to the1/8 power is a weighted geometric mean with total exponent5/8, extended by a constant coordinate, and q depends linearly on p. For positive p, merging pair a,b makes product q=(product p)(1/p_a+1/p_b), maximized by the two smallest entries. The same conclusion follows on the boundary by continuity. Again the ordered simplex permits using one fixed merged pair across the cell.
