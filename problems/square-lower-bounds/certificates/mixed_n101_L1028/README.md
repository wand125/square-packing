# s(101) >= 257/25 = 10.28

A certificate proving that 101 unit squares do not fit in a square of side `L = 257/25 = 10.28`.
This exceeds Green's reported bound for `k = 10` (Friedman DS7, Theorem 9),
`G_10 = 2√2 − 1 + (810 + 18√5)/101 = 10.2467…`, by more than `0.0332637`
(compared exactly with integer square-root bounds; see `completion-audit.json`).

The measure is linear: 333 point masses, 897 segments of uniform linear density and 4 rectangles, with exact rational
geometry and masses, D4-symmetric. The total mass is `10099999/100000 = 100.99999 < 101`. The setting is that of the
other certificates here: core side `B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

At every net angle, every closed core of side `B` at that angle has measure `>= 1`. This was checked with the verifier in
`code/` (`unified_linear_verify.cpp` and its Python driver), which proves the bound over every centre domain with
outward-rounded interval arithmetic. It is the verifier of [`mixed_n50_L735`](../mixed_n50_L735/README.md).

The initial measure came from a floating-point LP over points and segments on a lattice at multiples of `B` from the
walls, and was then repaired against exact counterexamples on the full net and proved at all 201 angles.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit square, at any orientation,
contains a closed core of side `B` at a net angle, strictly in its interior. Each such core has measure `>= 1`. Cores
chosen inside the squares of a packing are disjoint, so 101 squares would need total mass `>= 101`.

## Files

- `candidate.json`: the rational measure (points, segments and rectangles with their weights).
- `certificate.json`: the per-angle records, including every input's SHA-256.
- `manifest.json`: the angle net.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay states, the source hashes
  and the exact comparison with `G_10`.
- `code/`: the verifier (Python 3 and a C++17 compiler) and `replay_linear_bundle.py`.
- `n101-L10.28-proof-bundle.tar.gz`: the complete bundle, 810 entries including every angle's input and result
  (SHA-256 `c32bba42686b9b27268a770c6505d9e8e0804bf0bb169848cecfb622775efdd5`).

## Reproduce

```sh
tar xzf n101-L10.28-proof-bundle.tar.gz
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/replay_linear_bundle.py n101-L10.28-proof-bundle --workers 3
```

You need Python 3 with numpy, scipy, numba and highspy, and a C++17 compiler. The replay regenerates all 201 inputs
from the candidate, re-runs the verifier on each, and requires every record to equal the stored one. It ends with
`ALL_LINEAR_ANGLES_REPLAYED_MATCHING_CERTIFICATE`.

Before publication the full replay was run from this tarball on a separate machine and ended with that status. The
replay re-executes the same outward-rounded implementation; it is not an independent second algorithm or a
proof-assistant formalization.
