# s(87) >= 191/20 = 9.55

A density certificate proving that 87 unit squares do not fit in a square of side `L = 191/20 = 9.55`. This exceeds our earlier certificate `mixed_n87_L948` (9.48), the bound 9.5 that `mixed_n86_L950` gives for n = 87 by monotonicity, and Nagamochi's closed form `1 + √70 = 9.3666…` (a reference value, see jlevy/squares#295).

This supersedes [`mixed_n87_L948`](../mixed_n87_L948/README.md) for `n = 87`.

The measure is 509 rectangles with uniform density and no point masses. The total mass is
`8699999/100000 = 86.99999 < 87`. The setting is that of the rectangle certificates in this repository: core side
`B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`: at the 200 oblique angles the lowest is `1.0000000016`, and at
angle 0 the integer table's minimum is `1.001107`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was built from scratch at L = 9.55 from a structured initial measure (bands at integer distances from the walls, as in the Green-series certificates), searched under the n = 87 budget, and repaired against counterexamples on the full net.
The pre-publication replay was run on a fresh Ubuntu 24.04.5 machine (x86_64) with only the README's requirements installed: g++ 13.3.0, Python 3.12.3 and NumPy 2.5.3. The tarball's SHA-256 and all its file hashes were checked first.
## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 87 squares would need total mass `>= 87`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 509 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n87-L9.55-proof-bundle.tar.gz`: the complete bundle, 622 files including every angle's
  input and result (SHA-256 `f8f4a19d25ecbe06df49fc2cd4244f3d9a17a2e97abe56467c70f8e76925f771`).

## Reproduce

```sh
tar xzf n87-L9.55-proof-bundle.tar.gz
cd n87-L9.55-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
