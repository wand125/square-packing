# Upstream provenance

The unchanged Sqpack modules, original Lake TOML, dependency manifest and
Lean toolchain listed in `UPSTREAM.sha256` originate in
[Evan Daniel's square-packing repository](https://github.com/evand/square-packing/tree/7d1407a0b66c46e32cdbcbd5619586fe2bdd52a1/lean),
commit `7d1407a0b66c46e32cdbcbd5619586fe2bdd52a1` (2026-10-15), directory `lean/`.
These files are also identical at commit
`96c4e427f228243adc6ed0e77caf9ca1139bb79e`.
They were originally copied through another local formalization of the same
project. No copied upstream file has been edited. Only the transitive
Sqpack dependencies of MixedMeasure and Spec are included.

Copyright Evan Daniel, MIT; see `LICENSE-evand-square-packing`.
The original configuration is preserved as `inputs/upstream/lakefile.toml`.
`UPSTREAM.sha256` is unchanged and covers that relocated copy, the licence,
Sqpack modules, `lake-manifest.json`, and `lean-toolchain`.

`lakefile.lean` is the active local configuration: it retains the upstream
Lean options and Mathlib version and additionally registers ClosedForm.
The unchanged upstream TOML was tried during development and failed to build
ClosedForm because it registers only Sqpack. `Sqpack.lean` is a new local
entry point, not an upstream file.

All ClosedForm modules are new work by Hiroaki Hosono (wand125).
`ClosedForm/Principle.lean` adapts the common-specification translation from
an earlier RectFam formalization attributed to Evan Daniel (MIT); its
scaling argument is reused through the unchanged MixedMeasure module.

Generated family and interval data come from the published
[closed-form certificate](https://github.com/wand125/square-packing/tree/main/problems/closed-form)
and its Release records (`family.json` and `family_right.json`). The original
generators check both family hashes against `intervals.json` and the interval
SHA256SUMS. Those generators exist but are not included in this bundle.
This provenance document has been rewritten for the public bundle; upstream
source bytes and the upstream checksum file have not changed.
