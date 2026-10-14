# Independent ZYZ interval checker

`far_check2.py` is a second implementation of the stated rotation-matrix
claim. It was written without reading or importing `far_bb.py`, and uses no
first-system code, certificates, or quaternion parametrization.

## Method

Use `R = Rz(alpha) Ry(beta) Rz(gamma)` with
`alpha,gamma in [0,2*pi]`, `beta in [0,pi]`. This covers SO(3): the first two
rotations can place the third axis anywhere on the unit sphere, and the last
rotation accounts for the remaining rotation about that axis. The redundant
angles at the poles and periodic endpoints are included.

The stack starts with the entire domain. Endpoints are stored as exact dyadic
coefficients of pi. Each angular interval is constructed by multiplying those
coefficients by **`mpmath.iv.pi`**. The default **`iv.prec = 64` bits** applies
to interval trigonometric functions and every matrix product, sum, absolute
value, square, row norm, and evaluation of `F_k`. Ordinary floating-point pi
and `math.sin/cos` are never used. Binary64 midpoint arithmetic on these dyadic
coefficients is exact through the fixed depth limit of 40.

For each still-open column, close it only when either:

- the interval lower endpoint of some `|R[i][k]|^2` is strictly greater than
  `1/2`; or
- the interval upper endpoint of `sum_i |R[i][k]|*(2-w_i)` is strictly less
  than `1`.

Interval dependency can make bounds loose, but cannot turn an inconclusive
box into a certificate. Closed columns remain closed in descendants. If any
column remains open, bisect the widest angular dimension and push both halves.
No symmetry reduction or sampling is used. An unresolved box at depth 40
prints `FAIL` with its bounds to stderr and exits nonzero. A time limit or
interrupt also exits nonzero. `ok: true` is emitted only after the entire
stack is exhausted; an exact integer volume tally additionally checks that
closed leaves cover the full parameter domain.

## Run

Requires Python 3 and mpmath (available here as version 1.3.0):

```sh
python3 -c 'import mpmath'
python3 -B check2/far_check2.py
```

The default wall-clock budget is 1,200 seconds; exactly one process is used.
Options: `--prec 64`, `--max-seconds 1200`, `--progress-seconds 30`.
Progress and unresolved-box diagnostics go to stderr. stdout contains one
final JSON line with `ok`, evaluated `boxes` (including internal nodes), fully
closed `leaves`, maximum evaluated depth (`0` at the root), and elapsed seconds.
`ok: false` means incomplete verification, not a mathematical counterexample.
Progress-based total-time estimates are traversal-dependent estimates only.

## Local validation and measured run

Additional checks passed for 48 exact cardinal-angle matrices against an
independently multiplied integer-matrix reference, strict rejection of an
`F_k = 1` boundary, depth-limit failure reporting, and complete-root success
reporting. The latter two exercise control flow with substituted predicates;
the actual mathematical verification below uses the unmodified checker.

Measured command (2026-10-14):

```sh
python3 -B check2/far_check2.py --max-seconds 180 > check2/run.jsonl 2> check2/run.log
```

The run exited with status 0 after about 2 minutes 44 seconds, using one
process. All columns closed throughout the full domain. The measured rate was
3,631 boxes/second, and the maximum depth was 22 (below the limit of 40).
Final stdout line, also preserved in `run.jsonl`:

```json
{"ok": true, "boxes": 594431, "leaves": 297216, "max_depth": 22, "seconds": 163.707932}
```

`run.log` preserves progress diagnostics and the final closed-domain fraction
of `1.0`. This successful result certifies the stated strict alternative for
every rotation and every column, subject to mpmath's interval arithmetic and
the Python runtime functioning correctly.
