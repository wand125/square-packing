# Unit squares in a rectangle: an upper bound for all real side lengths

Let ν(a, b) be the largest number of non-overlapping unit squares (any positions, any angles) that fit in an
a × b rectangle. This folder extends the closed-form lower bound for squares in a square
([`problems/closed-form/`](../closed-form/), cited as CF) to rectangles with real sides: it gives an upper bound
for ν(a, b) of the form ab minus a saving for each side, for all a, b from about 7 on.

## What is claimed

Write a = k + δ_a and b = m + δ_b with integers k, m and δ_a, δ_b ∈ [0, 1). CF splits (0, 1] into 34 intervals
J₁, …, J₃₄ (`../closed-form/intervals.json`) and proves on each a saving S_J(δ) = α_J δ + β_J with exact rationals.
For δ ∈ [0, 1) let J⁺(δ) be the interval with d₀(J) ≤ δ < d₁(J) (the interval just to the right of δ).

**Theorem A (both sides in one interval).** If J⁺(δ_a) = J⁺(δ_b) = J and k, m ≥ 7, then

    ν(k + δ_a, m + δ_b) ≤ ab − 2 S_J(δ_a) − 2 S_J(δ_b).

**Theorem B (any two intervals).** Let J_a = J⁺(δ_a), J_b = J⁺(δ_b) and K = min(k, m). For every pair of intervals
the table `data/paths.json` gives a rational E = E(J_a, J_b) ≥ 0 and an integer k₀ = k₀(J_a, J_b) ≥ 7. If K ≥ k₀, then

    ν(k + δ_a, m + δ_b) ≤ ab − 2 S_{J_a}(δ_a) − 2 S_{J_b}(δ_b) + 4E.

For J_a = J_b, E = 0 and k₀ = 7, which is Theorem A. For a = b both reduce to the square case of CF.
E is the total extra mass of the "seams" that join the wall profile of J_a to that of J_b; k₀ = 6 + 3r, where r is
the number of seams used. The largest E is 2907373/10⁶ ≈ 2.91 (between J₁ = (0, 1/50] and J₃₄ = (99/100, 1],
r = 16, k₀ = 54).

**Examples.** For a = 12.45 and b = 14.48 (intervals (9/20, 91/200] and (12/25, 97/200], E = 124601/10⁶, k₀ = 12)
Theorem B gives ν ≤ 178.85…, so ν(12.45, 14.48) ≤ 178; the area bound gives 180 and Karakuş's bound (below) 179.
For a = 9.45 and b = 11.45 Theorem A gives ν ≤ 106.27…, so ν ≤ 106 (area 108, Karakuş 107).

**Where the bound says something.** The theorems hold for all pairs, but improve on the area bound ν ≤ ab only
where 2S_{J_a}(δ_a) + 2S_{J_b}(δ_b) > 4E. Compared exactly at the corners of J_a × J_b (`checker/compare_bounds.py`,
`data/compare.json`), of the 595 unordered pairs of intervals:

| Compared with | stronger on all of J_a × J_b | on part of it | nowhere |
|---|---|---|---|
| the area bound ab | 257 | 3 | 335 |
| Karakuş's bound ab − max(δ_a, δ_b) | 231 | 6 | 358 |

Same-interval pairs: 33 of 34 are stronger than Karakuş's bound everywhere (the exception is J₁ at
δ_a = δ_b = 0). Pairs of different intervals that are useful have r ≤ 4 and k₀ ≤ 18; all 120 pairs inside
(21/50, 1/2] are useful. Seams far apart cost more than the savings, so for intervals far apart Theorem B is weaker
than ab.

Nothing is claimed about how many squares do fit: no packings are given.

**Status.** Computer-assisted, exact rational arithmetic throughout. Not formalised in Lean. The new finite
statements are checked twice, by the first checker in this folder and by an independent second checker: Lemmas
R1 and R2 for all 34 families, and the seams (every leaf of every record, the root list, coverage, the band
condition, the levels and the paths). Not yet reviewed by anyone outside this project.

## The argument

The full statements and proofs are in [`SPEC.md`](SPEC.md). In outline:

1. **Measure principle (Lemma M).** A non-negative measure on a slightly larger rectangle that gives mass ≥ 1 to
   every closed unit square in it bounds ν by its total mass. The enlargement is by one factor λ > 1 in both
   directions; letting λ ↓ 1 gives the bounds at the endpoints, which is why the interval to the right of δ is used.
