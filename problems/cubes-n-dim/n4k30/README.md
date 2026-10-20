# 30 unit 4-cubes in a 4-cube of side 2.9876881 (previous best 2.9895684)

Let s_4(30) be the side of the smallest 4-cube that contains 30 unit 4-cubes with pairwise disjoint interiors
(any positions, any orientations). This bundle gives a packing that shows

    s_4(30) ≤ 2.9876880563   (exactly: the rational number s in certs/n4k30.json),

improving the previously best known value 2.989568410, published by hockyy/tesseract-packing
(https://github.com/hockyy/tesseract-packing, `results/n30_side_2.989568410.json`, branch main, commit
e75c790976a051b973341e21eedeaa8c2f66fae8, 2026-10-09) and by xavierdmello/tesseract-packing
(https://github.com/xavierdmello/tesseract-packing, `results/best/d4_n30.json`, branch research, commit
fb230875c852da2199e3036ad6b09633d6eacb7b, 2026-10-10; the same coordinates). The improvement is 0.0018804.

## How the packing was found

The published coordinates of the 2.989568410 packing of hockyy/tesseract-packing and xavierdmello/tesseract-packing
were used as the starting point of the container-shrinking continuation: the side s of the container is fixed and decreased in steps of 0.0005; at each step the centres and
rotations of the 30 cubes are moved to minimise a quadratic penalty on pairwise overlap (measured along the
C(8, 3) = 56 candidate separating axes, the generalised cross products of columns of two frames) and on wall
violation (6,000 Adam steps, learning rate 0.003, penalty weight 300). At the third step (s = 2.98807) the
rotations changed substantially (largest change of a frame 0.43 in Frobenius norm) and the penalty vanished; the
packing was then legalised and tightened by sequential quadratic programming with the separation directions as
variables, giving the floating-point side 2.98806229; three further rounds of tightening with a larger set of
constrained pairs (all pairs closer than 1.5) and up to 2,000 iterations lowered it to 2.98768826 (with a wall margin of 10⁻⁷ kept on purpose). The result is a different packing from the published
one, but it was reached from it; the credit for the starting packing belongs to its authors.

The same continuation from the published packings for k = 26, 27, 28, 29 (4-cubes) and k = 14, 28, 31, 32, 33
(3-cubes) produced no improvement.

## Files

| Path | What |
|---|---|
| `packing/n4k30.json` | the packing in floating point: `n`, `k`, `s`, centres `c` (30 × 4) and frames `R` (30 × 4 × 4, columns = cube axes); cube i is c_i + R_i [−½, ½]⁴, container [0, s]⁴ |
| `certs/n4k30.json` | the exact rational certificate (format below) |
| `check_cert.py` | first checker of the certificate (Python 3, standard library only) |
| `check2/` | second checker, written independently from the certificate specification alone, with its corruption tests |
| `verify_float.py` | an independent floating-point check of `packing/n4k30.json` (orthogonality, vertices inside, separation of every pair) |
| `SHA256SUMS` | checksums of everything above |

## Certificate

```
{"n": 4, "k": 30, "s": "<rational>", "A": [[["<rational>", ...], ...], ...], "c": [["<rational>", ...], ...],
 "bits": 40, "delta": "0", "s_float": 2.988, "note": "..."}
```

Rationals are strings `"p/q"` (or `"p"`) accepted by Python's `fractions.Fraction`. Cube i has centre `c[i]` and
frame R_i = (I − A_i)⁻¹(I + A_i), the Cayley transform of the skew-symmetric matrix `A[i]`; its point set is
c_i + R_i [−½, ½]⁴ (closed), and the container is [0, s]⁴ (closed). Cubes may touch. The fields `bits`, `delta`,
`s_float` and `note` are informational and are not used by the checkers. The certificate proves s_4(30) ≤ s with
s exactly the rational number in the file.

A checker accepts the certificate if and only if

1. every `A[i]` is a 4 × 4 skew-symmetric matrix of rationals (so R_i is orthogonal with det +1);
2. every cube lies in the container: c_i[r] ± ½ Σ_m |R_i[r][m]| ∈ [0, s] for every coordinate r;
3. every pair i < j is separated by one of the 56 candidate axes a, the generalised cross products of k′ columns
   of R_i and 3 − k′ columns of R_j (k′ = 0, …, 3; zero axes are skipped), in the sense
   2 |a · (c_i − c_j)| ≥ Σ_m |a · R_i[:, m]| + Σ_m |a · R_j[:, m]|.

Item 3 is a sufficient condition for disjoint interiors (separating-axis theorem for two convex polytopes: every
facet normal of the Minkowski difference of two cubes is in the candidate set). All arithmetic is exact.

The certificate was made from the floating-point packing by taking the Cayley parameter of each frame (after
replacing the frame by an equivalent one under the symmetries of the cube, so that the parameter stays small),
rounding it and the centres to a denominator 2⁴⁰, re-checking separation exactly, and recomputing the container
side exactly. No scaling was needed (`delta` = 0). The certified side 2.9876880563 is slightly below the floating-point
side because the floating-point packing keeps a wall margin of 10⁻⁷ that the exact recomputation of the container removes.

## Checking

```
python3 -I check_cert.py certs/n4k30.json          # prints ACCEPT ..., exit code 0   (about 1 s)
python3 -I check2/cert_check2.py certs/n4k30.json  # prints ACCEPT ..., exit code 0   (about 1.5 s)
python3 -I check2/neg_tests.py certs/n4k30.json    # corrupted copies are all rejected; ends with ALL OK
python3 -I verify_float.py packing/n4k30.json      # prints ok s=2.9876882563 ...
sha256sum -c SHA256SUMS
```

Packing: Hiroaki Hosono (wand125), starting from the published packing of hockyy/tesseract-packing and
xavierdmello/tesseract-packing (commits above). Rational certificate and first checker: Hiroaki Hosono (wand125), 2026.
Second checker: see `check2/README.md`.
