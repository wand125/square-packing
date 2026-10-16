# Lean: the near-region lemma in any dimension

A Lean 4 + Mathlib formalization of the hand part of `../PROOF.md` §3, in any dimension. It covers the
polar-decomposition inequality and Lemma K. It does **not** formalize the reduction of §1, the far region of §4, or
Lemma F in dimension 3. Lemma F in dimension m is a hypothesis of the main theorem (`LemmaF m`).

## Setting

An orthogonal matrix of size m + 1 is written in blocks R = [c r; x M]. Here c = R_11, r is the rest of row 1,
x is the rest of column 1, and M is the lower-right m × m block. The structure `BlockOrth c r x M` lists the
orthonormality relations that the proof uses:
- column 1 and row 1 are unit vectors;
- column 1 is orthogonal to the other columns;
- rows 2, …, m + 1 are orthonormal.

`F1 c r x M` is F_1(R) = Σ_e |R_e1| (2 − ‖row e‖₁). `polarQ c x M = (1 + β x xᵀ) M`, with
β = (1/c − 1)/‖x‖₂², is the orthogonal factor Q of the polar decomposition M = P Q,
P = 1 − (1 − c)/‖x‖₂² · x xᵀ. It is an explicit formula, so no matrix square root is needed.

## Statements

| Lean name | Statement | `PROOF.md` |
|---|---|---|
| `polarQ_orth` | Q Qᵀ = 1 when c > 0 and x ≠ 0 | §3 (c) |
| `near_identity` | 1 − F_1 ≥ K(Q, x) + 2(1 − c)(1 − ‖Qᵀx‖₁), any m | §3 (a)–(d) |
| `l1_QTx_le_one` | ‖Qᵀx‖₁ ≤ 1 when Q Qᵀ = 1 and m‖x‖₂² ≤ 1 | §3 (e) |
| `lemmaK` | K(Q, x) ≥ 0 when Q Qᵀ = 1, every row of Q has ℓ¹ norm ≤ 2, and every column has F ≤ 1 | §3 (f) |
| `rowL1_le_two` | for m ≤ 4, every row of an orthogonal m × m matrix has ℓ¹ norm ≤ 2 | §3 (f) |
| `near_region` | for m ≤ 4, `LemmaF m` → (c > 0 and m(1 − c²) ≤ 1 → F_1 ≤ 1) | §3 |

`LemmaF m` says: every Q with Q Qᵀ = 1 has F_j(Q) ≤ 1 for every column j. For m = 3 this is Lemma F of
`../../cubes-in-cube/lemma_f/`, which is computer-assisted and not formalized. Applied with m = 3, `near_region`
gives the near region c² ≥ 2/3 of the n = 4 proof.

## Build

```sh
lake exe cache get   # Mathlib build cache for the pinned commit
lake build           # about 20 s for this library once Mathlib is available
lake env lean CheckAxioms.lean
```

The toolchain is `leanprover/lean4:v4.33.1`. `lake-manifest.json` pins Mathlib at commit
`0df444a360eaa60ab8c11dca51a86af692955474`. Our build log is in `build.log`; it has only style-linter warnings
(line length and the header comment). `CheckAxioms.lean` prints:

```text
'CubesNd.polarQ_orth' depends on axioms: [propext, Classical.choice, Quot.sound]
'CubesNd.near_identity' depends on axioms: [propext, Classical.choice, Quot.sound]
'CubesNd.l1_QTx_le_one' depends on axioms: [propext, Classical.choice, Quot.sound]
'CubesNd.lemmaK' depends on axioms: [propext, Classical.choice, Quot.sound]
'CubesNd.rowL1_le_two' depends on axioms: [propext, Classical.choice, Quot.sound]
'CubesNd.near_region' depends on axioms: [propext, Classical.choice, Quot.sound]
```

There is no `sorry`, `axiom`, `native_decide` or `decide` on large data.

## How it was made

We wrote the definitions and the theorem statements. Codex (OpenAI) wrote the proofs from a written proof
sketch and could not change the statements. We then checked with `#check` and `#print` that the statements and
definitions were unchanged, and checked the axioms.
