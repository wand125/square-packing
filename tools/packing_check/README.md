# packing_check: exact checks of packings (upper bounds)

An upper bound `s(n) ≤ S` is shown by a packing: `n` unit squares with disjoint interiors in the
container of size `S`. Every optimality result in this repository gives its packing as a
**packing certificate**, a JSON file with exact coordinates, and checks it with the two programs
here. The checks do not rely on any external table: when a packing is the one listed in Erich
Friedman's Packing Center, the page is cited as the source of the configuration only.

Both programs decide, in exact arithmetic,

1. the container has the claimed shape and size;
2. every square is a closed unit square (any orientation) contained in the closed container;
3. no two squares have overlapping interiors. Contact along edges or at corners is allowed.

The coordinates of the optimal packings are algebraic and the contacts are exact equalities, so
floating point cannot decide them. Both programs work in a real number field `Q(g)`, given by
the minimal polynomial of `g` and a rational interval that isolates it.

| | `check_packing.py` (method 1) | `check_packing2.py` (method 2) |
|---|---|---|
| containment | the 4 vertices of each square lie in the convex container | area(square ∩ container) = 1 |
| disjointness | separating axis: an edge of one square weakly separates the two | area(square ∩ square) = 0 |
| container | edge lengths and turning angles | all vertex-to-vertex distances |
| unit square | edges of length 1, each the previous turned by 90° | sides 1 and diagonals √2 |
| arithmetic | own polynomial arithmetic over `Fraction` | sympy polynomials over QQ |
| zero test | reduced representation is 0 (minpoly irreducible: rational root test, degree ≤ 3) | same, irreducibility by sympy |
| sign | interval arithmetic in `Fraction`, generator isolated by a Sturm sequence and bisection | mpmath interval arithmetic, generator isolated by sympy's real root isolation |
| dependencies | Python standard library | sympy (includes mpmath) |

The two programs share no code. Intersections in method 2 are computed by clipping one convex
polygon by the other (Sutherland–Hodgman) with exact intersection points.

## Usage

```sh
python3 tools/packing_check/check_packing.py  problems/hexagon/n3/packing.json
python3 tools/packing_check/check_packing2.py problems/hexagon/n3/packing.json
```

Each prints one line ending in `VALID` (exit code 0) or `INVALID` with the reasons (exit
code 1). `--json` prints a JSON report.

`test_packing_check.py` runs both programs on every packing of the repository (all must be
VALID) and on 14 broken variants (all must be INVALID): containers or squares moved by 10⁻¹²,
a tilt of the domino packing by a tiny change of angle, wrong sides and polynomials, a duplicate
square, a square that is not a square, a clockwise container. It takes about 5 s.

`make_packings.py` records how the packing files were written (`--check` compares them with the
files on disk).

## File format (`packing-certificate/1`)

```json
{
 "format": "packing-certificate/1",
 "problem": "squares in a regular hexagon, n = 3",
 "n": 3,
 "field": {"generator": "sqrt3", "minpoly": ["-3", "0", "1"], "interval": ["1", "2"]},
 "defs": {"v": "(1+sqrt3)/2", "h": "v*sqrt3/2"},
 "container": {"kind": "regular_hexagon", "side": "v",
               "vertices": [["-v/2", "-h"], ["v/2", "-h"], ["v", "0"], ["v/2", "h"], ["-v/2", "h"], ["-v", "0"]]},
 "packing": "free text describing the configuration",
 "source": "where the configuration is listed (not used by the checkers)",
 "squares": [ {"vertices": [[x, y], [x, y], [x, y], [x, y]]}, {"axis": [x, y]}, ... ]
}
```

- `field` (optional; omit for rational coordinates): `minpoly` lists the coefficients of the
  minimal polynomial of the generator, **constant term first**, as rational strings. `interval`
  is a rational interval containing exactly one real root, which is the generator; the checkers
  verify this.
- **Numbers** are either
  - an expression string with integers, `+ - * /`, parentheses, nonnegative integer powers `**`,
    the generator's name and names from `defs` (e.g. `"9 + 2*sqrt3/3"`); or
  - a list of rational strings, the coefficients of `1, g, g², …` (e.g. `["9", "2/3"]` for
    9 + (2/3)√3).
- `defs` (optional): named numbers, evaluated in order; later ones may use earlier ones.
- `container.kind` and its size:

  | kind | size | vertices (counter-clockwise) |
  |---|---|---|
  | `square` | `side` | 4 |
  | `rectangle` | `width`, `height` | 4, first edge = width |
  | `equilateral_triangle` | `side` | 3 |
  | `right_isosceles_triangle` | `side` = leg | 3, right angle at the first vertex |
  | `regular_hexagon` | `side` | 6 |

  The container may sit anywhere in the plane; only its shape and size are checked.
- `side_claim` (optional) states what the size is: `{"of": "height", "minpoly": [...],
  "largest_real_root": true, "below": "193/100"}` means the size is a root of the polynomial
  (constant term first) and, if `largest_real_root`, the largest real root. Method 1 checks this
  with a Sturm count above `below`; method 2 with sympy's root isolation.
- `squares`: exactly `n` entries. Each is `{"vertices": [4 points in cyclic order]}` (either
  orientation), a bare list of the 4 points, or `{"axis": [x, y]}` for the axis-parallel square
  with lower-left corner `(x, y)`.

## The certificates

| result | file |
|---|---|
| right isosceles triangle, n = 2, 3, 4, 6, 10, 15 | `problems/right-isosceles/certificates/nX/packing.json` |
| regular hexagon, n = 3 | `problems/hexagon/n3/packing.json` |
| 1 × 2 rectangle, n = 4 | `problems/domino/certificates/n4/packing.json` |
| square, s(22) = … = s(25) = 5 | `problems/square-lower-bounds/point_n21_L5/packing_n22.json` … `packing_n25.json` |
| square, s(45) = 7 | `problems/square-lower-bounds/point_n45_L7/packing_n45.json` |
| square, s(61) = 8 | `problems/square-lower-bounds/point_n61_L8/packing_n61.json` |
| square, s(77) = s(78) = 9 | `problems/square-lower-bounds/certificates/k2m4_n77_L9/packing_n77.json`, `packing_n78.json` |
