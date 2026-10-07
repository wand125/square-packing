# Point-only certificate for s(61) = 8

**Computer-assisted. The capture condition is checked by Evan Daniel's unmodified
`zmx2` checker; the remaining steps are exact arithmetic. Independent external
review and a proof-assistant proof are not claimed.**

`cover.txt` is a nonnegative point measure in the side-8 square: 15,193 distinct
points, invariant under the dihedral group D4, with total mass

```
8584985072679551 / 2^47 = 60.99998780001... < 61.
```

`zmx2 cert cover.txt --d4 --pair-points` reports `VERIFIED-D4`: every closed
unit square in `[0,8]^2`, at every position and angle, captures mass at least 1.
Suppose 61 non-overlapping unit squares fit in a square of side `L < 8`. Enlarge
the container to side 8 and shrink each square concentrically by the same
factor inside its enlarged copy; this gives 61 pairwise disjoint closed unit
squares in `[0,8]^2`. Together they would capture mass at least 61, more than the
total. The 8-by-8 grid packs 64 squares, so `s(61) = 8`.

Evan Daniel already published `s(60) = 8` with a mixed point-and-segment
measure, and `s(61) = 8` follows from it. This work does not claim priority for
the value; it is a separate route using points only. It relies on his checker,
which is fetched and built from the pinned upstream commit rather than copied
here (MIT licence, as in
[`../point_n21_L5/UPSTREAM-LICENSE.txt`](../point_n21_L5/UPSTREAM-LICENSE.txt)).

## Reproduce

Requires `git`, Python 3 and Rust 1.86 or later (the upstream source uses
`f64::next_up`). From this directory:

```sh
python3 check_cover.py                 # exact: hash, format, D4 invariance, total < 61
sh verify.sh /tmp/n61-verify 8         # new directory; 8 threads
```

`verify.sh` clones `evand/square-packing` at
`6e1223cf7ef2be4c70baaa36c0e7e7197076735a`, checks the SHA256 of `zmx2.rs`,
builds it in release mode, and runs the D4 check and the full D4-reduced sweep.
It accepts only `VERIFIED-D4`, all 6,400 roots, zero uncertified boxes and zero
capped roots, and ends with `N61_POINT_COVER_VERIFIED`. Set `CARGO` to choose a
toolchain. The reference run in `provenance.json` took 307 seconds with 4
threads (800,042 boxes, maximum depth 30); a second build of the same source on
Linux gave the same box count.

## How the measure was found

The measure was lifted from the point-only s(45) cover in
[`../point_n45_L7`](../point_n45_L7/README.md). A central band was inserted in
each axis direction (at `a = 7/2`, width `delta = 1`; atoms on the cut were split
in half), which turns the side-7 cover into a side-8 cover except near the new
cross bands. Extra mass on the cross bands (`nu = 15.30` in total) was found by a
linear program over candidate points, iterated against the weak poses that
`zmx2` and an exact all-centre check reported. Captures of exactly 1 at contacts
cannot be certified by interval bounds, so the LP result (total `60.2951`) was
scaled to just below 61 (each weight rounded up on a 2^49 grid) to create a
uniform margin. Extra LP rows removed the remaining contacts: a raised target
near the axis, and a slightly shrunken square elsewhere. None of this search is
needed to check the certificate; `provenance.json` records the LP output hash
and the scale.
