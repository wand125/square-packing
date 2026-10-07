# s(50) >= 147/20 = 7.35

A density certificate proving that 50 unit squares do not fit in a square of side
`L = 147/20 = 7.35`. This exceeds Green's bound for `n = 50`,
`2√2 + 101/25 + 3√14/25 = 7.3174260…`, by more than `0.0325739`
(compared exactly with integer square-root bounds; see `final-audit.json`).
It supersedes an earlier certificate, `s(50) >= 7.318`, since withdrawn (commit `b08fb24`).

The measure is 499 rectangles of uniform density with exact rational geometry and
masses, and no point masses. The total mass is `4999999/100000 = 49.99999 < 50`.
The setting is that of the other certificates here: core side `B = 9977/10000`,
and 201 half-angle net nodes with step `83/40000`.

The coverage lower bound at each net angle is `>= 1`, with the lowest at
`1.0000000005…`. That is below the `1.0001` which tokoharu's `verify.cpp` requires,
so this certificate is not in his format. It was checked with the verifier shipped in
the bundle (`src/unified_linear_verify.cpp` and its Python driver). That verifier
proves coverage `>= 1` over every centre domain with outward-rounded interval
arithmetic.

## Argument

D4 symmetry reduces orientations to `[0, π/4]`, and `B(1 + 83/40000) < 1`. So every
unit square, at any orientation, contains a closed core of side `B` at a net angle,
strictly in its interior. Each such core has measure `>= 1`. Cores chosen inside the
squares of a packing are disjoint, so 50 squares would need total mass `>= 50`.

## Files

- `candidate.json`: the rational measure.
- `certificate.json`: the per-angle records, including every input's SHA-256.
- `manifest.json`: the angle net.
- `final-audit.json`: the audit of geometry, mass, hashes, all 201 records and the
  exact Green comparison.
- `n50-L7.35-proof-bundle.tar.gz`: the complete bundle, 1,043 files: code, every
  angle's input and result, `audit.py` and `replay.py`
  (SHA-256 `b7e8ac3184738953312946648e889543ad4cefb4901465761203a166363bd387`).

## Reproduce

```sh
tar xzf n50-L7.35-proof-bundle.tar.gz
cd green-n50-L735
python3 audit.py
python3 replay.py --workers 3
```

You need Python 3 with numpy, scipy, numba and highspy, and a C++17 compiler.
`replay.py` first checks every packaged file against `SHA256.json`. It then
regenerates all 201 inputs from the candidate and re-runs the verifier on each one,
requiring every record to equal the stored one.

Before publication, the audit and the full replay were run again from this tarball,
in a fresh directory. Both passed:
`FINAL_CERTIFICATE_AUDITED` and `ALL_201_ANGLES_REPLAYED`. The replay re-executes the
same outward-rounded implementation; it is not an independent second algorithm or a
proof-assistant formalization.

## Provenance

The measure started from a structured L = 7.40 rectangle initialization. It was
contracted to L = 7.35 and repaired to a nonnegative measure by minimum-L1 repair,
keeping the native constraints and exact deficit witnesses. It does not establish
L = 7.40.
