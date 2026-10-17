# Two unit cubes in a cube, version 2: s_n(2) = 2 for n = 3, 4, 5 by a spectral bound

Let s_n(k) be the side of the smallest n-cube that contains k unit n-cubes with pairwise disjoint interiors (any
positions, any orientations). We prove

**s₃(2) = s₄(2) = s₅(2) = 2:** in dimensions 3, 4 and 5, two unit cubes do not fit in a cube of side less than 2.

The upper bound is the trivial packing. The lower bound follows from a centre lemma: every unit n-cube inside
[0, 2]ⁿ contains the centre of [0, 2]ⁿ. The proof is computer-assisted, with short exact rational certificates that
check in seconds with the Python standard library. It has not been peer reviewed.

This is version 2. Version 1, in the parent directory (`../`), proved s₄(2) = 2 by interval branch and bound; it
remains a separate, independent proof.

## The method

For an orthogonal matrix U let w_i be the ℓ¹ norm of row i and F_j(U) = Σ_i |U_ij| (2 − w_i). If F_j ≤ 1 for
every orthogonal n-by-n matrix and every column (Lemma F_n), the centre lemma follows (`PROOF.md` §1). Lemma F is
proved by induction on the dimension, starting from a one-line proof of F_2 (§2). For a column with squared entries p:
- **Near an axis, max p_i ≥ 1 − 1/(n − 1).** A polar-decomposition argument reduces the claim to Lemma F_{n−1}
  (§3). This step needs rows of ℓ¹ norm at most 2 in dimension n − 1, which holds for n ≤ 5.
- **Elsewhere.** Vectors with zero sum satisfy ‖z‖₁ ≥ √2 ‖z‖₂. With the triangle inequality for the nuclear norm this
  gives 1 − F_j ≥ q(p) = √2 Tr √(diag(p) − ppᵀ) − 2 Σ_i √p_i + 2 (§4). A certificate proves q(p) > 0 on the
  rest of the probability simplex. It uses branch and bound on simplices, the concavity of the trace square root, and
  rational witnesses for the matrix square root at the vertices (§5–§7).

The second part fails in dimension 6: there q is negative at the uniform p.

## Contents

| Path | What |
|---|---|
| `PROOF.md` | The whole proof for n = 3, 4, 5, the acceptance rule and the certificate format |
| `checkers/gen_spectral.py` | First system: generator; every acceptance is checked exactly (NumPy only proposes witnesses) |
| `checkers/check_spectral.py` | Second system: independent checker, standard library only, written from the specification alone |
| `n3/`, `n4/` | Certificate, receipt and logs for n = 3 and n = 4 |
| `n5/` | Receipt and logs for n = 5. Our certificate is the release asset (`n5/ASSET.json`) |
| `n5/supplied/` | The supplied proof for n = 5 that started this version: write-up (we added only its section on the certificate format), certificate, generator and two checkers. The programs are unmodified; we ran the two checkers, not the generator |
| `../lean/` | Lean 4 + Mathlib: the near-axis step (§3) in any dimension, with Lemma F in the dimension below as a hypothesis |
| `../` | Version 1: s₄(2) = 2 by two independent interval branch-and-bound checkers (release `cubes-n-dim-v1`) |

## Results

| n | certificate | leaves | min leaf margin | first system | second system |
|---|---|---|---|---|---|
| 3 | `n3/certificate.json` | 5 | 2.9 × 10⁻³ | regenerated identically, 0.1 s | PASS, 0.0 s |
| 4 | `n4/certificate.json` | 557 | 3.2 × 10⁻⁴ | regenerated identically, 0.2 s | PASS, 0.1 s |
| 5 | release asset (ours) | 135,255 | 4.1 × 10⁻⁷ | regenerated identically, 45 s | PASS, 30 s |
| 5 | `n5/supplied/certificate.json` | 21,502 | 2.3 × 10⁻⁷ | supplied `replay.py` and `independent_verify.py`: pass, 2.5 s and 4.2 s | PASS, 4.5 s |

All runs were on a laptop with Python 3.14 (NumPy 2.5 for the generator). Each `receipt.json` also records that the
second-system checker rejected five deliberately broken copies of each certificate it was tested on: a wrong witness,
a wrong midpoint index, a leaf placed too early, a missing record, and a missing initial simplex.

## Reproduction

```sh
cd n3 && python3 -B ../checkers/check_spectral.py certificate.json && cd ..
cd n4 && python3 -B ../checkers/check_spectral.py certificate.json && cd ..
cd n5/supplied && python3 -B ../../checkers/check_spectral.py certificate.json \
  && python3 -B replay.py && python3 -B independent_verify.py && cd ../..
# our n = 5 certificate: download the release asset (n5/ASSET.json), then
cd n5 && python3 -B ../checkers/check_spectral.py certificate.json
# regenerate any certificate (needs NumPy): python3 checkers/gen_spectral.py 4 n4-again.json
```

Do not use `python -O`, which disables the assertions.

## Changes from version 1

- New: s₃(2) = 2 and s₅(2) = 2 in the same framework, and a new proof of s₄(2) = 2. Dimension 3 no longer depends on
  the computer-assisted Lemma F of `../../cubes-in-cube/lemma_f/`, which remains an independent proof.
- `PROOF.md` §1 and §3 are §1 and §3 of `../PROOF.md`, written for general n and m. The near-axis step is the one
  formalized in `../lean/`. Version 1 itself is unchanged.

## Review status and provenance

- **Produced with Codex.** Codex (OpenAI) produced, under our direction, the n = 5 proof (the spectral bound, the
  triangulation and the acceptance rule) and the first n = 5 certificate (`n5/supplied/`).
- **Made by us with the same method.** Our generator (`checkers/gen_spectral.py`, the first system) made the
  certificates for n = 3 and n = 4 and the second certificate for n = 5.
- **Written by us from the description alone.** Both of our systems were written from the written proof only. The
  checker was written without reading the supplied programs, and the generator without reading the supplied
  generator. Our checker agrees with the two supplied checkers on the supplied certificate.
- **Reviewed by us.** We reviewed each step of the supplied proof. This covered the reduction, the zero-sum
  inequality, the direction of the nuclear-norm triangle inequality, the Loewner concavity, the monotonicity and
  concavity of the trace square root, the chord bound, the Weyl bound and the pulling triangulation. We also checked
  that the premise of the near-axis step matches §3.
- The near-axis step (§3) and Lemma K were checked line by line by an independent internal reviewer for version 1,
  and they are formalized in Lean (`../lean/`).
- No external review yet. Corrections are welcome as issues.

## Sources

- **Classical.** For n = 2 (two unit squares need a square of side 2), see Erich Friedman, "Packing unit squares in
  squares: a survey and new results", Electronic Journal of Combinatorics, Dynamic Survey DS7. We found no proof of
  s_n(2) = 2 for any n ≥ 3 in the literature. MathOverflow question 138808, "Two cubes in unit cube" (2013), asks the
  general question and has only partial answers. If you know of a proof, please open an issue.
- **Our earlier work.** s₃(2) = 2 by Lemma F in `../../cubes-in-cube/lemma_f/`, and s₄(2) = 2 in `../` (release
  `cubes-n-dim-v1`). The near-axis step (§3) is from there.
- **New here.** The spectral bound and the certificates for n = 3, 4, 5, and s₅(2) = 2.

## Credit and license

Hiroaki Hosono (wand125). MIT (see `../LICENSE`).
