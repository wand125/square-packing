# Unit squares in an equilateral triangle: optimal packings for n = 2, 3, 4, 6, 7, 11, 16, 22, 29 and a lower bound for n = 37

Let s△(n) be the side of the smallest equilateral triangle that contains n non-overlapping unit
squares (any positions, any angles).

| n | s△(n) | ≈ | optimal packing (upper bound) | lower-bound certificate |
|---|---|---|---|---|
| 2 | 2 + 2/√3 | 3.1547 | two squares side by side on the base | the centroid, weight 1 (total 1) |
| 3 | 3/2 + √3 | 3.2321 | "pinwheel": one square on each side | 7 points of weight 1/3 (total 7/3) |
| 4 | 3 + 2/√3 | 4.1547 | three squares on the base, one on top | 3 points of weight 1 (total 3) and Lemma P |
| 6 | 2 + 4/√3 | 4.3094 | pinwheel of three side-by-side pairs, one pair on each side | localization tree: 6 certificates with exclusion boxes and obstacle points, closed by a lemma on three squares |
| 7 | 4 + 2/√3 | 5.1547 | rows 4 + 2 + 1 | lattice, 6 points of weight 1 |
| 11 | 5 + 2/√3 | 6.1547 | rows 5 + 3 + 2 + 1 | lattice, 10 points |
| 16 | 6 + 2/√3 | 7.1547 | rows 6 + 4 + 3 + 2 + 1 | lattice, 15 points |
| 22 | 7 + 2/√3 | 8.1547 | rows 7 + 5 + 4 + 3 + 2 + 1 | lattice, 21 points |
| 29 | 8 + 2/√3 | 9.1547 | rows 8 + 6 + 5 + 4 + 3 + 2 + 1 | lattice, 28 points |
| 37 | ≥ 9 + 2/√3 | ≥ 10.1547 | (lower bound only) | lattice, 36 points |

The packings are the best known ones in Erich Friedman's Packing Center, "Squares in Triangles"
(https://erich-friedman.github.io/packing/squintri/). The certificates show that they are optimal. For n = 7, …, 29 the packing is rows of
axis-parallel squares standing on the base, and the certificate is a patch of the unit triangular lattice (all weights 1, with Lemma P);
the series and why it stops being sharp at n = 37 are described in `SERIES.md`.
The results are computer-assisted and checked by two independent checkers; all except n = 6 are also checked in Lean 4. They have not been peer reviewed.

## Novelty

- Friedman's table lists n = 1 and n = 2 as "Trivial". The proof for n = 2 is included because it
  is the simplest instance of the method.
- For n = 3, 4, 6, 7, 11, 16, 22 and 29 we are not aware of a previous proof of optimality. We checked:
  - Friedman's page (as of 2026-09-30), which gives the packings but no proofs or lower bounds;
  - an arXiv search of abstracts containing "equilateral triangle", "squares" and "packing";
  - general web searches.

  We did not find a lower bound for this container. If you know of one, please open an issue.
- For n = 37 we prove only the lower bound s△(37) ≥ 9 + 2/√3 ≈ 10.15470. Friedman's table (as of
  2026-10-01) lists a packing of side 10.15299 for n = 37, which is incompatible with this bound.
  See the remarks in `certificates/n37/PROOF.md`; we do not have the coordinates of that packing.

## The method

Each lower bound is a finite weighted point set in the triangle T_v of side v = the claimed
value. The checkers prove two things:

1. **Capture.** Every closed unit square Q ⊆ T_v, at any position and any angle, contains points
   of total weight ≥ 1. A point on the boundary of Q counts. This is checked at the container
   itself, with margin zero.
2. **Budget.** The total weight is < n.

Then n squares do not fit in a triangle of side L < v.

- Suppose they did, with disjoint interiors. Translate each square by (v/L − 1)(c_i − G), where
  c_i is its centre and G the common centroid.
- The translated squares are pairwise disjoint closed unit squares in T_v.
- Each of them captures weight ≥ 1, so the total would be ≥ n. This contradicts the budget.

With the packing of side v, this gives s△(n) = v. Details are in `certificates/n*/PROOF.md`.

**Localization (n = 6).** The optimal packing for n = 6 is held in place by contacts between squares, not only
by the walls, and the proof uses a tree of certificates instead of a single one (`certificates/n6/PROOF.md`):

1. A D3 certificate with total < 6 whose exceptions are small boxes around the pinwheel positions. So some square
   is within 0.01 of its pinwheel pose.
