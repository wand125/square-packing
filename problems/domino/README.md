# Unit squares in a 1:2 rectangle (domino): the optimal packing of 4 squares

Let s(n) be the smallest v such that n non-overlapping unit squares (any positions, any angles)
fit in a v × 2v rectangle.

| n | s(n) | ≈ | optimal packing (upper bound) | lower-bound certificate |
|---|---|---|---|---|
| 4 | largest real root of 5x³ + 8x² − 32x − 4 | 1.9302833067 | Stenlund (2010): two axis-parallel squares in opposite corners, two tilted squares (β ≈ 40.52°) in the middle | 7 points of weight 1/2 (total 7/2) |

The packing is the best known one in Erich Friedman's Packing Center, "Squares in Dominoes"
(https://erich-friedman.github.io/packing/squindom/). Friedman lists it as "s = 1.930+, found by
Evert Stenlund in June 2010". The certificate shows that it is optimal.

The result is computer-assisted. It has been checked by two independent checkers. It has not been
peer reviewed.

## Novelty

On Friedman's page (as of 2026-10-01), the entries other than the "Trivial" ones give packings
only, with no proofs or lower bounds. We are not aware of a previous proof that s(4) = 1.930+.
If you know of one, please open an issue.

## The method

The lower bound is a finite weighted point set in the rectangle R_v = [0, 2v] × [0, v], at the
claimed value v = v4. The checkers prove two things:

1. **Capture.** Every closed unit square Q ⊆ R_v, at any position and any angle, contains points
   of total weight ≥ 1. A point on the boundary of Q counts. This is checked at the container
   itself, with margin zero.
2. **Budget.** The total weight is < n.

Then 4 squares do not fit in a rectangle of short side L < v4. Move their centres away from the
centre of the rectangle by the factor v4/L. The squares become pairwise disjoint closed squares in
R_{v4}, each capturing weight ≥ 1, so the total would be ≥ 4 > 7/2. Details are in
`certificates/n4/PROOF.md`.

**Exact numbers.** v4 is a cubic irrational. The cubic is irreducible over Q and has three real
roots, so v4 has no expression in real radicals. Both checkers work exactly in Q(v4) (elements a + b·v4 + c·v4²). Signs are
decided by refining a rational isolating interval of v4.

**The wedge lemma.** The extremal packing is not rigid to first order: the two tilted squares can
rotate together, with overlap only of order t². So near the extremal pose, a square captures
either a corner point or the centre, and which one switches.

- Checker 1 proves "corner or centre" with a Farkas combination of two side constraints and one
  wall. Its key inequality is exactly v ≤ s(β), the formula of the one-parameter family of
  packings, whose minimum is v4.
- Checker 2 does not use this lemma. It handles the contact as a critical angle of an exact
  angular sweep.

## Two independent checkers

- **`checker/`** subdivides pose space (centre box × angle bin, with u = tan(θ/2)).
  - Capture is checked at the vertices of the admissible polygon, with exact Bernstein bounds
    over Q(v4).
  - It uses the D2 symmetry of the rectangle and the wedge lemma.
  - Standard library only.
  - The soundness argument and the field are described in `checker/README.md`.
- **`checker2/`** is an exact angular sweep of a line arrangement.
  - It uses no symmetry, no wedges and no box subdivision.
  - Its field implementation was written from the specification in `checker/README.md` only,
    without reading checker 1's code.
  - See `checker2/README.md` for the method and the independence statement.

Both verify `certificates/n4/n4_cert.json` at L = v4 exactly, and both reject the control at
L = v4 + 10⁻⁶.

## Reproducing

```bash
# checker 1 (Python 3.10+, standard library)
python checker/check.py certificates/n4/n4_cert.json --n 4 --max-depth 30 --jobs 4 \
    --u-breaks "K[-21/37;-11/37;15/37]"                      # ~5 s, "verified", total 7/2
python checker/check.py certificates/n4/below/n4_L9651_5000.json --n 4 --max-depth 44 --jobs 4
python tools/make_cert.py | cmp - certificates/n4/n4_cert.json   # regenerates the certificate byte for byte
(cd certificates && sha256sum -c SHA256SUMS)                 # or: shasum -a 256 -c
cd checker && python -m pytest -q tests                      # needs pytest; about 1 minute

# checker 2 (needs gmpy2 and sympy)
cd checker2 && python sweep_k.py ../certificates/n4/n4_cert.json --n 4 --jobs 4   # ~5 min
```

Each checker-1 run prints a JSON summary with `"status": "verified"`. The summary also contains
the certificate's sha256, the exact total weight and whether it is < n. The recorded runs are
`certificates/n4/check_record.json` and `certificates/n4/below/*.check_record.json`.

## Controls

`controls/` holds three certificates that must fail, with the recorded runs:

- the same 7 points at L = v4 + 10⁻³;
- the same 7 points at L = v4 + 10⁻⁶;
- the certificate at L = v4 without the wedges (checker 1 cannot certify the switching contact
  without the lemma).

All three fail as expected. Checker 2 rejects the L = v4 + 10⁻⁶ control with an explicit pose of
captured weight 1/2.

## Not done yet

- Lean formalisation.
- Other n. The next non-trivial entry is n = 9, s(9) = 2 + √2/3 (Stenlund 2010).

## Licence

MIT (see `LICENSE`). The packing shown in the table is from Erich Friedman's Packing Center.
