# Lean formalization toward s(11) = T (eleven unit squares)

Work in progress on a Lean 4 formalization of the computer-assisted proof, by
**Queuing Theory #1 Fan**, that Walter Trump's 1979 packing of 11 unit squares
is optimal:

> s(11) = T ≈ 3.8770835900, where T = (6u + 4)/(1 + 2u − u²) and u is the root in
> (9/25, 37/100) of 5u⁸ − 10u⁷ − 2u⁶ + 14u⁵ + 12u⁴ − 6u³ + 2u² + 2u − 1.

The proof being formalized is
[Queuingtheorydotcom/11SquaresOptimal](https://github.com/Queuingtheorydotcom/11SquaresOptimal),
commit `f9e0de713a0949d1bc6a0fa6b59d96edf6c3d65c`. The definitions of packings
(`Packs`, `minSide`, `sq`, `sqInt`, `box`), the admissibility lemma and the
kernel-checked containment test `ptOk` come from Evan Daniel's Lean project
[evand/square-packing](https://github.com/evand/square-packing) (`s12/lean`,
commit `6e1223c`, MIT), which is fetched by the build script and not copied.

## What is kernel-checked

Every theorem below depends only on the standard axioms `propext`,
`Classical.choice` and `Quot.sound` (twelve axiom reports in `Axioms.lean`). No
`sorry`, no `native_decide`, no new `axiom`.

The general pattern is the same throughout. A checker's soundness is proved once
in Lean, and each certificate is then checked by the kernel against it.

**1. The upper bound (Trump's packing).**

```lean
theorem SquarePacking.S11Opt.minSide_le_T : minSide 11 ≤ T
theorem SquarePacking.S11Opt.minSide_lt_U : minSide 11 < 387708359002281417731 / 10 ^ 20
```

`u₀` is defined as the unique root of the polynomial in (9/25, 37/100)
(intermediate value theorem, and P' > 0 there). Every coordinate of the packing
is written as a polynomial of degree ≤ 7 in u₀ with rational coefficients. The
44 wall inequalities (11 tight) and the 55 pairwise separations (14 contacts)
are each proved as an exact polynomial identity modulo P plus the sign of the
remainder on an isolating interval of width 10⁻⁴⁰. The sign is checked by the
kernel with an interval Horner evaluator whose soundness is proved once.
Separation uses the sufficient direction of the separating-axis theorem along
an edge normal (`disjoint_of_dir`).

**2. The first baseline field certificate, `field-00`, re-proved.**

```lean
theorem SquarePacking.S11Opt.F00.field00 {n : ℕ} (ctr : Fin n → ℝ × ℝ) (ang : Fin n → ℝ)
    (hin : ∀ i, sq (ctr i) (ang i) 1 ⊆ box Ux)
    (hdisj : ∀ i j, i ≠ j → Disjoint (sqInt (ctr i) (ang i) 1) (sqInt (ctr j) (ang j) 1))
    (σ : ℕ → Fin n) (hσ : ∀ a ∈ supp, ∀ b ∈ supp, σ a = σ b → a = b)
    (hcell : ∀ a ∈ supp, InCellU a (ctr (σ a))) : False
```

No family of unit squares in [0, U]² (U = 3.87708359002281417731) with
pairwise disjoint interiors has distinct squares whose centres lie in the
closed Voronoi cells 1, 2, 4, 5, 8, 9 and 13 of the author's 16-site centre
cover (`supp`).

**3. The transfer: field-00 excludes 126 of the 2184 canonical cases.**

```lean
def SquarePacking.S11Opt.CaseExcluded (J : List ℕ) : Prop := ¬ Realizes J
theorem SquarePacking.S11Opt.F00.excluded00_all : ∀ J ∈ excluded00, CaseExcluded J
lemma  SquarePacking.S11Opt.F00.excluded00_length : excluded00.length = 126
```

`canonicalMasks` (2184 sets of 11 cells, `J ≤ halfturn J`) and the 126 sets are
the same as the author's `canonical_eleven_cell_subsets` and
`transferred_canonical_mask_indices` for field-00.

### How field-00 is re-proved

Our argument follows the author's field certificate, but it is organized so that
none of the author's numerical values need to be trusted.

- **Capacity one of majority features** (`Majority.lean`, `FieldBridge.lean`).
  Take a feature with 2k − 1 sites. Call a set TRUE for it if the set meets the
  convex hull of every k-subset of the sites. Two disjoint open convex sets
  cannot both be TRUE. Proof: separate them by a line (Hahn–Banach); one closed
  side contains k sites, and the hull of those k sites misses the set on the
  other side. This is the capacity rule of the author's `majority_hull`
  features. PROOF.md does not state it.
- **A box-tree checker** (`FieldTree.lean`). Over pose space (centre, u = tan(θ/2)
  ∈ [0, 1]), a leaf certifies one of three things for every admissible pose in
  its box:
  - the wall-clipped box is empty;
  - a Voronoi bisector excludes the box;
  - one "option" holds: for each group of the option, one candidate point lies
    in the square. This uses evand's `ptOk`.

  Soundness is proved once (`soundF`). The trees are shipped as digit streams and
  decoded in the kernel.
- **Strictness without a boundary argument** (`FieldBridge.lean`). Everything is
  checked in the world scaled by 1/s, s = 1 − 2⁻²⁰. A point in the *closed* unit
  square about c/s is, after scaling back, in the *open* unit square about c.
- **The certificate** (generated in `F00/`):
  - For each of cells 1, 5 and 9, every admissible square with centre in the
    cell does one of two things. Either it contains a witness point of every
    majority hull of one of the two features (barycentric witnesses, checked in
    the kernel), or it contains a point owned by another square.
  - For each of the 37 owned points, the point lies inside its owner's square in
    every admissible pose with centre in the owner's cell.
  - The three squares in cells 1, 5 and 9 would therefore need three TRUE
    features among two. Each feature has capacity one, so this is impossible.
- **Size.** The cover trees have 104k leaves and the ownership trees 196k. The
  kernel time is about 740 CPU seconds in total (about 2.5 ms per leaf).

**What we use from the author's data.** We use only the structure of field-00:
which sites form each feature and its threshold, which cells have positive
thresholds, and which cells are owners. We also use the 16 Voronoi sites of the
centre cover (`center-cover-symmetric-exact.json`). The sites, witness points
and owned points in our certificate are our own grid points, rounded from the
author's values. The capacity argument holds for any points, so these values
need not be trusted. Floating point is used only to choose grid points; every
claim is checked exactly by the kernel. The author's two files are downloaded by
`build.sh` from the pinned commit and checked by SHA256; they are not
redistributed here.

**4. General field certificates: the generic layer, and field certificates 3, 6 and 19.**

```lean
theorem SquarePacking.S11Opt.field_generic … : CaseExcluded (supp ++ P)
theorem SquarePacking.S11Opt.F03.excluded (P : List ℕ) … : CaseExcluded (F03.supp ++ P)
theorem SquarePacking.S11Opt.F06.excluded …
theorem SquarePacking.S11Opt.F19.excluded …
```

All 59 of the author's baseline field certificates use only `majority_hull`
features, but several also carry weighted point sites, thresholds above one and
majority features with k up to 4. `FieldGen.lean` proves the general case once,
covering the following:

- barycentric witnesses for any number of points (`baryOk`);
- capacity one of point and majority atoms (`pt_capacity`, `maj_capacity`);
- double counting (`field_count`);
- the exclusion theorem `field_generic`, which each certificate instantiates
  with kernel-checked data.

Two parts are shared by all certificates: the Voronoi half-planes of the 16
cells (`Shared/Grid.lean`) and the ownership trees (`Own/`). Witness points are
chosen on a barycentric lattice and, where the lattice is too coarse, refined
to exact grid points with integer barycentric coordinates.

**5. The owned-point induction (the core of the author's generic, prior and
returned exclusions).**

```lean
theorem SquarePacking.S11Opt.Split.owned_of_cov … : Owned S J o p
theorem SquarePacking.S11Opt.Split.excluded_of_cov … : ¬ RealizesIn S J
theorem SquarePacking.S11Opt.Split.caseExcluded_of_not_in : ¬ RealizesIn Ux J → CaseExcluded J
```

The author's induction alternates outer pose domains and inner owned hulls
(rational polygons). We re-prove it with the same box trees, round by round, and
never represent a pose domain explicitly. Consider a cover of the poses of cell
`o` in which every leaf does one of three things:

- lies outside the cell or the walls;
- captures a point already owned by another square (such a pose would overlap
  that square, so it cannot occur);
- captures the target point.

Such a cover proves that the target is owned by `o`. The same cover without a
target excludes the case.

**6. The centred frame.** `SquarePacking.S11Opt.Split.frame`: a packing in a
square of side `S` translates into the square of side `S` centred in the
`Ux`-frame (PROOF.md §3).

## Not yet formalized

Section numbers refer to PROOF.md.

- **The other 55 field certificates.** Their trees (about 20 million leaves in
  all) have been generated and are being kernel-checked on a cloud machine. They
  will be added here, together with the combined theorem that the 59 field
  certificates exclude 1,904 cases.
- **The 276 remaining non-candidate cases (§5).** These are 27 generic, 76 prior
  and 173 returned cases, to be re-proved with the induction rules of item 5.
- **The remaining parts of the proof**, whose work is split into separate units
  on the branch `split`:
  - the injectivity half of the centre cover (§4; the covering half is
    `exists_cell`);
  - the D4 bridge (§6);
  - the local isolation of Trump's configuration (§7; the necessary direction of
    the separating-axis theorem, Taylor bounds and duals);
  - case 438 (§8).

  On that branch the composition `minSide 11 = T` already compiles. It depends
  only on the units' `sorry`s, and it is work in progress.

## Reproduce

Requires `git`, `curl`, Python ≥ 3.8 (standard library only), and
[elan](https://github.com/leanprover/elan). The toolchain
`leanprover/lean4:v4.33.1` is selected by the upstream project.

```sh
N11_JOBS=2 sh build.sh /tmp/n11-lean-build
```

The work directory must not exist. The script does the following:

1. Clones and pins the upstream commit, and overlays `lean/Sqpack/S11Opt`.
2. Downloads the author's input files and checks their hashes: the two files of
   field-00, the data index, and five Git LFS objects (the replay manifest, the
   centre cover, the packets of certificates 3, 6 and 19).
3. Regenerates all data and compares it with `MANIFEST.sha256`: the upper
   bound, field-00, and the search, ownership and emission of certificates 3, 6
   and 19. The generation is deterministic.
4. Rejects `sorry`, `native_decide` and `axiom`.
5. Downloads the Mathlib cache and builds everything: the upper bound, the
   field-00 trees and assembly, the shared grid, the ownership and cover trees of
   certificates 3, 6 and 19 (`N11_JOBS` at a time), their assemblies, and the
   induction rules.
6. Requires all twelve axiom reports to be the standard three, and prints
   `N11_LEAN_BUILD_VERIFIED`.

For the first release (upper bound and field-00 only), `N11_JOBS=2` took
47 minutes wall on an Apple M4 Mac mini, with about 20 CPU-minutes of user time;
this includes the Mathlib cache download and the build of the upstream
dependencies. Certificates 3, 6 and 19 add about 20 CPU-minutes of kernel
checking and a few minutes of search. Peak memory is about 2 GB per process.

## Files

- `lean/Sqpack/S11Opt/` contains the hand-written files:
  - `Basic` — interval Horner check, separation lemma, and the root and T;
  - `Upper` — Trump's packing and `minSide_le_T`;
  - `Majority` — capacity one;
  - `FieldTree` — the box-tree checker;
  - `FieldBridge` — scaling, angles, barycentric checks;
  - `Cells` — Voronoi cells, `Realizes`/`CaseExcluded`, the half-turn, canonical cases;
  - `FieldGen` — atoms, capacity, counting, `field_generic`;
  - `Split/Interface`, `Split/U2Rules`, `Split/Frame` — the shared interface of the
    remaining work, the induction rules, and the centred frame;
  - `Axioms`.
- `scripts/` contains the generators:
  - `gen.py` writes `Data.lean` for the upper bound, using `field.py` for exact
    arithmetic in Q(u) and `construct.py` for Trump's packing (closed forms after
    the author's pinned `trump11/packing.py`, from jlevy/squares `c55726e`);
  - `field_tree.py` writes the field-00 trees;
  - `gen_final.py` writes the field-00 assembly;
  - `field_all.py` (with `field_gen.py` and `author.py`) searches, and writes the
    other field certificates, the shared grid and the ownership trees.
- `MANIFEST.sha256` lists the SHA256 of every generated file.
- `REPLAY.md` summarizes our independent re-run of the author's verifier.

## Attribution and license

The mathematical proof, the certificates and the field-00 structure are by
Queuing Theory #1 Fan. The packing is Walter Trump's (1979); the exact closed
forms follow jlevy/squares. The Lean definitions of packings and the containment
checker `ptOk` are Evan Daniel's (MIT; see `UPSTREAM-LICENSE.txt`). The
formalization in this repository is released under the MIT license (`LICENSE`).
