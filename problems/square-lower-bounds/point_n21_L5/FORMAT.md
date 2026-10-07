# Point data and proof data

## Point file

The point file is whitespace-separated decimal integers. The first five are

```
side_numerator side_denominator coordinate_denominator weight_denominator count
```

They are followed by exactly `count` triples `X Y w`. A triple denotes an atom
of weight `w / weight_denominator` at
`(X / coordinate_denominator, Y / coordinate_denominator)`. All denominators
are positive and all weights are nonnegative. Boundary atoms count when the
tested square is closed. Entries are indexed in their original file order;
zero-weight entries must not be removed from a file used by the proof trees.

For this certificate, the container side is `5/1`, the coordinate denominator
is `1000`, the weight denominator is `1000000000000`, and there are `4604`
entries. There are `4520` positive-weight entries and `84` zero-weight entries.
The coordinates are distinct. The complete input SHA256 is
`84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679`.

The capture threshold for that file is `249987/250000`, not `1`. Its total mass
is `2624862500021/125000000000`, strictly below `21` times that threshold.

The separately normalised point file divides every weight by the threshold.
It has the same coordinates and entry order, weight denominator
`999948000000`, SHA256
`9f631fbae420e0376ea636a232b7680e937deebe205dc035cfb9c43a3d74b456`,
and total mass `2624862500021/124993500000 < 21`. This file has capture at least
`1` by exact uniform scaling of the original certified measure. The supplied
proof trees refer to the original file's hash and threshold; do not substitute
the normalised file into those trees without a new binding and verification.

## Pose boxes and rational proof records

A pose box has six rational entries
`[cx_lo,cx_hi,cy_lo,cy_hi,t_lo,t_hi]`. Rational JSON values are integers or
strings such as `249987/250000`; decimal display values are not proof premises.
The parameter is `t=tan(θ/2)`. Ordinary box intervals are closed. Any one-sided
open angular exclusion is explicitly checked by the stratified-coverage code;
it must not be inferred from a floating-point tolerance.

The proof data retain the local containment indices, rational dual multipliers,
branch trees, conflict witnesses, geometry, source identities and stage linkage
that the checker actually reads. They are JSON or gzip-compressed JSON, plus
the recorded sieve stream in JSON Lines. The checker does not execute pickle
data, invoke an LP solver to accept a bound, or use a saved success flag as a
replacement for replaying a local certificate.

Some retained records contain historical absolute source paths. These are
identifiers: `portable_replay.py` maps the manifest's original root to the
current bundle root and checks the retained bytes against their hashes. It
rejects references outside the bundle, parent-directory traversal, and unlisted
files. The historical directory need not exist. A separate audit hook prevents
the numerical replay from reading the original source tree as a fallback.

## Results

Individual numerical workers do not establish the whole theorem. The public
runner must execute both prefix stages and every frontier shard, require zero
exit status from each, and then check full assembly. The accepted final record
is `FRESH_ALL_DOMAIN_REPLAY_VERIFIED`, with `5000` roots, `8758` sieve parents,
`31678` replayed frontier parents, and exactly `7052` parents outside the required
representative angular region. The precise acceptance conditions are in
`PUBLICATION.md` and `PROOF-LEMMAS.md`.

A failure record, missing record, nonzero exit, partial replay, or successful
record-summary check alone is not this acceptance result.

## Lightweight data inspection

The distribution includes `certificates/n21-original.txt`,
`certificates/n21-capture-one.txt`, and
`certificates/upstream-s21-lower-4.9950.txt` as byte-identical copies.
Run `python inspect_certificate.py` to check their pinned hashes, well-formedness,
nonnegative weights, exact masses, original D4 invariance, uniform normalization,
and ordered upstream support scaling using Python rational arithmetic alone.
No NumPy or SciPy is required for this command.

Its result is `EXACT_CERTIFICATE_DATA_CHECKED`. This validates data and algebra;
it does **not** establish capture over all positions and angles. For that,
run the full `verify_portable.py` command described in `PUBLICATION.md`.
