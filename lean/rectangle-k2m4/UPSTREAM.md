# Files taken from evand/square-packing

`Sqpack/{Basic,Bentz,Bentz4,Bentz4Data,BentzData,BentzFam,Chord,Conjectures,Cover,D4,MixedMeasure,S32,S32Data,Spec,ValidSplit,ValidSplitData,ValidSplit9,ZeroMargin}.lean`,
`lakefile.toml`, `lake-manifest.json` and `lean-toolchain` are copied unchanged from
https://github.com/evand/square-packing, commit 7d1407a0b66c46e32cdbcbd5619586fe2bdd52a1 (2026-10-15), directory
`lean/`. MIT License, Copyright (c) 2026 Evan Daniel; see `LICENSE-evand-square-packing`. Their sha256 are in
`UPSTREAM.sha256` (`cd Sqpack && sha256sum -c ../UPSTREAM.sha256`).

The new files are `Sqpack/RectFam.lean` and `Sqpack/Rect4.lean` (sha256 in `NEW.sha256`), `Sqpack.lean` (imports)
and `Axioms.lean`.
