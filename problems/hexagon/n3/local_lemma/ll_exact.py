"""Exact verification (sympy, polynomial in c = cos, s = sin) of the contact-function decomposition used in
the local lemma for the n = 3 pinwheel in the regular hexagon of side v = (1 + sqrt3)/2.

Frame of square i (rotate everything by -2*pi*i/3): square i has its lower-left corner at V + p_i and angle
phi_i; square j = i+1 is R(V + p_j + R(psi)(1/2,1/2)) with angle 2pi/3 + psi, R = rotation by 2pi/3.
k_i = u . (TR_i - C_j) - 1/2 is the signed distance of the top-right corner TR_i of square i beyond the line
of the top edge of square j (outward normal u = R(2pi/3 + psi) e_y).
Claim:  k_i = F(phi_i, psi) + (R(psi) n) . p_i - (R(psi) e_y) . p_j  with
        F(phi, psi) = (1+v)(cos psi - 1) - v (cos(phi - psi) - 1) + (v - 1) sin(phi - psi).
"""
import sympy as sp
r3 = sp.sqrt(3)
v = (1 + r3) / 2
h = v * r3 / 2
c1, s1, c2, s2 = sp.symbols('c1 s1 c2 s2', real=True)     # cos/sin of phi and of psi
p1x, p1y, p2x, p2y = sp.symbols('p1x p1y p2x p2y', real=True)
def Rcs(c, s): return sp.Matrix([[c, -s], [s, c]])
half, cr = sp.Rational(1, 2), r3 / 2
R = Rcs(-half, cr)                                            # rotation by 2pi/3
V = sp.Matrix([-v / 2, -h])
n = sp.Matrix([-cr, -half]); ey = sp.Matrix([0, 1])
TR = V + sp.Matrix([p1x, p1y]) + Rcs(c1, s1) * sp.Matrix([1, 1])
Cj = R * (V + sp.Matrix([p2x, p2y]) + Rcs(c2, s2) * sp.Matrix([half, half]))
u = R * Rcs(c2, s2) * ey
k = sp.expand((u.T * (TR - Cj))[0] - half)
# cos(phi - psi) = c1 c2 + s1 s2,  sin(phi - psi) = s1 c2 - c1 s2
cosd = c1 * c2 + s1 * s2; sind = s1 * c2 - c1 * s2
F = (1 + v) * (c2 - 1) - v * (cosd - 1) + (v - 1) * sind
claim = F + ((Rcs(c2, s2) * n).T * sp.Matrix([p1x, p1y]))[0] - ((Rcs(c2, s2) * ey).T * sp.Matrix([p2x, p2y]))[0]
diff = sp.expand(k - claim)
# reduce with c^2 + s^2 = 1 for both angles
diff = sp.expand(diff.subs({s1**2: 1 - c1**2, s2**2: 1 - c2**2}))
print("k - claim =", sp.simplify(diff))
assert sp.simplify(diff) == 0
print("decomposition verified exactly")
# constants used in the proof
kappa_vec = ey - n
print("e_y - n =", list(kappa_vec), "; on the extreme rays (1,0) and (-1/2, sqrt3/2) of W:",
      sp.simplify(kappa_vec.dot(sp.Matrix([1, 0]))), sp.simplify(kappa_vec.dot(sp.Matrix([-half, cr]))))
