# Second checker for the n = 4, k = 30 certificate

`cert_check2.py` is an independent exact checker for `../certs/n4k30.json`. It was written from the certificate
specification alone (the conditions in `../README.md`); the first checker `../check_cert.py` was not read. It uses
only the Python standard library (`fractions.Fraction`); no floating-point number enters any decision.

## What it checks

For a certificate with dimension n, k cubes, side s, skew-symmetric matrices A_i and centres c_i:

1. **Shape.** n ≥ 2 is an integer; `A` and `c` have k entries; each A_i is n × n and each c_i has n entries. Every
   number is a string `"p/q"` or `"p"` with q > 0 (JSON numbers, decimals and other strings are refused).
2. **Frames.** A_i is skew-symmetric. R_i = (I − A_i)⁻¹(I + A_i) is computed exactly by Gauss–Jordan elimination
   over the rationals; R_iᵀR_i = I and det R_i = 1 are verified exactly.
3. **Container.** For every cube and every coordinate r, with h_r = ½ Σ_m |R_i[r][m]|: c_i[r] − h_r ≥ 0 and
   c_i[r] + h_r ≤ s. The smallest wall slack is reported.
4. **Separation.** For every pair i < j, some candidate axis a separates the two closed cubes:
   2 |a · (c_i − c_j)| ≥ Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|. The candidates are the generalised cross products
   of k′ columns of R_i and n − 1 − k′ columns of R_j, k′ = 0, …, n − 1; zero vectors are skipped.

The certificate is accepted only if all four hold. The exit code is 0 for ACCEPT, 1 for REJECT and 2 for unreadable
input. Item 4 is a sufficient condition: a correct packing that no candidate axis separates would be rejected.

## Result

`../certs/n4k30.json` is accepted in about one second: n = 4, k = 30, certified s ≈ 2.9876880563 (the exact
rational is printed), smallest wall slack 0. The certified s is below the previously published value 2.989568410
by about 0.00188 (compared exactly as rationals).

## Corruption tests

`neg_tests.py` makes broken copies of the certificate and requires each to be rejected (14 kinds): a cube moved
onto another; all centres pulled towards the middle by a factor 1 − 10⁻⁶; s reduced by 10⁻¹²; a cube touching the
wall at 0 pushed out by 10⁻¹²; A_0 made non-skew; a nonzero diagonal entry in A_0; k larger than the lists; A_0
with n − 1 rows; an entry `"x"`; a decimal string `"0.5"`; a denominator 0; an entry given as a JSON number; n = 1;
truncated JSON (exit 2). All are rejected. An informative case turns cube 0 by about 0.02 rad keeping A_0
skew-symmetric; it is rejected because the turned cube no longer fits.

`hand_tests.py` checks 10 hand-made cases (axis-parallel cubes in [0, 2]ⁿ for n = 2, 3, 4, a cube turned by
2 atan(1/3), two turned cubes with faces touching), each accepted as built and rejected after a tiny push.

## Run

```sh
# from problems/cubes-n-dim/n4k30; Python 3, standard library only
python3 -I check2/cert_check2.py certs/n4k30.json   # must print ACCEPT and exit 0
python3 -I check2/neg_tests.py certs/n4k30.json     # must end with ALL OK
python3 -I check2/hand_tests.py                     # must end with ALL OK
```
