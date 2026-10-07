# s(82) >= 233/25 = 9.32

A certificate proving that 82 unit squares do not fit in a square of side `L = 233/25 = 9.32`.
This exceeds Green's reported bound for `n = 82` (Friedman DS7, Theorem 9 with `k = 9`),
`2√2 + (247 + 12√2)/41 = 9.2667…`, by more than `0.0532` (exact comparison with 90-digit bounds, see
`completion-audit.json`). Green's bound is a reported value: the published argument behind it does not establish
Theorem 9 for k >= 4. Before this certificate, n = 82 was the only case in 82–85 where no verified bound reached it.

The measure is linear: 86 point masses, 222 segments of uniform linear density and 774 rectangles, with exact
rational geometry and masses, D4-symmetric. The total mass is `8199999/100000 = 81.99999 < 82`. The setting is that of
the other certificates here: core side `B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

At every net angle, every closed core of side `B` at that angle has measure `>= 1`. This was checked with the verifier in
`code/` (`unified_linear_verify.cpp` and its Python driver), which proves the bound over every centre domain with
outward-rounded interval arithmetic. It is the verifier of [`mixed_n83_L935`](../mixed_n83_L935/README.md) and
[`mixed_n101_L1028`](../mixed_n101_L1028/README.md).

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit square, at any orientation,
contains a closed core of side `B` at a net angle, strictly in its interior. Each such core has measure `>= 1`. Cores
chosen inside the squares of a packing are disjoint, so 82 squares would need total mass `>= 82`.

## Files

- `candidate.json`: the rational measure (points, segments and rectangles with their weights).
- `certificate.json`: the per-angle records, including every input's SHA-256.
- `manifest.json`: the angle net.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay states, the source hashes
  and the comparison.
- `code/`: the verifier (Python 3 and a C++17 compiler) and `replay_linear_bundle.py`.
- `n82-L9.32-proof-bundle.tar.gz`: the complete bundle with every angle's input and result
  (SHA-256 `296d8f09f6d9a49ecb7ee3438b31585788403044b4a60644a4ef93262476506f`).

## Reproduce

```sh
tar xzf n82-L9.32-proof-bundle.tar.gz
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/replay_linear_bundle.py n82-L9.32-proof-bundle --workers 3
```

You need Python 3 with numpy, scipy, numba and highspy, and a C++17 compiler. The replay regenerates all 201 inputs
from the candidate, re-runs the verifier on each, and requires every record to equal the stored one. It ends with
`ALL_LINEAR_ANGLES_REPLAYED_MATCHING_CERTIFICATE`.

Before publication the full replay was run from this tarball on a fresh Ubuntu 24.04.5 machine (x86_64) with only
these requirements installed (g++ 13.3.0, Python 3.12.3, NumPy 2.5.3, SciPy 1.18.1, Numba 0.68.0), with `--workers 32`, and
ended with that status. The replay re-executes the same outward-rounded implementation; it is not an independent second
algorithm or a proof-assistant formalization.
