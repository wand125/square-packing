# Unit cubes in a cube: s₃(25) = s₃(26) = 3

Let s₃(n) be the side of the smallest cube that contains n unit cubes with pairwise disjoint interiors (any
positions, any orientations).

| n | s₃(n) | upper bound | lower bound |
|---|---|---|---|
| 25 | 3 | 25 of the 27 grid cubes of [0, 3]³ | closed measure, this folder |
| 26 | 3 | 26 of the 27 grid cubes | follows from n = 25 (s₃ is non-decreasing) |

(s₃(27) = 3 is immediate from volume.) The result is computer-assisted, is checked by two independent checkers, and
has not been peer reviewed.

## Novelty

- We found no published proof of s₃(25) ≥ 3 or s₃(26) ≥ 3. If you know of one, please open an issue.
- The upper bounds are the trivial grid packings.

## The method

**Closed counting measure.** `measure.json` defines a finite measure μ on [0, 3]³ made of weighted points, segments
and plane rectangles (positive pieces: 36 points, 48 segments, 120 rectangles; every coordinate a multiple of 1/10).
It was found by a linear program over sampled poses; the proof uses only the final file.

**Main lemma.** With σ = 27/20, σ·μ(Q) ≥ 1 for every **closed** unit cube Q ⊆ [0, 3]³, in any orientation. Points,
segments and plane regions on the boundary of Q count.

**Theorem.** The total is σ·μ([0, 3]³) = 24.9123 < 25 (computed by both checkers with outward-rounded intervals and
cross-checked exactly with rationals). Suppose 25 unit cubes fit in [0, L]³ with L < 3. Scaling the centres by 3/L
(`../PROOF.md` §1, with s = 3) gives 25 pairwise disjoint closed unit cubes in [0, 3]³, so
25 ≤ Σ σ·μ(Q_i) ≤ σ·μ([0, 3]³) < 25, a contradiction. Hence s₃(25) ≥ 3.

The main lemma is proved by a branch and bound over the six parameters of a pose (rotation and centre). For each
parameter box B the checker computes, with interval arithmetic, a number L(B) with σ·μ(Q) ≥ L(B) for every pose in B,
and closes B when L(B) ≥ 1. L(B) sums, over the pieces of μ, the mass that is certainly inside Q, using these rules
(all stated and proved in `SPEC.md` §4):
- **S:** the point is inside the cube for every pose in the box;
- **F:** the centre rule (Lemma F of `../PROOF.md` §2);
- **W:** a wall rule in chord form for pieces on the planes x_w ≤ 1 or x_w ≥ 2;
- **M:** the wall lemma of `../PROOF.md` §3, generalised;
- **P, P′:** pair rules for a piece and its translate by a unit vector, which carry the same density: for every point,
  one of the two translates is in Q.

Pieces are refined adaptively into sub-cells inside each box. The enclosures use a mean-value form intersected with
the naive form (`SPEC.md` §9). Every closing inequality is closed and handles equality exactly; no epsilon is used.
`SPEC.md` is the specification both checkers were written from.

## The two checkers

| | System 1 (`checker1/`) | System 2 (`checker2/`) |
|---|---|---|
| Rotations | projective quaternions | ZYZ Euler angles |
| Domain reduction | 1,152-fold (24 cube rotations × 48 container symmetries) | 48 container symmetries on the centre, and a quarter turn |
| Sub-pieces | dyadic cells | exact polygon clipping with interval half-planes |
| Base | `../checker/` with the closing rules replaced | `../checker2/` with the closing rules replaced |

System 2 was written from `SPEC.md` without reading System 1's new code.

## Results (σ = 27/20)

| System | Status | Boxes | Max depth | Leaf digest (chained SHA-256) |
|---|---|---|---|---|
| 1 | complete, 0 pending, 0 unresolved | 72,779,027 | 51 | `dc3ff3b9350e6f3ee30f7c1b841678c8b14b8895bec01dd7d892453de06a3293` |
| 2 | complete, 0 pending, 0 unresolved (24 shards merged) | 387,289,685 | 48 | `9d9f972b7bd896518a802da12a088fd31ac1167b2642f8b8b74740574c8c636e` (merged) |

