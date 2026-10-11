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

## What is claimed

Constructions only. For every listed certificate, the k unit squares in it fit in the stated
a × b box; this is checked exactly by two checkers. Each box lies within 10⁻⁶ of the edge (for steps,
within 10⁻⁶ of the step's a). Nothing is claimed about optimality: we do not show that fewer than k squares fit
below the edge, and better packings may exist.

- k ≤ 10: the pieces are the boundary pieces of S_1, …, S_9 in Friedman's table, with the
  attributions given there. We add certified packings for them; the edges themselves are not new.
- k ≥ 11: the edges are our constructions. A piece is a grid packing, Friedman's piece of a smaller
  k with grid columns or rows added, a staggered family, or one of our types (named below). The
  formulas of our types were derived from the contact structure of numerically optimised packings
  (which squares and walls touch), solved symbolically; the certificates are the checked statements.

| k | pieces | certificates | our types |
|---|---|---|---|
| 2–10 | 1–9 each | 45 | — (Friedman's table) |
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

The edges for k ≤ 10 agree with Friedman's table. For k = 11 the square end (a = b) of the S11
piece reproduces the best known s(11) = 3.8770835900228….

## Files

- `data/edges/kNN.json`: the edge of F_k, one entry per piece (format in `FORMAT.md`).
- `certificates/kNN/<piece>-<i>.json`: the certified packings (release asset `rectangles-v1`,
  see `ASSET.json`).
- `checker/`: the two exact checkers and `check_all.py`.
- `SHA256SUMS`: checksums of the certificates (inside the release asset).

## How to check

From the repository root:

    gh release download rectangles-v1 -p certificates.tar.gz
    tar xzf certificates.tar.gz -C problems/rectangles
    cd problems/rectangles
    sha256sum -c SHA256SUMS
    python checker/check_all.py

`check_all.py` runs both checkers on every certificate (a few seconds) and checks that each
certificate's box and number of squares match its listing. Python 3, standard library only.

## Not done yet

- Lower bounds (that k squares do not fit below the edge).
- k ≥ 16.

## Author

Hiroaki Hosono (GitHub: wand125).

## Licence

MIT (see `LICENSE`). The edges for k ≤ 10 are from Erich Friedman's Math Magic, June 2010, with
the attributions given there.
