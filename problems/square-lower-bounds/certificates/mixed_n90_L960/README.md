# s(90) >= 48/5 = 9.6

A density certificate proving that 90 unit squares do not fit in a square of side `L = 48/5 = 9.6`. This exceeds Nagamochi's closed form `1 + √73 = 9.5440037…` (2005) and our earlier `9.5675`.

The measure is 762 rectangles with uniform density and no point masses. The total mass is
`8999999/100000 = 89.99999 < 90`. The setting is that of the rectangle certificates in this repository: core side
`B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`: at the 200 oblique angles the lowest is `1.000000000042`, and at
angle 0 the integer table's minimum is `1.018742`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was obtained from the published n = 89 certificate [`rect_n89_L9565`](../rect_n89_L9565/): its measure was read with the n = 90 budget and stretched to L = 9.60 by the "wall" variant of the end-fixed stretch (the bands along the walls are kept in place and only the interior is stretched, with the weights corrected by the local area ratio), then repaired against counterexamples on the full net.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 90 squares would need total mass `>= 90`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 762 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the source hashes and the exact comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n90-L9.60-proof-bundle.tar.gz`: the complete bundle, 622 files including every angle's
  input and result (SHA-256 `a3c4e731231b896c357c77c12d39284183d3b63c7824de44a82527a6dd9e2f37`).

## Reproduce

```sh
tar xzf n90-L9.60-proof-bundle.tar.gz
cd n90-L9.60-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