Both receipts record σ = 27/20, n_claim = 25, the measure's SHA-256
`565dbf5dd0059aa90929e4151d85fafdeef002a1b9e9aaf83f2e6243b2d393e0` and the SHA-256 of every source file; the sources in
this folder match them. The closed volume is exactly the whole root box in both systems (System 1 from its closed leaves
by depth, System 2 as an exact integer count in units of 2⁻²⁵⁶).

- System 1 ran as one run, resumed from its own checkpoints (`checker1/receipt.json`).
- System 2 ran as one run up to a checkpoint, then the pending boxes were split into shards that were run with the same
  binary and `--resume`; some shards were split again (`SPEC.md` §11). `checker2/shard.py merge` checks the partition, the
  hashes and the exact volume and writes `checker2/shards_s27_20/merged_receipt.json`. `checker2/shards_s27_20.sha256`
  lists the SHA-256 of every file of that tree.

## Reproduction

System 1 (Rust and Python 3 with NumPy):

```sh
cd checker1
cargo build --release --offline -j 1
python3 validate.py            # sanity tests, not part of the proof
./target/release/m4b-cert1 --server --threads 20 --seconds 1209600 --checkpoint-seconds 300 \
  --sigma 27/20 --output run_s27_20 --cell-depth 3
# after a stop, continue with the same command and --resume (the recorded receipt is from such a resumed run)
```

The receipt is written to `run_s27_20/receipt.json`. The run above took about 230,000 seconds of wall time with up
to 20 threads (the receipt's `seconds`). On macOS the checker refuses more than 2 threads and `--server`.

System 2:

```sh
cd checker2
cargo build --release --offline -j 1
shasum -a 256 -c shards_s27_20.sha256        # the recorded tree
python3 shard.py merge shards_s27_20          # re-checks it and rewrites merged_receipt.json identically
```

To recompute from scratch, run `./target/release/m4b-cert2 --server --threads 4 --seconds 1209600 --checkpoint-seconds 300
--sigma 27/20 --output run_s27_20` (the options of the recorded shard runs), and optionally split a stopped run with `python3 shard.py split` and resume each
shard (see `shard.py` and `SPEC.md` §11). The recorded shard runs add up to about 2.7 million seconds (each with at most
4 threads). `python3 test_shard.py` runs the positive and negative tests of the split and merge tool (log
`test_shard.log`).

System 1 checks at start-up that every source file matches the copy compiled into the binary. In both systems
`--resume` loads a checkpoint only under the same sources and measure (σ included). The checker READMEs describe further diagnostics and trial files
that are not included here.

## Contents

| Path | What |
|---|---|
| `SPEC.md` | Claim, measure checks, pose domain, rules with proofs, arithmetic, validation, amendments |
| `measure.json` | The measure (SHA-256 `565dbf5d…`) |
| `checker1/` | System 1: sources, `receipt.json`, validation logs |
| `checker2/` | System 2: sources, `shard.py`, the shard tree `shards_s27_20/` with `merged_receipt.json` |
| `summary.json` | The main numbers copied from both receipts, with their SHA-256 |
| `SHA256SUMS` | SHA-256 of every file in this folder |

## Sources

- **Classical.** The point-set lower-bound method for packing unit squares in squares is surveyed in Erich Friedman,
  "Packing unit squares in squares: a survey and new results", Electronic Journal of Combinatorics, Dynamic Survey DS7.
- **Our earlier work.** Lemma F, the wall lemma, the pair lemma and the two base checkers come from the s₃(9) result in
  the parent folder.
- **New here.** The closed measure, the rules W, P and P′ in chord form, the mean-value enclosures and the shard merge.

## Credit and license

Hiroaki Hosono (wand125). MIT (see `../LICENSE`).
