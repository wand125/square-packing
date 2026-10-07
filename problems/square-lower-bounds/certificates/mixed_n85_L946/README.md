# s(85) >= 473/50 = 9.46

A density certificate proving that 85 unit squares do not fit in a square of side `L = 473/50 = 9.46`. This exceeds Green's reported bound `2√2 + (247 + 12√2)/41 = 9.2667…` (Friedman DS7, Theorem 9 with k = 9, inherited from n = 82) and our earlier certificate `mixed_n85_L942` (9.42).

This supersedes [`mixed_n85_L942`](../mixed_n85_L942/README.md) for `n = 85`.

The measure is 525 rectangles with uniform density and no point masses. The total mass is
`8499999/100000 = 84.99999 < 85`. The setting is that of the rectangle certificates in this repository: core side
`B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`: at the 200 oblique angles the lowest is `1.0000000021`, and at
angle 0 the integer table's minimum is `1.002532`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was built from scratch at L = 9.46 from a structured initial measure (bands at integer distances from the walls, as in the Green-series certificates), searched under the n = 85 budget, and repaired against counterexamples on the full net.
The pre-publication replay was run on a fresh Ubuntu 24.04.5 machine (x86_64) with only the README's requirements installed: g++ 13.3.0, Python 3.12.3 and NumPy 2.5.3. It was run on a copy of this bundle that differs only in the provenance line of `bundle.json` (a local path, since removed); the proof files are byte-identical. The tarball's SHA-256 and all its file hashes were checked first.
## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 85 squares would need total mass `>= 85`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 525 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the source hashes and the exact comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n85-L9.46-proof-bundle.tar.gz`: the complete bundle, 622 files including every angle's
  input and result (SHA-256 `d518b3a95c337361f58d66f520b1fe91ca2e41ffb37bdbb53c7c3235e7ec768c`).

## Reproduce

```sh
tar xzf n85-L9.46-proof-bundle.tar.gz
cd n85-L9.46-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