2. With that square fixed in its box (an obstacle, given by obstacle points that every square disjoint from it
   avoids), a certificate with total < 5 forces a second square into its box.
3. With two squares in their boxes, a certificate with total < 4 forces the third square of a C3 image of the
   triple {0, 1, 3} into its box.
4. A lemma on three squares, checked in interval arithmetic, shows that three squares in these boxes need
   L ≥ v. With strictly disjoint squares this is a contradiction.

The checker handles exclusion boxes and obstacle points (`checker/SPEC.md`, last section); the obstacle points
are proved separately (`certificates/n6/stage2/`).

**Lemma P (used for n = 4).** For two points p, q at distance exactly 1, a square whose chord
along the line pq crosses two opposite edges and meets the segment [p, q] contains p or q. This
handles the middle square of the base row, which holds both lower points on its two edges.

## Two independent checkers

- **`checker/`** subdivides pose space (centre box × angle bin, with u = tan(θ/2)).
  - For fixed u, the admissible centres in a box form a convex polygon whose vertices are
    rational functions of u.
  - Capture is checked at the vertices, with exact Bernstein bounds over Q(√3).
  - The soundness argument is in `checker/README.md`; the specification is in `checker/SPEC.md`.
  - Standard library only.
- **`checker2/`** is a second checker written from the specification, the proof notes and the
  certificate format, with a different method. Its README describes the method and what its
  author read (Independence section). It verifies the same certificates (n = 2, 3, 4 and the
  series up to n = 37) and rejects the negative controls.
- **`checker2/n6/`** re-checks every part of the n = 6 proof (the six certificates, the obstacle points,
  the triple lemma and its hypotheses, and the links between the stages) by other methods, written
  without reading the first checker's code.

## Reproducing

```bash
# checker 1 (Python 3.10+, standard library)
python checker/check.py certificates/n2/n2_cert.json --n 2
python checker/check.py certificates/n3/n3_cert.json --n 3 --max-depth 44 --jobs 8
python checker/check.py certificates/n4/n4_cert.json --n 4 --max-depth 32 --jobs 8
python checker/check.py certificates/n29/n29_cert.json --n 29 --max-depth 36 --jobs 12   # likewise n7 … n22
python checker/check.py certificates/n37/n37_cert.json --n 37 --max-depth 40 --jobs 16
python tools/make_lattice_cert.py 9 out.json   # regenerates certificates/n37/n37_cert.json byte for byte
cd checker && python -m pytest -q tests          # needs pytest; about 1.5 minutes

# stand-alone check of the n = 2 lemma (needs sympy and mpmath)
python certificates/n2/check_n2.py

# n = 6: six certificates, obstacle points, triple lemma (commands in certificates/n6/PROOF.md)
python checker/check.py certificates/n6/loc3/cert_e1_100.json --n 6 --max-depth 40 --jobs 8
python certificates/n6/stage2/reprove_obstacles.py
```

Each run prints a JSON summary with `"status": "verified"`. The summary also contains the
certificate's sha256, the exact total weight and whether it is < n. The recorded runs are
`certificates/n*/check_record.json`. Checker 2 needs sympy and gmpy2; see `checker2/README.md`.

`tools/` has the float and exact random probes used as sanity checks (not part of the proofs).
It also has the script that checks the n = 3 pinwheel packing.

## Lean

`lean/` contains Lean 4 proofs of
- `minSideTri n` for n = 2, 3, 4: `2 + 2/√3`, `3/2 + √3`, `3 + 2/√3`;
- `minSideTri n` for n = 7, 11, 16, 22, 29: `m + 2/√3` for m = 4, …, 8;
- the n = 37 lower bound `∀ s, PacksTri 37 s → 9 + 2/√3 ≤ s`.

All are checked by the kernel with only the standard axioms (`propext`,
`Classical.choice`, `Quot.sound`; no `sorry`, no `native_decide`). The lower bounds use a third
checker, proved sound in Lean once: each leaf of a box tree carries a Farkas-type certificate
(nonnegative polynomial multipliers over Q(√3)) that the kernel checks. It covers all angles
directly and uses neither the D3 symmetry nor Lemma P. The trusted base and the build are
described in `lean/README.md`.

## Not done yet

- n = 5. Its best known side is 2 + 4/√3, the same as s△(6), so s△(5) ≤ s△(6) = 2 + 4/√3; the lower
  bound is work in progress.

## Licence

MIT (see `LICENSE`). The packings shown in the table are from Erich Friedman's Packing Center.
