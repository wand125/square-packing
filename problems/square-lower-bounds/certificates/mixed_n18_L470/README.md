# s(18) >= 47/10 = 4.7

A density certificate proving that 18 unit squares do not fit in a square of side `L = 47/10 = 4.7`. This exceeds our rectangle certificate `rect_n18_L4695` (4.695).

The measure is 136 rectangles with uniform density and no point masses. The total mass is
`1799999/100000 = 17.99999 < 18`. The setting is a finer angle net than the rectangle certificates in this repository: core side `B = 999/1000`, and 416 half-angle net nodes with step `1/1001`.

The coverage lower bound at each net angle is `>= 1`: at the 415 oblique angles the lowest is `1.0000000002`, and at
angle 0 the integer table's minimum is `1.017450`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was built from scratch at L = 4.7 from a structured initial measure (bands at integer distances from the walls), searched under the n = 18 budget, and repaired against counterexamples on the full net.
The pre-publication replay was run on a fresh Ubuntu 24.04.5 machine (x86_64) with only the README's requirements installed: g++ 13.3.0, Python 3.12.3 and NumPy 2.5.3. The tarball's SHA-256 and all its file hashes were checked first.
## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 1/1001) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 18 squares would need total mass `>= 18`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 136 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 415 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n18-L4.7-proof-bundle.tar.gz`: the complete bundle, 1267 files including every angle's
  input and result (SHA-256 `6c30eb7337e622371c865f5be9c52609ec319c39728784b5f6d9e1e342111873`).

## Reproduce

```sh
tar xzf n18-L4.7-proof-bundle.tar.gz
cd n18-L4.7-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 1266 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
