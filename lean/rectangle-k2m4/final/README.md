# The unconditional theorem

`RectFinal.lean` applies `Rect4.rect4_of_validTilt9` (this project) to `LemmaELeaf.validTilt9`, the kernel proof of
`Bentz4.ValidTilt9` from release
[`validtilt9-lean-v1`](https://github.com/wand125/square-packing/releases/tag/validtilt9-lean-v1)
([`problems/square-lower-bounds/certificates/k2m4_n77_L9/lean/`](../../../problems/square-lower-bounds/certificates/k2m4_n77_L9/lean/)):

```lean
theorem SquarePacking.Rect4.rect4 :
    ∀ A B : ℕ, 8 ≤ A → 8 ≤ B → ∀ a b : ℝ, a < A → b < B →
      ¬ UnitSquarePacking.Conjectures.PacksRect (A * B - 4) a b
```

`#print axioms` (`AxiomsFinal.lean`, output in `AXIOMS_FINAL.out`): `propext`, `Classical.choice`, `Quot.sound`.

**Same hypothesis.** `Bentz4.ValidTilt9` is one constant, defined in `Sqpack/ValidSplit9.lean`. The 16 library files
that both projects share, including `ValidSplit9.lean`, `Bentz4.lean` and `Bentz4Data.lean`, are byte-identical
(compare `../UPSTREAM.sha256` with `library/library.sha256` of the ValidTilt9 bundle). `lakefile.toml`,
`lake-manifest.json` and `lean-toolchain` are identical too. This project adds `Conjectures.lean` and `Spec.lean`
(upstream, unchanged), `RectFam.lean` and `Rect4.lean`; the ValidTilt9 project adds its own files. The two sets do
not overlap.

**How it was built.** Importing `Sqpack.V9.Main` loads all 1.27 million oleans of the ValidTilt9 run, so the build
needs that run's build tree (about 350 GB). It was done once, on the machine that still held it (48 Arm vCPUs,
376 GB, Lean v4.33.1), with `vm.max_map_count` raised to 4,194,304:

1. the oleans of `Spec`, `Conjectures`, `RectFam` and `Rect4` were built with `lean -o` next to the ValidTilt9
   oleans, reusing them through symbolic links so that the original tree was not modified;
2. `lean -o RectFinal.olean RectFinal.lean`: 2,944 s, 215 GB peak resident;
3. `lean AxiomsFinal.lean`: 228 s, 219 GB peak resident, output as above.

To rebuild, rebuild the ValidTilt9 run first (its README, section "Rebuilding"), then do steps 1–3.
