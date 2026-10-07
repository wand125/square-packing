# Lean 4 proofs: unit squares in an equilateral triangle, n = 2, 3, 4, 7, 11, 16, 22, 29, and a lower bound for n = 37

Kernel-checked proofs of

```lean
theorem minSideTri_two   : minSideTri 2 = 2 + 2 / Real.sqrt 3
theorem minSideTri_three : minSideTri 3 = 3 / 2 + Real.sqrt 3
theorem minSideTri_four  : minSideTri 4 = 3 + 2 / Real.sqrt 3
```

`minSideTri n` is the infimum of the sides `s` for which `n` closed unit squares, at any positions
and angles, fit in the equilateral triangle `tri s` (vertices `(0,0)`, `(s,0)`, `(s/2, s√3/2)`)
with pairwise disjoint interiors.

`#print axioms` shows only `propext`, `Classical.choice` and `Quot.sound` (see `Axioms.lean`).
There is no `sorry`, no `native_decide` and no new `axiom`.

## Trusted base

- The Lean kernel, Lean core and Mathlib.
- The definitions in the statements: `sq` and `sqInt` (closed and open square; copied from
  evand's Lean, see below), `tri`, `PacksTri`, `minSideTri`.

Everything else is proved. In particular the Python generator in `gen/` and both Python
checkers of the paper (`checker/`, `checker2/`) are not trusted. The generator only proposes
data, and every piece of data is re-checked by the kernel (`decide +kernel`).

## How the proof is organised

| file | content |
|---|---|
| `Sqtri/Evand.lean` | Copied from evand/square-packing (commit `6e1223c`, `s12/lean/Sqpack`, MIT, see `UPSTREAM-LICENSE.txt`). Includes `sq`, `sqInt`, `packing_le_weight`, the `u = tan(θ/2)` form of "p is in the square" (`mem_sq_iff_gval`), `sq_add_pi_div_two` and `coverA`/`coverW`. |
| `Sqtri/Poly.lean` | Exact arithmetic in `ℚ(√3)` (pairs of rationals) with an exact sign test (`nonnegB_sound`, `nonnegB_complete`); polynomials in `u` and forms affine in the centre. |
| `Sqtri/Check.lean` | The certificate checker `check` and its soundness `check_sound`. |
| `Sqtri/Geom.lean` | From the checker's forms to geometry. Admissibility gives nonnegative forms (`adm_nonneg`). Nonnegative capture forms put the point in the square (`mem_sq_of_captured`). Angles reduce to `u ∈ [0,1]`. `unavoidable_of_checks` puts these together. |
| `Sqtri/MinSide.lean` | `PacksTri`, `minSideTri`, and the lower-bound argument `le_of_unavoidable`. |
| `Sqtri/Upper.lean` | Exact tests for "a square with centre and (cos, sin) in `ℚ(√3)` lies in `tri L`" and "two such squares have disjoint interiors" (a separating edge normal). Both come with soundness proofs. |
| `Sqtri/Data/N{2,3,4}/` | The generated certificates: one kernel-checked theorem per leaf (`Leaves*.lean`), glued along the tree by `check_sx`/`check_sy`/`check_su`/`check_lin` (`All.lean`). |
| `Sqtri/Main.lean` | The three theorems. |

### Lower bound

1. **Scaling.** Suppose `n` unit squares with disjoint interiors fit in `tri s` with `s < v`.
   Scale the whole picture by `v/s > 1`. This gives `n` squares of side `v/s` in `tri v`, still
   with disjoint interiors. The concentric unit squares are then pairwise disjoint closed squares
   in `tri v` (`packing_le_weight`).
2. **Unavoidable set.** The certificate's weighted points meet every closed unit square in
   `tri v` with total weight ≥ 1, and the total weight is < n. So `n ≤ W < n`, a contradiction.
3. **Checking the unavoidable set.** A pose is a centre `(x, y)` and `u = tan(θ/2) ∈ [0, 1]`.
   The square has period π/2, so this covers every angle. The range `[0,1]` is cut at
   `u = 2 − √3` and `√3/3` (θ = π/6, π/3), because margin-zero contacts occur exactly there.
   On each of the three bins a tree splits pose space:
   - at values of `x`, `y` or `u`, or
   - by the sign of an affine form.

   Every leaf carries a **Farkas–Bernstein certificate**: a polynomial identity
   `Σ c_e · (u − U0)^i (U1 − u)^(d−i) · h_e = target`. Here
   - every `c_e ≥ 0` lies in `ℚ(√3)`;
   - each `h_e ≥ 0` is a hypothesis form: one of the 12 admissibility forms (each square vertex
     lies in the triangle), a side of the centre box, or a split form (or `h_e = 1`);
   - `target` is one of the four side conditions of "point p is in the square", times `1 + u²`.

   Every term is `≥ 0` on the leaf's region, so the target is `≥ 0` there. For an empty leaf
   the identity is `Σ … + 1 = 0`, which is impossible. The kernel checks each identity
   coefficient by coefficient over `ℚ`.
   - No symmetry reduction and no chord-pair lemma are used.
   - The n = 4 family in which the captured point switches is handled by splitting on the sign
     of a capture form.

### Upper bound

Explicit packings with centres, cosines and sines in `ℚ(√3)`:

- n = 2: two squares side by side on the base.
- n = 3: Friedman's pinwheel, at angles 0, π/6, π/3 (equivalently 0, 2π/3, 4π/3).
- n = 4: three squares on the base and one on top.

Containment is checked at the four vertices. A linear function is `≥ 0` on a square once it is
`≥ 0` at its vertices. Disjointness is checked with an edge normal of one of the two squares as
a separating direction; the squares may touch.

## Build

Lean 4.33.1 and Mathlib v4.33.1 (`lean-toolchain`, `lake-manifest.json`).

```sh
lake exe cache get                     # Mathlib oleans
python3 scripts/fetch_data.py M6 M7 M8 M9   # the large certificate data, checked against data/MANIFEST-*.txt
for d in N2 N3 N4 M4 M5 M6 M7 M8 M9; do      # leaf files, at most 4 Lean processes (about 9 GB each)
  scripts/build_data.sh $d 4
done
lake build                             # everything else, and the theorems
lake env lean Axioms.lean
lake env lean AxiomsSeries.lean
```

A full build with the data of n = 16 and n = 37 took about 4 hours on a 16-vCPU machine and
about 22 GB of disk (Mathlib included). The data of n = 22 and n = 29 adds about 2.5 hours, and
up to about 8 GB of build output each. With little disk, check one theorem at a time: for
example `scripts/build_data.sh M8 4` and then `lake build Sqtri.Series.M8`. Afterwards,
`.lake/build/{lib/lean,ir}/Sqtri/Data/M8` can be deleted before the next dataset.

The data for n = 16, 22, 29 and 37 (`Sqtri/Data/M6/` … `Sqtri/Data/M9/`) is too large for the
repository. It is published as the release assets `tri-lean-M6.tar.xz` … `tri-lean-M9.tar.xz`
(release `lean-data-v1`), with `SHA256SUMS`.

`scripts/fetch_data.py` (Python standard library only) does the following:
1. downloads the archives and `SHA256SUMS`;
2. checks each archive against `SHA256SUMS`;
3. extracts only regular files of `Sqtri/Data/<dataset>/`;
4. checks the exact file set and every sha256 against `data/MANIFEST-<dataset>.txt`;
5. only then puts the directory in place.

The header of each MANIFEST records the certificate's sha256 and the generator settings.
The data can also be regenerated with `gen/` (see below). The kernel is the only trusted
part: the scripts only make sure that the files you build are the published ones.

## Regenerating the certificates

```sh
cd gen
uv venv .venv && uv pip install --python .venv/bin/python gmpy2 numpy scipy
.venv/bin/python tree.py ../../certificates/n4/n4_cert.json --max-depth 26 --out out/n4.json
.venv/bin/python emit2.py out/n4.json ../../certificates/n4/n4_cert.json N4 ../Sqtri/Data/N4
```

A clean build of this project (Mathlib from the cache) took 9 minutes of wall time on a
16-vCPU Linux machine. The kernel certificates account for most of it: about 12 CPU-minutes for
n = 3 and 26 CPU-minutes for n = 4. The largest single process used 8.8 GB
(`logs/build_clean.log`, `logs/axioms.txt`).

The generator searches for multipliers with a floating-point LP (HiGHS) and then solves exactly
over `ℚ(√3)` (a small exact simplex). Only the exact result is written.

| n | points (weight) | leaves | of which empty | tree generation |
|---|---|---|---|---|
| 2 | 1 (1) | 3 | 0 | < 1 s |
| 3 | 7 (1/3 each) | 86 | 42 | ≈ 1 min |
| 4 | 3 (1 each) | 240 | 36 | ≈ 2.5 min |

## The series n = T(m−1) + 1 in a triangle of side m + 2/√3

```lean
theorem minSideTri_7   : minSideTri 7  = 4 + 2 / Real.sqrt 3          -- Sqtri/Series/M4.lean
theorem minSideTri_11  : minSideTri 11 = 5 + 2 / Real.sqrt 3          -- Sqtri/Series/M5.lean
theorem minSideTri_16  : minSideTri 16 = 6 + 2 / Real.sqrt 3          -- Sqtri/Series/M6.lean
theorem minSideTri_22  : minSideTri 22 = 7 + 2 / Real.sqrt 3          -- Sqtri/Series/M7.lean
theorem minSideTri_29  : minSideTri 29 = 8 + 2 / Real.sqrt 3          -- Sqtri/Series/M8.lean
theorem le_of_packs_37 : ∀ s, PacksTri 37 s → 9 + 2 / Real.sqrt 3 ≤ s  -- Sqtri/Series/M9.lean
```

All six are kernel-checked with only the standard axioms (`AxiomsSeries.lean`,
`logs/axioms_series.txt`).

- **Upper bound (n = 7, 11, 16, 22, 29).** Rows of axis-parallel unit squares: `floor(m − 2k/√3)`
  squares in row `k` (height `[k, k+1]`), each row pushed against the left side. `axisPackB`
  checks in one Boolean test that all squares are axis-parallel, lie in the triangle, and are
  pairwise separated. `packs_of_axisPackB` is its soundness.
- **n = 37 is a lower bound only.** At side 9 + 2/√3 the rows packing holds 36 squares, not 37.
  The theorem says that 37 unit squares do not fit in an equilateral triangle of side less than
  9 + 2/√3 ≈ 10.15470.
- **Lower bounds.** The same Farkas–Bernstein leaf certificates as for n = 2, 3, 4, for the
  lattice certificates `lattice_m{4,…,9}.json`. Every point has weight 1; the points form a
  triangular patch of the unit triangular lattice with side `m − 2`, centred at the centroid of
  the container. None of them uses a symmetry reduction or a chord-pair lemma.

| theorem | certificate | points | leaves | leaf files | data |
|---|---|---|---|---|---|
| n = 7 | `lattice_m4.json` | 6 | 1,013 | 51 | in the repository |
| n = 11 | `lattice_m5.json` | 10 | 1,863 | 94 | in the repository |
| n = 16 | `lattice_m6.json` | 15 | 3,753 | 188 | release asset (4.1 MB) |
| n = 22 | `lattice_m7.json` | 21 | 6,884 | 345 | release asset (9.2 MB) |
| n = 29 | `lattice_m8.json` | 28 | 8,661 | 434 | release asset (10.4 MB) |
| n = 37 | `lattice_m9.json` | 36 | 9,776 | 489 | release asset (12.2 MB) |

### How the certificates are laid out

Checking a whole tree with a single `decide +kernel` is very slow. So `gen/emit2.py` writes
every leaf as its own declaration: `def lfK : Tree` and `theorem leafK : check … lfK = true`,
20 leaves per file in `Sqtri/Data/M*/Leaves*.lean`. `All.lean` rebuilds the tree from the
leaf names, and glues the leaf theorems along it with `check_sx`, `check_sy`, `check_su` and
`check_lin` (`Sqtri/Check.lean`).

Building the leaf files took about 60–90 s and about 9 GB of memory each. Lake has no option to
limit parallel jobs, so `scripts/build_data.sh` builds the leaf modules one Lake invocation each,
at most four at once. On a 16-vCPU machine the n = 37 leaves took about 10.9 hours of process time
(about 2.7 hours of wall time), and the final assembly took 11 minutes. Large trees also need
`set_option maxHeartbeats 0` and a `noncomputable` tree skeleton in `All.lean`; `gen/emit2.py`
writes both.

### Generator changes

These changes affect data generation only, not the trusted base.

- `gen/tree.py` tries every candidate point in turn, rather than only the heaviest.
- The number of linear splits along one branch is configurable (`MAX_LIN`).
- Some regions have no floating-point sample: very thin regions between two nearly coincident
  split lines, or a region on a line `f = 0`. For these, the candidate points are chosen from
  samples taken without the split forms. The split forms stay in the LP as hypotheses.
- `gen/cert.py`: when the floating-point LP fails numerically, the exact simplex over Q(√3) is
  run on the whole LP, with a larger iteration limit.
  - An infeasible verdict of a fallback floating-point method is never trusted.
- `gen/cert.py` compares the coefficients of the identity in the rescaled variable
  `t = (u − U0)/(U1 − U0)` instead of `u`.
  - On very narrow angle bins, the basis `(u − U0)^i (U1 − u)^(d−i)` written in powers of `u`
    is badly conditioned, and the floating-point LP wrongly reported some feasible boxes as
    infeasible (n = 29).
  - A linear change of variable keeps every identity, so the multipliers and the Lean check are
    unchanged.
- `gen/repair.py` regenerates only the failed leaves of a tree, with more depth and more linear
  splits. The settings of each dataset are in the header of its `data/MANIFEST-*.txt`.
  - n = 37: `--max-depth 32`, then a repair with `--extra-depth 8 --max-lin 8`.
  - n = 22: a second repair with `--extra-depth 12 --max-lin 12`.
  - n = 29: a repair with the rescaled LP.
- `gen/series.py` writes the rows packing and the theorem statement for a given `m`.
