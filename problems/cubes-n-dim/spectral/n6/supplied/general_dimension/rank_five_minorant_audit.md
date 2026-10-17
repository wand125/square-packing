# Independent audit of rank-five minorant

Date: 2026-10-16. Mathematical audit PASSED; independent exact acceptance/coverage replay PASSED; standalone saved-tree exact replay result is recorded in positive_c5_standalone_replay_result.json.

## Certified statement and scope

Full C5 holds: for nonnegative b and ||v||2<=1,

(|b dot v| + sum b_i |v_i|)/2 >= v^T H(b)v,

where H has diagonal b_i and off-diagonal (b_i+b_j-sqrt(b_i^2+b_j^2))/2. This follows from the positive C5 certificate below and the previously audited sign lifting using C1 through C4. No arbitrary-ambient full support-six conclusion follows from the available far-region certificate.

## Exact fixed allocation test

For u>=0, let S=sum u and N=||u||. The expansion is

u^T H(b)u = S(b dot u) - sum_{i<j} u_i u_j sqrt(b_i^2+b_j^2).

If nonnegative r_ij satisfy r_ij^2+r_ji^2<=1 and sum_{j!=i}r_ij u_j>=S-N, Cauchy bounds each pair square root below by b_i r_ij+b_j r_ji. Multiplying and summing gives u^T H(b)u<=N(b dot u). Thus it proves the desired positive C5 statement for unit u and, by radial scaling, for the ball.

The rational parametrization ((1-h^2)/(1+h^2),2h/(1+h^2)) has nonnegative entries and capacity exactly one whenever 0<=h<=1. All ten pairs are checked explicitly in the independent replay. For simplex centroid m and a verified rational M>=||m||, Cauchy gives ||u||>=m dot u/M. Hence the exact row inequalities at vertices,

M sum_j (r_ij-1)u_j + m dot u >=0,

extend linearly to the whole simplex and imply the required demands. M is positive; the independent checker verifies its square bracket explicitly. No floating-point result participates in an acceptance in the standalone verifier.

## Analytic near-axis cells

After normalization let largest coordinate be a, tail norm s, tail sum R, delta=1-a, and t=R-delta. For nonzero tails define r_ij=t/(S-u_i). These denominators are positive; coefficients increase with u_i, so only the two largest rows need be checked. Put T=S-u_2>=a. Their squared pair capacity is

(1-delta/R)^2 [1+(R/T)^2].

Here 0<=delta/R<=1 since S>=1. The inequality 1-x/2<=1/sqrt(1+x) for x>=0 shows that delta>=R^3/(2T^2) suffices. At most four tails give R<=2s. Since delta=s^2/(1+a), a sufficient condition is 4s(1+a)<=a^2. For s<=1/10 the left side is at most 4/5 while a^2>=99/100, so the condition holds strictly whenever s>0. The exact axis is immediate.

Every accepted near-axis simplex has sum of squared coordinate maxima <=1/100 in the chart u=(1,x,y,z,w). This bounds every unnormalized tail norm by 1/10 and therefore also bounds the normalized tail norm by 1/10. Thus its entire closed simplex is covered.

## Coverage and degeneracies

Every nonzero nonnegative vector can be sorted and scaled into 1>=x>=y>=z>=w>=0. This closed ordered domain is exactly the four-simplex with vertices having respectively zero through four leading ones. Every checked vertex remains ordered and nonnegative. Replacing either endpoint of an edge with its exact midpoint yields two child simplices with union equal to their parent; the children have half its volume. The replay requires the saved tree to consume exactly the pending stack, with no missing or excess records. It additionally checks exact total relative leaf volume one. All inequalities are non-strict, so faces, ties and zero coordinates are included. The zero vector and exact axis require no division. The rational centroid always has leading coordinate one and nonzero norm.

## Sign lifting and ambient-independent near-axis implication

The sign lifting proof was independently reviewed again. Its positive-part bound follows by restricting to indices u_i>||u||lambda_i; internal edges give W(U-||u_S||), cross edges give (1-W)U. The triangle-defect bound is Cauchy applied to a convex combination of unit support vectors. Two applications establish the weighted-balanced mixed-sign bound. Scaling one sign group's weights produces a convex quadratic expression below balance; beyond balance the derivative relative to its linear objective is nonpositive. Each sign group in a mixed-sign five-vector has at most four entries, so audited C1--C4 suffice. Zero weights/probabilities follow by continuity; zero vector coordinates can be removed. Overall sign reversal covers negative vectors. Radial extension from the sphere uses q(ru)<=r^2 f(u)<=r f(u), without assuming H is positive semidefinite.

