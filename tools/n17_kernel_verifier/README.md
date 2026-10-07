# n17_kernel_verifier: an independent Rust verifier of n = 17 kernel certificates

A second implementation of the standing verifier of saved n = 17 kernel certificates,
`packing/devtools/verify_n17_kernel_certificate.py` in
[jlevy/squares](https://github.com/jlevy/squares). It reads the same seed and node
(`seed-*.json.gz`, `node-*.json.gz`), performs the same checks in the same order, and
writes the same receipt: every field agrees with the Python verifier's except
`provenance` (this implementation's own), `directory` (the argument as given) and
`seconds`.

It is written from the Python verifier as the specification. It shares no code with
any certificate generator: the generator (`check_n17_subpattern`, `sqpack.hull_kernel`)
was not read, and the integer library (GMP through `rug`, with an `i128` fast path) is
not the one used by the Rust generator work it is meant to check (`malachite`).
See PROVENANCE.md.

## What it checks

Exactly what the Python verifier checks, with exact rational and integer arithmetic
throughout (no floating point decides anything):

- the frame: the seed's and node's schemas, cap, mask and world against the cells, and
  the node naming the seed by the SHA-256 of its canonical JSON;
- the seed: every owned point owned (bisection on the half-angle), every row the cell
  cut by the row's legal box, the uniform grid of row intervals;
- every step: prior owned hulls, the refinement of the half-angle rows, partner pose
  covers (domain and strictly interior core), common-core planes, outer bounds and
  domains, and, for the rows checked in full, the required domain, every collision
  region against every facet of the exact Minkowski difference, and coverage of the
  required domain by an exact vertical sweep (or exact parameter intervals for a
  degenerate domain);
- compression witnesses (exact convex combinations on the 2^-20 grid, hull size ≤ 16);
- the closure derived after each step and equal to the declared one, no step after it,
  and the final state.

The node is streamed a step at a time and its content id is computed over the same
canonical bytes as Python's `json.dumps(sort_keys=True, separators=(",", ":"))`.
`--sample N` chooses the same rows as Python's `random.Random(seed).sample`.

## Build and run

```bash
cargo build --release --locked
target/release/n17-kernel-verifier CERT_DIR --output receipt.json [--threads K]
target/release/n17-kernel-verifier CERT_DIR --output receipt.json \
    --cells CELLS.json --cells-sha256 HEX [--sample N --sample-seed S] [--progress]
```

Without `--cells`, the 24-cell unique-state cover (design `ring-3-voronoi-8-tabbed-unique`,
cap 1169/250), exported once from the upstream cover tool into `cells/cover.json`, is
embedded at build time and reported as `{"kind": "cover", "design": ...}`, as the Python
verifier reports its default cells. The exit status is 0 only for PASS.

Building needs a C toolchain and `m4` for GMP (`build-essential` and `m4` on Ubuntu).

## Agreement and speed

On seven certificates produced with upstream's standard procedure (main `4148483da`;
four closed, three stalled), the receipts agree with the Python verifier's on every
field above, at 1 and 16 threads. Same machine (16 vCPU, otherwise idle), wall seconds:

| certificate | Python | Rust, 1 thread | Rust, 16 threads |
|---|---:|---:|---:|
| W7, bins 16, octagon core (stall) | 186 | 13.2 | 8.4 |
| W7, bins 32, octagon core (stall) | 340 | 26.2 | 15.7 |
| W7, bins 64 (closed) | 265 | 38.9 | 18.8 |
| W7, bins 64, split floor 128 (closed) | 309 | 47.7 | 21.5 |
| BC-428 u3 (closed) | 702 | 125.8 | 67.5 |
| BC-428 u4 (closed) | 792 | 82.4 | 47.3 |
| BC-428 u6 (stall) | 1181 | 198.1 | 97.0 |

Peak memory is at most the Python verifier's. Steps are checked in order; only the rows
of one step checked in full run in parallel, so extra threads give about a factor of two.

The 34 certificate mutations of upstream's 2026-10-03 verifier review are refused by both
verifiers with the same failure text. See TESTING.md.
