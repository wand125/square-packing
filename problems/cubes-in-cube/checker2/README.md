# Second checker: independent interval branch and bound (Rust)

This program proves the 8-point lemma of `../PROOF.md` a second time: every closed unit cube in [0, s]³, with
s = 2 + 1/√2, contains a point of V = {1, s − 1}³. It was written from the statements of the lemmas only, without
reading the first checker. It differs from the first checker on purpose:
- rotations are ZYZ Euler angles, not quaternions;
- the domain is reduced by 32 symmetries only: the 8 coordinate reflections of the container and a quarter turn
  about one cube axis (the first checker uses all 1,152 = 24 × 48);
- the interval type and the interval sine and cosine are its own.

The run is `complete` only when no box is pending and none is unresolved.

## Build and run

```sh
cargo build --release --offline
./target/release/m5-check2 --validate          # built-in soundness tests, about 2 minutes
python3 integration.py                         # determinism and resume tests (needs a Rust 1.86 build in target186/)
python3 stress_random.py; python3 stress_p0.py # extra sampled tests (need numpy)
./target/release/m5-check2 --server --threads 16 --seconds 1209600 --depth 72 --checkpoint-seconds 60 --output full
```

There are no third-party dependencies. The minimum Rust version is 1.86. On macOS the program refuses more than
2 threads, more than 1200 seconds, and `--server`; use `--resume` to continue a run there. Elsewhere `--server`
lifts these limits. `--output` must lie inside this directory. (The same guard also refuses a subdirectory
named `stopped_v1`, a development archive that is not part of this bundle. The sources here are byte-identical to
the ones that produced the receipt, so this line was left as it was.) `--keep-leaves` also writes the leaf stream.
`--batch` reads JSON lines `{"box": [[lo, hi] × 6]}` and prints the rule that closes each box and the points it
names.

The full run takes about 18 minutes with 16 threads on a 32-thread Linux server (about 4.7 thread-hours). It must
end with `"status": "complete"`, `"pending": 0`, `"unresolved": 0` and the leaf digest below. The search is
deterministic: the digest does not depend on the thread count or on stopping and resuming.

## Parametrisation and coverage

Write h_w = ½ Σ_j |R_wj| (half the ℓ¹ norm of row w). Each row is a unit vector, so ½ ≤ h_w ≤ √3/2 < s/2 and
s − 2h_w > 0. The feasible centres are exactly c_w = h_w + u_w(s − 2h_w) with u_w ∈ [0, 1].

- **Reflections.** Reflecting a world coordinate about s/2 preserves the container and permutes V. It changes
  the sign of that row, leaves every h_w unchanged, and sends u_w to 1 − u_w. If the frame becomes improper, negate
  a column; this changes neither the cube nor any h_w. So every feasible cube has a representative with a proper
  frame and u ∈ [0, ½]³. No coordinate permutation is used to reduce the domain.
- **Euler angles.** R = Rz(α) Ry(β) Rz(γ). The third column of a proper frame has spherical coordinates (α, β)
  with α ∈ [0, 2π], β ∈ [0, π]. Undoing Rz(α) Ry(β) fixes the third axis and leaves Rz(γ), so ZYZ covers SO(3),
  including the singular endpoints β = 0, π, where redundant angles are kept. Right multiplication by Rz(π/2)
  permutes and signs the first two cube axes and maps [−½, ½]³ to itself, so γ ∈ [0, π/2] suffices.
- **Root box.** [0, 2π] × [0, π] × [0, π/2] × [0, ½]³, with the angle endpoints enclosed outward.

## Closing rules (proofs in `../PROOF.md`)

| reason | rule |
|---|---|
| `point` | some p ∈ V has \|t_i(p)\| ≤ ½ for i = 0, 1, 2 on the whole box (t_i as defined at the start of `../PROOF.md`) |
| `centre` | centre rule from Lemma F (§2), in the collected form 2 − u_w s − 2h_w(1 − u_w) ≥ 0 so that a wall contact keeps its exact zero slack; for p_w = s − 1 use 1 − u_w |
| `wall` | wall lemma (§3), both walls; each of the six signed bounds of a point may come from intervals or from the lemma |
| `pair` | pair lemma (§4) for the 12 pairs at distance 1; \|d\| = 1 is used symbolically |
| `local` | local sign lemma L (§5) in all 288 forms: 3 walls × 2 orders of the other two axes × 48 signed column assignments |

The wall tightening of §3 is applied to the bounds on t before these tests.

