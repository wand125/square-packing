# s(77) = 9 (computer-assisted; not yet independently reviewed)

Let `s(n)` be the least side of a square that holds `n` non-overlapping unit squares with
arbitrary orientations. This directory contains a measure certificate for

```
s(77) >= 9,   hence   s(77) = 9   (the 9x9 grid packs 81 >= 77 squares).
```

By monotonicity this also gives `s(78) = 9`; that value was already known from Evan Daniel's
`k^2 - 3` series. The new statement is `s(77) = 9`, the case `k = 9` of the `k^2 - 4` series
(`s(60) = 8` is the case `k = 8`, due to Evan Daniel).

**Status.** The certificate passes three independent sweeps, listed below. It has not been
reviewed by anyone outside this project and has not been formalised in Lean.

## The argument

`n77_mixed_cover_9.txt` defines a finite nonnegative measure `mu` on the container `[0,9]^2`.
It uses Evan Daniel's "mixed 1" format: point masses plus axis-parallel segments, each segment
carrying its mass uniformly along its length. The certificate needs two facts:

1. Every closed unit square (any position and orientation) inside `[0,9]^2` has `mu >= 1`.
2. The total mass is `43347137744028965 / 2^49 = 76.999984600031... < 77`.

In a packing of 77 unit squares in a square of side `L < 9`, scale the packing up to side 9.
The squares get larger, so each enlarged square contains a closed unit square with mass `>= 1`.
The enlarged squares are interior-disjoint, so the total mass would be `>= 77`, a contradiction.
Hence `s(77) >= 9`.

The cover is invariant under the dihedral group D4 of the container. Exact invariance is checked
by `zmx2 d4` (and also by the cover reader). The `--d4` sweeps rely on this invariance; the
`zmx2 --full` sweep does not.

- Points: 28,273
- Segments: 6,420
- Coordinate unit: `1/D = 1/1000`
- Weight unit: `1/W = 2^-49`
- SHA256: `47b57cfe38cbfdbcf5320e59caffe712f4ef32df8aad42b0d7f697de6d26cdd7`

## Construction

