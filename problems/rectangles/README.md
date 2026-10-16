# Unit squares in a rectangle: certified constructions along the edges F_k (k = 2..15)

For a box of height a and width b (a ≤ b), let s(a, b) be the largest number of non-overlapping
unit squares (any positions, any angles) that fit in it. Following Erich Friedman, Math Magic,
June 2010 (https://erich-friedman.github.io/mathmagic/0610.html), S_n is the set of boxes that hold
at most n unit squares. Its boundary is where n + 1 squares begin to fit.

Here we use

    F_k = { (a, b) : a ≤ b, s(a, b) ≥ k },

so the edge of F_k is the boundary of S_(k−1). For each k = 2..15 we give the edge of F_k as a
sequence of pieces from a = 1 to the diagonal a = b. Each piece has a formula in a and b and one or
more certified packings near it.

This is version 2 (release `rectangles-v2`). Version 1 (release `rectangles-v1`) stays available
unchanged.

## What changed in version 2

The edge for k = 7 is lower on part of its range. Every other k is as in version 1.

- **k = 7, 2√2 ≤ a < 3 (new piece 7.N1).** Seven unit squares fit in an a × b box with

      a = −(3p² − 2p + 1)/(2p),   b = (3p⁴ + 10p² − 4p − 1)/(4p²),   1 − √2 ≤ p < −1/3,

  where p = tan(θ/2) and θ is the tilt of two squares that lean against each other at the same
  angle; the other five squares are axis-parallel and the packing is rigid. Eliminating p, in
  Friedman's coordinates (x the long side, y the short side):

      3x² + 2xy² − 10xy − 10x − y⁴ + 6y³ − 14y² + 20y + 25 = 0,   2√2 ≤ y ≤ 3.

  At a = 2√2 (θ = 45°) it meets piece 6.5 of S_6 in Friedman's table, x + y = 5 + √2, at
  b = 5 − √2, and for 2√2 < a < 3 it is narrower: as a → 3, b → 10/3 against 2 + √2 for piece 6.5,
  a difference of 2 + √2 − 10/3 ≈ 0.0809. Piece 6.5 now ends at y = 2√2, aspect ratio
  y/x = (4 + 10√2)/23 = 0.788…; along 7.N1 the aspect ratio rises to 9/10 at a = 3. Besides the
  representative certificate of the piece, `data/sweeps/k07-7.N1.json` lists 150 certified boxes
  on 2√2 ≤ a < 3, each strictly below x + y = 5 + √2.

The new piece comes from a search over boxes below the version 1 edges, followed by sweeps in a
(b minimised at fixed a) and a symbolic solution of the contact structure, as for the version 1
types. It meets piece 6.5 at the crossing of the two formulas (a = 2√2), so the edge is given by
formulas throughout. We have not found the packing of 7.N1 in the literature or in other public
tables we know of; we do not claim that it is new.

## What is claimed

Constructions only. For every listed certificate, the k unit squares in it fit in the stated
a × b box; this is checked exactly by two checkers. Each box listed in `data/edges` lies within 10⁻⁶
of the edge (for steps, within 10⁻⁶ of the step's a); the boxes in `data/sweeps` are sample points
below piece 6.5, not points of the formula. Nothing is claimed about optimality: we do not show that fewer than k squares fit
below the edge, and better packings may exist.

- k ≤ 10: the pieces are the boundary pieces of S_1, …, S_9 in Friedman's table, with the
  attributions given there, except piece 7.N1 (ours, see above). We add certified packings for them;
  apart from 7.N1 the edges themselves are not new. Keys are Friedman's piece numbers; the new piece
  is 7.N1.
- k ≥ 11: the edges are our constructions. A piece is a grid packing, Friedman's piece of a smaller
  k with grid columns or rows added, a staggered family, or one of our types (named below). The
  formulas of our types were derived from the contact structure of numerically optimised packings
  (which squares and walls touch), solved symbolically; the certificates are the checked statements.

| k | pieces | certificates | our types |
|---|---|---|---|
| 2–10 | 1–9 each (k = 7: 7) | 46 | N7 (k = 7, piece 7.N1); otherwise Friedman's table |
| 11 | 17 | 25 | n11a, L11, R11, T41, S11 |
| 12 | 12 | 16 | P1, R12, 45°, R12b |
| 13 | 12 | 15 | 45° family |
| 14 | 19 | 35 | P1, R12, 45°, R12b (12-square types plus a column), L11, R11 (plus a column), T35, T22, T58, T54 |
| 15 | 15 | 21 | U1, V, U2, W |

Each piece also has a `note` with its kind (rigid type, one- or two-parameter mechanism with b at
its stationary point, grid, staggered family, Friedman's piece, step), the number of tilt angles
and the form of the curve (straight line, rational curve in p = tan(θ/2), implicit curve). A step is
a jump of b at constant a. Where an arrangement changes within the range of a formula, the piece is
split, so each piece has one arrangement.

The edges for k ≤ 10 agree with Friedman's table, except k = 7 on 2√2 < a < 3 (piece 7.N1, lower). For k = 11 the square end (a = b) of the S11
piece reproduces the best known s(11) = 3.8770835900228….

## Files

- `data/edges/kNN.json`: the edge of F_k, one entry per piece (format in `FORMAT.md`).
- `data/sweeps/k07-7.N1.json`: 150 further certified boxes along piece 7.N1 (same certificate format).
- `certificates/kNN/<piece>-<i>.json` and `certificates/k07-sweep/`: the certified packings (308
  in all; release asset `rectangles-v2`, see `ASSET.json`).
- `checker/`: the two exact checkers and `check_all.py`.
- `SHA256SUMS`: checksums of the certificates (inside the release asset).

## How to check

From the repository root:

    gh release download rectangles-v2 -p certificates.tar.gz
    tar xzf certificates.tar.gz -C problems/rectangles
    cd problems/rectangles
    sha256sum -c SHA256SUMS
    python checker/check_all.py

`check_all.py` runs both checkers on every certificate listed in `data/edges` and `data/sweeps`
(a few seconds) and checks that each certificate's box and number of squares match its listing. Python 3, standard library only.

## Not done yet

- Lower bounds (that k squares do not fit below the edge).
  Upper bounds for rectangles just below integer size: see [../rectangle-upper-bounds/](../rectangle-upper-bounds/).
- k ≥ 16.
- Further pieces for k = 11 to 15 found by the same search (a later version).

## Author

Hiroaki Hosono (GitHub: wand125).

## Licence

MIT (see `LICENSE`). The edges for k ≤ 10, apart from piece 7.N1, are from Erich Friedman's Math
Magic, June 2010, with the attributions given there.
