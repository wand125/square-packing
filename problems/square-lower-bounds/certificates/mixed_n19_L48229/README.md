# s(19) >= 48229/10000 = 4.8229

A lower-bound certificate for 19 unit squares in a square container. This improves
our earlier `rect_n19_L48175 (4.8175)`. This is not a claim that s(19) equals 4.8229.

The rational measure has 313 source rectangles with uniform density, no points,
and total mass `1899999/100000 < 19`. The core side is `B = 999/1000` and the
uniform half-angle net has 416 nodes, with step `1/1001`.

## Argument and checker

D4 symmetry reduces orientations to [0, pi/4]. The exact net endpoint covers this
interval, and B(1 + step) < 1. Thus every unit square contains a closed net-angle
B-core strictly inside it. The checker verifies measure >= 1 at every admissible
centre at every net angle. Selected cores from distinct packing squares are
disjoint, contradicting total mass < 19.

The bundled checker uses exact rational admission and an integer table for the
axis direction, and outward-rounded interval branch-and-bound for the other
415 directions. Its complete recorded proof and replay both cover 416/416.
The measures were built from structured initial measures at the stated target
side and repaired against the full net. The numerical search is not trusted by
the checker. Credit: Tokoharu's rectangle-measure method and base checker;
wand125's measure, core/net adaptation and bundled modified checker.

## Verification evidence

The full bundled-checker replay was also run before publication on a separate
machine: 416/416, exit 0, with all 1266 original bundle file hashes matching.
The recovered run log is in `verification/prepublication-replay.txt`. This was
a repeat of the same outward-rounded algorithm, not an independent implementation.
A separate check of this bundle's exact candidate with the adapted Rust verifier
reported 416 directions VERIFIED and zero failures; its full output is included.

The independent checker is Joshua Levy / the squares project's `sqverify_fast`,
adapted to read the declared uniform `proof_net`; its exact source snapshot,
upstream attribution and reproduction instructions are in
[`verification/sqverify-net`](../../verification/sqverify-net/README.md).
It checks the rational measure itself with a separate implementation, rather
than replaying the bundled C++ checker's records. Neither check is a
proof-assistant formalization. No upstream acceptance or registration is implied.

The publication audit checks exact mass, symmetry and net premises, every
recorded direction/replay result and the input/source hashes. It does not
reexecute the full bundled geometric computation. Absolute path metadata was
made relative; `candidate.json`, `certificate.json` and all bundled checker
sources are byte-identical to the audited originals. The old/new file hashes
are in `publication-audit.json`. The original proof/replay receipts do not give
a complete runtime/compiler inventory. Packaging metadata and independent
checker build/platform information are retained rather than inferred.

## Files and reproduction

- `candidate.json`, `certificate.json`, `manifest.json`: rational data and replay record.
- `code/`, `requirements.txt`: bundled checker and dependencies (Python 3, NumPy, C++17).
- `n19-L4.8229-proof-bundle.tar.gz`: all direction inputs/results and relocatable checker.
- `publication-audit.json`, `verification/`: audit and independent verification receipts.

Published tarball SHA-256: `03aeca45921bcb8fd0be2f4869fb98e596cad673758c79022d337b8ad9629c54`.
The archive contains 1267 hashed files plus `files-sha256.json`.

```sh
tar xzf n19-L4.8229-proof-bundle.tar.gz
cd n19-L4.8229-proof-bundle
python3 - <<'CHECK'
import hashlib, json
from pathlib import Path
for name, expected in json.loads(Path('files-sha256.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
print('All file hashes match')
CHECK
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 1
```

The last command performs the full replay and may take substantially longer
than the independent Rust verification. Hash validation should precede replay,
since replay writes regenerated reports.
