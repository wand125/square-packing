# Unrestricted dimension-six Lemma F and two-cube packing

## Status: verified

The cap and strip certificates have both passed two exact verifier implementations. The C5 near-axis theorem has passed independent mathematical review and standalone exact saved-tree replay. The proof is complete.

Theorem: every U in O(6), without any row-l1 restriction, satisfies

    F_j(U)=sum_i |U_ij|(2-||U_i||_1)<=1

for every column j. Consequently two unit six-cubes require an enclosing six-cube of side at least 2, and side 2 is attained.

The proof covers max p<=13/20 with the completed cap certificate, 13/20<=max p<=159/200 with the generated strip certificate, and max p>=141/200 with the independently audited C5 theorem. The strip and near-axis regions overlap. No dimension-four or dimension-five packing theorem is a premise. The C5 dependency graph is in [c5_dependency_graph.md](../general_dimension/c5_dependency_graph.md).

## 1. Reduction to a weighted orthonormal complement

Fix a column of U, change row signs, and permute columns to write U=[x C], where x>=0 and ||x||_2=1. Put p_i=x_i^2, S=sum x_i, and

    L=sum_(i,k) x_i|C_ik|.

Then F_j=2S-1-L, so it suffices to prove L>=2(S-1). No row-feasibility hypothesis is imposed.

Let Z=diag(x)C and B=ZZ^T=diag(p)-pp^T. Each column z_k of Z has coordinate sum zero. Write s_k=||z_k||_1 and t_k=||z_k||_2. A zero-sum vector has l1 norm at least sqrt(2) times its l2 norm, so

    L>=sqrt(2)sum_k t_k>=sqrt(2)Tr sqrt(B).             (1)

The second inequality is the nuclear norm triangle inequality. Let T(p)=Tr sqrt(B) and q(p)=sqrt(2)T(p)-2sum_i sqrt(p_i)+2.

## 2. Missing-edge improvements

For each nonzero z_k retain its largest positive coordinate and its largest negative absolute coordinate, and mark their unordered pair. At most five pairs are marked. Let R(p) be the sum of the ten smallest pair products p_i p_j among the fifteen pairs.

Writing rho_k for the discarded l1 mass, one has

    rho_k<=s_k-2t_k^2/s_k,
    R(p)<=sum_k(s_k^2-2t_k^2).

For the second assertion, the covariance offdiagonal entry at each unmarked pair is -p_i p_j; its absolute value must be supplied by products involving discarded coordinates. Summing those products and using the first inequality gives the estimate. Weighted Cauchy-Schwarz gives s_k<=1, and therefore

    R(p)<=2sum_k(s_k-sqrt(2)t_k),
    L>=sqrt(2)T(p)+R(p)/2.                            (2)

A stronger quadratic variant is used in the strip certificate. Put delta_k=s_k-sqrt(2)t_k and D=sum delta_k. If rp,rn are the discarded masses of the two signs and v their squared norm, the total absolute offdiagonal mass involving discarded entries is

    E=s rho-rho^2/2-v/2,
    E-(s^2-2t^2)/2=(rp-rn)^2/2+v/2<=rho^2.

Together with rho<=2delta and t<=sqrt(lambda_max(B)), this gives

    R(p)<=(9/2)D^2+sqrt(2lambda_max(B))D.

The absolute row sum of B is 2p_i(1-p_i)<=1/2, so lambda_max(B)<=1/2. Solving the quadratic yields the valid lower bound

    L>=sqrt(2)T(p)+(sqrt(1+18R(p))-1)/9.              (3)

The optional sharper constant developed elsewhere is not used by the current strip certificate. Full proofs and interpolation losses for (2), (3) are in [EDGE_BOUND.md](../d6_spectral/EDGE_BOUND.md).

## 3. Determinant and exterior-power bounds

The zero-sum l1 unit ball is the convex hull of roots (e_i-e_j)/2. Every deleted-row maximal minor of Z has absolute determinant product_i x_i, by the cofactor identity for [x C]. Multilinearity reduces the determinant of normalized columns to reduced incidence matrices of five edges, whose determinants are 0 or +/-1 before scaling. Therefore

    product_k s_k>=2^5 product_i x_i,
    L>=10(product_i p_i)^(1/10).                     (4)

