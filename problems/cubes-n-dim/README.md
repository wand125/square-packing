# Two unit cubes in a cube in four dimensions: s₄(2) = 2

Let s_n(k) be the side of the smallest n-cube that contains k unit n-cubes with pairwise disjoint interiors (any
positions, any orientations). We prove

**s₄(2) = 2:** two unit 4-cubes do not fit in a 4-cube of side less than 2.

The upper bound is the trivial packing. The lower bound follows from a centre lemma: every unit 4-cube inside
[0, 2]⁴ contains the centre of [0, 2]⁴. The result is computer-assisted. The far region is checked by two
independent checkers. It has not been peer reviewed.

## The method

For R ∈ O(n) let w_i be the ℓ¹ norm of row i, and let F_k(R) = Σ_i |R_ik| (2 − w_i). If F_k ≤ 1 for every
orthogonal R and every column k, then every unit cube in [0, a]ⁿ with a < 2 contains the centre in its interior.
Then two cubes with disjoint interiors cannot both fit (`PROOF.md` §1). Write c for the largest |R_e1|.
- **Near an axis, c² ≥ 2/3 (hand proof).** A polar-decomposition argument gives
  1 − F_1 ≥ K(Q, x) + 2(1 − c)(1 − ‖Qᵀx‖₁). Here x is the rest of column 1 and Q ∈ O(3) is the orthogonal factor
  of the lower-right block. The term K(Q, x) is non-negative by Lemma F in dimension 3, which is published in
  `../cubes-in-cube/lemma_f/` (`PROOF.md` §2–3).
- **Away from the axes, c² ≤ 2/3 (computer-assisted).** We check F_1 < 1 by interval branch and bound with outward
  rounding. Two independent programs do this, in different coordinates and with different symmetry reductions
  (`PROOF.md` §4).

## Contents

| Path | What |
|---|---|
| `PROOF.md` | The theorem, the reduction to F ≤ 1, the near-region proof, and the statement checked by computer |
| `checker/` | First system: Rust, std only; column 1 plus a quaternion for the other columns; reduction by 9,216 |
| `checker2/` | Second system: independent Rust, std only; a pair of quaternions; written from `SPEC.md` alone |
| `lean/` | Lean 4 + Mathlib: the near-region lemma in any dimension and Lemma K, with Lemma F in dimension m as a hypothesis |
| `verify_logs.py` | Checks the run logs of both systems: coverage of all tasks, no failures, tree identity |
| `spectral/` | Version 2: s_n(2) = 2 for n = 3, 4, 5 by a spectral bound and short exact rational certificates, and n = 6 in `spectral/n6/` (release `cubes-n-dim-v2`) |

## Version 2: n = 3, 4, 5, 6

`spectral/` gives a second, shorter proof of s₄(2) = 2 and extends it to s₃(2) = 2 and s₅(2) = 2. It uses the
near-region step of §3 for all three dimensions. Away from the axes it replaces the interval branch and bound by
the bound 1 − F ≥ √2 Tr √(diag(p) − ppᵀ) − 2 Σ √p_i + 2, where p is the squared column, together with exact rational
certificates (5, 557 and 21,502 simplices). Each certificate is checked by two independent systems in seconds with
the Python standard library. See `spectral/README.md`. Dimension 6 (`spectral/n6/`) splits the columns into a cap, a
strip and a near-axis region, with further lower bounds and larger certificates. The version 1 proof below is
unchanged.

## Results

| System | Status | Tasks | Boxes | Max depth | Time |
|---|---|---|---|---|---|
| first | complete, 0 unresolved | 4,096 | 88,110,984 | 22 | 3 min 38 s, 2 threads, laptop |
| second | complete, 0 unresolved | 65,536 | 192,488,546 | 30 | 23 min 48 s, 2 threads, laptop, plus a retry of 102 tasks |

In the second system's full run, 102 tasks reached the per-task time cap of 8 seconds. Those tasks were run again
with a cap of 3,600 seconds, and every one closed. The two source versions differ only in the accepted range of the
cap option. Details are in `checker2/README.md` and `checker2/receipt.json`.

The published sources differ from the sources as run only in comments (internal labels, reviewer notes and
references to internal notes); no code changed. Each `receipt.json` gives the SHA-256 of the published source and of the source as run,
together with the counts.

## Reproduction

```sh
(cd checker  && cargo build --release && ./target/release/m2bb --selftest && ./target/release/m2bb --jobs 2 --log full.jsonl)
(cd checker2 && cargo build --release && cargo test --release && ./target/release/m2check2 --jobs 2 --log full.jsonl)
# logs of our runs: release asset cubes-n-dim-v1, then
python3 verify_logs.py logs
```

Rust 1.86 or later is required (`f64::next_up`/`next_down`); no crates are used.

## What is checked in Lean

The hand part of the near region (`PROOF.md` §3) is formalized in `lean/` for any dimension. This covers the
polar-decomposition inequality, the orthogonality of the explicit polar factor, and Lemma K. The main theorem
`near_region` takes Lemma F in dimension m as an explicit hypothesis (`LemmaF m`) and gives F_1 ≤ 1 for m ≤ 4
when c² ≥ 1 − 1/m. It has no `sorry`, and its only axioms are Lean's standard three. The reduction of §1, Lemma F in
dimension 3 and the far region of §4 are not formalized.

## Review status

- The hand parts (§1–3 of `PROOF.md`: the reduction, the polar-decomposition steps in dimension 4, and Lemma K) were
  checked line by line by an independent internal reviewer.
- That reviewer also checked the reductions of the first system (the 384 signed permutations, the Voronoi cell,
  the passage from O(3) to SO(3), and the Householder formula) and the specification of the second system,
  including its two corrections made during implementation.
- No external review yet. Corrections are welcome as issues.

## Sources

- **Classical.** For n = 2 (two unit squares need a square of side 2), see Erich Friedman, "Packing unit squares in
  squares: a survey and new results", Electronic Journal of Combinatorics, Dynamic Survey DS7. Friedman's
  Packing Center page "Cubes in Cubes" (https://erich-friedman.github.io/packing/cubincub/) gives no lower bound for
  two cubes, and we found no proof of s_n(2) = 2 for any n ≥ 3 in the literature. If you know of one, please
  open an issue.
- **Our earlier work.** Lemma F in dimension 3 and s₃(2) = 2 are in `../cubes-in-cube/lemma_f/`. The near-region
  argument (a)–(c) is the n = 3 argument from there.
- **New here.** The lift of the near-region argument to dimension 4 (Lemma K), the far-region statement, the two
  checkers, and s₄(2) = 2.

## Credit and license

Hiroaki Hosono (wand125). MIT (see `LICENSE`).
