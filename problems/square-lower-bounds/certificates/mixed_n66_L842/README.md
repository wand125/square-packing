# s(66) >= 421/50 = 8.42

A density certificate proving that 66 unit squares do not fit in a square of side `L = 421/50 = 8.42`. This exceeds our earlier rectangle certificate `8.385` ([`rect_n66_L8385`](../rect_n66_L8385/)).

The measure is 631 rectangles with uniform density and no point masses. The total mass is
`6599999/100000 = 65.99999 < 66`. The setting is that of the rectangle certificates in this repository: core side
`B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`: at the 200 oblique angles the lowest is `1.0000000009`, and at
angle 0 the integer table's minimum is `1.003102`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was built from scratch at L = 8.42 with a structured initial measure (bands at integer distances from the walls, as in the Green-series certificates), searched under the n = 66 budget, and repaired against counterexamples on the full net.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 66 squares would need total mass `>= 66`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 631 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the source hashes and the exact comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n66-L8.42-proof-bundle.tar.gz`: the complete bundle, 622 files including every angle's
  input and result (SHA-256 `f7c7d908f00ec5f9e88224f96250ce57eb243d310929e95b3e16c0ab242e02bf`).

## Reproduce

```sh
tar xzf n66-L8.42-proof-bundle.tar.gz
cd n66-L8.42-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
