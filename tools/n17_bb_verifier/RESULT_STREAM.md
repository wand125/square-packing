# Streaming verifier results

Implemented and validated on macOS / Apple silicon, 2026-10-10, Rust 1.98.0 with
system GMP. The large-certificate measurement below was made on a Linux host.

## Implementation

- `--stream` dispatches after the existing header and trig checks. The successful
  path reads each chunk once in manifest order, using the same Rayon thread pool
  configuration and `NodeVerifier::check_node` with the same compact parent `final`.
- Live open nodes keep the classic compact JSON projection (including removal of
  the tightening replay E), depth, expected child count, and child-state strings.
  Expected states and window sorting use the existing helpers. Closed nodes are
  counted immediately. Completed parents are removed after the chunk's parallel
  child checks finish; no global JSON interning arena retains retired data.
- Running totals supply depth, reasons, closures, checked nodes, every tick counter,
  all four v3 summary checks, and `summary.complete`. The stream path emits PASS
  only. Errors discard its candidate receipt and all streaming state, log one
  `stream fallback:` line, and restart the classic path from scratch.
- `load_tree`, `check_tree`, and `check_nodes` are unchanged. The default run's
  receipt assembly is unchanged. Invalid-order inputs that classic accepts can
  still PASS via fallback, with exactly the classic receipt.
- `--stream --node-ids FILE` is explicitly rejected with exit 2. Usage and memory
  behavior are documented in README.md. Stderr reports peak live nodes and the
  seen-ID count, capacity, estimated bucket bytes, and visited node count. Failed
  attempts report partial statistics; header errors can precede stream creation.

The memory bound is peak live JSON/child states plus the largest decoded chunk,
its parent references and per-node result maps, thread-local verifier work, and a
compact all-seen-ID table. Fallback intentionally uses classic memory. This is not
an unconditional 20 GB bound for arbitrary chunk sizes or wide live frontiers.

## Receipt comparisons

All comparisons remove **only `seconds`**, and also compare process exit codes.
No directory, certificate identity, count, failure, or other field is excluded.
The three valid retained fixtures PASS directly without fallback. All 17 retained
mutants fall back and agree, including partial receipts returned on helper errors.

| Fixture | Receipt nodes | Status | Identical | Fallback |
| --- | ---: | --- | --- | --- |
| mutated-bound | 83 | FAIL | yes | yes |
| mutated-cut | 83 | FAIL | yes | yes |
| mutated-drop-leaf | 82 | FAIL | yes | yes |
| mutated-multiplier | 83 | FAIL | yes | yes |
| mutated-narrow-final | 83 | FAIL | yes | yes |
| mutated-split | 83 | FAIL | yes | yes |
| small-certificate | 83 | PASS | yes | no |
| v3-angle | 1 | PASS | yes | no |
| v3-child-window | 2 | FAIL | yes | yes |
| v3-drop-partner | 1 | FAIL | yes | yes |
| v3-in-v1 | omitted | FAIL | yes | yes |
| v3-missing-trig | 1 | FAIL | yes | yes |
| v3-not-empty | 1 | FAIL | yes | yes |
| v3-repeat | 1 | FAIL | yes | yes |
| v3-small-final | 1 | FAIL | yes | yes |
| v3-summary | 1 | FAIL | yes | yes |
| v3-target | 2 | FAIL | yes | yes |
| v3-tighten | 2 | PASS | yes | no |
| v3-wall | 1 | FAIL | yes | yes |
| v3-wrong-pair | 1 | FAIL | yes | yes |

`tests/stream.rs` runs these 20 comparisons with both 1 and 2 threads. It also
covers 19 structural/header/trig/I/O cases, 12 v3 schema/helper/summary/mutation
cases, and single-record chunks with descending sparse IDs near `u64::MAX`.
Those chunk tests include a late extra child whose parent was already retired.
Every irregular case asserts fallback and complete classic receipt equality.
`--stream --node-ids` rejection is also tested.

Unit tests replay the existing angle partition, bad partition, sparse-ID,
closed-child, and numeric pair-window tree cases through the stream state machine.
They verify retirement, depth, closures, and a sparse seen-ID memory bound.

`scripts/compare_stream.py CERT_DIR [--cells FILE] [--manifest NAME] [--threads N]`
is the reusable two-run comparator. It automatically hashes custom cells and
prints a unified receipt diff on disagreement. `scripts/check_stream.py` uses it
for all retained fixtures and six locally reconstructed mutation types from
`check_v3.py`: `drop_partner_interval`, `pair_as_wall`, `widen_eliminated`,
`angle_not_empty`, `wrong_pair_index`, and `drop_window`. All six FAIL, fall back,
and have identical receipts.

