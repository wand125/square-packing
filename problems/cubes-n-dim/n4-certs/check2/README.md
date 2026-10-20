# Second checker for the n = 4 certificates (v2)

All 13 certificates in `../certs/` (k = 17 … 29) are in the `alg-v1` format of `../SPEC-ALG.md`. Each number is a
pair of rationals `["a", "b"]` meaning a + b√d. The certificates use d = 3 for k = 17 and d = 2 for the others.
`alg_check2.py` checks them. It was written from the specification alone: the first checker `../check_alg.py` was not
read. It uses only the Python standard library (`fractions.Fraction`), and no floating-point number enters any
decision. It prints ACCEPT or REJECT with the reason and exits 0 for ACCEPT, 1 for REJECT and 2 for unreadable input.

## What it checks

The certificate describes k cubes with centres c_i and frames R_i in the container [0, s]⁴. All arithmetic is exact
in Q(√d), and the sign of a + b√d is decided by comparing a² with d·b².

1. **Shape.** Every number is a pair of strings of the form `"p/q"` or `"p"`. JSON numbers, decimals and anything
   else are refused.
2. **Frames.** The columns of every R_i are orthonormal.
3. **Container.** For every cube and coordinate, c_i[r] − h_r ≥ 0 and s − c_i[r] − h_r ≥ 0, where
   h_r = ½ Σ_m |R_i[r][m]|.
4. **Separation.** For every pair i < j some candidate axis a satisfies
   2|a · (c_i − c_j)| ≥ Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|. The candidate axes are the generalised cross
   products of k′ columns of R_i and 3 − k′ columns of R_j, which gives 56 axes per pair.

## Results

All 13 certificates are accepted. In every certificate the smallest wall slack is 0.

| certificates | s (exact) | s (decimal) |
|---|---|---|
| n4k17 | 2 + √3/3 | ≈ 2.577350269190 |
| n4k18 … n4k25 | 2 + √2/2 | ≈ 2.707106781187 |
| n4k26 … n4k29 | 2 + 2√2/3 | ≈ 2.942809041582 |

Further checks:

- **Nesting.** n4k18 … n4k24 are subsets of n4k25: comparing their (centre, frame) pairs as sets shows
  18 ⊂ 19 ⊂ … ⊂ 25. Each of them keeps the 16 axis-parallel cubes of n4k25. Likewise, n4k27 is a subset of n4k28.
- **Comparison with the published values.** The comparison is exact: s = 2 + 2√2/3 < p is the same as
  √2 < (3/2)(p − 2), which is decided by squaring.

  | k | published value p | p − s |
  |---|---|---|
  | 27 | 2.942809214 | 1.72 · 10⁻⁷ |
  | 28 | 2.942826011 | 1.70 · 10⁻⁵ |
  | 29 | 2.942830937 | 2.19 · 10⁻⁵ |

- **Touching pairs.** In n4k26 … n4k29 many pairs touch with gap exactly 0. In floating point these show as
  "overlaps" of about 10⁻¹⁶. The exact check accepts them.

## Corruption tests

`alg_neg_tests.py` makes 15 broken copies of each certificate and requires every copy to be rejected. The copies are:

- one frame entry changed;
- s reduced by 10⁻⁶, once in the rational part and once in the √d part;
- one cube of the tightest pair moved by 1/64 towards the other;
- two centres made equal;
- d changed (2 ↔ 3);
- malformed numbers: a JSON float, a decimal string, a zero denominator, a bare `"sqrt2"`;
- k larger than the lists;
- a frame with a missing row;
- a wrong format tag;
- n = 1;
- truncated JSON.

NumPy is used only to choose the tightest pair. On the 13 certificates all 195 broken copies are rejected.

`alg_hand_tests.py` runs 7 small exact cases. Squares turned by 45° and by 30° fill [0, √2]² and [0, (1 + √3)/2]²
exactly, and two 45° squares touch corner to corner. Each case is accepted as built and rejected after a 10⁻⁶ change.

## Earlier version

In the first version of this bundle, n4k17 and n4k26 … n4k29 were rational certificates with A_i skew-symmetric. The
second checker for that format is `cert_check2.py`, with its tests `neg_tests.py` and `hand_tests.py`. They are kept
here for reference and are not needed for the certificates of this version.

## Run

```sh
# from the bundle root; Python 3
for f in certs/n4k*.json; do python3 -I check2/alg_check2.py "$f"; done     # each line: ACCEPT
python3 -I check2/alg_neg_tests.py certs/n4k*.json                          # ends with ALL OK
python3 -I check2/alg_hand_tests.py                                         # ends with ALL OK
```
