# Projected exterior bounds for thin-coordinate regions

## Dimension-six result

Let p,x,C,L be as in EXTERIOR_FAMILY.md, and let R be any five of the six coordinate indices. Write

    B_R=(diag(p)-pp^T)[R,R],
    E_R=e_4(B_R)
       =sum_(I subset R, |I|=4) (product_(i in I)p_i)(1-sum_(i in I)p_i).

Then

    L >= 4[(256/5) E_R]^(1/8).                        (P4)

The right side is concave in p. At the thin-coordinate example proportional to (.795,.05120,.05095,.04980,.04926,.00379), choosing R to omit the last coordinate gives a numerical gap approximately +.05584 over 2(sum sqrt(p)-1), substantially stronger than the unprojected fourth-exterior bound.

## Projected root-polytope calculation

Put Z=diag(x)C and s_j=||Z[:,j]||_1, retaining the full six-coordinate l1 norms. Every normalized column is a convex combination of roots (e_i-e_j)/2. Project these roots onto the five coordinates R. Roots between visible indices remain (e_i-e_j)/2; a root to the omitted index becomes +/-e_i/2.

Treat the omitted coordinate as a ground vertex0. A collection of four projected roots is a reduced incidence matrix of four edges on the six vertices {0} union R, with the ground row deleted. If the edges contain a cycle, its columns are dependent. Otherwise the forest has two components. The component containing ground contributes1 to its incidence-column Gram determinant: after deleting the ground row, its tree incidence matrix is square with determinant +/-1. The nongrounded component of size b contributes b, by the usual Cauchy-Binet tree-minor identity. Thus the unscaled squared wedge volume is b<=5. (An isolated ground vertex is allowed and attains b=5.) Scaling all four columns by1/2 gives squared volume at most5/256.

By multilinearity of the exterior product and the triangle inequality, this bound extends from roots to normalized columns. Therefore

    e_4(B_R)=sum_(|J|=4)||wedge_(j in J)Z[R,j]||^2
           <=(5/256)e_4(s_1^2,...,s_5^2)
           <=(5/256)(L/4)^8.

The last step is the scalar optimization proved in EXTERIOR_FAMILY.md. Rearranging proves (P4).

## Concavity needed by simplex certificates

For every m and1<=k<=m, the function A -> e_k(A)^(1/k) is increasing and concave on positive-semidefinite m-by-m matrices. Here e_k(A) denotes the elementary symmetric function of its eigenvalues. A self-contained reduction to the scalar Marcus–Lopes theorem is as follows.

The scalar function f(lambda)=e_k(lambda)^(1/k) is symmetric, increasing and concave on the nonnegative orthant. If V diagonalizes theta A+(1-theta)B, write its eigenvalue vector as theta diag(V^T A V)+(1-theta)diag(V^T B V). Concavity of f bounds its value below by the corresponding convex combination of f on those two diagonal vectors. Each such diagonal vector is a doubly stochastic combination of the matrix's eigenvalue vector, since the squared entries of an orthogonal eigenbasis-change matrix are doubly stochastic. By Birkhoff's theorem, symmetry, and scalar concavity, f on that diagonal vector is at least f on the eigenvalue vector. This proves matrix concavity. Loewner monotonicity follows from eigenvalue monotonicity and the scalar coordinatewise monotonicity.

The covariance matrix B(p)=diag(p)-pp^T is Loewner-concave, because its excess over the convex combination at p=theta a+(1-theta)b is theta(1-theta)(a-b)(a-b)^T. Principal compression preserves this property. Composing B_R(p) with the increasing concave matrix function e_4^(1/4), and then with the increasing concave square root, proves concavity of E_R(p)^(1/8). Therefore (P4) is directly compatible with vertex Jensen plus square-root chord-loss certificates.

The scalar concavity source is Marcus and Lopes (1957), Theorem2, https://doi.org/10.4153/CJM-1957-037-9.

## General projected family

The same argument works for an arbitrary visible row set R of size m<n and any k<=m. For k<m, the maximum projected root-forest squared-volume constant is P_(m,k)/4^k, where P_(m,k) is the balanced product of m vertices in m-k components defined in EXTERIOR_FAMILY.md. Indeed the grounded component contributes1; making it an isolated ground maximizes the available nongrounded component sizes. For k=m the constant is1/4^m (a spanning tree rooted at ground).

Together with D_(n-1,k), the exact scalar constant for the n-1 full column costs, this gives

    L >= [4^k e_k(B_R)/(P_(m,k)D_(n-1,k))]^(1/(2k)) (k<m),
    L >= [4^m det(B_R)/D_(n-1,m)]^(1/(2m))          (k=m).

All these bounds are concave in p by the same PSD argument. They can also supply lower invariants for the nonnegative joint scalar inequalities and rational supporting-tangent construction of JOINT_EXTERIOR_BOUND.md.

## Explicit five-group corollary in dimension six

Taking a visible set R of four coordinates and k=m=4 gives

    det(B_R)=(product_(i in R)p_i)(1-sum_(i in R)p_i),
    L>=8[(product_(i in R)p_i)(sum_(i notin R)p_i)]^(1/8).

Equivalently merge any two probabilities into one, obtaining a five-component probability vector q. Then L>=8(product q)^(1/8). This does not assume that a rectangular Parseval frame can be compressed into an orthonormal basis: it follows from the four-column exterior sum and the proved five-variable scalar inequality.

For positive p, merging the two smallest probabilities maximizes product q, because for the merged pair i,j the product is (product_all p)*(1/p_i+1/p_j). Boundary cases follow by continuity. For certificate concavity, keep the merged pair fixed on each cell; the product is a weighted geometric mean of five nonnegative linear functions of p and its eighth root is concave. Do not infer that maximizing over pairs preserves concavity.
