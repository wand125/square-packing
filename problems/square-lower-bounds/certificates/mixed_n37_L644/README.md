# s(37) >= 161/25 = 6.44

A density certificate proving that 37 unit squares do not fit in a square of side
`L = 161/25 = 6.44`. This exceeds Green's bound for `n = 37 = 6² + 1`,
`2√2 + (113 + 10√3)/37 = 6.3506030…`, by more than `0.0893`. The comparison is exact, with
90-digit integer square-root bounds (see `completion-audit.json`).

The measure is 350 rectangles with uniform density and no point masses. The total mass is
`3699999/100000 = 36.99999 < 37`. The setting is that of the rectangle certificates in this
repository: core side `B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`, with the lowest at `1.0000000054…`. That is
below the `1.0001` that tokoharu's `verify.cpp` requires, so the certificate is not in his format.
It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`, the same checker as
for [`mixed_n50_L740`](../mixed_n50_L740/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was generated directly at L = 6.44 by the search used for the n = 50 and n = 65
certificates, then repaired against counterexamples on the full net until none were left.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 37 squares would need total mass `>= 37`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 350 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the source hashes and the exact Green comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n37-L6.44-proof-bundle.tar.gz`: the complete bundle, 621 files including every angle's
  input and result (SHA-256
  `61a29142ec81cfa0fadffba3e04bd6e512ee0439897fb6dfd7610ecc737542f8`).

## Reproduce

```sh
tar xzf n37-L6.44-proof-bundle.tar.gz
cd n37-L6.44-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
