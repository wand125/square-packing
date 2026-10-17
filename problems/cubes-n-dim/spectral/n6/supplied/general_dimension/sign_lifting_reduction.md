# Reducing each higher-rank minorant to its nonnegative-vector case

## Status

This general sign-lifting argument is proved and independently audited in rank_five_minorant_audit.md. The positive C5 certificate includes every lower-rank positive inequality by zero padding. It therefore supplies all hypotheses needed below without any lower-dimensional packing theorem.

## Notation and equivalent positive-vector formulation

Let H(b) have diagonal b_i and off-diagonal (b_i+b_j-sqrt(b_i²+b_j²))/2. Let C_k be

f_b(v)=(|b·v|+Σb_i|v_i|)/2>=v^T H(b)v, ||v||2<=1.

For nonnegative vectors, C_k is equivalent to the following statement: for every probability vector lambda and u>=0,

L(lambda,u):=Σ_(i<j) sqrt(lambda_i²u_j²+lambda_j²u_i²)
 >=Σ_i u_i-||u||2.                                      (P_k)

The equivalence follows from the exact expansion of v^THv and the substitution lambda_i=b_i v_i/(b·v). The reverse substitution b_i=lambda_i/u_i handles strictly positive u, with zero coordinates obtained by continuity.

## 1. A strengthened consequence of the positive-vector inequalities

Assume P_j for every j<=k. For probability lambda in R^k and u>=0, set s=||u||2 and S={i:u_i>s lambda_i}. Then

L(lambda,u)>=Σ_i (u_i-s lambda_i)_+.                     (B)

To see this, let W=Σ_(i in S)lambda_i and U=Σ_(i in S)u_i. Internal edges contribute at least W(U-||u_S||2), by P_|S| after normalizing the restricted lambda. Edges joining S to its complement contribute at least (1-W)U, since each such norm is at least lambda_j u_i for i in S,j outside. All remaining edges are nonnegative. Thus

L>=U-W||u_S||2>=U-Ws,

which is (B). Empty sets and W=0 are immediate or follow by continuity.

## 2. A generalized acute triangle-defect bound

For u>=0, probability lambda, and w>=0,

Σ_i sqrt(u_i²+lambda_i²w²)-sqrt(||u||2²+w²)
 <=Σ_i(u_i-||u||2 lambda_i)_+
 <=L(lambda,u),                                         (D)

provided P_j holds for j<=k, where k is the number of components.

For the first inequality put s=||u||2. Choose c_i,d_i>=0 with c_i²+d_i²=1 and sqrt(u_i²+lambda_i²w²)=u_i c_i+lambda_i w d_i. The convex combination (Σlambda_i c_i,Σlambda_i d_i) has Euclidean norm at most one. Therefore

sqrt(s²+w²)>=sΣlambda_i c_i+wΣlambda_i d_i.

Subtracting gives a bound by Σ(u_i-s lambda_i)c_i, which is at most the positive-part sum. The second inequality is (B).

## 3. Balanced mixed-sign vectors

Assume P_j for all j up to the size of each sign group. Let a unit vector have positive coordinates u_i and negative coordinates -v_j, with nonnegative weight groups b_i,c_j satisfying weighted balance

Σ_i b_i u_i=Σ_j c_j v_j=A.

If A=0 use continuity. Define probability vectors lambda_i=b_i u_i/A and mu_j=c_j v_j/A. Direct expansion gives

v_full^T H(b,c)v_full/A
 =Σ_(i,j) sqrt(lambda_i²v_j²+mu_j²u_i²)
  -L(lambda,u)-L(mu,v).

For each i, apply (D) to negative-group coordinates v, weights mu, and scalar w=u_i/lambda_i, then multiply by lambda_i. This gives

Σ_j sqrt(lambda_i²v_j²+mu_j²u_i²)
 <=sqrt(u_i²+lambda_i²||v||2²)+lambda_i L(mu,v).

Zero lambda_i follow by continuity. Sum over i, and apply (D) again to u,lambda with scalar w=||v||2. Since ||u||2²+||v||2²=1,

Σ_(i,j) sqrt(lambda_i²v_j²+mu_j²u_i²)
 <=1+L(lambda,u)+L(mu,v).

Thus the quadratic is at most A=f_b(v_full), proving every balanced mixed-sign case.

## 4. Reduction from arbitrary mixed signs to balance

Fix positive weights b on positive coordinates u and a reference negative weight vector c on negative coordinates v. Scale all negative weights together by t>=0. Set A=b·u and B=c·v. The norm functional is max(A,tB).

Let q(t) be the corresponding quadratic. Its same-sign terms are q_P+t q_N. Each cross term is

-[b_i+t c_j-sqrt(b_i²+t²c_j²)]u_i v_j,

a convex function of t. Hence q(t) is convex. On 0<=t<=A/B, q(t)-A has maximum at an endpoint. At t=0 the positive subgroup inequality gives q(0)<=A. The other endpoint is balanced and was proved above.

For t>=A/B, differentiation shows

(d/dt)[q(t)-tB]
 =q_N-B-Σ_(i,j)c_j[1-tc_j/sqrt(b_i²+t²c_j²)]u_i v_j<=0,

because the positive-vector inequality on the negative subgroup implies q_N<=||v||2 B<=B. Thus no larger value occurs beyond balance. Degenerate A,B=0 follow by continuity.

## Consequence

If the positive-vector C_j inequalities hold for every j<=m, then full C_m holds for every sign pattern. For the mixed-sign cases of C_m one only needs the positive-vector inequalities in dimensions strictly smaller than m.

For m=5, the positive C5 certificate supplies every positive C_j by zero padding. Thus this consequence proves full C5 directly.