For a target supported on at most six coordinates in any ambient dimension, choose largest coordinate a>=0 and tail b in R^5, s=||b||. The five-row restriction of each completion column has norm at most one and covariance sum I-bb^T. Full C5 therefore gives Phi/2>=sum b-b^T H(b)b. Applying positive C5 to b/s gives b^T H(b)b<=s^3. Thus

1-F >=2(1-a-s^3)=2s^2[1/(1+a)-s].

The sufficient condition is (1-a)(1+a)^3<=1. Its derivative is 2(1+a)^2(1-2a), nonpositive for a>=1/2. At a=21/25 it equals 389344/390625<1. Consequently a^2>=441/625=0.7056 suffices; in particular 71/100 is safe. The axis s=0 is immediate. The stronger simple rational threshold could reduce a remaining finite-dimensional strip, but does not justify extending a fixed-complement-column far certificate to arbitrary ambient dimension.

## Independent computational evidence

1. audit_positive_c5_v3.py uses the producer only as an untrusted proposal oracle. All acceptance conditions, norm brackets, capacities, geometry and traversal are independently implemented. It obtained 7,892 splits; 7,887 fixed-flow and 6 near-axis leaves; depth 24; exact relative volume one. Its complete leaf digest is e2b3d866799d36188399784c3ac7065d97607e7b506b2b802903204a544fd18e.
2. replay_positive_c5_exact_tree.py reads only positive_c5_exact_tree.json.gz, imports no producer code, and uses rational arithmetic plus integer square root. It independently reconstructs every split, decodes all rational unit-circle witnesses, and validates every leaf. See positive_c5_standalone_replay_result.json for its completion counts and tree digest.

The standalone saved-tree replay completed successfully: 15,785 records, 7,892 splits, 7,887 fixed-flow leaves, 6 near-axis leaves, maximum depth 24, and exact relative volume one. SHA-256 of the compressed tree is 12c4704d887eccc01d879935e495c3532fbe794a5c022255c8e40cb3d599d56d.

### Sharper rational squared-coordinate threshold

For a>0, expansion of (1-a)(1+a)^3<=1 gives a^3+2a^2>=2. With p=a^2 in [0,1], both sides of p^(3/2)>=2(1-p) are nonnegative, so this is equivalent to p^3>=4(1-p)^2. The derivative of p^3-4(1-p)^2 is 3p^2+8(1-p)>0 throughout [0,1]. At p=141/200 the exact positive margin is 18421/8000000; at p=71/100 it is 21511/1000000. Thus the near-axis conclusion already holds for p>=141/200=0.705. This polynomial arithmetic was checked independently after the original .7056 observation.

## Dependency simplification: positive C5 is sufficient by itself

Confirmed on final dependency audit. The positive C5 allocation proof holds for every nonnegative weight vector b, including zero weights: the pairwise Cauchy inequality and weighted summation use no division by any b_i. Its closed simplex cover includes all zero-coordinate faces. Thus, for every j<=5, pad b and u with zeros to five entries. Since b_i>=0, each new cross entry is (b_i+0-sqrt(b_i^2))/2=0, and each new diagonal entry is zero. Therefore H(b,0)=H(b) direct-sum 0, while the norm and positive-vector objective are unchanged. Positive C5 directly implies every positive C_j for j<=5.

The sign-lifting argument requires only these positive-vector statements P_j, not previously proved full C_j statements. Its restricted-sign-group and restricted-subset applications are consequently all supplied by zero-padding the positive C5 theorem. The conversion to P_j for zero coordinates or probabilities is legitimate by continuity of both sides; no boundary assumption beyond the already certified closed domain is needed. Hence positive C5 plus the analytic sign-lifting argument establishes full C5 without separate C1--C3 proofs or the C4 certificate.

The analytic near-axis carve used inside the positive C5 certificate depends only on the explicit constant allocations and the bound of four tail entries, as proved above. It invokes no F4, F5, or earlier minorant theorem. The resulting full-C5 covariance proof of the F6 near-axis region is therefore independent of F4, F5, and the d5 far-region certificate. This addendum supersedes the earlier description of C1--C4 as necessary dependencies; they were sufficient but redundant.
