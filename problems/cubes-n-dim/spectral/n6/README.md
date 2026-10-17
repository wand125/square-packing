# Two unit cubes in a cube in dimension six: s₆(2) = 2

**s₆(2) = 2:** two unit 6-cubes with disjoint interiors do not fit in a 6-cube of side less than 2.

The upper bound is the trivial packing. The lower bound follows from Lemma F in dimension 6: for every orthogonal
6-by-6 matrix U and every column j, F_j(U) = Σ_i |U_ij| (2 − ‖U_i‖₁) ≤ 1. Then every unit 6-cube inside a cube of
side less than 2 contains the centre in its interior (`supplied/d6_proof_handoff/PROOF.md` §8). The proof is
computer-assisted. It has not been peer reviewed.

The proof does not use the results for n = 4 or n = 5 (version 1 in `../../` and the spectral proofs in `../`) as
premises.

## The method

Fix a column with squared entries p, sorted so that p_1 is the largest. The proof covers all columns with three
overlapping regions (`supplied/d6_proof_handoff/PROOF.md`):

| Region | Argument | Check |
|---|---|---|
| max p ≤ 13/20 (cap) | the spectral bound of `../PROOF.md` plus a missing-edge correction R(p)/2 (§1–2) | exact rational certificate, 818,303 simplices |
| 13/20 ≤ max p ≤ 159/200 (strip) | on each simplex one of five lower bounds: the spectral bound with one of two missing-edge corrections, a determinant bound, a grouped determinant bound, or a combination of exterior-power bounds (§2–4) | exact rational certificate, 2,000,762 simplices |
| max p ≥ 141/200 (near the axis) | a quadratic minorant C5 for the tail, summed over the completion columns, gives 1 − F ≥ 2s²(1/(1 + a) − s) (§7) | C5 by an exact rational tree with 7,893 cells and an analytic sign-lifting argument |

The spectral bound alone fails in dimension 6, because q is negative at the uniform p. The missing-edge correction
and the other bounds close that gap.

## Contents

| Path | What |
|---|---|
| `supplied/` | The supplied proof as received, without its private handoff notes and local run records. The certificates of the cap and the strip are release assets (`ASSET.json`); unpack them to the paths given there |
| `supplied/d6_proof_handoff/PROOF.md` | The whole proof; it links to the detailed notes below |
| `supplied/d6_spectral/` | Missing-edge bounds (`EDGE_BOUND.md`); cap (`certificate_cap65/`) and strip (`certificate_cap795/`) with their generators, checkers and receipts |
| `supplied/d6_central/`, `supplied/d6_exterior_audit/` | Determinant and exterior-power bounds, with their audits and small exact checks |
| `supplied/d6_strip_independent/` | A second checker for the strip from the same source |
| `supplied/general_dimension/` | C5: the allocation proof, the exact tree, the sign lifting, the dependency graph and the near-axis threshold |
| `checkers/check_d6.py`, `checkers/check_c5.py` | Our checkers (second system), standard library only |
| `checkers/mutate_d6.py`, `checkers/mutate_c5.py` | Broken-copy tests for our checkers |
| `receipt.json`, `logs/` | Our runs: our checkers, the broken-copy tests and the supplied checkers |

The supplied `README.md` mentions a `STATUS.json` and a top-level `SHA256SUMS`. They are not included. The
per-certificate `SHA256SUMS` files are included.

## Results

| Check | cap | strip | C5 tree |
|---|---|---|---|
| certificate SHA-256 | `c33aa400…` | `0bd2317b…` | `12c4704d…` (compressed) |
| leaves | 818,303 | 2,000,762 | 7,893 (7,887 fixed-flow, 6 analytic) |
| maximum depth | 32 | 38 | 24 |
| minimum leaf margin | 8.86 × 10⁻¹⁰ | 8.14 × 10⁻¹⁰ | — |
| our checker | PASS, 134 s | PASS, 331 s | PASS, 5 s |
| supplied checkers | two checkers pass, 120 s and 88 s | two checkers pass, 277 s and 299 s | pass, 5 s |
| broken copies rejected by our checker | 6 of 6 | 8 of 8 | 5 of 5 |

The strip leaves use bound types 0, 1, 2, 3 and 5 (1,153,604, 649,006, 25,391, 93,810 and 78,951 leaves). No leaf
uses the projected exterior bound (type 4, `PROOF.md` (8)), so the proof does not depend on it. All runs were on a
laptop with Python 3.14. The three small supplied checks of the exterior-power constants also pass.
`logs/run-A.jsonl` and `logs/run-B.jsonl` give each command, its directory, its start time
and its exit code.

## Reproduction

Download the two release assets of `cubes-n-dim-v2` and unpack them as in `ASSET.json`. Then, in this directory:

```sh
python3 -I checkers/check_d6.py cap supplied/d6_spectral/certificate_cap65/certificate.json
python3 -I checkers/check_d6.py strip supplied/d6_spectral/certificate_cap795/certificate.json
python3 -I checkers/check_c5.py supplied/general_dimension/positive_c5_exact_tree.json.gz
```

The supplied checkers run from `supplied/` as described in `supplied/README.md`. Some of them rewrite their result
files, so run them on a copy. Do not use `python -O`, which disables the assertions.

## Review status and provenance

- **Produced with Codex.** The n = 6 proof and certificates were produced with Codex (OpenAI) under our direction.
  This covers everything in `supplied/`, including the audits and the second strip checker there; those come from
  the same source and are not independent of it.
- **Checked by us from the description alone.** We wrote `checkers/check_d6.py` and `checkers/check_c5.py` from the
  written proof and the certificate descriptions, without reading any supplied program. They check every
  acceptance with exact rational arithmetic. For the initial cover, our checker verifies that the five starting
  simplices lie in the domain, are separated pairwise by hyperplanes and have volumes adding up to the exact volume
  of the domain.
- **Reviewed by us.** We checked each step of the written proof:
  - the reduction and the missing-edge bounds (2) and (3), including λ_max(B) ≤ 1/2;
  - the forest constants M_k, the identity e_k(B) = (k + 1)e_{k+1}(p), the pair-smoothing lemma (6), the grouped
    bound (7) and the tangent combinations (9);
  - the interpolation losses;
  - the C5 allocation argument, its analytic near-axis cells and the sign lifting;
  - the covariance summation and the threshold g(141/200) = 18421/8000000 > 0.
- **Outside results used.** Concavity of e_j(p)^{1/j} (M. Marcus and L. Lopes, Canad. J. Math. 9 (1957), 305–312,
  Theorem 2), and the monotonicity and concavity of the trace square root on positive semidefinite matrices, as for
  n = 5.
- No external review yet. Corrections are welcome as issues.

## Credit and license

Hiroaki Hosono (wand125). MIT (see `../../LICENSE`).
