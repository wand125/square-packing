# Independent strip-certificate audit

This audit concerns only sorted probability vectors in dimension six with 13/20 <= p_1 <= 159/200. It does not itself claim a complete dimension-six proof. Final verification status is recorded in result.json only after the full certificate replay succeeds.

The verifier verify.py uses only Python's standard library. It neither imports the generator nor any producer verification module. Floating-point arithmetic is not used in acceptance.

## Coverage

The sorted five-coordinate tail simplex has vertices with k equal nonzero coordinates, k=1,...,5. At either fixed p_1 cap these give exactly the ten supplied initial vertices. The proposed five staircase simplices are checked against the exact expected list. Each simplex has nonzero determinant. Their positively oriented chain is checked face by face: interior faces cancel, and every uncancelled face lies on a supporting hyperplane of the frustum (one of the two p_1 caps, a tail ordering equality, or p_6=0). Hence the chain's multiplicity is constant on the interior of the convex frustum. All simplex interior contributions have positive orientation, so the constant counts coverage without cancellation. Independently computing its volume gives exactly the frustum volume [(7/20)^5-(41/200)^5]/(5!)^2. The multiplicity is therefore one; coverage and disjoint interiors follow.

Every tree record consumes exactly one pending simplex. A split is checked to use the exact rational midpoint of two distinct vertices and replaces each endpoint in one child. Both children are pushed, in the producer's documented traversal order. Every pending simplex must eventually become a strictly accepted leaf. Extra records and unfinished subtrees fail. All stored vertices must be used.

## Analytic lower bounds

The covariance nuclear-norm bound is valid since B(p)=diag(p)-pp^T=ZZ^T and the sum of column Euclidean norms dominates its nuclear norm. Zero-sum columns have l1 norm at least sqrt(2) times their Euclidean norm. The spectral trace witness does not require its rational matrix A to be PSD: a row-sum residual bound gives ||A^2-B||_op <= delta, whence Tr sqrt(B) >= Tr |A|-6 sqrt(delta) >= Tr A-6 sqrt(delta). The verifier recomputes the residual exactly, encloses roots at 100 bits and uses only conservative endpoints.

The two missing-edge corrections and their interpolation losses follow EDGE_BOUND.md. I checked the stronger correction's discarded-mass calculation: E-d/2=((r_pos-r_neg)^2+v)/2 <= rho^2, rho <= 2 delta_column, and t_column <= sqrt(1/2). These imply R <= (9/2)D^2+D, hence correction (sqrt(1+18R)-1)/9. Its derivative is between zero and one. The pair-product covariance interpolation error is sum(width_i width_j)/4, with half of that for R/2.

The determinant and exterior formulas follow the root-polytope incidence-forest calculation. The verifier independently derives the forest constants by balanced component sizes. Joint facets need not be exhaustive: every supplied nonnegative normal must satisfy its five equal-support scalar inequalities. Pair smoothing proves these inequalities for all nonnegative column-cost vectors. Each rational Young tangent is then checked against its exact formula and exact 2^-40 downward rounding.

The fixed projected exterior bound uses the same omitted coordinate throughout each leaf. Its concavity follows the Loewner concavity of covariance, the increasing concavity of the elementary symmetric spectral mean and an increasing concave square root. Fixed grouped coordinates likewise give a linear probability map; thus the corresponding lower bound is concave. No maximum over differing concave functions is used in a leaf's Jensen argument.

The elementary-symmetric mean concavity is the Marcus–Lopes theorem identified in the source proof. The remaining negative square-root terms are controlled by an exact conservative chord loss. For coordinate extrema l,u, twice the maximum square-root chord gap is (sqrt(u)-sqrt(l))^2/[2(sqrt(u)+sqrt(l))]. Its implemented upper enclosure increases the numerator and decreases the denominator. Constant coordinates are omitted.

All leaf tests recompute one fixed bound at every leaf vertex, subtract the appropriate rational interpolation errors, and require strictly positive rational slack. Rational root computations use independent binary search and explicitly verify lower^n <= radicand <= upper^n.

## Fixed grouped bound derivation

Merge the last two coordinates of every column z by summation, obtaining five-coordinate zero-sum columns y. Their l1 costs do not exceed the original costs s. Their covariance is diag(q)-qq^T with q=(p_1,p_2,p_3,p_4,p_5+p_6), because the aggregation matrix has one unit entry per original coordinate and disjoint row supports. Cauchy–Binet gives the sum of all four-column squared volumes as e_4(covariance)=5 product(q). The root-polytope bound in five coordinates gives each squared volume at most (5/256) times the relevant product of squared s costs. Therefore e_4(s^2) >=256 product(q). Among five nonnegative costs with total L, the exact equal-support comparison gives e_4(s^2)<=L^8/4^8 (support four is maximal). Consequently L>=8 product(q)^(1/8). The right-hand side is a constant times a weighted geometric mean of five linear nonnegative coordinates with exponent sum 5/8, hence concave. This validates type3, without assuming that aggregation preserves an orthonormal-complement representation with four columns.

## Terminal result

Independent replay completed successfully with process exit code 0. It verified 59,961 vertices, 4,001,519 tree nodes and 2,000,762 strictly accepted leaves, with no pending subtrees and no unused vertices. Leaf counts by types 0 through 5 were 1,153,604; 649,006; 25,391; 93,810; 0; 78,951. Thus no projected-bound leaf is actually needed by this particular certificate.

The exact minimum slack is recorded in result.json and equals the producer's reported rational value (approximately 8.143593676332183e-10). Runtime was 358.614 seconds. The checked certificate SHA256 is 0bd2317bd8c2fdc87ec9d2350ee6f136680d74430511aa70ca10467862fee149.

An initial file watcher encountered a JSON parse error because it read while the producer was still writing. No verification had run at that point. After the producer confirmed exit code 0, replay on the complete artifact succeeded; the final replay.log is this successful complete run.
