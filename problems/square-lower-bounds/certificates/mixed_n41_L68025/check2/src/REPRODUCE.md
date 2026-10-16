# Reproducing the independent check on a plain Ubuntu 24.04 host

The certificate is checked by one independent implementation: sqverify_fast from
jlevy/squares with one change, reading the certificate's declared angle net. This page
rebuilds it from source and runs it on the certificate, with a tamper control.

## What you need

| File | Contents | SHA-256 |
|---|---|---|
| `sqverify-proof-net-fe12e036c.tar.gz` | `packing/sqverify_fast` of jlevy/squares at commit fe12e036c (branch wand125/sqverify-proof-net), made with `git archive` | e495f9bf14dc5ca20d8890aa0601183b8b955b94580c4e99ddffa64254371e81 |
| `fine_net_check.sh` | runs the check and the control, writes the receipt (bash and the Python 3 standard library) | see the bundle's file list |
| `candidate.json` | the certificate (in the bundle) | see the bundle's file list |

The same sources are published in github.com/wand125/square-packing-tools at commit
`5fba675` (`fine_net_verifier/`, with `fine_net_check.py`; `fine_net_witnesses/` is the
separate repair aid). Either source gives the same `build.source_sha256`.

## Steps

```bash
# 0. Check the files
sha256sum sqverify-proof-net-fe12e036c.tar.gz fine_net_check.sh candidate.json

# 1. System packages (all that a fresh Ubuntu 24.04 needs)
sudo apt-get update
sudo apt-get install -y build-essential curl ca-certificates python3

# 2. Rust via rustup (the crate's rust-toolchain.toml pins 1.98.0)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain 1.98.0
. "$HOME/.cargo/env"

# 3. Build (dependencies pinned by Cargo.lock, fetched from crates.io)
tar xzf sqverify-proof-net-fe12e036c.tar.gz
(cd sqverify_fast && cargo build --release --locked)

# 4. Check and control
chmod +x fine_net_check.sh
./fine_net_check.sh sqverify_fast/target/release/sqverify-fast candidate.json out
```

## The receipt (`out/receipt.json`)

- `verdict` is `PASS` only when all of these hold (the script then exits 0, otherwise 1):
  - `status` is `VERIFIED` (the verifier's summary) and the verifier exited 0;
  - `directions_verified` equals `directions_expected` (= `proof_net.last` + 1);
  - the control (every mass scaled by 0.985, on 32 directions spread over the net) is
    `REFUSED`, with at least one direction where the capture is shown below 1 in exact
    rationals (`exact_below_threshold`).
- `candidate_digest`: SHA-256 of the JSON of {n, L, B, rectangles, points, total_mass,
  proof_net} with sorted keys and no spaces; compare it with the bundle's README.
- Also `file_sha256`, `input_sha256` (the bytes the verifier read),
  `build.source_sha256` (digest of the verifier's sources, Cargo files and build script),
  and `seconds`.
- Raw records: `run.jsonl` (one line per direction), `control.jsonl`, `*.stderr`.

## Time

With 4 threads: about 1 to 2 minutes to build; the check takes from about 1 minute
(n = 18, 416 directions) to about 25 minutes (832 directions, n around 30); the control
adds about a tenth. On a plain 4-vCPU Ubuntu host, n = 29 at L = 5.81 took 584 seconds.

## The verifier

- sqverify_fast is a clean-room verifier (interval arithmetic with outward rounding);
  direction 0 is an exact event sweep, every other direction an interval branch and bound
  over centre boxes. Its soundness argument is its SOUNDNESS.md, its independence record
  INDEPENDENCE.md.
- The change: a format M candidate's `proof_net {step, last}` sets the net (the original
  fixes step 83/40000 and 201 directions). The net premises are checked as before.
- The measure is the D4 average of the listed rectangles, the threshold Γ = 1 and the
  total mass below n. The specification is SPEC.md.
