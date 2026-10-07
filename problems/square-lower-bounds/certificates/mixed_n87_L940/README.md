# s(87) >= 47/5 = 9.4

A density certificate proving that 87 unit squares do not fit in a square of side `L = 47/5 = 9.4`. This exceeds Nagamochi's closed form `1 + √70 = 9.3666002…` (2005) by more than `0.0333`, and our earlier `9.39`.

This supersedes [`mixed_n87_L939`](../mixed_n87_L939/README.md) for `n = 87`.

The measure is 634 rectangles with uniform density and no point masses. The total mass is
`8699999/100000 = 86.99999 < 87`. The setting is that of the rectangle certificates in this repository: core side
`B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`: at the 200 oblique angles the lowest is `1.0000000235`, and at
angle 0 the integer table's minimum is `1.031024`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was obtained from the published n = 86 certificate [`rect_n86_L9365`](../rect_n86_L9365/): its measure was read with the n = 87 budget and stretched to L = 9.40 by a "central" stretch (the band within distance 0.5 of each wall is kept in place, and the interior is stretched by a smooth power-2 map that stretches most at the centre, with the weights corrected by the local area ratio), then repaired against counterexamples on the full net. Certificates at L = 9.375 to 9.395 obtained the same way are implied by this one and are not published separately.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 87 squares would need total mass `>= 87`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 634 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the source hashes and the exact comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n87-L9.40-proof-bundle.tar.gz`: the complete bundle, 622 files including every angle's
  input and result (SHA-256 `c33a44d66f4656f23f0f20eef82eacddc053a991b2c581a75df417fb1f5f4435`).

## Reproduce

```sh
tar xzf n87-L9.40-proof-bundle.tar.gz
cd n87-L9.40-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
