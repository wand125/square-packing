# Tests

`REFERENCE_VERIFIER` is the path of upstream's `verify_n17_kernel_certificate.py`; the
Python scripts run it, with its provenance import stubbed, as the oracle. Python 3.14.

| command | what it checks |
|---|---|
| `cargo test --release` | geometry and sweep helpers on exact inputs; the sweep against an exact area-subtraction reference on random rational polygons; facets against the hull of vertex differences; the 256-bit product comparison; canonical JSON and float `repr` tables from CPython; the `random.sample` table; receipts of the fixtures at 1, 2 and 4 threads |
| `python3.14 tests/make_fixtures.py` | regenerates the tiny closed, stalled, sampled and dead-row fixtures and their oracle results |
| `python3.14 tests/make_fixture_ohi.py` | a fixture closed by `owned_hulls_intersect` (no recorded certificate closes this way) and two controls: a wrong declared kind, and the point moved out of the hull |
| `python3.14 tests/differential.py` | 185 mutations of the fixtures at 1 and 4 threads: status, failure text, counts and content ids equal to the oracle's |
| `python3.14 tests/cli_check.py` | receipt bytes equal to Python's `json.dumps(indent=1)`, exit codes, progress lines, the embedded cover |

## Upstream's mutations

The 34 mutations of upstream's verifier review (2026-10-03, lane R6, script
`audit-verifier-rewrites/mutate_cert.py.txt`) were applied to `tests/data/stall-w7-bins8`
with a local loader and saver (canonical JSON, gzip, SHA-256 names) in place of the
generator's. Both verifiers refuse all 34, naming the expected check, with identical
failure text.

## Certificates from upstream's procedure

Seven certificates produced with upstream's standard procedure at `4148483da`
(`--bins 64 --max-rounds 24 --hull-limit 16 --producer-share 0.6 --split-floor 512
--max-rows 1152 --split-patience 1` for BC-428; W7 variants at bins 16, 32 and 64):
receipts equal at 1 and 16 threads, and the timings in README.md. They are not
included here (215 MB).
