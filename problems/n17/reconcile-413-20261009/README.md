# Reconciliation of the jlevy/squares#413 roster with the upstream admitted ledger and the distance-two tail (2026-10-09)

All counts below are computed with upstream tools only, on upstream's own state space and D4 action, not with our counting.

**Upstream versions used.**

- Tools and ledger: jlevy/squares `main` at `f0ec5b663b10167f1ff5ccbc3b2a3de8dd1ee9ae`. `packing/devtools/census_n17_certified.py` is blob `923813b6`, the same blob the merged receipt `exp-258-n17-draw-31/census.json` (at `9137815`) records; `select_n17_sub_patterns.py` is `81409f66`; the ledger `certified-sub-patterns.yaml` is blob `9e72b79b`, the one the receipt and the partition record. None of these files differs between `9137815` and `f0ec5b6`.
- Baseline check: the 58 admitted entries leave 36,784 states / 4,685 orbits, as in the merged receipt.
- PR404 baseline: the ledger at `ecb0bf82` (blob `a4c2ee00`, 60 admitted) leaves 36,768 / 4,683, as in its receipt.
- Distance-two tail: `exp-259-current-admitted-residue/partition.json` at `ecb0bf82` (SHA-256 `c2fd3816…`); its orbits with `distance == 2` are 95 orbits / 744 states (`orbit_size` summed), as stated in #405.

**Method.**

- Canonical D4 mask: `census_n17_certified.class_mask` on the row's cell names. Every row's listed cells are already the canonical representative.
- Overlap with an admitted entry: whether some D4 image of the entry's class lies inside the row's class (the row is implied by the entry), or some image of the row lies inside the entry (the row implies the entry), using the entries' `cells`.
- Tail coverage: a tail orbit is covered when its representative state (`mask`) contains some D4 image of the row; all states of a covered orbit are covered.
- Alone: `census_n17_certified.removal` on the survivors of the admitted entries, the same function the census uses for a pending entry's marginal count.

**Common premises of every row.** All of the following hold for every row:

- Cover design `ring-3-voronoi-8-tabbed-unique`, cap U = 1169/250.
- Square s is centred in the closed cell s (touching allowed).
- Every square has the same independent angle interval [3602879701896397/2^53, 8875677602976641/2^52] (about [0.4, 0.4 + π/2]), recorded in the header as `root_angles`. The standing verifier checks that its width exceeds an upper enclosure of π/2.
- The 17-square container is [0, U]²; cell polygons are the cover's.

For rows with a verified certificate, the verifier's header check confirms these premises: the cells equal the cover's, the cap equals the cover's U, and each root angle interval is wider than π/2. For computed rows they are the producer's settings, and the header will be checked when the certificate exists.

