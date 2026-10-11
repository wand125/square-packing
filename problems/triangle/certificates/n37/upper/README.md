# n = 37: a packing in the triangle of side 9 + 2/√3 (upper bound)

**Claim.** 37 non-overlapping unit squares fit in the equilateral triangle of side v = 9 + 2/√3 ≈ 10.15470.
With the lower bound s△(37) ≥ 9 + 2/√3 (`../PROOF.md`), this gives s△(37) = 9 + 2/√3.

## The packing (`n37_packing.json`, picture `n37_packing.png`)

- **Bottom row.** Nine axis-parallel squares stand on the base, at x = 1/√3 + i (i = 0..8). At height 1 the
  width of the triangle is exactly 9, so this row is tight.
- **The triangle above.** Above height 1 lies an equilateral triangle of side 9. It holds 28 squares in the shape
  of the n = 28 packing in Erich Friedman's table "Squares in Triangles" (side 3 + 10/√3 ≈ 8.774, Friedman 1997):
  - axis-parallel rows of 7, 6, 3 and 2 squares, each pushed against the left side;
  - a block of 3 + 2 squares aligned with the right side, at distances 3 and 89/25 along that side;
  - a block of 3 + 2 squares aligned with the left side, at distances 53/10 and 23/4 along that side.
  Since 3 + 10/√3 < 9, there is room to spare: apart from the contacts inside each row and block and with the
  sides they lean on, the groups are at least about 0.08 apart.

We do not claim this construction as new. Friedman's table lists a packing of 37 squares by Gianluca Costantino
(May 2026), which may well have the same structure, and the upper part uses the shape of Friedman's n = 28 packing
(1997). Here the packing is given with exact coordinates and an exact check.

Every coordinate is written as [p, q], meaning p + q√3 with rational p, q. `construct.py` writes the file.

## Checks

Two checkers, written independently, both with exact arithmetic in Q(√3):

- `check_sat.py` (sympy): each polygon is a unit square (sides 1, right angles, counter-clockwise), every
  corner lies in the closed triangle, and every pair of squares is separated by an edge normal of one of them
  (touching allowed).
- `check_clip.py` (its own Q(√3) number class, no sympy): each polygon has sides 1 and area 1; clipping it by
  the triangle leaves area 1; and for every pair, the Sutherland–Hodgman intersection has area 0.

Both print VALID for `n37_packing.json`. The file is also in the shared format `packing-certificate/1` and passes
the repository's common checker: `python3 tools/packing_check/check_packing.py problems/triangle/certificates/n37/upper/n37_packing.json`
(run from the repository root).

Negative controls (`make_negatives.py` writes them; both checkers, and the common checker, reject each of them):

| file | change | result |
|---|---|---|
| `neg1_outside.json` | bottom-left square moved left by 1/1000 | outside the triangle |
| `neg2_overlap_row.json` | a square of the second row moved down by 1/1000 | overlap |
| `neg3_short_side.json` | triangle side shortened by 1/1000 | outside the triangle |
| `neg4_block.json` | a square of the left block moved down by 1/100 | overlap |
| `neg5_rblock.json` | a square of the right block moved down by 1/100 | overlap |

## Running

```
python construct.py n37_packing.json     # regenerates the file byte for byte
python make_negatives.py                 # regenerates the negative controls
python check_sat.py n37_packing.json     # needs sympy
python check_clip.py n37_packing.json    # standard library only
```
