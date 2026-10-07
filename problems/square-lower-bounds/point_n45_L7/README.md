# Point-only certificate for s(45) = 7

**Computer-assisted. The capture condition is checked by Evan Daniel's unmodified
`zmx2` checker; the remaining steps are exact arithmetic. Independent external
review and a proof-assistant proof are not claimed.**

`cover.txt` is a nonnegative point measure in the side-7 square: 12,645 distinct
points, invariant under the dihedral group D4, with total mass

```
12666371418707823 / 2^48 = 44.99999100001... < 45.
```

`zmx2 cert cover.txt --d4 --pair-points` reports `VERIFIED-D4`: every closed
unit square in `[0,7]^2`, at every position and angle, captures mass at least 1.
Suppose 45 non-overlapping unit squares fit in a square of side `L < 7`. Enlarge
the container to side 7 and shrink each square concentrically by the same
factor inside its enlarged copy; this gives 45 pairwise disjoint closed unit
squares in `[0,7]^2`. Together they would capture mass at least 45, more than the
total. The 7-by-7 grid packs 49 squares, so `s(45) = 7`.

Evan Daniel already published `s(45) = 7` with a mixed point-and-segment
measure. This work does not claim priority for the value; it is a separate route
using points only. It relies on his checker, which is fetched and built from the
pinned upstream commit rather than copied here (MIT licence, as in
[`../point_n21_L5/UPSTREAM-LICENSE.txt`](../point_n21_L5/UPSTREAM-LICENSE.txt)).

## Reproduce

Requires `git`, Python 3 and Rust 1.86 or later (the upstream source uses
`f64::next_up`). From this directory:

```sh
python3 check_cover.py                 # exact: hash, format, D4 invariance, total < 45
bash verify.sh /tmp/n45-verify 8       # new directory; 8 threads
```

`verify.sh` clones `evand/square-packing` at
`6e1223cf7ef2be4c70baaa36c0e7e7197076735a`, checks the SHA256 of `zmx2.rs`,
builds it in release mode, and runs the D4 check and the full D4-reduced sweep.
It accepts only an exact `D4: measure invariant` line, `VERIFIED-D4`, all 4,900
roots, zero uncertified boxes and zero capped roots, and ends with
`N45_POINT_COVER_VERIFIED`. It also records the toolchain and the hash of the
built binary (`toolchain.txt` in the work directory) and compares the new
per-root log with the reference run in `reference/` root by root. Set `CARGO` to choose a
toolchain. The reference run in `provenance.json` took 204 seconds with 8
threads (1,295,460 boxes, maximum depth 38). Its per-root log and summary are
shipped as `reference/roots.txt` (SHA256 `a353a0ca…`, the `roots_sha256` in
`provenance.json`) and `reference/run.txt`. A replay with the corrected
`verify.sh` on Linux x86_64 (rustc 1.86.0, binary SHA256 `80596601…`) agreed
with it on every root: the same 4,900 roots and the same box, certified, empty
and uncertified counts per root.

Earlier versions of `verify.sh` checked D4 invariance with
`zmx2 d4 cover.txt | tee d4.log; grep -q invariant d4.log`. That test could not
fail: the pipeline's status is `tee`'s, and zmx2's failure message also
contains the word "invariant". The cover itself is D4-invariant (checked
exactly by `check_cover.py`, and by `zmx2 d4`, which exits with status 2 on a
non-invariant cover), so the result is unaffected.

## How the measure was found

The weights came from a linear program over candidate point supports, iterated
against counterexamples. `zmx2` itself located the weak poses. Captures of
exactly 1 at contacts cannot be certified by interval bounds, so the LP result
was scaled by about 1.000835 (each weight rounded up on a 2^49 grid) to create
a uniform margin while keeping the total below 45. Extra LP rows removed the
remaining contacts: a raised target near the axis, and a slightly shrunken
square elsewhere. None of this search is needed to check the certificate;
`provenance.json` records the LP output hash and the scale.
