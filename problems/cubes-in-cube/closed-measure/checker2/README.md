# System 2: the side-three closed-measure checker

`m4b-cert2` implements the contract in `../SPEC.md` using the published
second Euler checker as its base. It has no third-party Rust dependencies
and requires Rust 1.86 or later. No first-checker source is used.

```sh
cargo build --release --offline -j 1
./target/release/m4b-cert2 --threads 1 --check-data
./target/release/m4b-cert2 --threads 1 --validate
python3 integration.py
python3 stress_random.py
python3 stress_p0.py
./target/release/m4b-cert2 --threads 1 --seconds 300 --output trial \
  --unresolved-list trial-unresolved.jsonl
```

The measure is read from `../measure.json`. Positive densities are exact
binary64 values obtained with Rust's correctly rounded parser. Coordinates
are converted to integer tenths after checking the contract's tolerance.
All 48 symmetries are checked as multisets. Partners have identical density
bits and exact translated bounds; each piece is counted at most once. The
receipt includes counts, the outward interval total, the rational scale
(default `--sigma 27/20`), and `n_claim`. The published measure hash is required.
`--measure FILE` is useful for rejection tests.

## Pose coverage and arithmetic

The rotation is ZYZ Euler. Amendment 2 uses all 48 container symmetries:
reflect each centre parameter into `[0,1/2]`, then sort the three parameters.
The corresponding signed row permutation acts on R; a column sign change
restores determinant +1 when needed, without changing the cube. The right
quarter turn about the third cube axis commutes with these world actions.
The domain is `[0,2*pi] x [0,pi] x [0,pi/2] x Delta`, where
`Delta = {0 <= u_0 <= u_1 <= u_2 <= 1/2}`. The enclosing root box remains
`[0,2*pi] x [0,pi] x [0,pi/2] x [0,1/2]^3`.
A box is `outside` exactly when `u_0.lo > u_1.hi` or `u_1.lo > u_2.hi`.
These comparisons are strict: equality faces are retained. No rotation
restriction or numerical canonicalisation is used to prune search boxes.
Centres are exactly parametrised by `c_w = h_w + u_w (3 - 2 h_w)`.
The inherited independent binary64 interval arithmetic and Taylor sin/cos
provide outward enclosures; zero multiplication, unit multiplication, zero addition and exact singleton
cancellation are preserved.
Amendment 1 uses a forward-mode interval dual with six parameter derivatives.
Analytic sine/cosine derivatives propagate through the ZYZ rotation and
`c_w = h_w + u_w (3 - 2 h_w)`. At zero crossings, absolute values use
`[-1,1]` times the derivative interval (the Clarke enclosure). Each expression
also carries an outward-rounded value evaluated at the representable box
midpoint; parameter differences are outward-rounded interval subtractions.

Every rule quantity has a mean-value enclosure intersected with its naive
enclosure. The collected F expressions remain the naive intersection partner,
including their exact wall zeros. Polygon clipping retains the centred spatial
term until enumerating coefficient corners, so a coefficient is not rounded
independently twice when changing coordinates. A second, lower-corner form
intersects the naive collected constant directly and preserves wall contacts.
The larger certified area of these two enclosures counts; they are never
summed. Both forms also tighten coefficient intervals. Rotation, support,
centre derivatives and affine rule coefficients are cached once per box;
only the cell-dependent derivative sums and clipping are evaluated per piece.

There is no tolerance in a closing inequality. A box closes by `L(B) >= 1`
or by the strict `outside` predicate.
Depth-capped boxes are unresolved, never accepted.

## Sub-piece certification

`geometry.rs` labels the implementations of S, F, W, M, P and P'. F uses
collected centre inequalities. W/P require a direction interval excluding
zero. M uses the generalised wall lemma for one face, the opposite face
inequality, and the transverse hypotheses. This is a sufficient route to
M, without enumerating mixtures of different wall axes for different faces.

Each rule is an intersection of affine inequalities. On a plane, the code
substitutes the exact rational lower corner, enumerates every corner of
the remaining coefficient intervals, and clips the rectangle by all these
half-planes. Floating intersections propose a polygon only: its dyadic
vertices must pass outward interval checks against every inequality and
against the rectangle. If necessary they are moved towards their centroid;
uncertified proposals contribute zero. Convex cyclic order is also checked
with outward determinants. A triangle-fan interval calculation rounds the
certified polygon's area down. Thus rounding an intersection cannot enlarge
the certified region. On lines, interval clipping returns certified inner
endpoints. Points use interval predicates at exact rational coordinates.

Alternative rule regions can overlap, so only their maximum area counts.
A pair contributes the maximum of its pair area and the sum of the two
single areas, multiplied by its common density. Pieces and pairs are then
summed with outward rounding and scaled by sigma. No optional grid is used.
`--cell-depth` defaults to 6 and is recorded for contract compatibility;
it does not change this system's direct polygon/segment clipping. There is
no dyadic cell refinement in system 2.

## Search and receipts

Search batches have a fixed size of four, independent of worker count.
Results are committed in input order, with deterministic bisection and
frontier order. The leaf stream records depth, `bound`, `outside` or `unresolved`, and
hexadecimal endpoint bits. Each batch updates the inherited chain convention
`SHA256(previous hexadecimal chain || leaf records)`, including empty batches.

`--max-depth` (alias `--depth`) defaults to 72. `--rounds` provides a
deterministic stopping limit. `--keep-leaves` saves the leaf stream.
`--checkpoint-seconds` defaults to 10. Checkpoints are atomically replaced
and synced. Resume with the same output directory and `--resume`; source,
measure, sigma, depth, cell-depth and leaf-retention mismatches are rejected.
Uncommitted leaf bytes after a crash are truncated at the checkpoint offset.

