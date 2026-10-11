# n = 6: the pinwheel packing in the triangle of side 2 + 4/√3 (upper bound)

**Claim.** 6 non-overlapping unit squares fit in the equilateral triangle of side v = 2 + 4/√3 ≈ 4.30940.
With the lower bound in `../PROOF.md`, this gives s△(6) = 2 + 4/√3.

## The packing (`packing.json`)

Two axis-parallel squares stand on the base, with bottom-left corners (1/√3, 0) and (1 + 1/√3, 0). The other four
squares are their images under the rotations by 120° and 240° about the centroid of the triangle: one pair of
side-by-side squares on each side. This is the packing listed in Erich Friedman's table "Squares in Triangles"
for n = 5 and n = 6 (Friedman, 1997); we claim no originality. The squares are the same as in `n6_packing.json`
of the release asset.

Every coordinate is written as [p, q], meaning p + q√3 with rational p, q, in the shared format
`packing-certificate/1` (see `tools/packing_check/README.md` at the repository root). `construct.py` writes the
file.

## Checks

From the repository root, with the two exact checkers of `tools/packing_check/`:

```
python3 tools/packing_check/check_packing.py  problems/triangle/certificates/n6/upper/packing.json
python3 tools/packing_check/check_packing2.py problems/triangle/certificates/n6/upper/packing.json   # needs sympy
```

Both print VALID. Negative controls (`make_negatives.py` writes them; both checkers reject each of them):

| file | change | result |
|---|---|---|
| `neg1_outside.json` | left base square moved left by 1/1000 | outside the triangle |
| `neg2_overlap.json` | right base square moved right by 1/1000 | overlaps the pair on the right side |
| `neg3_overlap_up.json` | right base square moved up by 1/1000 | overlaps the pair on the left side |
| `neg4_short_side.json` | triangle side shortened by 1/1000 | outside the triangle |

## Running

```
python construct.py packing.json     # regenerates the file byte for byte
python make_negatives.py             # regenerates the negative controls
```
