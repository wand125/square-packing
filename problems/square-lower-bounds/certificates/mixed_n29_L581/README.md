# s(29) >= 581/100 = 5.81

A density certificate proving that 29 unit squares do not fit in a square of side `L = 581/100 = 5.81`. This exceeds our rectangle certificate `rect_n29_L57975` (5.7975) and Nagamochi's closed form `1 + √20 = 5.4721…` (a reference value, see jlevy/squares#295).

The measure is 505 rectangles with uniform density and no point masses. The total mass is
`2899999/100000 = 28.99999 < 29`. The setting is a finer angle net than the rectangle certificates in this repository: core side `B = 999/1000`, and 416 half-angle net nodes with step `1/1001`.

The coverage lower bound at each net angle is `>= 1`: at the 415 oblique angles the lowest is `1.0000000009`, and at
angle 0 the integer table's minimum is `1.003704`. That is below the `1.0001` that tokoharu's `verify.cpp` requires, so
the certificate is not in his format. It was checked with the verifier shipped here, `code/mixed_rotated_verify.cpp`,
the same checker as for [`mixed_n87_L939`](../mixed_n87_L939/README.md) and [`mixed_n65_L835`](../mixed_n65_L835/README.md).

The candidate was built from scratch at L = 5.81 from a structured initial measure (bands at integer distances from the walls), searched under the n = 29 budget with a core of side B = 0.999 on a finer half-angle net (step 1/1001, 416 angles, declared in proof_net), and repaired against counterexamples on the full net. Each screening pass collected up to 32 separated low-coverage witnesses per net angle and the repair tolerance was scaled to the remaining mass slack; twelve screening/repair rounds (eight, then four more from the saved state) were needed before every net angle passed.
Before publication the bundle's candidate was checked with the independently implemented `sqverify_fast` (jlevy/squares, adapted to read the declared net; source digest `ab6e33e164db`) on a fresh Ubuntu 24.04.5 LTS (x86_64), Rust 1.98.0 machine: 416/416 directions VERIFIED in 584 s, and the control (every mass x 0.985, 32 directions) was refused in 32 directions. The tarball's SHA-256 and all its file hashes were checked first.
## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 1/1001) < 1`. So every unit
square, at any orientation, contains a closed core of side `B` at a net angle, strictly in
its interior. Each such core has measure `>= 1`. Cores chosen inside the squares of a
packing are disjoint, so 29 squares would need total mass `>= 29`.

## Files

- `candidate.json`: the rational measure (`L`, `B`, the 505 rectangles and their weights).
- `certificate.json`: the result of the full replay, covering the axis table and all 415 oblique angles.
- `manifest.json`: the angle net and the verifier's SHA-256.
- `code/`: the checker (Python 3 with NumPy, and a C++17 compiler).
- `n29-L5.81-proof-bundle.tar.gz`: the complete bundle, 1267 files including every angle's
  input and result (SHA-256 `057d3df36634f062d6eaad37d5c3195bb2c0adfcd7ba7ce6e149d8333be9dc56`).

## Reproduce

```sh
tar xzf n29-L5.81-proof-bundle.tar.gz
cd n29-L5.81-proof-bundle
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

Before publication the bundle's candidate was checked with the independently implemented `sqverify_fast` (jlevy/squares, adapted to read the declared net; source digest `ab6e33e164db`) on a fresh Ubuntu 24.04.5 LTS (x86_64), Rust 1.98.0 machine: 416/416 directions VERIFIED in 584 s, and the control (every mass x 0.985, 32 directions) was refused in 32 directions. The tarball's SHA-256 and all its file hashes were checked first. The full replay in this bundle was run where the certificate was made. Nothing here is a proof-assistant formalization.
