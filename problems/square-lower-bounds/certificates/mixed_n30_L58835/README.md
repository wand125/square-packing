# Fine-net measure certificate: n=30, L=11767/2000 (5.8835)

**Claim.** No packing of 30 closed unit squares (interiors disjoint) fits in the closed square of side L=11767/2000.
Total mass of the certificate measure: 2999999/100000 < 30. candidate_digest: `8836a300570e321de3b7a171924dad8850548c130675eb371df07e083ee3b93e`.
This is a lower bound s(30) >= 5.8835; it is not a claim of optimality. Compared with: our earlier certificate rect_n30_L5875 (5.875).

## What is in this bundle

- `candidate.json` — the certificate: a nonnegative measure given by axis-parallel rectangles with masses
  (each rectangle is averaged over the 8 images of the container's symmetry group, mass/8 per image), optional points,
  the core side `B`, and the declared half-angle net `proof_net = {step: 1/2006, last: 831}` (832 directions).
- `check2/receipt.json` — the independent second-system check: every direction `verified` with threshold 1,
  file and digest of the candidate it was run on, the verifier's own summary (nodes, seconds, threads).
- `check2/run.jsonl.gz` — the verifier's per-direction log.
- `check2/control.json`, `check2/control.jsonl.gz` — negative control: the same candidate with every mass x0.985 is refused
  (exact coverage below 1 found in the sampled directions), showing the check is not vacuous.
- `check2/src/` — the verifier source as a `git archive` (jlevy/squares `packing/sqverify_fast`, branch
  `wand125/sqverify-proof-net`, commit fe12e036c: upstream sqverify-fast plus proof_net support in `certificate.rs`),
  the check script `fine_net_check.sh`, the reproduction notes `REPRODUCE.md` and the specification `SPEC.md`.
- `provenance/` — how the candidate was found (numerical search; not an input to the check).
- `bundle.json`, `files-sha256.json` — metadata and hashes of every file.

## Certificate semantics

Orientations reduce by D4 symmetry to t=tan(theta/2) in [0, sqrt(2)-1]. The net has nodes t_j=j*step, j=0..831.
Because B*(1+step) < 1 (B=1999/2000, step=1/2006), every unit square at orientation t contains, in its interior, the concentric
core of side B at the nearest net angle. A unit square at orientation t >= a has its centre at least r(a)=(cos+sin)/2 from the
walls, so for node j all centres in [r(a_j), L-r(a_j)]^2 with a_j=max(0,t_j-step/2) are checked. The verifier certifies that
at every net direction and every admissible centre the core carries measure >= 1. Cores of distinct packed squares are
disjoint, so 30 squares would carry measure >= 30 > 2999999/100000: contradiction. No Nagamochi score lemma is used.

## Reproduce the check

See `check2/src/REPRODUCE.md`. In short, on a plain Ubuntu 24.04 host: install build-essential and rustup (toolchain pinned
by `rust-toolchain.toml`), unpack `check2/src/sqverify-proof-net-fe12e036c.tar.gz`, `cargo build --release --locked`, then

```sh
bash check2/src/fine_net_check.sh sqverify_fast/target/release/sqverify-fast candidate.json out/
```

which re-runs all 832 directions with `--confirm` and a negative control (masses x0.985 must be refused) and writes
`out/receipt.json`. Compare its `candidate_digest` and `status` with `check2/receipt.json`.

## Relation to earlier bundles

Bundles published before 2026-10-06 (n18 L=4.70, n18 L=4.704, n19 L=4.8229) carry the full per-angle record of a shipped
C++ verifier plus its replay (about 24 CPU hours per certificate). Bundles from 2026-10-06 on carry the second-system
check above instead (minutes per certificate); their candidates are in the same format and can still be run through the
shipped verifier of the earlier bundles.

## Pre-publication check

Before publication the bundle's candidate was checked again with the independently implemented `sqverify_fast` (jlevy/squares, adapted to read the declared net; source digest `ab6e33e164db`) on a fresh Ubuntu 24.04.5 LTS (x86_64), Rust 1.98.0 machine, from the source in `check2/src/`: 832/832 directions VERIFIED in 1411 s, and the control (every mass x 0.985, 32 directions) was refused in 32 directions. The tarball's SHA-256 and all its file hashes were checked first. The receipt is `verification/prepublication-receipt.json`.
