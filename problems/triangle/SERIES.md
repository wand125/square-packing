# The series n = T_{m−1} + 1 and the lattice certificate

For m ≥ 3 let v_m = m + 2/√3 and n_m = m(m − 1)/2 + 1 = T_{m−1} + 1.

## Construction of the certificate

`tools/make_lattice_cert.py m out.json` writes the certificate for side v_m:

- take the points of the unit triangular lattice that form an equilateral triangle of side m − 2,
  that is, T_{m−1} points of weight 1;
- place it so that its centroid is the centroid of the container.

The bottom row then lies at height 1/3 + √3/3 for every m, at x = 1 + 1/√3 + i. These are exactly
the shared vertical edges of a tight bottom row of m squares. All pairs at distance 1 are listed
for Lemma P. The certificate is invariant under the symmetry group of the triangle, and m = 3
gives the n = 4 certificate.

Each certificate proves s△(n_m) ≥ v_m: its total weight T_{m−1} is smaller than n_m.

## Where it is sharp

Axis-parallel rows standing on the base fit floor(m − 2j/√3) squares at height j, for j = 0, 1, ….

- For 3 ≤ m ≤ 8 the rows hold exactly n_m squares, so s△(n_m) = v_m:

  | m | n | rows |
  |---|---|---|
  | 3 | 4 | 3 + 1 |
  | 4 | 7 | 4 + 2 + 1 |
  | 5 | 11 | 5 + 3 + 2 + 1 |
  | 6 | 16 | 6 + 4 + 3 + 2 + 1 |
  | 7 | 22 | 7 + 5 + 4 + 3 + 2 + 1 |
  | 8 | 29 | 8 + 6 + 5 + 4 + 3 + 2 + 1 |

- For m = 9 the rows hold only 9 + 7 + 6 + 5 + 4 + 3 + 2 = 36 squares, so for n = 37 the
  certificate gives a lower bound only.

In general the lattice triangle has about m²/2 points. The number of squares that fit in the
triangle of side v_m grows only like its area, about (√3/4)m² ≈ 0.433m². So for large m the
certificate gives a valid but weak lower bound. It is not a route to a statement for all m.

## Results in this folder

| n | m | statement | checker nodes | time |
|---|---|---|---|---|
| 7 | 4 | s△(7) = 4 + 2/√3 | 1080 | 8 s |
| 11 | 5 | s△(11) = 5 + 2/√3 | 1586 | 15 s |
| 16 | 6 | s△(16) = 6 + 2/√3 | 2706 | 25 s |
| 22 | 7 | s△(22) = 7 + 2/√3 | 4240 | 63 s |
| 29 | 8 | s△(29) = 8 + 2/√3 | 5770 | 91 s |
| 37 | 9 | s△(37) ≥ 9 + 2/√3 (lower bound only) | 7668 | 171 s |

For n = 37 see the remarks in `certificates/n37/PROOF.md` about the value listed in Friedman's table.
