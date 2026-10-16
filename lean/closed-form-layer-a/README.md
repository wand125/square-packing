# Closed-form lower bound: Lean layer A

**This is a conditional theorem. Layer B, checking every leaf of the certificate
records in Lean, is not done.** The assumption `LocalCovers` for every interval
is precisely the local coverage assertion that the records of the published
computer-assisted closed-form certificate check, leaf by leaf. This bundle
proves the implication from those assumptions, not those assumptions themselves.

The main theorem is `ClosedForm.closed_form_of_covers`: assuming `LocalCovers`
for every one of the 34 intervals, for every natural number N >= 49,
`a N <= UnitSquarePacking.minSide N`. Its production proof uses only the
standard axioms `propext`, `Classical.choice`, and `Quot.sound`.

```lean
ClosedForm.closed_form_of_covers
  (hcov :
    ∀ (i : Fin 34), ∀ δ ∈ ClosedForm.I i, ClosedForm.LocalCovers (ClosedForm.family i) (ClosedForm.familyRight i) δ)
  (N : ℕ) : 49 ≤ N → ClosedForm.a N ≤ UnitSquarePacking.minSide N

```

See the [computer-assisted certificate and records](../../problems/closed-form/)
([repository link](https://github.com/wand125/square-packing/tree/main/problems/closed-form)).
The local coverage hypothesis uses the four left, straddle, top and right
regions, the parameter range [-13/32, 7/16], and admissible centres as defined
in `ClosedForm/Measure.lean` and the linked specification. The records are not
included or replayed by this Lean bundle.

The generated sources are in the Release `closed-form-lean-layer-a-v1`.

## Proof structure

1. **Definitions.** Family, Measure and PublishedDefs encode exact rational
   segment families, the local and global measures, the 34 intervals, and the
   certified affine lines. StatementCore defines the closed-form bound `a`.
2. **Algebra.** Algebra reduces the target inequality to a strict measure
   deficit, with the floor/square-root decomposition of N.
3. **Measure principle and area bound.** Principle connects the measures to
   Evan Daniel's packing specification and measure obstruction. Area establishes
   the square-root area bound used at the boundary cases.
4. **Total mass.** Mass, the structure bridges and StatementCore prove the
   global mass formula `(k + delta)^2 - 4 * saving`, including terminal mass.
5. **Structural checks.** Each interval has small kernel-checked integer
   canonical tables, support and nonnegativity checks, permutation witnesses
   and symbolic cross-multiplication links to the rational family data.
   `PublishedStructure` assembles all 34 interval results.
6. **Saving.** Saving and SavingCertificate prove affinity and endpoint
   sufficiency. Each interval has an exact integer mass computation, two
   integer endpoint comparisons and an assembly. `PublishedSaving` assembles
   the 34 results, including all 68 endpoint comparisons.
7. **Reduction.** Rotation and orientation symmetry, closed local windows,
   wall seams and periodic shifts transport mass. They reduce k >= 7 to k = 7
   and local coverage to global coverage. The strict deficit then gives the
   conditional main theorem for N >= 49.

The production graph is `ClosedForm/FinalAudit.lean`, importing the two proved
providers and `ClosedForm/Cloud/Statement.lean`. It prints axioms for
`published_structure`, `published_saving`, `total_mass`, `covers_k_of_covers7`
and `closed_form_of_covers`. All five have exactly the three standard axioms
in the recorded final audit.

**The default local graph is not the production verification target.**
`StatementCore.lean` retains two local provider placeholders; its Algebra,
Statement, Audit and the default `Sqpack.lean` entry point therefore report
`sorryAx`. They are preserved as hand-written source and provenance. The
Cloud modules replace those providers while retaining the downstream proofs.
The scheduler rejects any dependency on that default placeholder graph.
Do not use a plain `lake build` as evidence for the production theorem.

## Files and generated-source boundary

`source-inventory.tsv` classifies every ClosedForm source individually.
The repository contains 34 hand-written ClosedForm files:

- `ClosedForm/Algebra.lean`
- `ClosedForm/Area.lean`
- `ClosedForm/Audit.lean`
- `ClosedForm/CanonicalBridge.lean`
- `ClosedForm/CornerBridge.lean`
- `ClosedForm/Family.lean`
- `ClosedForm/GridCertificate.lean`
- `ClosedForm/IntegerMeasureBridge.lean`
- `ClosedForm/IntegerStructure.lean`
- `ClosedForm/LocalReduction.lean`
- `ClosedForm/LocalWindow.lean`
- `ClosedForm/Localization.lean`
- `ClosedForm/Mass.lean`
- `ClosedForm/Measure.lean`
- `ClosedForm/MeasureBridge.lean`
- `ClosedForm/Orientation.lean`
- `ClosedForm/PeriodicShift.lean`
- `ClosedForm/Principle.lean`
- `ClosedForm/PublishedDefs.lean`
- `ClosedForm/Reduction.lean`
- `ClosedForm/ReflectionBridge.lean`
- `ClosedForm/Rotation.lean`
- `ClosedForm/Saving.lean`
- `ClosedForm/SavingCertificate.lean`
- `ClosedForm/Statement.lean`
- `ClosedForm/StatementCore.lean`
- `ClosedForm/StructPermutation.lean`
- `ClosedForm/StructSupport.lean`
- `ClosedForm/StructuralSoundness.lean`
- `ClosedForm/Structure.lean`
- `ClosedForm/StructureDefs.lean`
- `ClosedForm/WallPeriod.lean`
- `ClosedForm/WallPlacement.lean`
- `ClosedForm/WallSeam.lean`

In particular, Audit is hand-written; PublishedDefs, Saving and
SavingCertificate are hand-written. StructuralI01 is generated even though
its header describes only a compatibility import.

The Release archive contains exactly 1,201 generated Lean files:

| Path | Files | Role |
| --- | ---: | --- |
| `ClosedForm/Data/` | 36 | I01–I34 families, Families and Intervals |
| `ClosedForm/Struct/` | 1,022 | Split structural certificates |
| `ClosedForm/Saving/` | 136 | Four saving modules per interval |
| `ClosedForm/Cloud/` | 3 | Production copies of StatementCore, Algebra, Statement |
| `ClosedForm/PublishedStructure.lean` | 1 | Structural provider |
| `ClosedForm/PublishedSaving.lean` | 1 | Saving provider |
| `ClosedForm/StructuralI01.lean` | 1 | Default local compatibility import |
| `ClosedForm/FinalAudit.lean` | 1 | Production axiom audit |

Generated Lean sources belong to the Release as `generated-sources.tar.xz`,
not to the repository. `generated-sources.sha256` has one SHA-256 line per
file. `scripts/fetch.sh` downloads the archive and checks every file against
that list. `.gitignore` excludes the archive and the extracted sources.
Generators exist but are not part of the bundle. The original JSON inputs,
Bench experiments and compiled artifacts are also excluded.

`Sqpack/` is unchanged upstream source, including upstream S32Data. The local
`Sqpack.lean`, active Lake file, pinned manifest/toolchain, original upstream
TOML, `UPSTREAM.md`, `UPSTREAM.sha256`, and upstream MIT licence are included.
`expected/statement.txt` is the full printed theorem type; `expected/axioms.txt`
is the full main-theorem axiom line from the recorded production final audit.
`receipts/` contains the run evidence; `receipts.sha256` checks those bytes.

## Recorded runs

All proof runs used Lean **v4.33.1**, Mathlib **v4.33.1**, commit
`0df444a360eaa60ab8c11dca51a86af692955474`, with the transitive dependencies
pinned in `lake-manifest.json`. The development and cloud runs were recorded
on 2026-10-16–17. Machines are described here as **a laptop (Apple M4, macOS)**
and **a cloud VM with 48 Arm vCPUs and 376 GB**.

The laptop ran one Lean process at a time, four threads, requested nice 10,
and a 600-second per-process limit. macOS refused the priority adjustment;
the logs retain that diagnostic.

| Laptop check | Result | Sum of file wall seconds | CPU seconds | Maximum file RSS (bytes) |
| --- | --- | ---: | ---: | ---: |
| Unsplit I01 kernel benchmark | Timed out | 600.030 | Not recorded | Not reliably measured |
| Earlier I01 structural assembly | Passed | 42.155 | See historical receipt | 6,609,190,912 |
| Split I01 structure, 34 files | Passed | 940.335 | 858.135 | 8,583,069,696 |
| Split I04 structure, 35 files | Passed | 881.663 | 831.199 | 8,723,611,648 |
| I01 saving, 4 files | Passed | 82.084 | 81.956 | 6,109,134,848 |
| I04 saving, 4 files | Passed | 97.857 | 88.253 | 6,144,409,600 |

The unsplit attempt was terminated at 600.03 seconds; its wrapper RSS is not
a Lean peak-memory measurement. It was not a successful check. I04 is the
largest original family input. Split totals include separate compiler startup
and serialization and exclude shared prerequisites and development attempts;
they are not the duration of one Lean process. The 2–3 GB per-file planning
target was not attained. The retained local measurement history has six
failed development entries (two Check01 attempts, StructPermutation, Fields,
Geometry, and Saving.I01.Mass); all final sample files passed.
`development-runs.tsv` additionally lists the recorded individual development
outcomes, including failures, from the retained measurement JSON records.

| Cloud run | Successful build entries | Sum of file wall seconds | CPU seconds | Maximum file RSS (bytes) |
| --- | ---: | ---: | ---: | ---: |
| Initial 34-interval structure | 1,083 | 5,825.043 | 5,662.410 | 12,061,859,840 |
| Saving/reduction/final audit follow-up | 226 | 1,515.233 | 1,092.070 | 9,861,611,520 |
| Combined recorded history | 1,309 | 7,340.276 | 6,754.480 | 12,061,859,840 |

The cloud run logs show up to 12 active compiler processes, each requesting four threads,
`nice -n 10 lake env lean -o ...`, with a 600-second deadline per process.
The follow-up logged 1,013 hash-matched reused modules; 70 modules from the
previous graph were rebuilt alongside 156 additional modules. There are
1,239 distinct production modules in the combined history. Both cloud runs
have no failures or timeouts. The initial CPU total is approximately 1.57
hours; combined CPU is approximately 1.88 hours. Summed per-file wall time is
not elapsed parallel job time; an exact overall wall duration is not asserted.

FinalAudit itself passed in **3.655 seconds**, with 2.310 user + 1.327 system
CPU seconds and 7,171,555,328 bytes peak RSS. Its five theorem reports use
only the standard axioms. Cloud RSS is wait4's maximum for the Lake/Lean
process and reaped descendants, normalized to bytes; it is not simultaneous
whole-job RSS. See `receipts/README.md` for receipt interpretation.

During bundle preparation, the default local theorem type was printed using
the installed Lean and existing dependencies, offline and sequentially.
An initial formatting attempt failed in 48.420 seconds because `pp.width`
and `pp.maxDepth` were unsupported. The corrected run passed in 19.602
seconds, with 5,738,397,696 bytes peak RSS. Its `sorryAx` output belongs to
the default graph and was not used for expected production axioms. The
statement was taken from the successful Lean output, and the expected axiom
line was copied verbatim from the historical production audit. No full cloud
rebuild or independent kernel replay was performed during bundle preparation.

## Verification

Requirements: a POSIX system with Bash, Python 3.10+ (including lzma), curl,
nice, process groups and wait4; the pinned Lean toolchain; Mathlib and its
pinned dependencies with their compiled cache. The scripts do not install
dependencies. Provision them separately before the build. Network access is
needed for the normal Release download and dependency provisioning; verification
can then run with preinstalled dependencies. For an offline transfer, supply
the archive as the optional fetch argument.

After the proposed Release has been published:

```sh
bash scripts/fetch.sh
python3 scripts/verify.py
```

For the staged asset, without downloading:

```sh
bash scripts/fetch.sh generated-sources.tar.xz
python3 scripts/verify.py
```

The fetch step validates the complete archive file list and every file against
the pinned manifest before installing sources. On a suitably provisioned cloud
machine, `python3 scripts/verify.py --jobs 12` matches the peak concurrency seen in the logs;
the default is one compiler process. The production scheduler is adapted from
the actual cloud runner, removing local measurement modes and generator hooks.
Its proof targets, invocation, dependency ordering, source/dependency/output
hash resume checks and per-process deadline are retained.

The verifier builds the production graph through FinalAudit, compares the
full main-theorem axiom report with `expected/axioms.txt`, then asks Lean for
the full theorem type and compares it with `expected/statement.txt`.
It prints `VERIFIED` only if the build and both exact comparisons succeed.
New run logs and state are written under `BUILD.step7-state/`; historical
receipts are not overwritten. A timeout writes a persistent TIMEOUT marker,
stops new scheduling, and returns failure; do not erase it and silently retry.
With multiple jobs, already running workers finish under their own deadlines.

For planning, recorded per-file wall totals are about two hours sequentially
on the measured cloud hardware, including the recorded rebuilds. This is a
rough reference, not a measured fresh-build prediction. Parallel time depends
on dependency ordering and machine load. The largest measured cloud process
was about 11.24 GiB; allow at least 16 GiB for one compiler plus system/cache
headroom. Twelve workers can require roughly 135 GiB by summing measured peaks;
the recorded machine had 376 GB. Laptop times and memory are shown above.

Bundle preparation checked archive round-trip hashes, upstream integrity,
production dependency closure, script success/failure handling with simulated
commands, and public-content sanitization. Those packaging checks are distinct
from the historical Lean proof runs. No download, push or upload was performed.

## Credits

Closed-form layer A: **Hiroaki Hosono (wand125)**.
Upstream Sqpack files: **Evan Daniel**, MIT licence.
See `UPSTREAM.md` and `LICENSE-evand-square-packing`.
