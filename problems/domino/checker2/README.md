# Checker 2: an independent angular sweep

Run the commands from `checker2/`. In the table, certificate names are relative to `certificates/n4/` (the control: to the repository root). Requires Python 3.10+, `gmpy2` and `sympy`.

## Usage and results

`sweep.py` is the check2 angular sweep, with `--container rect2` for the container
[0, 2L] × [0, L]. No symmetry is used: every angle u = tan(θ/2) ∈ [0, 1] is swept. Points that
are listed twice on x = L are counted with their summed weight.

    python sweep.py ../certificates/n4/below/n4_L1927_1000.json --container rect2 --n 4 --jobs 8 --out out.json
    python sweep_k.py ../certificates/n4/n4_cert.json --n 4 --jobs 4 --out out.json

| certificate | points | total | min captured | critical angles | time | verdict |
|---|---|---|---|---|---|---|
| below/n4_L1927_1000 | 12 | 77/20 | 11/10 | 1,171 | 30 s | verified |
| below/n4_L77_40 | 12 | 77/20 | 11/10 | 1,167 | 29 s | verified |
| below/n4_L957_500 | 3 | 3 | 1 | 153 | 2 s | verified |
| below/n4_L9651_5000 | 7 | 7/2 | 1 | 427 | 10 s | verified |
| n4_cert (L = v4 exactly) | 7 | 7/2 | 1 | 1,723 | 342 s | verified |
| controls/control_v4_plus_1e-6 (must fail) | 7 | 7/2 | 1/2 | 1,735 | 336 s | failed, with an explicit pose |

Times are for 8 processes (the runs at L = 9651/5000, v4 and v4 + 10⁻⁶: 4 processes) on a 16-vCPU Linux machine. The recorded runs are in `results/`; each holds the sha256 of the certificate it checked.

## L = v4 exactly (`sweep_k.py`, `kfield.py`)

`sweep_k.py` is the same sweep over the cubic field K = Q(alpha), where alpha = v4 is the
largest real root of 5x³ + 8x² − 32x − 4 (`kfield.py`).
- Elements are a + b·alpha + c·alpha² with rational a, b, c.
- Signs are decided exactly, by interval evaluation on a rational isolating interval of alpha
  that is halved by the sign of f.
- The critical-angle polynomials are mapped to rational polynomials by the norm (the
  determinant of the multiplication matrix), whose real roots contain theirs.

The wedges in the certificate are not used, and neither is any symmetry. The second-order,
switching contact at the extremal angle u* is handled like any other margin-zero contact:
- u* is a critical angle, where three lines of the arrangement are concurrent;
- the open intervals on both sides of u* are checked exactly at sample angles;
- u* itself is covered by the closure argument. The captured weight is upper semicontinuous, so
  its value at a limit pose is ≥ the lim sup of nearby values.

The control at L = v4 + 10⁻⁶ fails with an exactly checked pose: u = 121/329 (next to
u* ≈ 0.3691), captured weight 1/2.

`kfield.py` was written from the specification `../checker/README.md` only. The first
checker's code (`../checker/*.py`) was not read. `kfield.py` was tested against 80-digit sympy
values on 3,000 random elements (products, inverses, signs) and near-zero elements; there
were no mismatches. Times above are for 4 processes on one machine.