More generally, a wedge of k normalized columns is bounded by its maximum on k roots. Independent roots form a forest. Its unscaled squared volume equals the product of its component sizes. In six coordinates the maximum squared-volume constants, including the factor 4^(-k), are

    M=(1/2,1/4,1/8,9/256,6/1024), k=1,...,5.

Cauchy-Binet then gives

    e_k(B)<=M_k e_k(s_1^2,...,s_5^2),
    e_k(B)=(k+1)e_(k+1)(p).                          (5)

The second identity follows by summing principal minors p_I(1-sum_(i in I)p_i).

For any nonnegative coefficients a_k, the maximum of sum a_k e_k(s^2) on sum s_i=1 is attained at equal positive coordinates on some support of size m. Indeed, holding a+b fixed and putting u=ab, each elementary symmetric summand is a convex quadratic in u. Choose a maximizer with minimum support; any unequal positive pair is an interior point of this interval, and either an endpoint improves the objective or the zero endpoint preserves it while reducing support. Both contradict that choice. Thus

    sum_k a_k e_k(s^2/L^2)
       <=max_(1<=m<=5) sum_k a_k binom(m,k)/m^(2k).   (6)

In particular e_4(s^2)<=(L/4)^8. This gives two more strip bounds:

- Group the two smallest probabilities into one mass. With sorted p,

    L>=8[((p_4+p_5)product_(i=0)^3 p_i)]^(1/8).       (7)

  This is also a four-row square-projection determinant bound. It does not assume compression of a rectangular frame into an orthonormal basis.

- Project Z onto its five largest-probability rows R. The projected roots are roots between visible vertices or coordinate vectors corresponding to a ground vertex. A four-edge forest has a grounded component of Gram determinant 1 and one nongrounded component of size at most 5. Thus the squared-volume constant is 5/256, and

    L>=4[((256/5)e_4(B_R))]^(1/8).                   (8)

For joint bounds, define H_k=[(k+1)e_(k+1)(p)/M_k]^(1/(2k)). Choose nonnegative rational a_k satisfying

    sum_k a_k binom(m,k)/m^(2k)<=1 for every m=1,...,5.

Equations (5), (6) imply sum_k a_k(H_k/L)^(2k)<=1. For arbitrary nonnegative rational t_k put

    D0=1+sum_k(2k-1)a_k t_k^(2k),
    c_k=2k a_k t_k^(2k-1)/D0.

Convex tangency to sum a_k u_k^(2k) at t gives

    L>=sum_k c_k H_k(p).                             (9)

Rounding any c_k downward preserves validity. All support inequalities and rational tangent coefficients are checked exactly by the certificate verifier. Exhaustive facet enumeration is useful for finding witnesses but is not needed for their validity: every recorded witness is verified individually.

Detailed self-contained proofs are in [DETERMINANT_BOUND.md](../d6_central/DETERMINANT_BOUND.md), [EXTERIOR_FAMILY.md](../d6_central/EXTERIOR_FAMILY.md), [JOINT_EXTERIOR_BOUND.md](../d6_central/JOINT_EXTERIOR_BOUND.md), and [PROJECTED_EXTERIOR_BOUND.md](../d6_central/PROJECTED_EXTERIOR_BOUND.md). Independent audits are in [d6_exterior_audit](../d6_exterior_audit/).

## 4. Concavity, exact arithmetic, and simplex acceptance

T(p) is concave: B(p) is Loewner-concave, and trace square root is increasing and concave on positive-semidefinite matrices. The functions on the right of (4),(7) are concave weighted geometric means of nonnegative linear forms.

The elementary-symmetric-root concavity theorem of Marcus and Lopes (1957), Theorem 2, https://doi.org/10.4153/CJM-1957-037-9, proves that e_j(p)^(1/j) is concave. Composing with the increasing concave powers j/(2(j-1)) proves concavity of H_k. The same scalar symmetric concavity lifts to positive-semidefinite matrices by diagonalizing a convex combination and applying doubly stochastic averaging to the two diagonal vectors. It is also Loewner-monotone. Thus (8) is concave because B_R(p) is Loewner-concave. Every fixed nonnegative rational combination (9) is concave. No maximum of concave bounds is assumed concave.

