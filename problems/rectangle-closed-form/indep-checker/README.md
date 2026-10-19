# Independent second check of the seam records

(The independent check of Lemmas R1 and R2 for the 34 interval families is in [`r1r2/`](r1r2/).)

A second checker for the 30 seams of this folder (52 records). It was written from the task statement
`TASK_INDEP_SEAM.md`, `../../closed-form/SPEC.md` and §5 of the specification of this folder, and from the
interface of the published independent closed-form checker `cfcheck` ([`../../closed-form/indep-checker/`](../../closed-form/indep-checker/)).
The first checker's seam and record tools (`run4d`, `check_record4d`, the seam builders, `../checker/`) were not read.

## Tools

| File | SHA-256 (first 16) | Role |
|---|---|---|
| `seam_check2.py` | 8ecaf1d5bd19ceca | items 1–7 per seam; item 6 reads the leaf-replay reports |
| `seamleaf/src/main.rs` | 3445ad0feeacd8c6 | leaf replay (Rust): every leaf of every root of a record, checked with `cfcheck`'s leaf tests (`leaf::check`, `record::tiling`, `stage_b::local_family`); `--part K/M` |
| `make_jobs.py`, `jobs.tsv` | | the job list of the leaf replay (seam × level × part) |
| `run.sh`, `run_one.sh` | | the driver of the leaf replay (24 chunks at a time) |
| `seam_neg.py`, `leaf_neg.py` | | negative controls |
| `layout_from_release.py`, `tables/` | | added for publication, not part of the run: rebuild the input layout from the release (below) |

`seamleaf` depends on `cfcheck` by path; the run used `cfcheck` at commit 746e2c5a, whose files are identical to
those in `../../closed-form/indep-checker/`.

## Items

1. The extra mass e of the final seam family is recomputed and equals the recorded e.
2. Structure: the pieces are P on [2, 5), the transition on [5, 6) and P′ on [6, 9) (S = 5), with P, P′ the wall
   profiles of the two interval families; the band condition of Lemma R5 with d = 2/5, compared as line densities.
3. Each level's family dominates the previous one; the final family dominates all levels.
4. The R5 root list is recomputed: 17,550 grid roots, of which 11,206 touch the bands; the list in the release is equal.
5. Coverage: the pieces of all levels lie in the roots, do not overlap and add up in volume (11,206 to 13,292 pieces
   per seam).
6. Leaf replay: every record of every seam is replayed leaf by leaf by `seamleaf`. For each record: all parts
   0..M−1 are present; every report binds the record's and the family's SHA-256; there are no refusals; every leaf
   is checked (`every` = 1, `checked_leaves` = `part_leaves`); part roots and leaves add up to the record totals.
7. Paths: least-E paths in the graph of the 30 seams and the 4 neighbouring pairs with equal profiles, with
   k₀ = max(7, 6 + 3r), for all 595 pairs, compared with the table.

## Results (2026-10-19)

- All 30 seams pass items 1–7: `../receipts/indep/seam_report_all.json` ("ALL PASS").
- Item 4: 17,550 roots, 11,206 touching; the shared list is equal.
- Item 6: 52 records, 363,550 roots, 4,921,514 leaves, 0 refusals. Leaves by kind: B3D 609,299; B3T:y 4,778;
  B3U:y 78,787; CORE 1,988,807; CORE1:Ty 1,128,338; CORE1:y 829,471; CORE1:P 29; EDGE 64,470; EMPTY 217,535.
  About 573 CPU hours, as 309 chunks on one cloud machine (24 at a time). The 309 reports are in
  `../receipts/indep/leaf_reports/`.
- Item 7: 595 rows, 0 mismatches; largest E 2907373/1000000 (r = 16, k₀ = 54).
- Controls: removing one part report, or writing a refusal into one report, makes item 6 fail for that seam;
  `seam_neg.py` and `leaf_neg.py` hold the controls for the other items and for single leaves, which fail as expected.
- A fix during the run: an earlier version of `seam_check2.py` looked up the leaf reports of the record `merged.rec`
  of one seam checked as a single level under the name `merged`, while the job list names it `L0`, and reported its
  8 complete parts as missing. The published version uses the job list's naming; the checks are unchanged.

## Names and paths in the published reports

The run used the working layout, which names intervals by labels (`tables/intervals_order.json`) and two records
of seam_11_12 by the runs that made them. For publication the absolute paths in the reports were made relative to
the input folder and those two record names were replaced by `record_part1` and `record_part2`, in the report
contents and file names and in `jobs.tsv`; nothing else was changed. The reports bind the SHA-256 of the records as
they were checked; the records in the release differ from them only in their first line, where the absolute paths
of the command line were reduced to file names. `../data/seam_records.json` lists both hashes and the hash
without the first line, which is the same for both.

## Run

    python3 layout_from_release.py RELEASE_DIR inputs          # rebuild the input layout from the release
    python3 seam_check2.py inputs --out report.json            # items 1-5 and 7
    cargo build --release --manifest-path seamleaf/Cargo.toml  # leaf replay, then run.sh in a folder with jobs.tsv and inputs/
    python3 seam_check2.py inputs --leaf-reports out --out report.json   # with item 6

With the published leaf reports, item 6 on the release records reports the hash difference described above; new
reports made by `seamleaf` from the release records bind the release hashes.
Items 1–5 and 7 on the layout rebuilt from the release (a laptop, 2026-10-19): all 30 seams PASS, item 7 with
0 mismatches, ALL PASS (`../receipts/indep/release_layout_items1to5_7.out`).
