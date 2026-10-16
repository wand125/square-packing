# m2bb: first system for the far region (n = 4)

**Claim checked.** For every R ∈ O(4) whose first column u satisfies max_e u_e² ≤ 2/3,

  F_1(R) = Σ_e |R_e1| (2 − w_e) < 1,  w_e = Σ_j |R_ej| (the ℓ¹ norm of row e).

The near region max_e u_e² ≥ 2/3 is the hand lemma of `../PROOF.md` §3. Std-only Rust, no crates.

## Coordinates and reductions

- **Column 1.** Left multiplication by a signed permutation permutes and negates the rows of R, so |R| changes only
  by a row permutation and F_1 is unchanged. Hence we may assume u_1 ≥ u_2 ≥ u_3 ≥ u_4 ≥ 0. Then u_1 ≥ 1/2, and
  we use t = (u_2, u_3, u_4)/u_1 with 1 ≥ t_0 ≥ t_1 ≥ t_2 ≥ 0, so u = (1, t)/√(1 + |t|²).
- **Columns 2–4.** R = [u | N_u S] where N_u is the last three columns of the Householder reflection that maps e_1
  to u (it is non-singular because u_1 ≥ 1/2) and S ∈ O(3). Rows e ≥ 2 of N_u are δ − t_e t_j (1 + u_1)/|t|².
  F_1 depends only on |R|, so S may be replaced by −S, and by S P for any signed permutation P of columns 2–4.
  Hence S may be taken in SO(3) and in any fundamental domain of the rotation group of the cube (order 24).
- **Rotation.** S is the rotation of the quaternion (1, x, y, z) (normalised), restricted to the Voronoi cell of 1
  in the binary octahedral group: |x|, |y|, |z| ≤ √2 − 1 (rounded up to 0.4143) and |x| + |y| + |z| ≤ 1.
- Together the reductions cut the domain by 384 × 24 = 9,216.

## Closing rules

A box of the six coordinates (t, x, y, z) is closed when one of these holds for every point of the box:
1. **infeasible:** the ordering of t or the ℓ¹ condition on (x, y, z) is violated;
2. **near:** |t|² ≤ 1/2, i.e. max_e u_e² = u_1² ≥ 2/3 (the hand lemma applies);
3. **F:** an upper bound of F_1 is < 1. Two upper bounds are used, and the smaller one counts:
   Σ_e a_e(2 − w_e), and 2‖u‖₁ − 1 − Σ_e a_e ‖m_e‖₁ (m_e is row e without its first entry, a_e = |u_e|; the two
   are equal as real numbers). The bound G(u) = 2‖u‖₁ − 1 − Σ_e a_e √(1 − a_e²) (from ‖m_e‖₁ ≥ ‖m_e‖₂) closes
   some boxes without using S (counted as `closed_g`).

Otherwise the box is split in two along the coordinate with the largest Σ |∂_k R| · width.

**Rigour.** Every entry of R is enclosed by the mean-value form R(c) + Σ_k ∂_kR(box)(z_k − c_k), where the gradient
over the whole box comes from forward-mode automatic differentiation in interval arithmetic. The result is
intersected with the naive interval enclosure and with [−1, 1]. Every interval operation rounds outward with
`next_down`/`next_up` after the correctly rounded f64 operation (+, −, ×, ÷, sqrt), so every decision is rigorous.
A box whose |t|² interval contains 0 gets an unbounded reciprocal and is never closed by rule 3.

## Build and run

Rust 1.86 or later (for `f64::next_up`/`next_down`).

```sh
cargo build --release
./target/release/m2bb --selftest                 # random points in random boxes: F ≤ bound, orthogonality
./target/release/m2bb --jobs 2 --log full.jsonl  # the full run
```

The root boxes are split into 4⁶ = 4,096 tasks; each finished task appends one JSON line to the log and is skipped
on resume.

## Full run

Laptop (aarch64 macOS, Rust 1.99.0), `--jobs 2`, 3 min 38 s:

`{"run_tasks": 4096, "boxes": 88110984, "infeasible": 3000039, "near": 376969, "closed_g": 542, "closed_f": 40679990, "max_depth": 22, "fails": 0}`

- 44,057,540 leaves, and boxes = 2 × leaves − 4,096 (a full binary tree per task, nothing dropped).
- The largest upper bound among the boxes closed by rule 3 is 0.99999999808.
- The log is in the release asset (`logs/checker/full.jsonl`); `../verify_logs.py` checks coverage and the tree
  identity.
- The published `src/main.rs` differs from the source as run only in comments; no code changed. Both SHA-256
  values are in `receipt.json`.
