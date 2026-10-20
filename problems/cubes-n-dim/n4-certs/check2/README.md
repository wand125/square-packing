# Second checkers for the n = 4 certificates

The 13 certificates in `../certs/` come in two formats:

| certificates | format | second checker |
|---|---|---|
| n4k26, n4k27, n4k28, n4k29 | rational (`A_i` skew-symmetric, `c_i`, `s` as `"p/q"` strings) | `cert_check2.py` |
| n4k17 | `alg-v1` over Q(√3) (`../SPEC-ALG.md`): every number is `["a", "b"]` = a + b√d | `alg_check2.py` |
| n4k18 … n4k25 | `alg-v1` over Q(√2) | `alg_check2.py` |

Both checkers were written from the specifications alone. They do not read the first checkers `../check_cert.py` and
`../check_alg.py`. They use only the Python standard library (`fractions.Fraction`), and no floating-point number
enters any decision. Each prints ACCEPT or REJECT with the reason, and exits 0 for ACCEPT, 1 for REJECT, 2 for
unreadable input.

## What they check

For k cubes in [0, s]⁴, with centres c_i and frames R_i:

1. **Shape.** Every number must be a string `"p/q"` or `"p"`. In alg-v1 it is a pair of such strings. JSON numbers,
   decimals and other strings are refused.
2. **Frames.**
   - Rational format: A_i must be skew-symmetric. R_i = (I − A_i)⁻¹(I + A_i) is computed by exact Gauss–Jordan
     elimination, and RᵀR = I and det R = 1 are then verified.
   - alg-v1: the columns of R_i must be orthonormal, exactly in Q(√d).
3. **Container.** c_i[r] − h_r ≥ 0 and s − c_i[r] − h_r ≥ 0, with h_r = ½ Σ_m |R_i[r][m]|.
4. **Separation.** Every pair i < j must be separated by some candidate axis a:
   2|a · (c_i − c_j)| ≥ Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|. The candidates are the generalised cross products
   of k′ columns of R_i and 3 − k′ columns of R_j (56 axes per pair).

In Q(√d), the sign of a + b√d is decided exactly by comparing a² with d·b².

## Results

All 13 certificates are accepted, each in a few seconds. In every certificate the smallest wall slack is 0.

| certificate | s (exact) | s (decimal) |
|---|---|---|
| n4k17 | 2 + √3/3 | ≈ 2.577350269190 |
| n4k18 … n4k25 | 2 + √2/2 | ≈ 2.707106781187 |
| n4k26 | rational | ≈ 2.94280904194 |
| n4k27 | rational | ≈ 2.94280921431 |
| n4k28 | rational | ≈ 2.94282601089 |
| n4k29 | rational | ≈ 2.94283093693 |

The certificates n4k18 … n4k24 are subsets of n4k25. Comparing their (centre, frame) pairs as sets shows that they
are nested, 18 ⊂ 19 ⊂ … ⊂ 25, and that each keeps the 16 axis-parallel cubes of n4k25.

## Corruption tests

Each test script makes broken copies of a certificate and requires every copy to be rejected.

- **`neg_tests.py`** (rational certificates, 14 kinds):
  - a cube moved onto another;
  - all centres pulled towards the middle by a factor 1 − 10⁻⁶;
  - s reduced by 10⁻¹²;
  - a cube touching the wall pushed out by 10⁻¹²;
  - non-skew A_0, and a nonzero diagonal entry in A_0;
  - several malformed inputs.

  On the 4 rational certificates, all 56 broken copies are rejected. An informative case turns a cube by about
  0.02 rad; it is rejected too.
- **`alg_neg_tests.py`** (alg-v1 certificates, 15 kinds; needs NumPy, used only to choose which pair to corrupt):
  - one frame entry changed;
  - s reduced by 10⁻⁶ in the rational part and in the √d part;
  - one cube of the tightest pair moved by 1/64 towards the other;
  - two centres made equal;
  - d changed from 2 to 3;
  - a JSON float, a decimal string, a zero denominator and a bare `"sqrt2"`;
  - k too large, a frame with a missing row, a wrong format tag, n = 1 and truncated JSON.

  On the 9 alg-v1 certificates (one over Q(√3), eight over Q(√2)), all 135 broken copies are rejected; for n4k17 the
  d change is 3 → 2 and the √d change is in √3.
- **`hand_tests.py`** (10 cases) and **`alg_hand_tests.py`** (7 cases): small exact cases are accepted as built and
  rejected after a tiny change. They cover:
  - axis-parallel cubes in [0, 2]ⁿ;
  - squares turned by 45° and 30° that exactly fill [0, √2]² and [0, (1 + √3)/2]²;
  - two 45° squares touching corner to corner.

## Run

```sh
# from problems/cubes-n-dim/n4-certs; Python 3
for k in 26 27 28 29; do python3 -I check2/cert_check2.py certs/n4k$k.json; done          # each: ACCEPT
for k in 17 18 19 20 21 22 23 24 25; do python3 -I check2/alg_check2.py certs/n4k$k.json; done   # each: ACCEPT
python3 -I check2/neg_tests.py certs/n4k26.json certs/n4k27.json certs/n4k28.json certs/n4k29.json
python3 -I check2/alg_neg_tests.py certs/n4k17.json certs/n4k18.json certs/n4k19.json certs/n4k20.json certs/n4k21.json \
    certs/n4k22.json certs/n4k23.json certs/n4k24.json certs/n4k25.json
python3 -I check2/hand_tests.py
python3 -I check2/alg_hand_tests.py                                                        # each script: ALL OK
```
