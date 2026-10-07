# Code versions used by the full run

The run was resumed once with changed code.  Records are appended root by root, so the version of each root
is determined by its line number in the record.

| version | record lines (roots) | started (UTC, 2026-10-01) |
|---|---|---|
| V1 | roots 1 – 31,825 (record lines 2 – 31,826; line 1 is the header) | 05:10 |
| V2 | roots 31,826 – end | 07:57 (resumed with `--resume`) |

sha256 (first 16 hex digits) of the files that matter; all others identical in V1 and V2:

| file | V1 | V2 |
|---|---|---|
| cover `L4_k02_box7.txt` | c0a6750997897c21 | same |
| `run_all.py` | bc3bf0a55322163d | 899144f999e69cb0 |
| `tier_b2.py` | 36e97e6129f683f3 | ebd2a1d0a47a8481 |
| `tier_a.py` | bb23e935a2e30901 | same |
| `tier_b.py` | ca72a14909e3d242 | same |
| `solver.py` | aa462c15f7230991 | same |
| `rf.py` | c527689cec0072e3 | same |
| `cover.py` | bdaee4f0390d76d0 | same |

The V1 hashes are those in the record's header line.  `versions/V1/` holds `run_all.py` and `tier_b2.py` of V1,
reconstructed by reverting the edits and checked against these hashes; `versions/V2/` holds the V2 copies.

**What changed V1 → V2 (no change to any proof step):**
* `run_all.py`: (a) the hand-off rule for boxes not touching `u = 0`: V1 handed a box to Tier B when its centre
  width was `<= 1/40`; V2 when both the centre width and `1.4 x` its u-width are `<= 1/320`.  This only decides
  which certifying method is tried on which box; every leaf is still certified by Tier A or Tier B.  (b) The
  message of an uncertified box includes a witness pose when Tier B finds one.
* `tier_b2.py`: on a failed value check, Tier B also returns a concrete pose with its exact mass below 1
  (`witness`).  The acceptance logic is unchanged.

**Before V1** (discarded, not in the record): a run with a defect in the algebraic-number class `Alg`
(`tier_b.py`): an isolating interval whose end was a root of the same polynomial could be refined towards that
end.  Fixed in V1 (ends are moved off roots with exact Sturm counts at construction); all records made before the
fix were discarded.

**Version-independent checks.**  `check_record.py` does not use the driver's code or its version: it re-checks
that the roots are exactly the product grid of `[0, 7]² × [−1/2, 1/2]`, that the leaves of every root form a
bisection partition of it, that EMPTY leaves contain no admissible centre (exact), that no Tier B leaf contains
`u = 0` in its interior, and that there are no uncertified boxes or counterexamples.  It does not re-run the
certificates of every CORE or TIERB2 leaf; `--recheck N` and `--recheck-b N` re-run Tier A on N random CORE leaves and Tier B (current code) on N random TIERB2 leaves, so leaves of both versions can be re-certified by one code version.

## Split over two machines (2026-10-01, 20:47 UTC)

From the split on, the remaining roots were divided by centre x (same code V2, same cover):

| record | centres | how |
|---|---|---|
| `runs/full.jsonl` (machine 1) | x in [0, 11/2) | `--centers 0 11/2 0 7 --resume` (101,563 roots were already in the record, all with x < 11/2) |
| `runs/full_b.jsonl` (machine 2) | x in [11/2, 7] | `--centers 11/2 7 0 7`, a new record with its own header |

The two records are checked together: `check_record.py <cover> full.jsonl full_b.jsonl` requires the union of
their roots to be exactly the product grid, each root exactly once.

## Records as published

Before publication, only the header line (line 1) of each record was edited: the keys of its `sha256` map, which
were absolute paths on the compute machine, were made relative (`src/run_all.py`, ...), and a `note` field saying
so was added.  The hash values and every other line are unchanged; `check_record.py` does not read the header.

| record | sha256 as run (uncompressed) | sha256 as published (uncompressed) |
|---|---|---|
| `full.jsonl` | abf9ad740cd9c63923e7f2075e216f588360fcc22921581d83464d73c11e2755 | bff065feffed8551fcbb636c00417061417fee14164368296f2ece3ccc8d5ba6 |
| `full_b.jsonl` | d9eaf41d4f9846b867265a400bbdaeff14678b2af9486eaf01ecba90bb70f9d9 | e0fb45b60ed9e4986f7dd7dba3ff6b01787a7f5943387d1dd6a57231fd10123a |

`records.sha256` (in the release) lists the published files, compressed and uncompressed.

## After the Valid7 run

For the ValidTilt9 run (README, section ValidTilt9) `src/run_all.py` was extended once more (sha256 cd6627de…):
it adds the options `--bmid-u` / `--bmid-w` and behaves exactly as before with their defaults.  The Valid7 run's
drivers remain in `versions/V1/` and `versions/V2/` above; the ValidTilt9 run's versions and history are in the
`MERGE.md` of the release `records-tilt9-v1`.
