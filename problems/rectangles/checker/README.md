# Checkers

Both checkers are plain Python 3 (standard library only; tested with Python 3.9 and 3.12) and use exact
rational arithmetic (`fractions.Fraction`). No floating-point value enters a decision.

- `verify.py`: for every pair of squares, finds a separating axis among the edge normals of the two
  squares, and checks every vertex against the four walls of the box. Exact.
  Single file: `python checker/verify.py certificates/k14/14.13-1.json --exact`.
- `verify_fast.py`: the same test with an exact axis-aligned bounding-box rejection first, so most
  pairs are separated without the edge-normal test. Exact.
- `check_all.py`: runs both on every certificate listed in `data/edges/k*.json` and also checks that
  each certificate's box, number of squares and height match its listing.

Note on independence: `verify_fast.py` imports the vertex formula from `verify.py`. The two
checkers share that formula (the four vertices of a unit square from its centre and the rational
cosine and sine of its angle); the separation tests are written separately.

Both files are part of this repository (MIT, see `../LICENSE`). There is no third-party code.
