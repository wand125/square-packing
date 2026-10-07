# hexs2: second implementation of stage 2

A dependency-free Rust (1.85) interval branch-and-bound verifier for the stage-2 claim of
`../n3/SPEC_stage2.md`. It was written from that specification and the local lemma
(`../n3/local_lemma/LOCAL_LEMMA.md`) only, without reading the first implementation
(`../stage2_checker/`), section 5 of `../n3/PROOF.md` or its design notes.

## Result

All 742 excused boxes are PROVED, with 0 unproved leaves.

- 16 threads, `--max-depth 80`: wall time 1401 s, about 6.1 core-hours, 4.37·10^9 nodes in total.
- Largest depth reached: 77. Per box: median 13 s, maximum 117 s.
- Machine: 16-vCPU x86-64 Linux (c2d-highcpu-16).
- Records: `del11_run/full.jsonl` (one line per box), `del11_run/full.stderr` (summary),
  `del11_run/run.sh` (the commands). `del11_run/SHA256SUMS` covers the results, the sources and
  the stage-1 certificate; check it from this directory with `sha256sum -c del11_run/SHA256SUMS`
  (or `shasum -a 256 -c`).

Pruning rules: (A) containment by support functions; (B) the two squares cannot be separated by
any of the 4 edge normals (separating-axis test); (C) exchange of squares 2 and 3; (D) the local
lemma, over the 4 cosets of the pinwheel's stabiliser in D6, the 6 labellings and the 4 signed
axes of each square. The lemma thresholds (cos 0.08 and |p|² ≤ 0.0025) are compared on the
conservative side.

**Negative control** (`del11_run/neg.jsonl`): at side 1.01·v, where the scaled pinwheel is a
genuine packing, and without the lemma, box 1 is not proved (769,232 unproved leaves after
6.9·10^6 nodes, near the pinwheel).

## Build and use

```sh
cargo build --offline --release
cargo test --offline
# the recorded run (depth 80 is needed; the default 60 is not enough):
./target/release/hexs2 --cert ../n3/stage1_cert.json --threads 16 --max-depth 80 --out full.jsonl
# the negative control:
./target/release/hexs2 --cert ../n3/stage1_cert.json --k 1 --threads 1 --max-depth 45 \
    --side-scale 1.01 --no-lemma --out neg.jsonl
```

`--k` accepts an inclusive range or one index; omission selects all 742 boxes.
Other defaults: `--wu 4`, `--max-depth 60`, `--side-scale 1.0`, lemma enabled,
threads = available parallelism. `--out PATH` writes JSONL to that file instead of
stdout, replacing an existing file. Stderr always receives the final summary.
Records are flushed on completion, in worker completion order.

Exit codes: 0 = all selected boxes proved; 1 = at least one UNPROVED box;
2 = invalid arguments/input or I/O error. A panic is an execution failure, never a
proof. Counts and timing describe visited nodes, including internal nodes.
UNPROVED means that residual boxes remain, not that a packing was found.

## Rigour and implementation

* `src/interval.rs`: IEEE-754 next-up/down via bits, outward-rounded arithmetic,
  signed-zero/infinity handling, squaring and absolute values. Exactly representable
  constants use thin intervals. Rational endpoints are expanded after division;
  numerator/denominator limits and nonzero denominators are checked before casting.
* `src/json.rs`: strict recursive JSON parser, preserving string/number lexemes,
  including escaped Unicode. Rejects duplicate keys and malformed JSON. No serde.
* `src/geometry.rs`: monotone half-angle axes; containment, separating-axis overlap,
  exchange symmetry and the given local lemma, in the requested order.
  The lemma uses outward-enclosed matrices, all four cosets and six labellings,
  and all four signed axes for each square. Its threshold comparisons use an
  upper enclosure of CR and a lower enclosure of the squared radius.
* `src/main.rs`: certificate validation and frame conversion, explicit depth-first
  stack, weighted widest-coordinate splitting, atomic work queue over k, and
  JSONL reporting. Children share the same floating split point with no gaps.
* `src/tests.rs`: exact i128 rational comparisons (binary endpoints are decoded and
  cross-multiplied, not compared to rounded reference divisions), rounding edges,
  JSON/input validation, the packing control, all D6 images and labellings of the
  pinwheel, depth/accounting checks, and the explicit tangency limitation below.

The certificate must have exactly 742 excused boxes with ordered rational
endpoints and exact rational u bounds in [0,1/7]. Outward-rounded u endpoints are
intersected with the known domain [0,1], so an exact zero does not become a negative
parameter. Position roots use the outer bounds of v and h. Interval products are
never evaluated with fast-math or epsilon tests.

Symmetry C is justified by exchangeability of squares 2 and 3 in each root: an
excluded ordering has an equivalent surviving ordering. It is not by itself a
geometric impossibility for a fixed labelled tuple.

## A test that is deliberately ignored: exact contact

An assertion that B prunes the exact pinwheel (a touching configuration) is incompatible with the mandated
outward-rounded calculation. Exact contact has a separating-axis gap of zero;
the computed enclosing interval extends slightly above zero. With thin floating
poses, the largest G.hi for the three pairs is respectively approximately
2.4425e-15, 2.6645e-15, and 2.4425e-15. With interval enclosures of the algebraic
exact poses, it is 5.9952e-15, 5.3291e-15, and 7.7716e-15. Consequently B does not
prune any of those pairs. Replacing `G.hi <= 0` with an epsilon would be unsound.
Also, an irrational exact pose cannot literally be a thin f64 box.

The precise requested assertion is retained as the explicitly ignored test
`requested_b_exact_pinwheel_tangency`. Running it demonstrates the failure:

```sh
cargo test --offline requested_b_exact_pinwheel_tangency -- --ignored --nocapture
```

This command exits 101. It is an unmet requirement,
not a passing test. The active regression test checks that B is conservative at
contact, B certifies overlap with a strict interior margin, and D certifies the
pinwheel (including its algebraic interval enclosure). Satisfying the requested B
assertion would require an additional exact symbolic contact argument outside the
specified interval-only B calculation.

The side-scale 1.01 negative control has minimum containment slack 0.005 and
minimum pairwise separating gap 0.011830127019. A, B and C do not prune either the
thin configuration or boxes of full coordinate width 1e-6 around it (u is clipped
to its domain). D is disabled. D is refused for any side scale other than 1.

## Tests

`cargo test --offline`: 8 passed, 0 failed, 1 explicitly ignored (above).

## Interpretation choices where the specification was not explicit

1. Root depth is 0. Pruning is attempted before applying the depth cutoff. An
   unpruned node at depth greater than max-depth is UNPROVED, so the default can
   visit depth 61. If no representable interior split exists, it is also UNPROVED.
2. Equal weighted widths choose the first coordinate. Unsplittable coordinates
   are skipped. The left child is searched first.
3. CLI real numbers denote their parsed finite f64 values; side-scale is enclosed
   outward for multiplication (exact 1 is special-cased). For scaled controls the
   frame subtraction uses scaled v and h. Scale is restricted to (0,1e100] to
   keep geometric arithmetic finite. The lemma is allowed only at scale exactly 1.
4. Worker count defaults to available parallelism. JSONL is emitted in completion
   order. Incomplete runs use nonzero exit status as documented above.
5. Absolute value only selects or negates endpoints (exact operations); a
   straddling interval has exact lower bound 0. Squaring a straddling interval
   likewise has lower bound 0 and an outward-rounded upper bound. Non-straddling
   squares widen both product endpoints.

These choices do not strengthen pruning or silently declare a residual box proved.