On a simplex with coordinate ranges [l_i,u_i], define

    E_sqrt=sum_i (sqrt(u_i)-sqrt(l_i))^2/[2(sqrt(u_i)+sqrt(l_i))],

with zero contribution for constant coordinates. This is twice the maximum square-root chord gap, summed over coordinates. For any concave lower bound A(p) for L,

    L-2(S-1)>=min_vertex[A(v)-2sum sqrt(v_i)+2]-E_sqrt. (10)

For R(p), writing Delta_i=u_i-l_i, the bounded covariance inequality gives

    R(p)>=sum_vertex theta_v R(v)-sum_(i<j)Delta_i Delta_j/4.

Thus bound (2) incurs an additional loss sum Delta_i Delta_j/8. The scalar correction f(R)=(sqrt(1+18R)-1)/9 is increasing, concave, and 1-Lipschitz; hence bound (3) incurs an additional loss sum Delta_i Delta_j/4. Each accepted leaf chooses one fixed bound and proves its rational lower margin strictly positive.

At rational vertices, square-root and higher-root endpoints are checked using integer powers and integer root extraction. Spectral square-root witnesses are symmetric rational matrices A with exact residual delta=max_i sum_j|B_ij-(A^2)_ij|. Eigenvalue perturbation gives

    Tr sqrt(B)>=Tr A-6sqrt(delta).

No numerical eigensolver claim is trusted. Rational residuals, root intervals, vertex values, interpolation losses, midpoint identities, and exhaustion of every subdivision tree are checked exactly. Numerical calculations only propose spectral witnesses, tangent witnesses, and splits.

## 5. Central cap: verified

Sort p decreasingly. The domain p_1<=13/20 has vertices

    v_k=(1/k repeated k times, then zeros),
    w_k=(13/20,7/[20(k-1)] repeated k-1 times, then zeros),
    k=2,...,6.

In alternating order v2,w2,...,v6,w6 indexed 0,...,9, the five initial simplices are

    (0,2,4,6,8,1), (2,4,6,8,1,3), (4,6,8,1,3,5),
    (6,8,1,3,5,7), (8,1,3,5,7,9).

This standard pulling triangulation covers the capped ordered simplex. Its exact midpoint subdivision certificate uses bound (2) and proves strict positivity on every leaf.

The completed certificate has 25,755 vertices, 1,636,601 tree records and 818,303 leaves, maximum depth 32. Its minimum positive leaf margin is approximately 8.86324e-10. Both the standard exact replay and an independently implemented exact replay passed. The latter's result records SHA-256 c33aa40033275bf66488a8b781898dcb051aad39459caa6900e0d30413986b82.

Files: ../d6_spectral/certificate_cap65/README.md, certificate.json, replay.py, independent_verify.py, result.json, and independent_result.json.

## 6. Intervening strip: verified

The sorted strip 13/20<=p_1<=159/200 is the convex frustum with alternating vertices

    (13/20,(7/20)/k repeated k times, remaining zeros),
    (159/200,(41/200)/k repeated k times, remaining zeros),
    k=1,...,5.

The projective change (p_1,p_tail)->(p_1/(1-p_1),p_tail/(1-p_1)) sends it to an interval times the ordered normalized-tail simplex. The staircase triangulation of that product pulls back to the same five index tuples used above. Thus the initial simplices cover the entire closed strip.

The completed generator uses bounds (2), (3), (4), (7), (8), (9), with exactly the acceptance rules of Section 4. It reports 4,001,519 records, 2,000,762 leaves, 59,961 vertices and maximum depth 38, with minimum rational slack approximately 8.14359e-10. Both exact replay implementations completed successfully with process exit code 0. They agree on all leaf counts and the exact minimum positive rational slack. The independently implemented verifier additionally checked exact initial-domain coverage, exhaustion of all subtrees, and use of every stored vertex.

Files are in ../d6_spectral/certificate_cap795/: certificate.json, result.json, certify.py and README.md. The raw certificate SHA-256 is `0bd2317bd8c2fdc87ec9d2350ee6f136680d74430511aa70ca10467862fee149`. The independently implemented checker is in ../d6_strip_independent/.

