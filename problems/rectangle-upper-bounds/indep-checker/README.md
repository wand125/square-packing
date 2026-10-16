# Independent checkers

The two scripts here were written separately from the checkers in `../checker/`, from the statements and the
published specifications only, without access to the code in `../checker/`. They check the same finite statements
by their own construction of the measures. Their outputs are in `../receipts/`.

## `rect_k2m4_indep.py` (Theorem 1: the measure mu_{A,B} and Lemma R6)

`rect_k2m4_indep.py` is a self-contained Python 3 standard-library implementation
using `fractions.Fraction` for all geometry and mass calculations. It was written
from the statement of the checks, the two input files and their documentation in
evand/square-packing; no other checker was read or reused.

Run from `problems/rectangle-upper-bounds` after `./fetch_inputs.sh`:

```sh
python3 indep-checker/rect_k2m4_indep.py > receipts/rect_k2m4_indep.out
```

The recorded full run exited with code 0: all checks passed, including **38,342
window pairs** for all 17 requested rectangles. Runtime was **15.072 seconds** on
a laptop. Each check prints PASS/FAIL; any failed check or fatal error gives a
nonzero exit code. Input SHA256 values are checked against the required values;
the script's own SHA256 is printed as well.

The checker verifies exact equality with the supplied 9-box, nonnegativity of all
family masses, the all-size mass identity and strict deficit bound, and the
localisation restrictions. Canonical measures sum overlaps and merge adjacent
equal densities on each horizontal/vertical line, combine point masses, and
retain the density-one area rectangle. Restriction respects half-open ends:
a whole perpendicular line or atom on an excluded end is removed. Segment
endpoints themselves have no atoms, and area boundaries have zero area.
Supplemental hand-constructed checks of overlap normalization, point addition,
open/closed boundaries, and translation also passed.

## Assembly and total mass

Reflect the SW corner module into all four corners. On each wall of integer
length `L`, restrict the period-one profile to the **closed** tangential interval
`[3,L-3]`: place horizontal profile pieces at integer offsets `3,...,L-4`;
place vertical pieces at those offsets and also include the phase-zero vertical
pieces at `L-3`. Swap coordinates for the left/right walls and reflect for the
opposite walls. Corner and wall pieces on their common lines both contribute.
This reconstruction agrees exactly, as a measure, with the supplied box file.

The Lebesgue pieces described for the corner, wall profile, and middle together
form the single density-one rectangle `[14/5,A-14/5] × [14/5,B-14/5]`.
They are counted once. Let `P` be the singular profile mass per period, `C` the
singular corner mass, and `E` the phase-zero vertical profile mass. Direct exact
summation gives

```
P = 14/5
C = 338051747203/50000000000
E = 225022785617/200000000000
D = 214770225571/200000000000 > 1
M = 4C + 2(A+B-12)P + 4E + (A-28/5)(B-28/5) = AB-4D < AB-4.
```

The script checks the polynomial coefficients, proving the identity for every
integer `A,B >= 8`, and independently sums each tested rectangle's measure.

## Shift rule and exhaustive localisation

For an axis of length `L`, and window start `x` on the fifth-grid, use

```
s_L(x) = 0             if x <= 3,
         9-L           if x > L-5,
         4-ceil(x)     otherwise.
```

Apply this independently to each axis. A middle window starts in `(3,4]` after
translation; its half-open upper end is at most 6. It therefore avoids the extra
corner mass on both seam lines 3 and 6. End windows preserve distance to their
respective container end. Only the last window, starting at `L-2`, is closed at
its upper end; translated restrictions retain this closure flag.

For a given wall length the windows fall into three kinds: those starting at x <= 3 (left end), those starting
at x > L-5 (right end, including the closed last window) and the middle ones. This checker tests every window
of every listed size with this rule. The extension to all integer `A, B >= 8` is not a consequence of these
finite tests; it is the proof of Lemma R6 in `../README.md`. At 9 x 9 every shift is 0, so the shift rule itself
is exercised only by the sizes with a side of at least 10.

Every closed unit square has bounding width at most `sqrt(2) < 9/5` in each axis.
Rounding its minimum down to the fifth-grid loses less than `1/5`, so its maximum
is strictly inside the open end of the resulting length-two window. If the start
is capped at `L-2`, the last window is closed and still contains the square.
Equality of restricted measures therefore proves equal mass for the translated
closed square at every angle.

This checks the rectangle construction and the window agreement with the supplied 9-box.
It does not independently prove that every unit square in that box has mass at
least one (the separate `Valid9` statement).

## `rect_r1r2_indep.py` (Theorem 2: Lemmas R1 and R2 for interval 34)

Run from `problems/rectangle-upper-bounds` after `./fetch_inputs.sh` (Python 3.8 or later):

```sh
python3 indep-checker/rect_r1r2_indep.py > receipts/rect_r1r2_indep.out
```

The implementation uses only the Python standard library and `fractions.Fraction`
for all mathematical checks. Its sources are the statement of the checks, `../closed-form/SPEC.md` and the
family JSON files; no other checker was read or reused.

It extracts the wall profile from `family.json`, subtracts the seven stored wall
periods to recover the corner pieces, and verifies nonnegativity, repetition,
transposition, reversal, grid placement, and the terminal phase. Segment measures
are canonicalized by sweeping each supporting line, summing overlapping densities,
and merging adjacent equal densities. Closed-box restrictions retain lines on
box boundaries; isolated endpoint intersections have zero mass. Lebesgue parts
are compared separately as rectangles with density one.

For all 32 requested combinations of sizes and interval endpoints, it checks R2
(total mass, nonnegativity, support, and half-turn invariance), R1 at SW and in
SE local coordinates, and the adjacent wall profiles. Applicable square cases
are compared with a separate four-rotation construction. It also checks the
geometric inequalities at every endpoint pair at the minimum size, recomputes
both endpoint savings, checks they exceed 3/4, and prints SHA-256 hashes of both
family files and the script. `family_right.json` is hashed for identity; the
rectangle construction uses `family.json`.

The script explains how the exact profile identities, affine corner structure,
and monotone geometric inequalities extend the finite checks to the whole
interval and all integer side parameters at least seven. Endpoint sampling alone
is not the argument. This checks the requested structural R1/R2 claims for one
family; it does not replay the unit-square coverage certificates or verify the
full packing theorem.

The recorded full run passed **313/313 checks**, with **0 failures**, and exited
with status **0**. Runtime was **5.183 seconds** on a laptop. Runtime varies
by environment. Mathematical failures and fatal input errors produce `FAIL` and
a nonzero exit status. Full exact savings and all individual results are in
`rect_r1r2_indep.out`.