2. **Same interval (Lemmas R1, R2).** The CF family of J (corner pieces, a periodic wall profile, a terminal line,
   Lebesgue measure inside) is placed in the four corners and along the four walls. For k, m ≥ 7 every unit
   square sees only one corner's local model (R1), so the CF checks apply; the total mass is
   ab − 2S_J(δ_a) − 2S_J(δ_b) (R2).
3. **Seams.** For different intervals the walls change profile. A seam is one transition period between the wall
   profiles of two intervals; its family was found by linear programming and checked by CF's 4D checker over all
   poses near the transition. Lemma R5 (a band condition on the transition) reduces the check to poses touching
   both bands: 11,206 of 17,550 roots. 30 seams join the 34 intervals into one connected graph (with 4 pairs of
   neighbouring intervals whose profiles are identical).
4. **Paths (Lemma R7).** Between J_a and J_b the walls run along a path of seams. Keeping seams and corners two
   periods apart makes them independent, which needs k, m ≥ 6 + 3r; the extra mass on the four walls is 4E.
   For every pair the path of least E also has the fewest seams, so one (E, k₀) per pair suffices.

## What was checked, and how

| Statement | Checks | Result |
|---|---|---|
| The 34 interval families: μ ≥ 1 in the four regions of CF | CF's records, the Rust replay and the independent checker `cfcheck` | as published in [`problems/closed-form/`](../closed-form/) |
| Lemmas R1 and R2 for each of the 34 families, at both ends of the interval and 8 pairs (k, m) | `checker/validate_rect.py` | all pass (R1a, R1b, R1c, R2 and the symmetry checks) |
| Each seam: every root of the R5 list has μ ≥ 1 | CF's `run4d` on the seam family, levels 0, 1, … (a failed piece is repaired by raising masses and checked again) | 30 seams, 51 levels, 0 uncertified pieces |
| Each record: structure and sampled recomputation | CF's `check_record4d` (2,000 leaves recomputed per record) | all records accepted; the only findings are "roots are not the full grid", expected (coverage is checked below) |
| Each seam: the R5 root list and coverage by the pieces of all levels | `checker/seam_cover.py` (exact; each left-out root is proved not to reach a band) | 30/30: 6,344 roots left out with proof, 363,550 pieces, 0 uncertified leaves |
| Each seam family: band condition of R5, agreement with the published profiles, monotone levels | `checker/seam_exact.py` (exact, pointwise line densities) | 30/30, 51 levels |
| E, r, k₀ for all pairs | `checker/paths.py` | 595 pairs; largest E 2907373/10⁶ |
| Lemmas R1 and R2, the walls, the square case and the certified saving line, independently | `indep-checker/r1r2/rect_r1r2_all.py` (generalised from the independent checker of [`problems/rectangle-upper-bounds/`](../rectangle-upper-bounds/); written without reading `checker/`) | 34/34 intervals, 341 checks each; 8 negative controls rejected |
| The seams, independently: structure and e, band condition, levels, the R5 root list, coverage, every leaf of every record, paths | `indep-checker/` (written from the specifications only; leaf tests of CF's independent checker `cfcheck`) | 30/30 ALL PASS; 52 records, 4,921,514 leaves, 0 refusals; 595 paths, 0 mismatches |

**A repair found by the exact check.** The band condition of R5 was first checked in floating point. The exact
check (`seam_exact.py`) found that in two seams one wall segment of length 2/5 had less mass than the profile
(the lower bounds of the linear program were set per grid cell of length 1/5 and missed a segment spanning two
cells). We added the missing mass, rounded up to 2001/10⁶, to the final family of each of these two seams
(`family_final.json`). Adding mass keeps every proved piece valid; e of the two seams went up by 2001/10⁶ and the
tables above use the repaired values.

**Who checked what.** The first checker did not recompute every leaf of the seam records: the records were
produced by `run4d` (which proves each piece) and checked by `check_record4d` with 2,000 recomputed leaves per
record. Every leaf was recomputed once, by the second checker (about 573 CPU hours on one cloud machine). Lemmas R1
and R2 for the 34 families were checked by both checkers (the second one in about 2.5 minutes on a laptop).

**Records as checked.** The second checker read the records before their first line (the command line of `run4d`)
was reduced to file names for publication; all other lines are identical (`data/seam_records.json` lists the
hashes). On the records in the release, the second checker's items 1–5 and 7 were run again and pass
(`receipts/indep/release_layout_items1to5_7.out`).

The outputs are in `receipts/`.

## Files

- `SPEC.md`: statements, lemmas and proofs.
- `checker/validate_rect.py`: Lemmas R1, R2 for an interval family (`--theorem2` adds the condition S > 3/4 used
  only by Theorem 2 of [`problems/rectangle-upper-bounds/`](../rectangle-upper-bounds/)).
- `checker/seam_exact.py`, `checker/seam_cover.py`: the exact checks of the seam families and of coverage.
- `checker/paths.py`, `checker/compare_bounds.py`: the tables `data/paths.json` and `data/compare.json`.
- `data/edges.json`: the 34 edges (30 seams with their e, 4 identical-profile pairs).
- `receipts/`: the outputs of the checks.
- `indep-checker/`: the independent second checker of the seams, with its own README; `indep-checker/r1r2/`: the
  independent check of Lemmas R1 and R2, with its own README.
- `data/seam_records.json`: the hashes of each record as checked and as released.
- `data/compare.json`: the comparison table.

The checkers import `../closed-form/structure/validate_family.py` and use `../closed-form/intervals.json`.

## Inputs (release `rectangle-closed-form-v1`)

One asset, `rectangle-closed-form-v1.tar.xz` (22,881,952 bytes, sha256
`783e4e5f6a5f1597e62fed16a227e7428d7bf83af3a364292c02b4d8dad1fde7`; 445 MB unpacked), containing:

- `rectangle-closed-form-v1/seam_AA_BB/` for each seam between intervals AA and BB: `L<j>/family.json` and `L<j>/record.rec` for each
  level j (`record_part1.rec`, `record_part2.rec` where a level was split over two runs), and `family_final.json`.
- `rectangle-closed-form-v1/roots_r5.json`: the R5 root list (the same for all seams).
- `families/`: the 34 interval families, unchanged from release `closed-form-v1` (their SHA-256 are the
  `family_sha256` of `../closed-form/intervals.json`).
- `rectangle-closed-form-v1/SHA256SUMS` and `families.SHA256SUMS`.

The record headers list the command line of `run4d`; absolute paths there were reduced to file names.

## How to check

Python 3 (standard library only). After unpacking the release next to this folder as `release/`:

    python3 checker/validate_rect.py release/families/<interval>/family.json
    python3 checker/seam_exact.py release/rectangle-closed-form-v1/seam_AA_BB/family_final.json FA FB --dominates <earlier levels>
    python3 checker/seam_cover.py release/rectangle-closed-form-v1/roots_r5.json <records of all levels>
    python3 checker/paths.py && python3 checker/compare_bounds.py

The first line of each file in `receipts/` is the exact command, run from the unpacked release folder
(the checker paths there are relative to this folder). On a laptop (Apple M4, two checks at a time) all the
checks of `checker/` took about 16 minutes (2026-10-19).
The leaves of the records can be replayed with CF's `checker/replay4d` (the records are in CF's format).

