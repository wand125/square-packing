# Task: a bounded-memory `--stream` mode for n17bb-verify, with byte-identical receipts

Work only in `tools/n17_bb_verifier/` of this git worktree (branch `stream-verify`). Commit locally in
small commits. Never push, never run `gh`, change no remote state. Delete this file in your last commit.

Build environment (macOS, Apple silicon):

```bash
export PATH="$HOME/.rustup/toolchains/1.98.0-aarch64-apple-darwin/bin:$PATH"
export CPATH=/opt/homebrew/opt/gmp/include LIBRARY_PATH=/opt/homebrew/opt/gmp/lib
cargo build --locked --release
```

## Problem

`n17bb-verify` (`src/main.rs`: `load_tree`, `check_tree`, `check_nodes`, `run`) keeps compact metadata
for **every** node of the certificate (`Tree.index`, `Tree.values`, `Tree.children`) for the whole run.
Measured peak RSS is 2.3–2.5 KB per node (8,983,825 nodes -> 20.8 GB; 14,199,335 nodes -> 35.6 GB).
A 30,111,276-node certificate would need about 75 GB; we must check it on a 50 GB Linux host with a
20 GB budget.

## Goal

Add an opt-in flag `--stream`. With it, a certificate that the current code would PASS must produce a
receipt identical to the current code's receipt (every field except `seconds`; including `nodes`,
`closed_leaves`, `max_depth`, `reasons`, `checked_nodes`, `node_failures`, `counts` with every counter,
`certificate`, `pattern`, `status`, `failure_count`, `failures`, `mode`, `directory`, `schema`,
`verifier`), while peak memory is bounded by the number of nodes that are *live* at once (see below)
plus a small per-node cost (target: at most ~64 bytes per node overall, e.g. a set of seen ids).
Without `--stream`, behaviour must be byte-for-byte unchanged.

## Required design: stream, and fall back to the classic path on anything irregular

The pilot writes node records in processing order and the manifest lists chunks in that order; a
parent normally appears before its children (`check_nodes` already relies on this: "The oracle
requires a parent to be loaded in this or an earlier chunk").

In `--stream` mode, after the header and trig checks exactly as now, read the chunks once, in manifest
order, and for each chunk:

1. Validate each node exactly as `load_tree` does (the same malformed/schema/T2/T3 checks).
2. Track a node as *live* from its arrival until (a) all of its expected children have arrived and been
   checked, or (b) immediately if it is closed. Expected children of an open node: `split.angle` -> 2,
   `split.tighten` -> 1, `split.pair` -> `len(split.pair[1])`. Keep for a live node only what later
   checks need: its compact JSON (angles, windows, split, final), depth, and the list of children seen so
   far (their states for the T2 comparison).
3. Per node, do the T1–T3 work that `check_tree` does, incrementally: depth = parent depth + 1 (root 0),
   closed counts and `reasons`, the angle-split-point check, and when the last expected child of a node
   arrives, compare the sorted child states with `expected_children(node)` exactly as `check_tree` does.
4. Run the per-node verifier (`verifier.check_node(node, parent)`) on the chunk's nodes in parallel with
   the same rayon pool and the same parent data as `check_nodes`, and sum the ticks into `counts` the
   same way. Order of summation must not change any counter (they are sums).
5. Compute `summary.*` comparisons (`nodes`, `leaves`, `tighten_nodes`, `angle_leaves`) and
   `summary.complete` from running totals, exactly as `run` does now.

**Fallback rule (this is what makes receipts identical):** the moment anything would add a failure,
or the streaming order cannot reproduce the classic semantics, stop streaming and run the existing
classic path from scratch (`load_tree` + `check_tree` + `check_nodes`, unchanged), and emit its
receipt. "Anything" includes at least: any failure message that the classic code would push; a node
whose parent has not arrived yet or is no longer live; a child of a closed node; more children than
expected; a duplicate node id; more than one root or a missing root; nodes with pending (unarrived)
children at the end; any node failure from `check_node`; any `Err` from a helper. Log the fallback
reason to stderr (one line) so we can see it; do not put it in the receipt.

Because the stream path only ever reports PASS, and every FAIL comes from the unchanged classic path,
receipts are identical by construction as long as the PASS-path counters are computed identically.
`--node-ids` (sample mode) with `--stream`: refuse with a clear error (exit 2), or fall back; choose one
and document it.

Memory: drop a node's data as soon as it stops being live. Keep a compact set of all seen ids for the
duplicate check (sorted `Vec<u64>` with periodic merge, a bitmap over dense ranges, or a `HashSet<u64>`
— measure and choose; ids may be sparse, do not assume density without a fallback). Print to stderr at
the end: peak live node count, seen-id structure size, and nodes.

## Validation (all required)

1. `cargo test --locked`, `cargo clippy --locked --all-targets`, `cargo fmt --check` pass.
2. Unit tests for the stream path: the existing tree tests' trees through `--stream`, and each fallback
   trigger above (assert the fallback happens and the receipt equals the classic one).
3. For every fixture in `tests/fixtures/` (and the v3 fixtures from `scripts/make_v3_fixtures.py` if they
   need generating), and for the mutants that `scripts/check_v3.py` / existing CLI tests use, run the
   binary with and without `--stream` and assert the receipts are equal after removing only `seconds`.
   Put this as a script `scripts/compare_stream.py CERT_DIR [--cells ...]` that runs both and diffs.
4. Report peak RSS (`/usr/bin/time -l`) with and without `--stream` on the largest fixture available.

Write the results to `RESULT_STREAM.md` (what changed, the design, the comparison table, memory).
Do not run anything on remote machines; we will run the large-certificate comparison ourselves.