The 288 forms of Lemma L have two separate justifications.
- **World part.** Renaming the wall w and the other two axes as x, y, z is a coordinate permutation. It is a
  symmetry of [0, s]³ that maps V to V and the wall {w = 0} to {x = 0}; c, h, g, d, e and the points move with it.
  This transports the lemma; it does not reduce the search domain.
- **Frame part.** Any signed permutation of the columns describes the same cube and leaves every h_w unchanged.
  The proof of Lemma L uses only orthonormality, unit rows and columns, Cauchy–Schwarz and the stated signed
  hypotheses. It never uses the determinant, the handedness or the original labels, so it holds for proper and
  improper frames alike.

The strict hypothesis ‖d‖₂ < ½a_0x − a is certified without a square root: the lower bound of ½a_0x − a must be
positive and the upper bound of d_y² + d_z² strictly below the lower bound of (½a_0x − a)². The hypothesis
t_0(q) ≥ −½ is checked for all four points q.

## Arithmetic

- **Intervals.** Every addition and multiplication is rounded one representable step outward at each endpoint, by
  bit-level successor and predecessor. Division only occurs by exact positive integers and is rounded the same way.
  No epsilon or tolerance appears in any closing inequality.
- **Constants.** π is enclosed by [3.141592653589793, 3.1415926535897936]. 1/√2 is enclosed by
  [0.7071067811865475, 0.7071067811865476]; the validation checks this with exact integer arithmetic.
- **Sine and cosine.** For an interval X narrower than 6, take a representable midpoint m and an integer k near
  m/(π/2), and form Z = m − kπ/2 outward with |Z| < 1. Taylor polynomials to degree 33 and 32, with the remainder
  bound 1/33! < 2⁻¹²⁰ added, enclose sin Z and cos Z; the quadrant identities give sin m and cos m. Both functions
  are 1-Lipschitz, so widening by the radius of X encloses every value on X. The result is intersected with [−1, 1].

## Search and receipt

- **Splitting.** The coordinate to halve is the one with the largest scaled width: angle widths in radians, centre
  widths divided by 4. Ties go to the lower coordinate. The midpoint must lie strictly inside the interval, and both
  children are always kept. The choice only affects speed, not soundness.
- **Scheduling.** The frontier is a stack. Each round pops at most 256 boxes and forms 64 tasks of 4 boxes. Each task
  runs its own depth-first search for at most 4096 boxes. Results are committed in task order, and the remaining
  stacks are pushed back so that task 0 continues first. Tasks do not depend on the thread count, so the tree and
  the digest do not either.
- **Leaf records.** One ASCII line per leaf: `depth:rule:points:endpoint bit patterns`. Unresolved leaves use rule 0.
- **Leaf digest.** Starting from the hex of sha256(""), after every round h ← sha256(h_hex ‖ the round's
  records). The final h is `leaf_chain`. SHA-256 is implemented locally and checked against three test vectors.
- **Checkpoints.** Written to a temporary file, synced and renamed atomically. Resuming restores the frontier order,
  the counters and the digest exactly.

## Result

`receipt.json` (16 threads, Linux x86_64, rustc 1.86.0):
- status `complete`, pending 0, **unresolved 0**;
- 784,835,241 boxes, maximum depth 45, 1,051 seconds;
- leaves by reason: point 292,654,066, pair 94,356,391, wall 3,774,181, centre 1,295,486, local 337,497;
- `leaf_chain` = `c56bdc3b51ef3015cc1856cf00e61ac1218d40c1746200e192b5a66fb8dd2ca2`;
- the SHA-256 of each source file is listed in the receipt and matches the files here.

## Validation

None of these tests is part of the proof. They compare closures against an ordinary floating-point reference with
tolerance 10⁻¹², used only in testing.
- `--validate` (`validation.log`):
  - 100,000 random poses and 20,000 poses at walls, all closed, with zero false closures;
  - each rule alone on 20,000 further boxes;
  - 432 boxes around the images of the 45° wall pose, all closed by `local`;
  - four degenerate poses;
  - a symmetry test on 10,000 poses, comparing all eight containment bits;
  - thread determinism.
- `integration.py`: 1 and 2 threads, a resume with a changed thread count and a damaged stream tail, and a Rust
  1.86 build give identical counters, frontier, digest and leaf stream.
- `stress_random.py`: 20,000 random boxes anywhere in the domain, a quarter of them at a wall. 14,307 closed;
  1,487,928 poses sampled in them; 0 failures.
- `stress_p0.py`: 6,000 boxes around the Euler representatives of the 45° wall pose and its axis images. 5,572
  closed by `local`; 579,488 poses sampled in them; 0 failures.