## Relation to earlier work

Here ν(a, b) counts squares in the a × b rectangle itself.

- **Nagamochi** (H. Nagamochi, Packing unit squares in a rectangle, Electron. J. Combin. 12 (2005) #R37) states
  that the number of unit squares in a rectangle with sides strictly smaller than a and b is less than
  ab − (a + 1 − ⌈a⌉) − (b + 1 − ⌈b⌉). Its proof rests on a scoring lemma for which counterexamples have since
  been given, so the published proof is incomplete. We do not use it.
- **Karakuş** (H. Karakuş, A counterexample to Nagamochi's scoring lemma and a new rectangle packing bound,
  arXiv:2609.37410, 2026) proves ab − max(Δ(a), Δ(b)) with Δ(t) = t + 1 − ⌈t⌉ (a, b ≥ 3) and leaves open how
  to combine savings along both directions. Applied to the a × b rectangle itself (as a limit from larger
  rectangles) it reads ν(a, b) ≤ ab − max(δ_a, δ_b); this is the comparison in the table above. Theorems A and B
  combine savings on both sides, with the seam cost 4E when the fractional parts lie in different intervals.
- [`problems/closed-form/`](../closed-form/): the square case and all interval families used here.
- [`problems/rectangle-upper-bounds/`](../rectangle-upper-bounds/): for integer A, B ≥ 8, ν(a, b) ≤ AB − 5 when
  a < A and b < B (Theorem 1 there, also in Lean). That bound is for sides just below integers; the bounds here
  are for all fractional parts and are weaker than AB − 5 just below integers.

## Credits

Hiroaki Hosono (wand125): the rectangle layout, the seams, Lemmas M, R1, R2, R5, R7, the checks in this folder,
and the closed-form families of CF. The bounds of Nagamochi and
Karakuş are credited above.

## Licence

MIT (see `LICENSE`).