| Row | Cells (canonical) | D4 mask | Arity | Status | Premises | Overlap with main's 58 admitted | Overlap with PR404's 2 added | Distance-2 tail orbits / states | Alone on main: orbits / states | Alone on PR404: orbits / states |
|---:|---|---:|---:|---|---|---|---|---:|---:|---:|
| 1 | side-S1, side-S2, interior-SW, interior-NW, interior-W, interior-S, interior-SE | 5181696 | 7 | certificate verified (unmodified standing FULL + fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 19 / 152 | 19 / 152 |
| 2 | side-W0, side-N1, interior-SW, interior-NW, interior-W, interior-S, interior-SE | 5177920 | 7 | certificate verified (unmodified standing FULL + fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 38 / 284 | 38 / 284 |
| 3 | side-S0, side-S1, interior-SW, interior-NW, interior-W, interior-S, interior-N | 2031888 | 7 | certificate verified (standing node checks over all nodes via a parallel driver + fast verifier; unmodified standing FULL receipt pending #445) | header checked by verifier | independent | independent | 0 / 0 | 6 / 48 | 6 / 48 |
| 4 | side-W0, side-W2, interior-SW, interior-NW, interior-W, interior-S, interior-N | 2048064 | 7 | certificate verified (standing node checks over all nodes via a parallel driver + fast verifier; unmodified standing FULL receipt pending #445) | header checked by verifier | independent | independent | 0 / 0 | 15 / 108 | 15 / 108 |
| 5 | interior-NW, interior-W, interior-S, interior-N, interior-E, interior-SE | 8257536 | 6 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 38 / 288 | 38 / 288 |
| 6 | side-S1, side-N1, interior-SW, interior-NW, interior-S, interior-N, interior-SE, interior-NE | 14353152 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 72 / 560 | 72 / 560 |
| 7 | side-W0, side-S1, side-W1, side-W2, interior-SW, interior-NW, interior-W, interior-S | 1000768 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 5 / 32 | 5 / 32 |
| 8 | side-N0, side-W0, side-S1, interior-SW, interior-NW, interior-W, interior-S, interior-N | 2031968 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 21 / 168 | 21 / 168 |
| 9 | side-S0, side-W0, side-W2, interior-SW, interior-NW, interior-W, interior-S | 999504 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 54 / 420 | 54 / 420 |
| 10 | corner-SE, side-S0, side-S1, side-S2, interior-SW, interior-NW, interior-W, interior-S | 987410 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 8 / 64 | 8 / 64 |
| 11 | side-W0, side-W1, interior-SW, interior-NW, interior-W, interior-S, interior-N | 2032704 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 42 / 328 | 42 / 328 |
| 12 | side-N0, side-N1, interior-SW, interior-NW, interior-W, interior-N, interior-E, interior-SE | 7799328 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 1 / 8 | 1 / 8 |
| 13 | side-E1, interior-SW, interior-NW, interior-W, interior-N, interior-E, interior-SE | 7800832 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 33 / 264 | 33 / 264 |
| 14 | corner-SW, side-S0, side-W0, side-W2, interior-SW, interior-NW, interior-W | 475217 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 357 / 2800 | 357 / 2800 |
| 15 | corner-SW, side-N0, side-W0, side-W1, interior-SW, interior-NW, interior-W | 459873 | 7 | computed (no certificate yet) | producer settings | independent | row inside Tail A and Tail B (both entries contain an image of the row) | 0 / 0 | 770 / 6152 | 768 / 6136 |
| 16 | side-N0, side-W2, interior-SW, interior-NW, interior-W, interior-S, interior-E | 3096608 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 15 / 120 | 15 / 120 |
| 17 | side-W0, side-W2, interior-SW, interior-NW, interior-W, interior-N, interior-E, interior-SE | 7815232 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 35 / 280 | 35 / 280 |
| 18 | side-N0, side-W0, side-S1, side-W1, interior-SW, interior-NW, interior-W, interior-S | 984416 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 112 / 896 | 112 / 896 |
| 19 | side-S0, side-W0, side-E1, interior-SW, interior-NW, interior-W, interior-S, interior-E | 3082320 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | row inside Tail A and Tail B (both entries contain an image of the row) | 0 / 0 | 79 / 632 | 77 / 616 |
| 20 | side-W0, side-S1, side-W2, interior-SW, interior-NW, interior-W, interior-S, interior-E | 3096896 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 40 / 316 | 40 / 316 |
| 21 | side-S1, side-S2, interior-NW, interior-W, interior-S, interior-N, interior-SE | 6164736 | 7 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 26 / 208 | 26 / 208 |
| 22 | corner-SW, side-W0, side-S1, side-W1, interior-SW, interior-NW, interior-W, interior-S | 984385 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | independent | 0 / 0 | 139 / 1112 | 139 / 1112 |
| 23 | corner-NW, side-N0, side-W0, side-W1, side-W2, interior-NW, interior-W, interior-S | 935012 | 8 | computed (no certificate yet) | producer settings | independent | independent | 1 / 8 | 39 / 308 | 39 / 308 |
| 24 | corner-SE, side-S0, side-S1, side-S2, interior-NW, interior-W, interior-S, interior-SE | 5116178 | 8 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 2 / 16 | 2 / 16 |
| 25 | corner-SW, corner-NW, side-S0, side-W0, side-W1, side-W2, interior-SW, interior-NW | 214101 | 8 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 465 / 3636 | 465 / 3636 |
| 26 | side-N0, side-W0, side-W1, interior-SW, interior-NW, interior-W, interior-S, interior-E | 3081312 | 8 | certificate verified (fast verifier) | header checked by verifier | independent | row inside Tail A and Tail B (both entries contain an image of the row) | 0 / 0 | 143 / 1144 | 141 / 1128 |
| 27 | side-N1, side-E1, interior-SW, interior-W, interior-S, interior-N, interior-E | 4000256 | 7 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 322 / 2500 | 322 / 2500 |
| 28 | side-N0, side-W0, side-S1, interior-SW, interior-NW, interior-W, interior-S, interior-E | 3080544 | 8 | certificate verified (fast verifier; after the issue body was written) | header checked by verifier | independent | independent | 0 / 0 | 95 / 760 | 95 / 760 |
| 29 | side-N0, side-W2, interior-SW, interior-NW, interior-W, interior-N, interior-E, interior-SE | 7815200 | 8 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 52 / 416 | 52 / 416 |
| 30 | corner-NW, side-S1, side-W1, side-W2, interior-SW, interior-NW, interior-W, interior-S | 1000708 | 8 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 44 / 352 | 44 / 352 |
| 31 | corner-NW, side-N0, side-W0, side-S1, interior-SW, interior-NW, interior-W, interior-S | 983396 | 8 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 117 / 936 | 117 / 936 |
| 32 | side-W0, side-S1, side-W1, interior-SW, interior-NW, interior-S, interior-N, interior-SE, interior-NE | 14353728 | 9 | computed (no certificate yet) | producer settings | independent | independent | 0 / 0 | 105 / 828 | 105 / 828 |
| 33 | corner-SW, side-N0, side-W0, interior-NW, interior-W, interior-S, interior-N, interior-SE | 6160481 | 8 | computed (certificate not generated) | producer settings | independent | independent | 0 / 0 | 192 / 1520 | 192 / 1520 |

**Totals.**

- No row overlaps any of main's 58 admitted entries; all 33 are independent of them.
- Rows 15, 19 and 26 each lie inside both PR404 additions, Tail A (state 3096311) and Tail B (3096315), so each of these rows alone already removes both tail orbits.
- The 33 rows together with main's 58 entries leave 19,164 states / 2,449 orbits, from 36,784 / 4,685.
- With PR404's 60 entries they leave 19,164 / 2,449; the two added entries are implied by the rows.
- No row contains another row.
- Of the 95 distance-two orbits / 744 states, the rows cover 1 orbit / 8 states: row 23 covers the orbit of state 1965787. The other 94 orbits / 736 states are untouched by every row.
- The endpoint state survives in every count.

Every number in the table is reproducible from the listed upstream files. The script (`reconcile_413.py`), its input rows (`rows413.json`) and full output (`reconcile_413.json`) are in this folder. Run the script from `packing/` of upstream main with the listed upstream files.


Note: `rows413.json` was read from the #413 issue body before the correction of 2026-10-09 (https://github.com/jlevy/squares/issues/413#issuecomment-6064443079), so its `verified_with` text for rows 3 and 4 still says "upstream standing verifier (full)". That text is not used in any count; the table above gives the corrected verification status.