Terminal evidence is in ../d6_spectral/certificate_cap795/replay_result.json and replay.log, and ../d6_strip_independent/result.json and replay.log. The independent receipt records the same raw certificate SHA-256.

## 7. Near axis: unrestricted proof for max p>=141/200

### The minorant

For b in R^5 with b_i>=0, define the symmetric matrix H(b) by

    H_ii=b_i,
    2H_ij=b_i+b_j-sqrt(b_i^2+b_j^2)  (i!=j).

The audited C5 theorem states that, for every v in R^5 with ||v||_2<=1,

    v^T H(b)v <= f_b(v):=(|b dot v|+sum_i b_i|v_i|)/2.       (C5)

The positive-vector allocation proof, exact saved-tree certificate, standalone rational replay, and sign-lifting audit are supplied in `../general_dimension/positive_c5_certificate_proof.md`, `../general_dimension/positive_c5_exact_tree.json.gz`, `../general_dimension/replay_positive_c5_exact_tree.py`, and `../general_dimension/rank_five_minorant_audit.md`. The exact replay checks 15,785 records, 7,893 leaves, maximum depth 24, and covered relative volume 1.

### Covariance summation

Let x be a nonnegative unit target column, supported on at most six coordinates, in an orthogonal matrix of ambient dimension at least six. Smaller ambient dimensions are first embedded by adjoining an identity block, which leaves F for every original column unchanged. Choose its largest coordinate a and write its remaining nonzero coordinates, padded with zeros, as b in R^5. Put s=||b||_2, so a^2+s^2=1. For a completion column y, let v be the restriction to these five tail rows. Then ||v||_2<=1, and orthogonality gives

    a y_1=-b dot v.

Its weighted l1 contribution is therefore

    a|y_1|+sum_i b_i|v_i|=2f_b(v)>=2v^T H(b)v.

If v_k are these restrictions for all completion columns, row orthogonality gives

    sum_k v_k v_k^T=I_5-bb^T.

Consequently the total weighted completion cost L satisfies

    L/2 >= Tr(H(b)(I_5-bb^T))
         =sum_i b_i-b^T H(b)b.

If s=0, the target is a coordinate vector and F=1 immediately. Otherwise apply C5 at the nonnegative unit vector b/s. Here f_b(b/s)=s, hence

    b^T H(b)b<=s^3.

Writing S=a+sum_i b_i and F=2S-1-L gives

    1-F >=2(1-a-s^3)
         =2s^2[1/(1+a)-s].                                (1)

No row-l1 hypothesis and no frame-compression argument is used.

### Exact threshold

The bracket in (1) is nonnegative precisely when

    (1-a)(1+a)^3<=1.

For a>0, expand and divide by a to obtain a^3+2a^2>=2. Set p=a^2. Since both sides of p^(3/2)>=2(1-p) are nonnegative, the condition is equivalent to

    g(p):=p^3-4(1-p)^2>=0.

On [0,1], g'(p)=3p^2+8(1-p)>0, and the exact endpoint calculation is

    g(141/200)=18421/8000000>0.

Thus every target supported on at most six coordinates satisfies F<=1 in every ambient dimension whenever its maximum squared coordinate is at least 141/200. The inequality is strict except at a coordinate target.


## 8. Packing conclusion

If a unit cube c+U[-1/2,1/2]^6 is contained in an axis-parallel six-cube of side a<2 centered at the origin, coordinatewise containment gives

    |c_i|<=(a-r_i(U))/2.

The unrestricted Lemma F proved above applies. If the origin were not in the interior of the unit cube, some column u_j of U would satisfy |u_j dot c|>=1/2. But

    |u_j dot c|<=1/2 sum_i |U_ij|(a-r_i(U))
               <1/2 F_j(U)<=1/2,

a contradiction. Thus every unit six-cube in an enclosing cube of side less than 2 contains the enclosing center in its interior, so two cannot have disjoint interiors. Side 2 is attained by placing two axis-aligned unit cubes side by side. This proves s_6(2)=2.

## References

M. Marcus and L. Lopes, “Inequalities for Symmetric Functions and Hermitian Matrices,” Canadian Journal of Mathematics 9 (1957), 305–312, Theorem 2. [Publisher and DOI](https://doi.org/10.4153/CJM-1957-037-9).
