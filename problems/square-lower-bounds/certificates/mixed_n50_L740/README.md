# s(50) >= 37/5 = 7.40

A density certificate proving that 50 unit squares do not fit in a square of side
`L = 37/5 = 7.4`. This exceeds Green's bound for `n = 50`,
`2√2 + 101/25 + 3√14/25 = 7.3174260…`, by more than `0.082573`. The comparison is exact,
with 90-digit integer square-root bounds (see `completion-audit.json`). This certificate
supersedes [`mixed_n50_L735`](../mixed_n50_L735/README.md).

The measure is 553 rectangles with uniform density and no point masses. The total mass is
`4999999/100000 = 49.99999 < 50`. The setting is that of the rectangle certificates in this
repository: core side `B = 9977/10000`, and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`, with the lowest at `1.0000000004…`.
That is below the `1.0001` that tokoharu's `verify.cpp` requires, so the certificate is not
in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`.
That is a research copy of `verify.cpp` which proves coverage `>= 1` over every centre domain
with outward-rounded interval arithmetic. It is the same checker as for `mixed_n65_L835`.

The candidate was built directly at L = 7.4, from a structured initialization, then priced
over free support and repaired against counterexamples on the full net. It was not obtained
by shrinking a larger certificate.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 50 squares would need total mass `>= 50`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 553 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 200 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `completion-audit.json`: the audit of the candidate, the mass, the angle set, the replay
  states, the net containment, the source hashes and the exact Green comparison.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n50-L7.40-proof-bundle.tar.gz`: the complete bundle, 621 files including every angle's
  input and result (SHA-256
  `2c405bbd4e9c6a7000f0095ca6ca494023d75e169b03243526e4fef5a8c8e133`).

## Reproduce

```sh
tar xzf n50-L7.40-proof-bundle.tar.gz
cd n50-L7.40-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The checker first regenerates every input from the rational candidate. It then checks the
symmetry, the angle-net containment and the budget. It rechecks the axis case with integer
tables, using an implementation independent of the one that produced them. Finally it
re-executes the 200 oblique centre-domain proofs.

The full replay was run where the certificate was made. Before publication it was run again
from this tarball, after checking all 621 file hashes, and both runs ended with
`ALL_ANGLES_VERIFIED_AND_REPLAYED`. The oblique replay uses the same outward-rounded algorithm
as the proof. It is not an independent second implementation, and nothing here is a
proof-assistant formalization.
