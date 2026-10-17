# Minimal dependency graph for the C5 near-axis theorem

## Conclusion

The C5 near-axis proof is independent of every earlier Lemma F result in dimensions four and five, and independent of the d5 spectral/covariance certificate. In fact it does not need the separate C4 certificate or analytic C1-C3 minorant proofs either.

The sufficient dependency chain is:

1. Elementary pair-allocation implication for positive C5.
2. The completed exact rational C5 simplex cover, including its elementary analytic near-axis carve.
3. Zero padding, giving every positive C_j for j<=5.
4. The general sign-lifting reduction, giving full C5.
5. Tail covariance summation and the scalar inequality p³>=4(1-p)².

This proves unrestricted Lemma F for target columns of support at most six whenever max squared entry is at least 141/200=.705. It therefore supplies the near-axis region of a six-dimensional proof without any lower-dimensional F premise.

## 1. Positive C5 and its elementary near-axis carve

The main exact cover is positive_c5_exact_tree.json.gz. Its standalone checker replay_positive_c5_exact_tree.py imports no producer code and uses no floating point. Each fixed-flow leaf checks nonnegative rational pair coefficients r_ij with r_ij²+r_ji²=1 and all five exact linear demand inequalities throughout its simplex. The analytic implication from demands to positive C5 is in positive_c5_certificate_proof.md.

The six near-axis leaves use only the following direct allocation calculation, not a lower-dimensional theorem. Normalize a positive five-coordinate vector so its largest entry is a, tail norm is s<=1/10, and tail sum is R. Put delta=1-a=s²/(1+a), t=R-delta, and use constant row allocations r_ij=t/(S-v_i). The largest pair capacity involves the largest two coordinates and equals t²(R^(-2)+T^(-2)), where T>=a. It is at most one if delta>=R³/(2T²), using (1+q)^(-1/2)>=1-q/2. Since R<=2s, it suffices that 8s(1+a)<=2a². The left side is at most 8/5, the right side at least 198/100. The axis itself is immediate. This proves the analytic carve directly.

## 2. Lower-rank positive minorants by zero padding

For b in R_+^j with j<=5, append 5-j zero entries. The scalar kernel h(x,y)=(x+y-sqrt(x²+y²))/2 satisfies h(x,0)=0. Consequently

H(b,0)=H(b) direct-sum 0.

For a nonnegative unit vector v in R^j, its zero-padded vector is a nonnegative unit vector in R^5, including when some original coordinates already vanish. The certified positive C5 inequality therefore gives positive C_j immediately. Homogeneity gives the corresponding unit-ball statement.

The exact simplex cover includes its boundary faces; no limiting argument through strictly positive coordinates is required for this step.

## 3. Sign lifting

sign_lifting_reduction.md proves full C_m from positive C_j for j<=m. Its balanced-sign argument uses only the positive subgroup inequalities, and its scaling argument reduces arbitrary signs to balance or a vanished sign group. Apply it with m=5 and the zero-padded consequences above. No earlier F theorem or covariance certificate occurs in this argument.

## 4. Near-axis F consequence

Let the target column be x=(a,b_1,...,b_5,0,...) and let M be any orthonormal completion. For every completion column, its tail restriction v has norm at most one. Orthogonality gives weighted cost 2f_b(v), so full C5 yields

Phi/2>=Tr H-b^T H b=sum b-b^T H b.

Applying positive C5 to v=b/||b|| gives b^T H b<=||b||³. Thus

Phi/2-(a+sum b-1)>=1-a-(1-a²)^(3/2).

This is nonnegative whenever p=a² satisfies p³>=4(1-p)². In particular p>=141/200 works by the exact arithmetic in near_axis_threshold.md.

## Separate corollary that DOES use d5

The ambient-independent theorem for every target of support at most five, with no near-axis condition, combines C4 near-axis control with the d5 covariance certificate in its far region. That separate corollary does use d5. It is not a dependency of the C5 near-axis proof, nor of a six-dimensional proof formed from independent six-dimensional cap/strip certificates plus C5 near-axis control.

The C5 near-axis result likewise does not automatically give unrestricted support-six control in arbitrary ambient dimension outside its stated near-axis range.
