"""Radius conditions of the local lemma (exact rational arithmetic with explicit rational bounds for
sqrt3, sin and the like), and a float search for a counterexample inside the lemma's region."""
from fractions import Fraction as Fr
import math, numpy as np
from scipy.optimize import minimize

# ---------- exact check of the two radius conditions -------------------------------------------
# v = (1+sqrt3)/2 with rational bounds: 1.732050807 < sqrt3 < 1.732050808
s3lo, s3hi = Fr(1732050807, 10**9), Fr(1732050808, 10**9)
vlo, vhi = (1 + s3lo) / 2, (1 + s3hi) / 2
kap_lo = s3lo / 2                                   # kappa = sqrt3/2
rho, rhop = Fr(8, 100), Fr(5, 100)                  # angle radius, translation radius
D = 2 * rho                                         # max |delta|
# (A) angle condition:  (v-1)/2 * (1 - D^2/24)  >  v*D/2 + rho*(v*D^2 + (v-1)*D^3/2) / (D*(kappa - 2 rho))
#     (from  k_j <= -(v-1) sin(D/2) + v D^2/2 + rho * Sigma F/(kappa - 2 rho),  Sigma F <= v D^2 + (v-1) D^3/2,
#      sin(x) >= x (1 - x^2/6) and division by D; the right side increases with D so D = 2 rho is the worst case)
lhs = (vlo - 1) / 2 * (1 - D * D / 24)
rhs = vhi * D / 2 + rho * (vhi * D * D + (vhi - 1) * D ** 3 / 2) / (D * (kap_lo - 2 * rho))
print(f"(A) angle condition: {float(lhs):.6f} > {float(rhs):.6f} : {lhs > rhs}")
assert 2 * rho < kap_lo and lhs > rhs
# (B) validity of the contact inequality: the top-right corner of square i stays strictly inside the other
#     three edge lines of square i+1.  Margins at the pinwheel: 2 - sqrt3 (= 0.2679...)?  computed below.
#     Change of a margin <= |p_i| + |p_j| + sqrt2 |phi_i| + (|Y0| + 2 rho_p + sqrt2 rho) |psi|, |Y0| <= 1.065
s2hi = Fr(14143, 10000)
Y0hi = Fr(1065, 1000)
change = 2 * rhop + s2hi * rho + (Y0hi + 2 * rhop + s2hi * rho) * rho
m0_lo = Fr(366025, 10**6)                           # smallest margin at the pinwheel: (sqrt3 - 1)/2 > 0.366025
print(f"(B) contact validity: margin change {float(change):.6f} < {float(m0_lo):.6f} : {change < m0_lo}")
assert change < m0_lo

# ---------- float search: can all three contacts be positive inside the region? ----------------
R3 = math.sqrt(3); v = (1 + R3) / 2
n = np.array([-R3 / 2, -0.5]); ey = np.array([0.0, 1.0])
def Rot(a): return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
def F(a, b): return (1 + v) * (math.cos(b) - 1) - v * (math.cos(a - b) - 1) + (v - 1) * math.sin(a - b)
r1, r2 = np.array([1.0, 0.0]), np.array([-0.5, R3 / 2])            # extreme rays of the wedge W
def mink(z):
    phi = z[6:9]; P = []
    for i in range(3):
        a, b = abs(z[2 * i]), abs(z[2 * i + 1])
        p = a * r1 + b * r2
        if np.linalg.norm(p) > float(rhop):
            p = p / np.linalg.norm(p) * float(rhop)
        P.append(p)
    phi = np.clip(phi, -float(rho), float(rho))
    ks = []
    for i in range(3):
        j = (i + 1) % 3
        ks.append(F(phi[i], phi[j]) + (Rot(phi[j]) @ n) @ P[i] - (Rot(phi[j]) @ ey) @ P[j])
    return min(ks)
rng = np.random.default_rng(0); best = -9; bz = None
for _ in range(3000):
    z = np.concatenate([rng.uniform(0, 0.04, 6), rng.uniform(-0.08, 0.08, 3)])
    r = minimize(lambda z: -mink(z), z, method="Nelder-Mead", options={"maxiter": 2000, "xatol": 1e-10, "fatol": 1e-14})
    if -r.fun > best: best, bz = -r.fun, r.x
print(f"float search: max over the region of min_i k_i = {best:.3e} (lemma says <= 0, = 0 only at the pinwheel)")
print("  at", np.round(bz, 6))