1. **Base.** Evan Daniel's mixed cover for `s(60) = 8`:
   - file: `s12/certificates/s60/s60_mixed_cover_8.txt` in
     [evand/square-packing](https://github.com/evand/square-packing), MIT licence;
   - SHA256: `2d0e456ea86cceeadc92d9f8fa7d468ba570a16d00d7343ebfbfb0b3b3b12a41`;
   - container `[0,8]^2`, total `748233441/12500000`.
2. **Central band insertion** (container `8 -> 9`). Cut at `a = 4` in both coordinates:
   - coordinates `< 4` stay; coordinates `> 4` move by `+1`.
   - Mass lying exactly on a cut line is split in halves between `x = 4` and `x = 5`, and likewise
     for `y`. A point on both cut lines is split in quarters.
   - A segment crossing a cut is split there into two pieces, each keeping its share of the mass in
     proportion to its length; each piece moves rigidly with its side.

   On each of the four corner blocks, the new measure is therefore a translate of the old one.
   A unit square that does not meet the inserted cross-shaped band `([4,5] x [0,9]) ∪ ([0,9] x [4,5])`
   lies in one corner block, so it inherits its capture from the base cover.
3. **Band mass.** Unit squares that meet the band need extra mass. We added a D4-symmetric measure
   `nu` of mass about 16.43: about 8.08 in points and about 8.34 in segments on integer lattice lines.
   - Shapes: segments are cut into pieces of length 1/8; support lies in `[5/2, 13/2]`.
   - Method: a linear program over D4 orbits, alternated with a counterexample exchange. In each
     round, poses that `zmx2` could not certify were added as LP rows. The loop converged in 31 rounds.
4. **Scaling.** The whole measure (base plus `nu`) was multiplied by `77/M * (1 - 2*10^-7)`, where `M`
   is its unscaled total. Weights were rounded up on the unit `2^-49`, so the total stays just below 77.
5. **Points on lattice lines replaced by short segments.** 84 points of `nu` lay exactly on integer
   lattice lines that also carry segment mass.
   - Each was replaced by a segment of length `2/1000` on the same line, with the same centre and the
     same mass. A point at a crossing of two such lines was split half and half between the two lines.
   - Counts changed as follows: points 28,357 -> 28,273; segments 6,320 -> 6,420.
   - The total mass and the D4 invariance are unchanged.

   **Why this step is needed.** In `--cert-mode`, `zm_mixed.py` disables its Corollary T'. As a result,
   a point lying on a loaded line is not counted as part of that line's mass. Before the replacement,
   `zm_mixed` left 291 boxes uncertified, all near the axis-aligned unit square
   `[1,2] x [3,4]`, which sits exactly on lattice lines. In those boxes the certified lower bound fell
   short of 1 by `1.1e-5` to `2.7e-3`, while the true minimum there is about 1.0116. `zmx2` verified both versions. After the replacement, all three
   sweeps pass.

The first comment line of the cover file is a leftover working note from step 5. It is kept
unchanged so that the file hash matches the hashes recorded in the logs and the manifest.

## Checks

All three sweeps cover the whole container, and all three were run on the file in this directory
(same SHA256). Logs are included.

| check | command | result | roots | uncertified | time |
|---|---|---|---|---|---|
| zmx2, D4-reduced | `zmx2 cert COVER --d4 --pair-points` | `VERIFIED-D4` | 8,100 | 0 | 1,102 s wall (16 threads), 5,810,824 boxes |
| zmx2, unreduced | `zmx2 cert COVER --full --pair-points` | `VERIFIED` | 64,800 | 0 | 8,431 s wall (16 threads), 46,583,600 boxes |
| zm_mixed, exact rationals | `zm_mixed.py cert COVER --d4 --cert-mode --disj --depth 24 --pitch 1/20 --ubins 16` | `VERIFIED-D4` | 129,600 | 0 (TPTS 0) | 21,176 s wall / 337,745 s CPU (16 processes) |

- **zmx2 sweeps.** `zmx2` is a Rust checker that encloses chord endpoints in floating-point intervals.
  The unreduced sweep checks every root without using the symmetry.
- **zm_mixed sweep.** `zm_mixed.py` works in exact rational arithmetic. Its settings are the ones
  Evan Daniel used for his `s(60)` mixed cover. `TPTS 0` means no leaf was closed by line points.

Logs of these original runs:
- `zmx2_d4/run.txt`
- `zmx2_full/run.txt`
- `zm_mixed_d4/run.txt` and `zm_mixed_d4/manifest.json`

The manifest records the SHA256 of the input and of the three checker files. The per-root logs
of the original runs were not kept; the complete record of a later replay is in `record/`
(next section).

### Replay record (`record/`)

All three sweeps were replayed on 2026-10-04 with `bash verify.sh <work> 31 --full --zm` on
Linux x86_64 (32 vCPU). Every step passed and the run ended with `N77_COVER_VERIFIED`. The
record contains everything the run wrote except the upstream clone and the build output:

| file | content |
|---|---|
| `record/toolchain.txt` | upstream commit, `cargo`/`rustc` versions (1.86.0), platform, SHA256 of the built `zmx2` binary and of the cover |
| `record/d4check.txt` | output of `zmx2 d4` |
| `record/zmx2_d4_run.txt`, `record/zmx2_d4_roots.txt.gz` | `--d4` sweep: summary and per-root log (8,100 `ROOT` lines) |
| `record/zmx2_full_run.txt`, `record/zmx2_full_roots.txt.gz` | `--full` sweep: summary and per-root log (64,800 `ROOT` lines) |
| `record/zm_mixed_run.txt`, `record/zm_mixed_manifest.json`, `record/zm_mixed_roots.jsonl.gz` | zm_mixed sweep: log, manifest, per-root records (129,600) |

The replay agrees with the original runs: the same box counts (5,810,824 for `--d4`,
46,583,600 for `--full`), zero uncertified, and an identical zm_mixed census (826,120 boxes; PIECE 9,032, ADM 156,385, CHAIN 181,324,
SPLIT 97,450, EMPTY 33,669, UNCERTIFIED 0, TPTS 0). Replay times: `--d4` 703 s, `--full`
4,302 s, zm_mixed 12,287 s wall / 316,857 s CPU (31 threads or processes).
Absolute paths of the replay machine were replaced by relative ones in `zm_mixed_run.txt`,
`zm_mixed_manifest.json` and the header line of `zm_mixed_roots.jsonl` after the run; the
manifest's `records.sha256` was recomputed for the edited records file and its `note` field
gives the hash before the edit. The zmx2 files are unedited.
A new run can be compared root by root with these files.

### Checkers used (not bundled)

Both checkers are Evan Daniel's, from [evand/square-packing](https://github.com/evand/square-packing)
(MIT licence, see `s12/LICENSE` there). They are not copied here. `verify.sh` fetches them at the
pinned commit `b91d70b6ed314624c1434b628a9c7bf9a132c743` and checks these SHA256 values:

| file | SHA256 |
|---|---|
| `s12/verify2/src/bin/zmx2.rs` | `6b7f0f79466bf25c9a85f8fe2f3866de734935f0521ea188136818c2fb5b3fed` |
| `s12/search/zm_mixed.py` | `ee3e2915349b8795128417bca6414b205d526db9f01f88cd4cd32c32e8d760ac` |
| `s12/search/mixed_cover.py` | `bb89de15ecf5821dd7e1a36ebab8a50d792a406b7fb0f5cb38059f99ef74aae5` |
| `s12/search/zeromargin.py` | `640fe453c1a32f4aa580ca2b1261c6406923a4d7c131f65604a432c7fc2086ab` |

Later upstream commits change `zmx2.rs` and `zm_mixed.py`. Use the pinned commit.

`zmx2` needs Rust 1.86 or newer to build.

## Reproducing

Requirements:
- `git`;
- Python 3 with `numpy`;
- Rust >= 1.86 (`cargo`; set `CARGO=...` to pick a toolchain).

```sh
bash verify.sh /path/to/new/workdir 16            # hashes, exact total, D4, zmx2 --d4 (about 20 min)
bash verify.sh /path/to/new/workdir 16 --full     # also zmx2 --full (about 2.5 h more)
bash verify.sh /path/to/new/workdir 16 --zm       # also zm_mixed --d4 --cert-mode (about 94 CPU-hours)
```

`verify.sh` does the following, in order:
1. checks `SHA256SUMS`;
2. clones the upstream repository and checks out the pinned commit;
3. checks the checker hashes;
4. computes the exact total with the upstream reader and asserts that it is `< 77`;
5. builds `zmx2`, writes `toolchain.txt` (versions and binary hash) and checks D4 invariance
   (it requires the exact line `D4: measure invariant ...`);
6. runs the requested sweeps and checks the summary line.

The script runs under `bash` with `set -euo pipefail`, so a failing command inside a pipeline
also stops it. All logs it writes end in `.txt`, `.jsonl` or `.json`.

For the zmx2 sweeps it also checks that the per-root log has exactly the expected number of
distinct roots, each with `uncert 0` and `capped 0`.

It prints `N77_COVER_VERIFIED` only if every step passes.

## Files

| file | content |
|---|---|
| `n77_mixed_cover_9.txt` | the cover (mixed 1 format) |
| `verify.sh` | reproduction script |
| `zmx2_d4/run.txt` | zmx2 `--d4` sweep log (original run) |
| `zmx2_full/run.txt` | zmx2 `--full` sweep log (original run) |
| `zm_mixed_d4/run.txt`, `zm_mixed_d4/manifest.json` | zm_mixed sweep log and manifest (original run) |
| `record/` | complete record of the 2026-10-04 replay (see above) |
| `SHA256SUMS` | hashes of all files above |

The original logs were first published as `run.log`. The repository's `.gitignore` excludes
`*.log`, so those files were missing from a fresh clone while `SHA256SUMS` still listed them,
and `verify.sh` stopped at its first step. They are now named `run.txt`; their contents are
unchanged.

## Attribution

This result is built directly on Evan Daniel's work:
- the base cover is his `s(60) = 8` mixed cover;
- the format and both checkers are his ([evand/square-packing](https://github.com/evand/square-packing), MIT licence).

The central band insertion, the band mass `nu`, the point-to-segment replacement and the
runs recorded here are ours.
