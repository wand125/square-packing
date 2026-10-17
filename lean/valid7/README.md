# Valid7 in the Lean kernel, version 2: s(k² − 3) = k for every k ≥ 6

**This is version 2.** Version 1 is the kernel check in
[evand/square-packing](https://github.com/evand/square-packing) PR #6 (`lean/VALID7.md`), with its
certificates in the release
[`data/valid7-lean-certs-v1`](https://github.com/wand125/square-packing/releases/tag/data/valid7-lean-certs-v1).
Version 2 re-checks the same theorem from the same certificates with the method of the ValidTilt9 check
([`problems/square-lower-bounds/certificates/k2m4_n77_L9/lean/`](../../problems/square-lower-bounds/certificates/k2m4_n77_L9/lean/)). What changed is listed under [Differences from version 1](#differences-from-version-1).

`Sqpack/V7/Main.lean` (generated) proves, in namespace `SquarePacking.LemmaELeaf`,

```lean
theorem valid7 : Bentz.Valid7
theorem bentz : ∀ k : ℕ, 6 ≤ k → minSide (k ^ 2 - 3) = k
theorem validTilt7 : Bentz.ValidTilt7
```

with (`Axioms7.lean`; the same lines are in `expected/`)

```
'SquarePacking.LemmaELeaf.valid7' depends on axioms: [propext, Classical.choice, Quot.sound]
'SquarePacking.LemmaELeaf.bentz' depends on axioms: [propext, Classical.choice, Quot.sound]
'SquarePacking.LemmaELeaf.validTilt7' depends on axioms: [propext, Classical.choice, Quot.sound]
```

No `sorry`, no `native_decide`, no new axioms. Every generated module is a `decide +kernel` check.

This folder records the run as it was done: what was run, on which machine, with which versions, how
long it took and what came out.

## Checking it yourself

1. Check out the library commit (below) and go to its `lean/` directory.
2. `./fetch.sh LEAN_DIR` downloads the generated sources from the release `valid7-lean-v2`, checks each
   asset against `release-assets.sha256`, unpacks them into `LEAN_DIR/Sqpack/V7/` and checks all 62,626
   files against `generated-sources.sha256`.
3. `python3 verify.py LEAN_DIR --jobs N` checks the library files against `library.sha256`, builds the
   library, checks every generated module with `lean -o` in import order, checks `Main.lean`, runs
   `Axioms7.lean` and compares its output with `expected/statement.txt` and `expected/axioms.txt`. It
   prints `VERIFIED` only when every module returned 0 and both comparisons agree.

The recorded run used about 800 CPU hours and at most 37 GB for one module (see below); `--jobs N` should
leave that much memory per job.

## What is proved and where the statement comes from

`Bentz.Valid7`, `Bentz.ValidTilt7` and the reductions `Bentz.valid7_of_tilt` and `Bentz.bentz_of_valid7`
are Evan Daniel's, in evand/square-packing (MIT licence): `lean/Sqpack/ValidSplit7.lean` and
`lean/Sqpack/Bentz.lean`. The certificates are the 9,800 per-root certificates of version 1 (the k2m3 run
`qx2_zm` run V3), unchanged: they were downloaded from `data/valid7-lean-certs-v1` and every file matched
its `v7cert.sha256` line.

### The Lean library used

The library is the commit `c5c7f00` of branch `validtilt9-kernel` of wand125/square-packing, the head of
evand/square-packing PR #8 (ValidTilt9). It is upstream `3f004b7` plus the ValidTilt9 files; for Valid7
the relevant additions are:

- `Sqpack/RowMinN.lean` (new): `rmChk`, the row-minimum check of `RowMinK.rmLoop` computed on
  natural-number digits, and `rmChk_sound : rmChk … = true → rmLoop … = true`;
- `Sqpack/LemmaEKM.lean`: calls `rmChk` where upstream calls `rmLoop`, with `rmChk_sound` as one step of
  its proof. No statement changes. The purpose is kernel speed.

`library.sha256` lists the 58 files in the import closure of `Main.lean` and the generated modules, plus
`lakefile.toml`, `lake-manifest.json` and `lean-toolchain`. In the run, the checkout had no changes to tracked
files.

## How the proof is organised

- The D4 root `[0, 7/2]² × (0, 1/2]` is cut into the 9,800 root cells of run V3. Root `N` is
  `Sqpack/V7/RNNNNN.lean` (theorem `root_NNNNN : CovT …`).
- The leaves of root `N` are in `Sqpack/V7/RNNNNN/`. A leaf whose rows hold at most 800 pair theorems is
  one module (data and rows). A larger leaf is a data module and row-group modules of 20 pair theorems
  each (`…_gJ`).
- `Main.lean` (from the library's `scripts/gen_main.py`, unchanged) glues the 9,800 root theorems with
  `CovT.splitX`, `splitY` and `splitU`, then applies `validTilt_of_tree`, `box7Cover_eq_mcoverP`,
  `Bentz.valid7_of_tilt` and `Bentz.bentz_of_valid7`.

## Differences from version 1

| | version 1 (PR #6) | version 2 (this folder) |
|---|---|---|
| certificates | `data/valid7-lean-certs-v1` | the same files |
| leaves | as in the certificates; the roots of `v7_xroots.txt` in X mode (`LemmaELeafX`), the others not | re-certified with rows' minima sub-bins and checked in X mode; see below |
| row minimum in the kernel | `rmLoop` | `rmChk` (`RowMinN.lean`) |
| modules | `--chunk 40` | merged leaves up to 800 pair theorems, else groups of 20 |
| statement and axioms | as above | the same lines |
| CPU time of the run | about 6,650 CPU hours (the root checks, from the release certificates) | 798 CPU hours (including 19.4 for re-certification) |

### The leaves

The re-check re-certified every leaf of every published certificate with the rows' minima sub-bins of the
ValidTilt9 check, and checked those leaves in X mode. When a leaf could not be re-certified, its published
certificate was used unchanged, in the mode version 1 used for its root. Lemma-K leaves were kept as they
were.

| leaves | count |
|---|---|
| re-certified (X mode) | 27,703 |
| published certificate kept (164 roots) | 302 |
| Lemma K, kept | 55 |
| total | 28,060 |

The 302 kept leaves use the same certificates and the same mode as in version 1.

### Why 800

Merging a leaf into one module saves the cost of importing its data once per row group. On 20 heavy leaves
(2026-10-16), merging was 1.09 to 1.39 times faster up to 800 pair theorems, with peak memory at most 19 GB.
Above 800 the gain fell to 1.03 times. In a trial of 5 roots with every leaf merged, one leaf of
1,946 pair theorems took 964 s and 71 GB. That trial's output was discarded and the run started again with
the threshold 800.

## The recorded run

All dates are UTC.

### Machine and versions

One Google Cloud c4a-highmem-48 Spot VM (48 Arm vCPUs, 376 GB, 350 GB disk), Ubuntu 24.04, Lean v4.33.1,
Python 3.12.

### Steps per root

The driver ran these steps for each root, admitting jobs by free memory (α 0.8, floor 40 GB, at most 48):

1. re-certify the root (`regen_root.py`): every leaf by `regen_m.sub_m`, keeping the published
   certificate when that fails;
2. write the Lean sources (`emit_v7r.py --chunk 20 --merge-max 800`);
3. `lean -o` of every leaf module, then every row group, then the root module.

The re-certification and emit scripts are not part of this bundle; the generated sources are, and
`verify.py` checks them as they are.

### The driver change

On 2026-10-16 at 05:50, 13 minutes after the start, the driver was replaced by one that differs only in the
memory it expects for a leaf data module (14 GB instead of 20 GB). The old driver had kept the machine at
about half load. It was stopped from issuing new jobs, its running jobs finished, and the new driver
started after them. The task markers before and after the change agree (none lost). The steps, scripts,
library and outputs are the same.

### Time and memory

The run took 29.4 hours, from 2026-10-16 05:39 to 10-17 11:01. 82,233 tasks returned 0. No task failed
and none ran out of memory.

| step | tasks | CPU hours | peak memory |
|---|---|---|---|
| re-certification | 9,800 | 19.4 | 0.4 GB |
| writing sources | 9,806 | 0.3 | 0.2 GB |
| leaf modules | 28,061 | 639.3 | 37.0 GB |
| row groups | 24,765 | 127.3 | 35.3 GB |
| root modules | 9,801 | 11.4 | 7.8 GB |
| `Main.lean` | 1 | 0.01 (38 s) | 50.6 GB |
| `Axioms7.lean` | 1 | 0.01 (30 s) | 50.6 GB |

A few tasks were counted twice because they ran again around the driver change.

`Main.lean` was first started without the Lean toolchain on its `PATH` and returned 127 without checking
anything. It was started again with the driver's environment and returned 0; that is the run recorded here.

## Files

- `README.md`, `fetch.sh`, `verify.py`, `Axioms7.lean`, `expected/statement.txt`, `expected/axioms.txt`.
- `library.sha256`: the library files.
- `generated-sources.sha256`: one line per generated file (62,626 files, paths relative to `lean/`).
- `release-assets.sha256`: the release assets.
- `receipts/`: the run's logs of `Main.lean` and `Axioms7.lean`.

Release `valid7-lean-v2` assets:

- `v7-sources.tar.zst`: the generated sources (`Sqpack/V7/R*` and `Main.lean`).
- `v7r-certs.tar.zst`: the re-certified per-root certificates (Python pickles; load them only after
  checking the sums).
- `v7r-logs.tar.zst`: the driver's task log and per-task logs.

Machine names, user names and local paths were replaced in the logs before publication.
