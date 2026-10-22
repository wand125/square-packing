# System 1: closed-measure interval certificate

`m4b-cert1` implements System 1 of `../SPEC.md`. It checks the proposed lemma
σ μ(Q) ≥ 1 for every **closed** unit cube Q contained in [0,3]³. Boundary points,
segments and plane regions count. A completed certificate would imply
s₃(n) ≥ 3 for n ≥ floor(σ T) + 1. At the default σ = 27/20 the checked total
implies n_claim = 25. This statement about the total does not certify the main
lemma: only a search with no pending or unresolved boxes does that.

## Build and reproduce

```sh
cargo build --release --offline -j 1
cargo test --release --offline -j 1 -- --test-threads=1
python3 validate.py
python3 validate_a1.py
./target/release/m4b-cert1 --threads 1 --seconds 300 --output trial \
  --unresolved-list trial/regions.jsonl
# Continue the identical binary, measure, cell depth and maximum depth:
./target/release/m4b-cert1 --threads 1 --seconds 300 --output trial --resume
```

No dependencies beyond the supplied lockfile are required. Validation needs
Python and NumPy. All commands above use one numerical worker. macOS rejects
more than two threads, more than 1200 seconds, and `--server`. Each invocation
checks the time limit between deterministic rounds, so it can finish its last
round after the requested time. Region diagnostics are written afterward.

## Input and arithmetic

The default `--measure ../measure.json` is checked before any bound or search.
All bounds are converted to integer tenths after checking the coordinate range
and 1e-9 conversion tolerance. This tolerance is only an input-format check.
Geometry thereafter uses exact rational cell endpoints. Positive pieces must
be points, lines or planes of the stated dimension. Densities are the exact
binary64 values obtained by correctly rounded JSON parsing.

The program checks all 48 signed axis permutations as multisets, records
unit-translation partners with identical densities, and computes an outward
interval for total mass T. `--sigma p/q` defaults to `27/20`; its interval and
T must prove σ T < n_claim, with n_claim computed from the lower endpoint.
`--measure-info --threads 1` prints the checks and density bit patterns. For
the supplied data there are 36 points, 48 lines and 120 planes, and respectively
15, 24 and 60 pairs. Six points are unpaired. If a different symmetric input
has multiple partner axes, the first axis is preferred, a disjoint matching is
used, and unused pieces remain single; the receipt reports this fallback.

Elementary interval operations widen by one representable step. Exact integer
constants and exact integer rational quotients need no enclosure widening.
Other rational constants, including tenths and σ, are outward enclosed. There
is no tolerance or epsilon in a closing inequality. Cell coordinates use
integer numerators over 10·2^level, never repeated floating midpoint updates.

## Pose coverage and root derivation

Rotation is the projective quaternion (1,x,y,z). The 24 cube rotations act on
the right. Choose the quaternion lift with largest scalar component. Comparing
it with the lifts having two nonzero entries ±1/√2 gives
1 ≥ (1+|x_i|)/√2, hence |x_i| ≤ √2−1. Comparing with the lifts
(±1,±1,±1,±1)/2 gives |x|+|y|+|z| ≤ 1.

The measure's checked 48 container symmetries permit proper signed
permutations to sort x ≥ y ≥ |z| with x,y ≥ 0. Central inversion preserves
the cube and sends u to 1−u, allowing u₀ ≤ 1/2. Thus the 1152-fold reduction
has the enclosing root [0,a]² × [−a,a] × [0,1/2] × [0,1]², where a is an
outward upper bound for √2−1. The rotation argument is independent of side.
`outside` uses only strict violations of these inequalities; ties remain.

For side 3 the support values satisfy 1/2 ≤ h_w ≤ √3/2 < 3/2, and the
centres are exactly c_w = h_w + u_w(3−2h_w), u_w ∈ [0,1]. In particular,
3−2h_w is positive and every admitted pose is contained in [0,3]³. No extra
centre feasibility rejection is needed.

## Lower bound

The only closing rules are `bound` and `outside`. At the depth cap, a leaf
is `unresolved`. The old eight-point and local-sign rules are removed.

`src/bound.rs` implements SPEC S, F, W, M, P and P′. Affine expressions use
coefficient vectors dotted with (y−c), including the collected full-chord
expression. W and P require a direction interval strictly excluding zero.
F collects the centre parametrisation and uses exact nonnegative terms to
retain zero slack at wall contacts. M proves each necessary face inequality
either directly or by the generalised wall lemma.

Pairs are visited once from the lower piece. For each cell the bound is the
maximum of the sum of certified singles, the pair contribution, and the sum
of child values. `--cell-depth 6` allows six bisections per free side; planes
split their longest available side first. An unpaired point is never split.
When a chosen feasible pose proves both entire cells disjoint from its cube,
every descendant's predicates must fail, so this zero subtree is skipped.
This is an optimisation of cell refinement, not another positive closing rule.
The running scaled bound stops as soon as its lower endpoint reaches one.

## Amendment 1 enclosures

