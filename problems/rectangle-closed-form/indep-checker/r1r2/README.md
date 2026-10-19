# Independent check of Lemmas R1 and R2 for all 34 interval families

A second checker for the rectangle version of the closed-form bound. For each of the 34 interval families it checks
Lemma R1 (localisation), Lemma R2 (total mass), the walls, the square case and the certified saving line. It works in
exact rational arithmetic (`fractions.Fraction`).

Written from the specifications only: the closed-form SPEC §1.3, §2.1 and §3, and the rectangle SPEC §1–§3. The
first-system checkers (`checker/validate_rect.py`, `problems/closed-form/structure/validate_family.py` and their
callers) were not read.

**Reused code.** The published independent checker `problems/rectangle-upper-bounds/indep-checker/rect_r1r2_indep.py`
(sha256 218b9d8839ec2c56…), which handles interval 34 only, was read and generalised. Its segment algebra and its
construction of the global and local measures are kept.

New in this version:
- the interval bounds and the family are taken per interval from `intervals.json`;
- each family is bound to its `family_sha256`;
- the Lebesgue part must be the standard quadrant;
- the saving is compared with the certified line α_J d + β_J;
- a terminal-line phase check is added;
- the output is a per-interval report;
- negative controls are added.

## Files

| file | sha256 (first 16) | role |
|---|---|---|
| `rect_r1r2_all.py` | 342a7a54dc816efa | the checker |
| `neg_controls.py` | ddfd1ee1fdfc0672 | negative controls, each of which must fail |
| `TASK_INDEP_R1R2.md` | | the task statement this checker was written from |

Outputs (in `../../receipts/indep/r1r2/`):

| File | SHA-256 (first 16) | Role |
|---|---|---|
| `report_all.json` | 3b0177a19fbb95c2 | per-interval report (34 entries: checks, groups, savings, m_v, time) |
| `run_all.txt` | | one line per interval, as run (`run_1_17.txt`, `run_18_34.txt`: the two processes) |
| `neg_34.txt`, `neg_1.txt` | | the controls as run on intervals 34 and 1 |

## What is checked (for every family; 341 checks per interval)

Inputs:
- The family file's sha256 equals `family_sha256` in `intervals.json`. The families' `SHA256SUMS` list agrees with `intervals.json` for all 34.
- d0 and d1 of the family equal those of `intervals.json`.
- α = 9/5, and U is absent or the standard quadrant.
- The V densities are ≥ 0 with xl ≤ 2 + d0.

Structure (closed-form SPEC §2.1, §3.2):
- One wall period is read from x ∈ [3, 4), owning its phase-0 line and not its phase-1 line.
- The profile has mass 9/5 and lies on the 1/5 grid, with the reversal identities h[j,p] = h[j,4−p] and v[q,i] = v[−q mod 5,i].
- Subtracting seven periods from T leaves a non-negative seam on x = 2, and subtracting seven transposed periods from F leaves a non-negative corner in [0, 2 + d0] × [0, 2]. Both reconstructions are exact.
- Every stored period [n, n+1), n = 3..8, of the bottom and left walls equals the profile.
- The fixed corner mass formula includes −2 m_v.
- At δ = d0 and d1 the corner is supported in [0, 2 + δ] × [0, 2], non-negative, and its mass is affine in δ.

For every (δ_a, δ_b) ∈ {d0, d1}² and (k, m) ∈ {(7,7), (7,9), (9,7), (8,11), (12,7), (7,13), (8,8), (10,14)}:
1. **R2.**
   - Total mass = ab − 2S(δ_a) − 2S(δ_b), with S recomputed from the family (closed-form SPEC §1.3).
   - All densities are ≥ 0, the support lies in [0, a] × [0, b], and the measure and the Lebesgue rectangle are invariant under σ(x, y) = (a − x, b − y).
2. **R1.** With r = 3/4 (r² > 1/2):
   - on the closed quarter box [0, a/2 + r] × [0, b/2 + r], the global measure equals the local model of SW at δ_a;
   - pulled back by τ(x, y) = (a − y, x), on [0, b/2 + r] × [0, a/2 + r] it equals the local model at δ_b;
   - the Lebesgue part agrees on both boxes;
   - the geometric gaps a/2 + r < a − (2 + δ_b), a − 2, a − 9/5 hold (and likewise for b) at k = m = 7.
3. **Walls.** The SW and SE left walls equal the transposed profile with integer phase at y = 2, and the terminal line of the bottom wall is the phase-0 line of the profile at x = a − 2.
4. **Square case.** For k = m and δ_a = δ_b, the four rotations of one side equal the rectangle measure.
5. **Saving.** S(d0) ≥ α_J d0 + β_J and S(d1) ≥ α_J d1 + β_J (certified line of `intervals.json`).

**Why finitely many (δ, k, m) suffice** (as in `rect_r1r2_indep.py`):
- Subtracting the seven stored periods verifies the fixed F/T/V decomposition.
- Reversal and transposition are exact profile identities, independent of δ and of the wall length.
- Corner coordinates and masses are affine in δ with a fixed structure on the interval, and non-negativity and containment are checked at both ends. The only varying length is the V rows, which have a fixed density.
- The geometric gaps are affine in the two deltas and grow with each integer side parameter, so the four endpoint pairs at k = m = 7 bound all larger containers.
- Larger k or m only add integer wall periods, which preserve the checked identities and shift the windows by integers. The sizes used cover both parities of k and m, and unequal sides.

Endpoint comparisons alone would not suffice without these structural and geometric checks. Coverage of all unit-square poses is the separate leaf replay of the closed form.

## Results (2026-10-19, a laptop, Python 3, standard library only)

- **All 34 intervals PASS**, 341/341 checks each (`report_all.json`, `run_all.txt`).
- **Time:** about 5 s per interval, 161 s in all, run as two processes of 17 intervals (84 s and 77 s).
- **Negative controls** (`neg_controls.py`, run on intervals 34 and 1): every control is rejected.

  | control | caught by |
  |---|---|
  | a corner mass in F perturbed by 10⁻⁶ | the saving line |
  | one wall-period row of T shifted by 1/100 | the seam remainder |
  | d1 of the family changed | the interval bounds |
  | a negative V density | the input checks |
  | a non-standard U | the quadrant check |
  | one T row removed | the seam remainder |
  | the certified line raised by 10⁻⁹ | the saving check |
  | one byte appended with the sha binding on | the binding |

  The content controls run with `--no-sha`, so that the binding alone does not reject them. On interval 34 the saving equals the certified line exactly at d0, so a corner perturbation of 10⁻⁶ already breaks item 5.

## Run

```sh
# FAMILIES = the folder of <asset>/family.json, INTERVALS = problems/closed-form/intervals.json
python3 rect_r1r2_all.py FAMILIES INTERVALS --report report_all.json    # ends with "SUMMARY: 34/34 intervals PASS"
python3 neg_controls.py FAMILIES INTERVALS 34                             # ends with "ALL CONTROLS FAIL AS REQUIRED"
```