Receipts identify this implementation with `enclosure: "mean-value-1"`.
The output directory contains `progress.json`, `checkpoint.json`, and a final
`receipt.json`. Receipts record the leaf chain, source hashes, measure hash,
compiler version, command line, counters, depth histogram, lemma counts and
total mass. Contribution arrays are ordered point/line/plane; lemma arrays
are ordered S/F/W/M/P/P'. Counts are diagnostic, not a partition of mass.
The closed-volume fraction is a floating diagnostic sum of dyadic volumes
of both bound and outside leaves, measured against the unchanged root box.
Outside leaves contribute no lemma counts. Their counts survive resume.
Receipts also contain the exact domain descriptor:
`fundamental_domain: "Delta x gamma in [0, pi/2] (u sorted, 48 container symmetries; quarter turn about the third cube axis)"`.

`--unresolved-list FILE` writes JSON lines containing each depth-capped box,
its lower bound, and contributions. Pending boxes remain in the checkpoint.
`--sample-box '{"box":[[0,0.0015],[0,0.003],[0,0.0015],[0,0],[0,0],[0,0]]}'`
prints one bound. `--batch` accepts the same JSON objects on standard input.
Batch responses add `outside: true/false` and retain numeric `L`. Outside
boxes return the valid trivial bound `L=0` with zero contributions and lemma
counts, skipping clipping. `--sample-box` still computes the geometric bound.
All runs should explicitly use `--threads 1` on the trial machine. On macOS,
more than two threads, more than 1200 seconds, and `--server` are refused.
Output paths and symlinks must stay within this directory.

## Validation and interpretation

`--validate` first checks 10,000 samples of every indexed T, translated T,
direction, absolute direction, chord, full-chord, F and M quantity on random
boxes (1,260,000 checks, including absolute-value zero crossings). It checks
the direct mean-value intersection and both polygon enclosure forms.
It then checks 20,000 boxes with 50 poses per box against an independent
floating evaluator that intersects the supports directly with the six cube
faces. A quarter of boxes touch a wall and a quarter use aligned coincidence
families. It also checks each rule on random support points and verifies the
bound at 200 poses, all 48 container images and each image's u-sorted
canonical representative on degenerate boxes (1e-9 test tolerance).
Another 10,000 random poses drawn with u in the full unit cube verify that
the program's representative lies in the domain and preserves independent
floating closed mass to 1e-9. Floating symmetry maps live in `symmetry.rs`
and are used only by validation. The floating test
uses a 1e-12 comparison tolerance; this is absent from certification. Nearly
parallel intersections can amplify binary64 pose errors. Apparent failures
are rechecked by an independent Python Decimal evaluator at 80 digits,
with its own trigonometric series and the same 1e-12 comparison tolerance.
The number of such rechecks is printed. Python 3 is therefore also required
for the full validation command.

The independent standard-library Python evaluator provides additional
random and aligned-family tests. `integration.py` uses `Fraction` for the
exact total, compares all positive density bits, verifies three corruption
rejections, and tests serial resume including a simulated crash tail.
`integration.py --two-threads` additionally tests worker-count determinism;
this opt-in is not run under the single-thread trial constraint.

A paused or unresolved receipt is not a proof of the main lemma. See
`TRIAL.md` for the actual trial result, sample bounds, and validation logs.

## Amendment 1 reproduction

See `TRIAL_A1.md` for the completed validation, gap comparison, Knuth estimate,
and observed batch throughput. These are diagnostics, not a completed proof.
After building and running `--threads 1 --validate`, `python3 validation-a1/run.py`
runs the integration and Python suites, a short receipt-producing search, and:

```sh
python3 ../estimate/gap.py 5 10
python3 ../estimate/knuth.py 2 300 1 27/20 --maxdepth 70 --procs 1
```

The runner retains outputs and elapsed times under `validation-a1/`, limits
each subprocess to 590 seconds, and enforces a remaining aggregate budget.
Its local Python startup hook adds explicit `--threads 1` to checker launches
made by the unchanged estimate scripts. Numerical library thread counts are
also set to one. The two-worker determinism comparison remains unexecuted
under this trial's single-thread restriction.

## Amendment 2 reproduction

See `TRIAL_A2.md` and `validation-a2/` for saved results. Build with
`cargo build --release --offline -j 1`, then run `python3 validation-a2/run.py`.
The runner serialises all work, limits each subprocess to 590 seconds,
and caps its aggregate elapsed time at 1100 seconds. It includes the existing
validation and gap diagnostic, the expanded symmetry and orbit tests, both
Knuth comparisons, and a short search receipt. Final-build results are in `trial-a2-final/`.
Use a fresh trial output directory when repeating the runner.

`knuth_a2.py` is copied from `../estimate/knuth.py`, with its location adjusted
and explicit `--threads 1`; System 2 closes on `L >= 1 or outside`:

```sh
python3 knuth_a2.py 2 300 1 27/20 --maxdepth 70 --procs 1 --uw 4
python3 knuth_a2.py 2 300 1 27/20 --maxdepth 70 --procs 1 --uw 1
```

The split coordinate maximises `width[i] / W[i]`, breaking ties by the
lowest index. Amendment 2 selects `W=[1,1,1,1,1,1]` after the comparison: `--uw 1`
estimates 1.87e8 nodes versus 5.12e8 for the previous `--uw 4` rule.
Only the choice of split coordinate changes. The closing rules and
Amendment 1 enclosures are unchanged. See `TRIAL_A2.md` for uncertainty
and throughput. `validation-a2/final.py` reruns the validation on this build.
The original gap script receives zero for outside boxes; the local
`validation-a2/gap.py` uses `--sample-box` on the same poses to inspect the
geometric bound, including outside boxes.
