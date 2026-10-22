# Unit cubes in a cube: s₃(9) = s₃(10) = 2 + 1/√2 and s₃(25) = s₃(26) = 3

**s₃(25) = s₃(26) = 3** (added 2026-10): proved with a closed counting measure and two independent checkers; see
[`closed-measure/`](closed-measure/). The rest of this page is about n = 9, 10.

Let s₃(n) be the side of the smallest cube that contains n unit cubes with pairwise disjoint interiors (any
positions, any orientations).

| n | s₃(n) | ≈ | optimal packing (upper bound) | lower bound |
|---|---|---|---|---|
| 9 | 2 + 1/√2 | 2.7071 | 8 corner cubes and 1 cube at the centre rotated 45° about a vertical axis | 8-point lemma |
| 10 | 2 + 1/√2 | 2.7071 | 8 corner cubes and 2 rotated cubes stacked in the central column | 8-point lemma |

The upper bounds come from the exact packings in `upper/`. Each is written in Q(√2) and checked by two
independent exact checkers. They are the packings listed on Erich Friedman's Packing Center page "Cubes in Cubes"
(https://erich-friedman.github.io/packing/cubincub/), and we claim no originality for them. The lower bound is new
as far as we know. The result is computer-assisted, is checked by two independent checkers, and has not been peer
reviewed.

## Novelty

- Friedman's page lists the packings for n = 9 and n = 10 at side 2 + 1/√2, with no proof of optimality.
- We found no published proof of a lower bound s₃(9) ≥ 2 + 1/√2. If you know of one, please open an issue.
- The case s₃(n) = 2 for 2 ≤ n ≤ 8 follows from Lemma F (`lemma_f/`) and is included because the main proof uses
  Lemma F. We do not claim novelty for it.

## The method

**8-point lemma.** Let s = 2 + 1/√2 and V = {1, s − 1}³. Every closed unit cube in [0, s]³ contains a point of V.
Boundary points count.

Suppose 9 unit cubes fit in a cube of side L < s. Push each cube away from the corner by the factor s/L, moving its
centre while keeping its orientation. This gives 9 pairwise disjoint closed unit cubes in [0, s]³. Each contains a
point of V, and V has only 8 points, so two of them share a point. This is a contradiction. The details are in
`PROOF.md` §1.

The 8-point lemma is the three-dimensional analogue of the 4-point set {1, s − 1}² used for packing squares in
squares. It is proved by a branch and bound over the six parameters of a pose (rotation and centre). Every
parameter box is closed by one of these rules, all proved in `PROOF.md`:
- **point:** a point of V is inside the cube for every pose in the box, by interval arithmetic;
- **centre rule:** from Lemma F, Σ_w |R_wk|(2 − 2h_w) ≤ 1, where h_w is half the ℓ¹ norm of row w of R;
- **wall lemma;**
- **pair lemma:** for two points at distance 1;
- **local sign lemma:** it handles the cube rotated 45° that touches a wall with four points of V on the midpoints
  of its face edges. There the contained point switches between neighbours, so no single point closes a box.

The bound is attained, so the margin is zero at several poses. Every rule is a closed inequality and handles
equality exactly; no epsilon is used anywhere.

## Contents

| Path | What |
|---|---|
| `PROOF.md` | The theorem, the scaling argument, and statements and proofs of all lemmas |
| `lemma_f/` | Lemma F: hand proof near the axes and two independent computer checks elsewhere |
| `upper/` | Exact packings for n = 8, 9, 10 and two exact checkers |
| `checker/` | First system: Rust interval branch and bound (quaternions; 1,152-fold reduction: 24 rotations of the cube and 48 symmetries of the container) |
| `checker2/` | Second system: independent Rust implementation (ZYZ Euler angles; 32-fold reduction: the 8 reflections and a quarter turn about one cube axis) |
| `closed-measure/` | s₃(25) = s₃(26) = 3: closed measure, SPEC, two checkers and their receipts |

## Results

| System | Status | Boxes | Max depth | Leaf digest (chained SHA-256) |
|---|---|---|---|---|
| first | complete, 0 unresolved | 6,539,999 | 42 | `8f974e817092a7e3a5a7247e4b6679d0ca9ada2739369e7dabd5b18c86a236b9` |
| second | complete, 0 unresolved | 784,835,241 | 45 | `c56bdc3b51ef3015cc1856cf00e61ac1218d40c1746200e192b5a66fb8dd2ca2` |

Reproduction commands are in each checker's README. On a laptop, the first system runs in about 3 minutes with
2 threads. The second system covers a domain about 36 times larger (it reduces by 32 of the 1,152 symmetries: the 8 reflections and a quarter turn about one cube axis) and
takes about 4.7 thread-hours; it ran in 18 minutes with 16 threads on a server.

## Sources

Our results build on three layers of earlier work:
- **Classical.** The point-set lower-bound method for packing unit squares in squares is surveyed in Erich
  Friedman, "Packing unit squares in squares: a survey and new results", Electronic Journal of Combinatorics,
  Dynamic Survey DS7.
- **Our earlier lemmas.** Lemma F, the wall lemma and the pair lemma come from our work on cubes in cubes for
  s₃(2) = 2 and side-k containers.
- **New here.** The 8-point lemma, the local sign lemma and the two checkers.

## License

MIT (see `LICENSE`). The packings in the table are from Erich Friedman's Packing Center.
