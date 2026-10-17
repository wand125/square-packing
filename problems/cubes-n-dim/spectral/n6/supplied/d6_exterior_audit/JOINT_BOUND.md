# Independent audit: joint nonnegative weighted-minor bound

The proposed extension is valid. Its restriction to nonnegative weights is essential to the proof below.

## Scalar support theorem

For n=5, let w_k≥0 and define H(s)=Σ_(k=1)^5 w_k e_k(s_1²,...,s_5²) on the simplex s_i≥0, Σs_i=1. Then H attains its maximum at a vector having m equal positive coordinates 1/m and the remaining coordinates zero, for some m∈{1,...,5}.

Proof: choose a global maximizer with minimal support. If two positive coordinates y,z are unequal, keep their sum t fixed and let u=yz vary over [0,t²/4]. Write E_j=e_j of the squares of the other coordinates, with E_0=1 and E_j=0 outside their available degrees. Then

    e_k(s²)=E_k+(t²−2u)E_(k−1)+u²E_(k−2).

Consequently H is a convex quadratic in u: its u² coefficient is nonnegative. The current unequal positive pair has u strictly inside the interval. Since the point globally maximizes H, this convex quadratic attains a maximum at an interior point and must be constant. In particular u=0 has the same objective value but smaller support, a contradiction. Thus all positive coordinates are equal. This proof covers vanishing coefficients and all boundary faces without a strict-convexity assumption.

Therefore, with V_(m,k)=binom(m,k)/m^(2k),

    Σ_k w_k e_k(s²) ≤ max_m Σ_k w_k V_(m,k).

The same argument works for any number of s coordinates, but only n=5 is used here.

## Matrix and counterexample reduction

For D=diag(x)C as in AUDIT.md, the k-column root-forest constants in six ambient coordinates are

    M_1=1/2, M_2=1/4, M_3=1/8, M_4=9/256, M_5=3/512.

Each follows by maximizing the product of component sizes of a forest with k edges on six vertices, then dividing by4^k. Hence

    e_k(B) ≤ M_k e_k(s_1²,...,s_5²),
    e_k(B)=(k+1)e_(k+1)(p).

Let T=2(Σsqrt(p_i)−1)>0. If L=Σs_i≤T, put z_i=s_i/L when L>0. Since L/T≤1, the normalized lower invariants

    b_k=(k+1)e_(k+1)(p)/(M_k T^(2k))

satisfy b_k≤e_k(z²). The scalar support theorem then implies b belongs to the downward-closed convex hull

    Dpoly=conv{V_1,...,V_5}−R_+^5.

This follows equivalently from separation by nonnegative normals. Every supporting normal for this downward-closed polyhedron must be nonnegative. The scalar theorem supplies all those support inequalities. Conversely they characterize the polyhedron, which is closed as the sum of a compact polytope and a closed polyhedral cone.

Thus any valid nonnegative weight vector a with a·V_m≤1 for every m, together with a·b>1, proves L>T and therefore F<1. Equality a·b=1 does not prove a strict margin. At T=0 the target x is a coordinate vector and F=1 directly; do not divide by T there. No row-feasibility assumption is used.

## Exact finite facets

Consider the compact coefficient polytope

    P={a∈R⁵: a≥0, a·V_m≤1 for m=1,...,5}.

It is bounded because V_5 has all coordinates positive, and has full dimension. Every vertex has five linearly independent active constraints among its ten defining halfspaces. `facets.py` enumerates all252 choices, solves their systems with exact Fraction arithmetic, checks every inequality exactly, and deduplicates the solutions. It finds32 vertices including zero. The other31 vertices give the complete finite family

    a·b≤1.

All31 normals have integer coordinates in this normalization. They are recorded in `facets.json`; no numerical LP tolerance or approximate dual conversion is needed. For example the normal active on all five support sizes is

    a=(1,8,270,19584,2427000).

The polytope maximum of any linear functional occurs at a vertex, so testing all31 nonzero vertices exactly reproduces the weighted-minor separation test. This algebraic result does not establish that those tests cover every p in the dimension-six cap; that remains the separate domain-certificate task.
