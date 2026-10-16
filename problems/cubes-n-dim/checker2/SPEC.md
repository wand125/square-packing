# Second system: specification given to the implementer

This is the specification as given before implementation (kept for the record). The section "Testing limits"
applied to development only; the full run is reported in README.md. Relative paths below refer to the
development tree (`../m2bb/` is the first system, published here as `../checker/`).

You are writing an INDEPENDENT rigorous checker. Do NOT read or reuse anything under `../m2bb/`, nor
the first system's design notes (summarised in `../PROOF.md` §4), nor `../numerics/` (they belong to the first system; independence matters).
Everything you need is in this file.

## The claim to check
For R in SO(4) write u = column 1 of R (u_e = R[e][0], e = 0..3), w_e = sum_j |R[e][j]| (row l1 norm), and

    F(R) = sum_e |R[e][0]| * (2 - w_e).

**Claim:** for every R in SO(4) with max_e u_e^2 <= 2/3, F(R) < 1.
(The region max_e u_e^2 >= 2/3 is handled by a hand-proved lemma; you only need to close it as "near".)

## Required coordinates (different from the first system)
Use the double cover S^3 x S^3 -> SO(4): R(p, q) x = p * x * conj(q) for quaternions p, q, with x in R^4 identified
with the quaternion x_0 + x_1 i + x_2 j + x_3 k. Derive the 4x4 matrix yourself (it is L(p) * Rt(conj q) with
entries bilinear in p and q) and divide by |p|^2 |q|^2 (equivalently use unnormalised p, q and divide).
Cover each S^3 factor by the 4 cube faces (one coordinate = 1, the other three in [-1, 1]); all 16 face pairs, each a
6-dimensional box [-1,1]^6. Test the matrix formula numerically (orthogonality, det = +1, R(p,q) = R(-p,-q), and
that random rotations are hit) in a unit test.

## Symmetry reduction: impose it as constraints on R (derive and check it yourself)
F depends only on |R|. For signed permutation matrices P_L (4x4) and P_R (acting on columns 2..4 only, keeping
column 1), |P_L R P_R| is |R| with rows permuted and columns 2..4 permuted, and F(P_L R P_R) = F(R).
Hence (argue it in the README; the determinant can be fixed by flipping the sign of column 4, which changes nothing
below) it suffices to check R in SO(4) satisfying all of:

    (C1) u_0 >= u_1 >= u_2 >= u_3 >= 0            (column 1 sorted, non-negative)
    (C2) R[0][1] >= 0, R[0][2] >= 0               (signs of row 0 in columns 2, 3)
    (C3) |R[0][1]| >= |R[0][2]| >= |R[0][3]|      (row 0 sorted in absolute value over columns 2..4)

A box may be **discarded** only if some constraint is violated at every point of the box, as certified by the
interval enclosures of the entries (e.g. hi(R[e][0]) < lo(R[e+1][0]), or hi(R[e][0]) < 0, or
hi(|R[0][2]|) < lo(|R[0][3]|), ...). Never discard on a guess.

## Closing a box
A box is closed if one of:
  (a) discarded by (C1)-(C3) as above;
  (b) near: max_e lo(|R[e][0]|)^2 >= 2/3 (rounded down), i.e. every point of the box is in the near region;
  (c) an upper bound of F over the box is < 1 (strictly).
Use ONLY F's upper bound for (c) (no other auxiliary bounds). Otherwise bisect.
Note: 2 - w_e >= 0 always holds for n = 4 (w_e <= sqrt(4) = 2), you may use that.

## Rigour requirements
- Interval arithmetic with outward rounding (e.g. after each correctly rounded f64 operation, move the lower end
  down by one ulp with `next_down` and the upper end up with `next_up`). No unrounded floats in any decision.
- Plain interval evaluation is far too weak in 6 dimensions (estimated ~1e12 boxes). Use a first-order (mean-value or
  Taylor-model) enclosure whose remainder is rigorously bounded over the whole box, e.g. the mean-value form
  f(c) + sum_k [df/dz_k over the box] * (z_k - c_k) with the gradient over the box from interval automatic
  differentiation, intersected with the naive enclosure and with [-1, 1]. You may choose a different but rigorous
  scheme (e.g. second-order) if it is faster.
- Choose the split coordinate by a heuristic of your own.

## Engineering requirements
- Rust, no external crates (std only), in this directory (`cargo new` here, binary name `m2check2`).
- `--selftest`: random boxes, random points inside: R orthogonal, point value of F <= the box's upper bound, and every
  entry of R(point) inside the entry enclosure. Also a unit test of the reduction: random R in SO(4), find P_L, P_R
  (with the det fix) mapping it into (C1)-(C3) and check F is unchanged.
- Split the 16 face pairs into tasks (e.g. each face pair cut into 4^6 = 4096 sub-boxes, or a coarser grid; your
  choice, but each task should take at most ~10 s). `--jobs N` threads. Each finished task appends one JSON line
  (task id, boxes, discarded, near, closed, max depth, fails, seconds) to `--log FILE`, flushed immediately; on start,
  tasks already in the log are skipped (resume). `--first/--last` select a task range. A box reaching `--max-depth`
  (default 60) without closing is a FAIL: record it (first few boxes in the log) and continue.
- Final line on stdout: a JSON summary with totals and `"ok": true` iff fails == 0 and every task ran.
- Also print/verify the tree identity: total boxes = 2 * leaves - tasks.

## Testing limits on this machine (important)
This is a shared machine: use at most `--jobs 2`, and keep any single run you start under 10 minutes. Do NOT start the
full run. Measure the speed on a few task ranges (some from the middle of the face pairs), extrapolate the total
box count and the time on 2 and on 16 cores, and write these numbers in README.md.

## Deliverables
- `Cargo.toml`, `src/main.rs`, `README.md` (coordinates, the derivation of the matrix, the reduction argument, the
  closing rules, how to run, measured speed and the extrapolation), `tests.log` (selftest output and the trial runs).

## Addenda (internal reviewer, 2026-10-14)
- In the README, state the order of the reduction explicitly: first permute columns 2..4 (C3), THEN fix the signs of
  columns 2, 3 (C2), then the sign of column 4 for det = +1. (The other order can break C2.)
- The reduction unit test must include ties (|R[0][1]| = |R[0][2]|) and rows with u_e = 0.
- For (c): |u_e| >= 0 and 2 - w_e >= 0, so an upper bound of each term is hi(|u_e|) * (2 - lo(w_e)) (rounded up).
