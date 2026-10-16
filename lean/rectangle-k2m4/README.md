# Lean: the rectangle version of s(k² − 4) = k, conditional on ValidTilt9

This project proves Theorem 1 of [`problems/rectangle-upper-bounds/`](../../problems/rectangle-upper-bounds/) in
Lean 4 with Mathlib, conditional on the finite statement `ValidTilt9` (equivalently `Valid9`) of Evan Daniel's
k2m4 certificate:

```lean
theorem SquarePacking.Rect4.rect4_of_validTilt9 (ht : ValidTilt9) :
    ∀ A B : ℕ, 8 ≤ A → 8 ≤ B → ∀ a b : ℝ, a < A → b < B →
      ¬ UnitSquarePacking.Conjectures.PacksRect (A * B - 4) a b

theorem SquarePacking.Rect4.rect4_of_valid9 (h : Valid9) : -- same conclusion
```

`PacksRect n a b` (upstream, `Sqpack/Conjectures.lean`) says that n unit squares, at any positions and angles,
with pairwise disjoint interiors, lie in [0, a] × [0, b]. `Valid9` and `ValidTilt9` are the upstream statements
about the box cover `K4_k008_box9.txt` (`Sqpack/Bentz4.lean`, `Sqpack/ValidSplit9.lean`); the axis-parallel case
`validAxis9` and the reduction `valid9_of_tilt_axis` are proved upstream in the kernel. `ValidTilt9` itself is a
computation: Evan Daniel's exact `qx2_zm` run, and independently our ValidTilt9 run
([`checks/valid7/`](../../checks/valid7/), release `records-tilt9-v1`). It is not proved in Lean.

## What is new here

`Sqpack/RectFam.lean` generalises the upstream square construction (`BentzFam.lean`) to two side lengths:

- `famRect F A B`, the measure on [0, A] × [0, B], and `famRect F k k = famCover F k`, so the upstream kernel check
  `box9Cover_measure` (the family at 9 × 9 is the box cover) is reused unchanged;
- `mass_shift_rect`, the localisation (Lemma R6): for A, B ≥ 8 every closed unit square in the rectangle has the
  same mass as an integer translate of it in the 9-box (per axis, with the upstream `Good`, `exists_good`,
  `good_cell`, `good_line`, `good_leb`);
- the total mass as a polynomial in the two side lengths, from the upstream one-axis sums;
- `not_packsRect_of_measure`, the measure principle for rectangles (scaling by 1/max(a/A, b/B) and the upstream
  `packing_le_measure`).

`Sqpack/Rect4.lean` instantiates it with the k2m4 family: total A·B − 4·(214770225571/200000000000) for
A, B ≥ 7, validity from `Valid9` by localisation, and the end theorems.

## Build

Lean 4.33.1 and Mathlib v4.33.1 (`lean-toolchain`, `lake-manifest.json`). From this folder:

    lake exe cache get        # Mathlib oleans
    lake build
    lake env lean Axioms.lean

Expected axiom output (also in `AXIOMS.out`):

    'SquarePacking.Rect4.rect4_of_valid9' depends on axioms: [propext, Classical.choice, Quot.sound]
    'SquarePacking.Rect4.rect4_of_validTilt9' depends on axioms: [propext, Classical.choice, Quot.sound]

No `sorry`, `admit` or `native_decide`. On a laptop the first build, which also checks the Mathlib oleans, took
about 13 minutes; the files of this project then build in about a minute.

## Credits

The upstream files are Evan Daniel's (MIT, see `UPSTREAM.md`). `RectFam.lean` and `Rect4.lean` are by Hiroaki
Hosono (wand125).