`src/dual.rs` carries an outward-rounded value and six interval partials.
Quaternion rotation derivatives use the quotient rule for N/(1+x²+y²+z²).
Absolute values use the fixed sign when the interval excludes zero, and the
Clarke multiplier [−1,1] otherwise. The centre derivative includes both h and u.
Box and midpoint geometry, chord coefficient derivatives, and centre derivative
terms are cached once per pose box; cell work uses only the y-dependent terms.

Each rule quantity is intersected with its mean-value enclosure: T at either
member of a pair, chord determinants, signed directions, absolute directions,
F slacks, and M absolute-value sums. The affine forms retain each y coordinate
once. Midpoint values are evaluated as degenerate intervals at representable
midpoints; parameter and cell displacements use outward-rounded subtraction.
The naive collected wall form remains the intersection partner, including the
existing exact nonnegative F shortcuts. No rule inequality, cell combination,
split rule, or leaf-record format changes.

## Search and receipts

The deterministic split heuristic balances the six dyadic levels. Rounds take
at most sixteen tasks of one node each; worker results are merged by task
index. `--rounds N` is useful for deterministic tests. `--max-depth 180`
(default; `--depth` is an alias) caps each path. Each coordinate is limited to
50 bisections, keeping dyadic integers exactly representable.

The leaf record contains its dyadic node and `result.reason` only. Refinement
choices, lower-bound values and lemma diagnostics do not enter the digest.
The inherited chain is h ← sha256(h_hex || round_leaf_bytes), initially
sha256(empty). `--keep-leaves` additionally saves the stream and its SHA-256.
Checkpoints preserve the chain without requiring the full leaf stream.

`receipt.json` and `progress.json` include `enclosure: "mean-value-1"` and report status, counts, parameter volume
coverage, depth histograms and digests. `metadata` records threads, depth caps,
σ, T, n_claim, measure SHA-256, data checks, every source SHA-256, binary SHA-256,
rustc version and the invocation. Sources are embedded in the binary and must
match files on disk before a search. Resume rejects different sources, binary,
measure or depth settings. Output directories and diagnostic files must stay
inside this directory; symlink escapes are refused.

Closed volume is relative to the entire root rectangle, including regions
removed by `outside`; it is not volume in physical pose space. Lemma counters
are the numbers of selected certified cell contributions, summed only over
`bound` leaves, in order S,F,W,M,P,P′. They are diagnostics, not separate
closing rules. A positive bound's per-piece-type contributions are scaled
point, line and plane masses (possibly truncated by early exit).

`--unresolved-list FILE` writes unresolved and pending boxes, their dyadic
nodes, L(B), and contributions. For a single diagnostic box use:

```sh
./target/release/m4b-cert1 --threads 1 --sample-box \
 '[{"lo":0,"hi":0.002},{"lo":0,"hi":0.002},{"lo":-0.002,"hi":0.002},
   {"lo":0,"hi":0},{"lo":0,"hi":0},{"lo":0,"hi":0}]'
```

The order is x,y,z,u₀,u₁,u₂. Diagnostics accept feasible boxes outside the
reduced root, and do not apply `outside`. `--batch` accepts JSON lines with
`box`, optional `domain`, and optional `full:true` to disable early exit.
The validator uses full sums for symmetry comparisons because an early-exit
partial sum depends on piece ordering. Its `cell` and `axis` query tests each
rule independently; this interface never closes search boxes.

## Validation and trial

`validate.py` implements an independent floating closed intersection evaluator:
point membership (1e-12 tolerance), line clipping against six slabs, and
rectangle clipping against the cube slice's halfplanes, followed by shoelace
area. It cross-checks T using `fractions.Fraction` and densities bit for bit.
The default scaled test has 400 random boxes, 12 poses each, quarter wall and
quarter aligned-family boxes; 1,000 rule queries; 144 symmetry images; three
symmetry-breaking data mutations; and fixed-round repeat/resume comparisons.
It writes `validation/report.json`. Two-thread validation is deliberately not
run under the task's strict one-thread limit. These sanity tests are not proof.

`validate_a1.py` tests 10,000 samples of each of 63 scalar quantities on
1,000 random boxes, including wall and aligned cases, zero-crossing rotations,
point boxes, and endpoint samples, without a containment tolerance. It writes
`validation/a1.json`. The `enclosures` batch field is a validation-only API.

Amendment diagnostics (run separately, with one worker):

```sh
python3 run_limited.py python3 gap_a1.py > gap_a1.log 2>&1
python3 run_limited.py python3 ../estimate/knuth.py 1 200 1 27/20 --maxdepth 70 --procs 1
```

`gap_a1.py` adapts the System 2-only `../estimate/gap.py` to System 1, using
the same ten seed-5 physical centres, quaternion-coordinate widths and centre
widths w/4. Its full rigorous sums and sampled ideal bounds are in
`gap_a1.json`; these boxes are not the original Euler boxes. The unchanged
Knuth script defaults to one checker thread; `--procs 1` runs one process.
`run_limited.py` limits each process group to 590 seconds and records a cumulative
1,200-second budget in `compute_a1.json`.

See `TRIAL_A1.md` for amended validation, performance and acceptance results.
`TRIAL.md` records the superseded pre-amendment diagnostic trial. A paused or unresolved receipt is not a proof of the lemma.
