# First checker: interval branch and bound (Rust)

This program proves the 8-point lemma of `../PROOF.md`: every closed unit cube in [0, s]³, with
s = 2 + 1/√2, contains a point of V = {1, s − 1}³. It covers the whole parameter domain and closes every box by
one of the rules proved in `../PROOF.md`. The run is `complete` only when no box is pending and none is
unresolved.

## Build and run

```sh
cargo build --release --offline
./target/release/m5-checker --threads 2 --seconds 1150 --output run
python3 validate.py           # random-pose soundness test of every rule (needs numpy)
python3 validate_local.py     # boxes near the 45-degree wall pose, rule local_ab
```

The full run takes about 3 minutes with 2 threads on a laptop. `run/receipt.json` must then report
`"status": "complete"`, `"unresolved": 0`, `"closed_volume_fraction": 1.0` and the leaf digest below. The run is
deterministic: the digest does not depend on the thread count or on stopping and resuming (`--resume`).
Leave the diagnostic environment variable `M5_EXCLUDE` unset. If it is set, boxes inside the given parameter box
are recorded as `excluded`, which is not a proof; the receipt here has no such leaves.

## Parametrisation

- **Rotation.** A projective quaternion (1, x, y, z), with R = N(q)/(1 + x² + y² + z²). The columns of R are the
  cube's axes.
- **Centre.** c_w = h_w + u_w(s − 2h_w) with u ∈ [0, 1]³, where h_w = ½ Σ_j |R_wj|. This is exactly the set of
  feasible centres, including all wall, edge and corner contacts, so no infeasible pose needs to be rejected. It
  also keeps the zero slack at walls exact in interval arithmetic.

## Symmetry reduction

- **Cube symmetries.** Quotient by the 24 rotations of the cube, acting on the right. Their quaternion lifts are
  the 8 signed unit vectors, the 16 vectors (±1, ±1, ±1, ±1)/2, and the 24 vectors with two entries ±1/√2.
  Choosing the representative with the largest scalar part gives the closed region |x_i| ≤ √2 − 1 and
  Σ|x_i| ≤ 1.
- **Container symmetries.** Quotient by the 48 symmetries of the container about its centre, all of which fix V.
  - A proper signed permutation H acts as R ↦ H R Hᵀ and on the vector part by H. Sorting gives x ≥ y ≥ |z| and
    x, y ≥ 0. Note |z|, not z: one chirality must not be dropped.
  - Central inversion c ↦ s − c gives u_0 ≤ ½.
- **Root box.** [0, a]² × [−a, a] × [0, ½] × [0, 1]², with a an upper bound for √2 − 1.
- **Outside boxes.** A box is marked `outside` only when a strict interval inequality puts it entirely outside
  the closed region. Ties on the boundary are kept.

## Closing rules (proofs in `../PROOF.md`)

| reason | rule |
|---|---|
| `point` | some p ∈ V has \|t_i(p)\| ≤ ½ on the whole box (interval arithmetic) |
| `centre` | centre rule from Lemma F, in the collected form 2 − u_w s − 2h_w(1 − u_w) ≥ 0 (mirror for p_w = s − 1) |
| `wall` | wall lemma, both walls; the bounds on t use the wall tightening |
| `pair` | pair lemma for the 12 pairs at distance 1 |
| `local_ab` | local sign lemma; all hypotheses are evaluated over the box, including t_0 ≥ −½ at the four x = 1 points |
| `outside` | outside the fundamental region (symmetry bookkeeping) |

Otherwise the box is bisected. The coordinate is chosen by a deterministic score, which only affects speed.

## Arithmetic and receipt

- **Intervals.** Every interval operation widens its result by `next_down`/`next_up`, and all constants have
  interval enclosures. No epsilon appears in any closing rule.
- **Nodes.** A node is an exact dyadic cell of the root box. Bounds are rebuilt from the root, so the cells
  partition it exactly.
- **Scheduling.** Work is handed out in bounded deterministic rounds: at most 16 tasks of at most 64 nodes each.
- **Leaf digest.** After every round, h ← sha256(h_hex ‖ the round's leaf records), starting from sha256(""). The
  final h is `leaf_chain`. `--keep-leaves` also writes the full leaf stream and its plain sha256.

## Result

`receipt.json`:
- status `complete`, closed volume 1.0, pending 0, **unresolved 0**;
- 6,539,999 boxes, maximum depth 42;
- leaves by reason: point 1,791,261, pair 1,243,037, outside 202,285, wall 19,593, centre 10,553, local_ab 3,271;
- `leaf_chain` = `8f974e817092a7e3a5a7247e4b6679d0ca9ada2739369e7dabd5b18c86a236b9`, the same with 1 and
  2 threads;
- the full leaf stream (737,851,783 bytes) has sha256 `c42d5cb7a93623eabee1c4fbf5669e38678125bb9fd1cb9d0a6f660e5280a13c`.

## Validation

None of these tests is part of the proof.
- `validate.py`: 100,000 random poses (20,000 at walls). For each box the checker closes, the stated witness is
  checked in floating point. 0 false closures.
- `validate_local.py`: 9,356 boxes of radius 10⁻⁴ to 10⁻² near the 45° wall pose. 4,962 close by `local_ab`, and
  248,100 poses sampled in them all contain A or B. 0 failures.
- `validate_leaves.py run/leaves.jsonl`: after a run with `--keep-leaves`, samples 200 poses and the 64 corners of
  every `local_ab` leaf. On our run, 863,544 poses gave 0 failures; the worst excess was 0.0, which is equality at
  the 45° pose.
