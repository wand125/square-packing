import sympy as sp
u = sp.sqrt(3); v = 2 + 4*u/3
a0,b0,a1,b1,p0,p1,p3,al,be0,be1,tau = sp.symbols('a0 b0 a1 b1 phi0 phi1 phi3 alpha beta0 beta1 tau', real=True)
A0 = (1/u + a0, b0); A1 = (1 + 1/u + a1, b1)
E = lambda p: (sp.cos(p), sp.sin(p)); Fv = lambda p: (-sp.sin(p), sp.cos(p))
add = lambda *P: tuple(sum(c) for c in zip(*P)); dot = lambda X,Y: X[0]*Y[0]+X[1]*Y[1]
T0 = add(A0, Fv(p0)); R0 = add(A0, E(p0), Fv(p0)); B0 = add(A0, E(p0)); P = add(A1, E(p1), Fv(p1)); T1 = add(A1, Fv(p1))
gL = (u*T0[0]-T0[1])/2
gR = (u*(v-P[0])-P[1])/2 - sp.cos(p3) - tau*sp.sin(p3)      # orthant phi3>=0 form; |sin| via sign of phi3
gb = b0 + be0*sp.sin(p0) + b1 + be1*sp.sin(p1)
seps = {"S1": dot(E(p1), A1) - (al*dot(E(p1), R0) + (1-al)*dot(E(p1), B0)),
        "S0": al*dot(E(p0), T1) + (1-al)*dot(E(p0), A1) - dot(E(p0), A0) - 1}
for k, g in seps.items():
    S = sp.expand(gL + gR + u/2*g + gb/2)
    F = sp.simplify(S.subs({a0:0,b0:0,a1:0,b1:0}))
    print(k, "F =", F)
    print("  grad at 0:", [sp.simplify(sp.diff(F, x).subs({p0:0,p1:0,p3:0})) for x in (p0,p1,p3)])
    for var in (a0,b0,a1,b1):
        print("  d/d", var, sp.simplify(sp.diff(S,var)))
