# s(18) >= 588/125 = 4.704

A lower-bound certificate for 18 unit squares in a square container. This improves
our earlier `mixed_n18_L470 (4.7)`. This is not a claim that s(18) equals 4.704.

The rational measure has 209 source rectangles with uniform density, no points,
and total mass `1799999/100000 < 18`. The core side is `B = 1999/2000` and the
uniform half-angle net has 832 nodes, with step `1/2006`.

## Argument and checker

D4 symmetry reduces orientations to [0, pi/4]. The exact net endpoint covers this
interval, and B(1 + step) < 1. Thus every unit square contains a closed net-angle
B-core strictly inside it. The checker verifies measure >= 1 at every admissible
centre at every net angle. Selected cores from distinct packing squares are
disjoint, contradicting total mass < 18.

The bundled checker uses exact rational admission and an integer table for the
axis direction, and outward-rounded interval branch-and-bound for the other
831 directions. Its complete recorded proof and replay both cover 832/832.
The measures were built from structured initial measures at the stated target
side and repaired against the full net. The numerical search is not trusted by
the checker. Credit: Tokoharu's rectangle-measure method and base checker;
wand125's measure, core/net adaptation and bundled modified checker.

## Verification evidence

The independent Rust check verified all 832 directions locally on macOS arm64
using one worker in 388.202 seconds (about 6 minutes 28 seconds), exit 0.
Its full direction output and build/source digest are in `verification/independent.jsonl`.
The negative controls and timing are recorded in `verification/control-results.json`.
No new full bundled-checker replay on a separate fresh machine was performed for
this release; the original complete replay and a new complete independent check
are distinct evidence.

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
- `n18-L4.704-proof-bundle.tar.gz`: all direction inputs/results and relocatable checker.
- `publication-audit.json`, `verification/`: audit and independent verification receipts.

Published tarball SHA-256: `a4098f8200686c944d20c4c9458c3412225b1ca06f77423206a3306d03d4a709`.
The archive contains 2515 hashed files plus `files-sha256.json`.

```sh
tar xzf n18-L4.704-proof-bundle.tar.gz
cd n18-L4.704-proof-bundle
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
