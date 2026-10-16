# n = 46: a packing in the triangle of side 10 + 2/√3 (upper bound)

**Claim.** 46 non-overlapping unit squares fit in the equilateral triangle of side v = 10 + 2/√3 ≈ 11.15470.
With the lower bound s△(46) ≥ 10 + 2/√3 (`../PROOF.md`), this gives s△(46) = 10 + 2/√3.

## The packing (`n46_packing.json`, picture `n46_packing.png`)

This is Joshua Wolk's n = 46 packing in Erich Friedman's table "Squares in Triangles" (September 2026, side
11.15470). We do not claim it as new. Here it is given with exact coordinates and an exact check.

- **Bottom row.** Ten axis-parallel squares stand on the base, at x = 1/√3 + i (i = 0..9). At height 1 the
  width of the triangle is exactly 10, so this row is tight.
- **Above it.** Nine more axis-parallel squares, 15 squares tilted by 60° (aligned with the left side) and
  12 squares tilted by −60° (aligned with the right side), placed as in the published picture.

We read the positions off the published picture, solved a linear program for the free offsets of each square
along its row or side, and rounded them to rationals with denominator 1000. The resulting exact centres and
angles are listed in `construct.py`; they are the whole construction, and the checks below do not rely on the
linear program.

Every coordinate is written as [p, q], meaning p + q√3 with rational p, q. `construct.py` writes the file.

## Checks

Two checkers, written independently, both with exact arithmetic in Q(√3) (the same two as for n = 37):

- `check_sat.py` (sympy): each polygon is a unit square (sides 1, right angles, counter-clockwise), every
  corner lies in the closed triangle, and every pair of squares is separated by an edge normal of one of them
  (touching allowed).
- `check_clip.py` (its own Q(√3) number class, no sympy): each polygon has sides 1 and area 1; clipping it by
  the triangle leaves area 1; and for every pair, the Sutherland–Hodgman intersection has area 0.

Both print VALID for `n46_packing.json`. The file is also in the shared format `packing-certificate/1` and passes
the repository's common checker: `python3 tools/packing_check/check_packing.py problems/triangle/certificates/n46/upper/n46_packing.json`
(run from the repository root).

Negative controls (`make_negatives.py` writes them; both checkers, and the common checker, reject each of them):

| file | change | result |
|---|---|---|
| `neg1_outside.json` | bottom-left square moved left by 1/1000 | outside the triangle |
| `neg2_overlap_row.json` | a square of the second row moved down by 1/100 | overlap |
| `neg3_short_side.json` | triangle side shortened by 1/1000 | outside the triangle |
| `neg4_pblock.json` | a square tilted by 60° moved right by 1/100 | overlap |
| `neg5_mblock.json` | a square tilted by −60° moved left by 1/100 | overlap |

## Running

```
python construct.py n46_packing.json     # regenerates the file byte for byte
python make_negatives.py                 # regenerates the negative controls
python check_sat.py n46_packing.json     # needs sympy
python check_clip.py n46_packing.json    # standard library only
```