**Data availability:** the v3 fixtures were already generated and present, so no
regeneration was necessary. `../joint_tools/runs/cert3` and
`../joint_tools/tamper/out` are absent in this worktree. Consequently the original
external A/C1/C2 certificates and exact external mutant files were not run; the
six local versions exercise the same mutation types, not the same source bytes.
No remote data was fetched. The large-certificate comparison remains for the user.

As a separate default-behavior regression, a release binary built from pre-change
commit `22a23c8` was compared against the new binary **without `--stream`** on all
20 fixtures. All receipts and exits agree after removing only `seconds`.
Evidence: `results/stream/baseline-agreement.json`.

## Checks

All passed:

```text
cargo build --locked --release
cargo test --locked                 22 unit + 4 existing CLI + 5 stream CLI tests
cargo clippy --locked --all-targets
cargo fmt --check
python3 scripts/check_stream.py     20 fixtures + 6 local mutants
```

The final stream CLI tests contain multiple cases as detailed above. Python
comparisons use the release binary; Cargo CLI tests use Cargo's test binary.

## Memory measurements

Largest available retained certificate: `small-certificate`, 83 nodes. Both runs
used 2 threads and `/usr/bin/time -l`; the initial sandbox attempt could not read
`kern.clockrate`, so the successful measurements used approved local access.
Raw output is retained in `results/stream/*time.txt`.

| Measurement | Peak RSS bytes | MiB | Receipt seconds |
| --- | ---: | ---: | ---: |
| Classic, 83 nodes | 4,866,048 | 4.641 | 0.049 |
| Stream, 83 nodes | 4,915,200 | 4.688 | 0.082 |
| Sparse HashSet, 1,000,000 IDs | 39,616,512 | 37.781 | n/a |

The 83-node fixture is too small to demonstrate RSS savings: stream was 49,152
bytes higher in this measurement. Do not extrapolate a full-certificate memory
reduction or throughput from these short runs. Stream diagnostics for it:

```text
peak_live=27 seen_ids=83 seen_capacity=112 seen_bytes_estimate=1168 nodes=83
```

`HashSet<u64>` was chosen for sparse IDs and amortized constant-time insertion.
The reproducible standalone benchmark `scripts/measure_seen.rs` inserts one
million sparse IDs incrementally, using the same standard HashSet implementation
and allocation growth as the verifier. It measured capacity 1,835,008 and estimated
18,874,384 retained bucket/control bytes (18.874 bytes/ID). Whole-process peak RSS,
including allocator growth history and runtime overhead, was 39.617 bytes/ID,
below the ~64-byte target. The smaller unit test uses 100,000 sparse IDs.

Bucket storage is about 10–21 bytes/ID at scale; simultaneous old/new tables during
a growth step can use about 31 bytes/ID, and allocator retention can raise RSS
further as measured. Sizes printed by the verifier are explicitly estimates of
bucket/control storage, not process RSS or allocator accounting. A 30,111,276-ID
set would have an estimated 576 MiB retained bucket allocation on this
implementation. This is an estimate, not a large-certificate measurement.

Reproduce the sparse benchmark:

```bash
rustc -O scripts/measure_seen.rs -o target/measure-seen
/usr/bin/time -l target/measure-seen 1000000
```

## Large certificate

On the 8,983,825-node certificate `m475217` (Linux, 8 threads, GNU time), the
streaming receipt matches the classic receipt in every field except `directory` and
`seconds`:

| Run | Peak RSS | Wall time |
|---|---:|---:|
| Classic (4 threads) | 20.8 GB | 17:17:27 |
| Stream, unbounded trig cache | 5.87 GB | 2:12:17 |
| Stream, bounded trig cache | 0.81 GB | 2:08:27 |

The first streaming run still grew by about 0.5 KB per node. The cause was the
per-thread `cos_sin` memo table in `src/exact.rs`, which kept every angle met. It is
now cleared when it reaches 65,536 entries per thread; the table only caches a pure
function, so receipts are unchanged. The remaining growth is the seen-ID table
(`seen_bytes_estimate=150994960`, about 17 bytes per node). Two damaged copies of a
smaller certificate (a broken tighten split and a dropped leaf) FAIL with receipts
identical to the classic verifier, through the fallback.
