# Positive C5: exact rational allocation certificate

Status: proved and independently audited. The certificate of record is positive_c5_exact_tree.json.gz. Its standalone checker replay_positive_c5_exact_tree.py imports no producer code and uses no floating point. The replay verified 15,785 records, 7,893 leaves, maximum depth 24, and exact covered relative volume 1. The mathematical proof and all degeneracies are audited in rank_five_minorant_audit.md.

## Pair-allocation implication

For b>=0 define H_ii=b_i and 2H_ij=b_i+b_j-sqrt(b_i^2+b_j^2). For u>=0 put S=sum u_i and N=||u||_2. Expanding gives

    u^T H(b)u=S(b dot u)-sum_(i<j)u_i u_j sqrt(b_i^2+b_j^2).

Suppose r_ij>=0 satisfy r_ij^2+r_ji^2<=1 and sum_(j!=i)r_ij u_j>=S-N. Pairwise Cauchy gives sqrt(b_i^2+b_j^2)>=b_i r_ij+b_j r_ji. Multiplying and summing proves

    u^T H(b)u<=N(b dot u).

For unit u this is the positive C5 inequality. For norm at most one it remains sufficient. Every nonzero nonnegative vector can be sorted and scaled into u=(1,x,y,z,w), with 1>=x>=y>=z>=w>=0. This ordered domain is the closed four-simplex with vertices having zero through four leading ones. The exact cover includes every boundary face.

## Elementary analytic near-axis cells

Normalize u so its largest coordinate is a, tail norm s<=1/10 and tail sum R. For s=0 the assertion is immediate. Otherwise put delta=1-a=s^2/(1+a), t=S-1=R-delta and r_ij=t/(S-u_i). All denominators are positive. The largest pair capacity involves the largest two coordinates, with denominators R and T>=a, so it is

    (1-delta/R)^2[1+(R/T)^2].

Since 0<=delta/R<=1 and (1+q)^(-1/2)>=1-q/2, this is at most one if delta>=R^3/(2T^2). There are at most four tails, hence R<=2s. It suffices that 8s(1+a)<=2a^2. Its left side is at most 8/5 and its right side at least 198/100. Thus this direct allocation proves the near-axis carve without any prior minorant or packing theorem. In the unnormalized simplex, sum of squared coordinate maxima<=1/100 implies the required normalized bound throughout the cell.

## V3 completed certificate: fixed rational allocations

The v3 certificate completed successfully: 7,892 splits, 7,893 leaves (7,887 fixed rational allocation cells, 6 analytic near-axis cells), maximum depth 24, square-root scale 2^48. Runtime was 7.28 seconds. See certify_positive_c5_v3.py and positive_c5_certificate_v3_result.json. Independent audit passed. 

V3 uses the same sufficient pair-allocation theorem, but fixes the entire rational allocation matrix on each simplex. A floating-point proposal supplies a nonnegative pair (p,q). For each pair it rounds q/(1+p) to a rational h in [0,1] and replaces the pair with

r_ij=(1-h²)/(1+h²), r_ji=2h/(1+h²).

Thus r_ij,r_ji>=0 and r_ij²+r_ji²=1 exactly, regardless of floating-point proposal accuracy. Diagonal entries are zero.

Let W be the five simplex vertices with a leading 1 appended, and m their exact rational centroid. Compute a rational M>=||m|| using the integer square-root enclosure, and set d=m/M. Then ||d||<=1, so ||v||>=d dot v for every v. For every row i the program checks, at every vertex w in W, the exact rational inequality

sum_j [d_j+r_ij-1] w_j >= 0.

This expression is linear in w. Consequently it holds throughout the simplex, and therefore

sum_(j!=i) r_ij v_j >= sum_j v_j-d dot v >= sum_j v_j-||v||=t.

All pair capacities and all demands are thus certified over the entire simplex. This proves the positive C5 inequality there. The only other acceptance rule is the previously proved analytic near-axis carve. Exact rational longest-edge bisection preserves the domain; emptying the stack certifies its complete cover.

Floating point cannot cause an unsound acceptance: it only chooses the rational h values. The proof uses only their exact capacities, exact rational vertex inequalities, and the exact square-root upper bound. A separate verifier may replace the proposal routine with a saved list of rational allocations, or reproduce those proposals and check the same exact conditions. The final certificate does not depend on the floating-point value of any asserted mathematical inequality.

The v3 generator now also exports positive_c5_exact_tree.json.gz, an exact witness file with no floating-point data. Its preorder records are ['s',i,j] for the edge split, ['a'] for an analytic near-axis leaf, or ['f',parameters] for a fixed-flow leaf. Parameters are rational strings h_ij in nested order i=0,...,4 and j=0,...,i-1; reconstruct r_ij=(1-h²)/(1+h²), r_ji=2h/(1+h²). At a split, push the child with vertex i replaced first and the child with vertex j replaced second; the stack therefore visits the latter next. A checker can reconstruct every simplex, verify each exact witness, and establish complete coverage without invoking the floating-point proposal function.

