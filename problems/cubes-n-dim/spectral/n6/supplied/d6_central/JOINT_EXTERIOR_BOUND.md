# Joint exterior constraints and a concave dimension-six lower bound

## Result for direct simplex certification

In the notation of EXTERIOR_FAMILY.md, define

    H4(p)=((1280/9)e_5(p))^(1/8),
    H5(p)=(1024e_6(p))^(1/10).

Then the following fixed rational combination is a rigorous lower bound:

    L >= (3297/1000) H4(p) + (121/125) H5(p).          (J)

The right side is concave in p. It is strictly stronger than the separate exterior bounds in an important transition region. For example, at the normalized probability vector proportional to (.795,.05120,.05095,.04980,.04926,.00379), its gap above 2(sum sqrt(p)-1) is approximately +.00766, whereas the separate fourth-exterior and determinant gaps are negative. This example is illustrative; the analytic inequality (J) is exact.

## Joint scalar optimization lemma

For any nonnegative coefficients a_k, the maximum of

    sum_k a_k e_k(s_1^2,...,s_N^2),  s_i>=0, sum s_i=1,

is attained at a vector having m equal positive coordinates and N-m zeros, for some integer1<=m<=N. Its value is therefore

    max_(1<=m<=N) sum_k a_k binom(m,k)/m^(2k),

with binom(m,k)=0 when k>m.

Proof: choose a maximizer of minimum support. If it has unequal positive coordinates a,b, hold a+b and the other coordinates fixed. Each summand is a convex quadratic in t=ab:

    e_k(s^2)=alpha_k t^2-2 beta_k t+constant,

where alpha_k,beta_k>=0, with the natural zero conventions for k=1. Their nonnegative weighted sum is convex in t on [0,(a+b)^2/4]. The current t is strictly interior. If either endpoint increases the value, maximality is contradicted. Otherwise both endpoints have the same maximal value (an interior maximum of a convex function forces constancy on the interval). In particular t=0 is also a maximizer and has smaller support, again a contradiction. Therefore the minimum-support maximizer has all its positive coordinates equal.

## A joint inequality for five column costs

Set

    M=1/4^8,
    c=(M-1/5^7)*5^10=1573625/65536.

The joint lemma gives, for nonnegative s_1,...,s_5 with sum L>0,

    e_4(s^2)/L^8 + c e_5(s^2)/L^10 <= M.            (1)

Indeed supports1,2,3 give zero, support4 gives M, and support5 gives1/5^7+c/5^10=M.

The exterior lower constraints proved earlier are

    e_4(s^2) >= (1280/9)e_5(p)=H4(p)^8,
    e_5(s^2) >=1024e_6(p)=H5(p)^10.

Thus, writing u=H4(p)/L and v=H5(p)/L,

    F(u,v)=u^8+c v^10 <= M.                         (2)

## A supporting linear inequality with exact coefficients

The function F is convex on the nonnegative quadrant. Put

    u0=5^(-7/8), v0=1/5,
    D=8u0^8+10c v0^10=8/5^7+10c/5^10,
    w4=8u0^7/D, w5=10c v0^9/D.

We have F(u0,v0)=M. The supporting-plane inequality for convex F gives

    F(u,v) >= M + 8u0^7(u-u0)+10c v0^9(v-v0).

Together with (2), this implies

    w4 u+w5 v <=1,
    L >=w4 H4(p)+w5 H5(p).

The coefficients satisfy w4>3297/1000 and w5>121/125. No transcendental estimate is needed to check this: the first comparison is equivalent to

    ((3297/1000)D/8)^8 < 5^(-49),

and the second is the rational inequality

    (121/125)D <10c/5^9.

Both are verified exactly by replay_joint.py. Replacing w4,w5 by these smaller positive rational coefficients proves (J).

Finally H4 and H5 are concave by elementary-symmetric-root concavity, as explained in EXTERIOR_FAMILY.md. Their nonnegative weighted sum is concave. Hence (J) can be inserted directly into the existing vertex-Jensen/square-root-chord simplex certificate, avoiding any concavity claim for a maximum or an implicit gauge.

## General rational tangent witnesses, without boundary root solving

This construction makes every joint scalar inequality compatible with exact concave simplex certificates. Suppose nonnegative rational coefficients a_k satisfy

    sum_k a_k binom(m,k)/m^(2k) <=1 for every m=1,...,N.

The joint scalar lemma then gives F(u)=sum_k a_k u_k^(2k)<=1 whenever u_k=H_k(p)/L, where

    H_k(p)=[4^k(k+1)e_(k+1)(p)/P_(n,k)]^(1/(2k)).

Choose arbitrary nonnegative rational numbers t_k. They need not lie on the boundary F(t)=1. Define

    D=1+sum_k (2k-1)a_k t_k^(2k),
    b_k=2k a_k t_k^(2k-1)/D.

Then

    L >=sum_k b_k H_k(p).                              (R)

Indeed convexity gives F(u)>=F(t)+grad F(t) dot (u-t). Combining this with F(u)<=1 yields

    sum_k 2k a_k t_k^(2k-1)u_k
       <=1-F(t)+sum_k2k a_k t_k^(2k)
       =D.

All coefficients b_k are nonnegative rational numbers, and every H_k is concave. Thus (R) is a fixed rational-weight concave lower bound. A certifier can choose a facet and t at each simplex or cell anchor, then verify the finitely many support inequalities and the rational coefficient construction exactly. Choosing t near H(p)/L at a promising anchor makes the witness sharp, but its validity never depends on how it was chosen.
