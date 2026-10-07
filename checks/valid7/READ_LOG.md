# Read log (independence record)

Upstream: github.com/evand/square-packing, commit d9f79bc1beb52a38854b675c330fd25a6d37eeee (2026-09-30).

## Read
- `s12/certificates/k2m3/README.md` (claim, proof paragraph, leaf-kind names; lemma *names* only, no proofs)
- `s12/certificates/s21/FORMAT.md` (mixed cover format v1)
- `s12/certificates/k2m3/verify.sh`, lines 1-60 (shell orchestration only)
- `s12/certificates/k2m3/L4_k02_box7.txt` (the cover, data)

## Not read (by design)
`qx2_zm.py`, `zm_mixed.py`, `zeromargin.py`, `mixed_cover.py`, `QUADRANT_EXACT.md`, `ZM_MIXED.md`,
`qx2_records.py`, `qx2_family_check.py`, the V3 run record and `lemmaZ.out`.

## Own prior work consulted
- `checker2/README.md` of github.com/wand125/squares-in-triangle (an exact angular sweep of a line arrangement for
  point covers; our own earlier work)

## Contact with other work in progress
During the work, another checker for covers of the same kind (different container, C4 symmetry) was being written
separately, possibly with reference to the upstream checker.  Only specifications and the usage of this checker
were exchanged with it (this checker was also run on its covers); none of its code or methods were read here, and
no content of the upstream checker or of its lemma documents was received.

## ValidTilt9 (2026-10-04; upstream commit 0c24309099b28a2ae88d09cb841ca3110b3dd1c2)
### Read
- `s12/certificates/k2m4/README.md`, lines 1-80 (claim, proof paragraph, the table of what is checked by what;
  lemma *names* only)
- `s12/lean/Sqpack/ValidSplit9.lean` and `ValidSplit.lean`: only the definitions `ValidTilt9` / `ValidTilt` and
  their doc comments (the statement to check: centres in `[0, 9/2]²`, `θ = 2 arctan u`, `u > 0`, `u² + 2u ≤ 1`,
  square inside `[0, 9]²`)
- `s12/lean/Sqpack/Basic.lean`: the definitions `coord`, `sq`, `sqInt` (rotation convention: `c + R_θ[−½, ½]²`,
  the same as ours)
- `s12/certificates/k2m4/K4_k008_box9.txt` (the cover, data)
### Not read
The checker programs and lemma documents listed above; the k2m4 run records and outputs; the rest of the Lean files.
