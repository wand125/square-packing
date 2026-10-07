# Results (2026-10-08)

All runs were on one machine with 6 processes (`run_all.sh`). JSON outputs are in `out/`. Certificate paths are
relative to `certificates/n6/`.

## Certificates (2-c to 2-f)

| certificate | sha256 | points / obstacles / exclusions | total | n | u-intervals | result |
|---|---|---|---|---|---|---|
| `loc3/cert_e1_100.json` (D3) | `bbf90e7a…` | 138 / 0 / 4 | 137013/22900 | 6 | 2,695 + window | **verified** (cellgrid outside the window, 4 s; sweepwin inside it, 241 s) |
| `stage2/cert_w_o1.json` | `f041908c…` | 4 / 178 / 5 | 4 | 5 | 1,997 | **verified** (21 s) |
| `stage2/cert_w_o0_p13_auto.json` | `cf8b6d7d…` | 14 / 456 / 3 | 14/3 | 5 | 2,188 | **verified** (24 s) |
| `stage2/cert_s3u2.json` | `e1162d62…` | 6 / 162 / 1 | 7/2 | 4 | 2,061 | **verified** (2 s) |
| `stage2/cert_o03d.json` | `5803379a…` | 3 / 622 / 2 | 3 | 4 | 2,149 | **verified** (16 s) |
| `stage2/cert_o13b.json` | `d670f9a8…` | 5 / 392 / 2 | 3 | 4 | 1,999 | **verified** (8 s) |

- The D3 certificate passes the exact invariance check, and U = 1/7 > tan(π/24) is proved exactly.
- **Stage-1 window.** Without the window, cellgrid stays stuck on u ∈ [0, h] for every h. The tight contact there
  is the bottom wall together with the top edge of the square at t = 0. The capture margin grows like t, and the
  Lipschitz shrinking costs h.
- Window: x ∈ [2, 2.3], y ∈ [0.4999, 0.50001], u ∈ [0, 10⁻⁸].
  - After the constant-sign reduction, sweepwin keeps 89 lines.
  - None of the 67,333 event polynomials has a root in (0, 10⁻⁸].
  - So one sample suffices: 183 vertices, 420 sectors, minimum weight 109/100.
- With E = 10⁻⁷ instead, there are 155 genuine critical angles, from 1.36·10⁻⁸ upward. They come from pairs of
  points whose x-distance is just below 1.

## Obstacle points (2-g)

`witness.py`, one obstacle box per stage. Stage 2 uses D = 1/100 and DTH = 1/100. Stage 3 uses D = 41/2500 and
DTH = 3/250.

| certificate | obstacle points | proved by square | result |
|---|---|---|---|
| `cert_w_o1.json` | 178 | 1: 178 | **verified** |
| `cert_w_o0_p13_auto.json` | 456 | 0: 456 | **verified** |
| `cert_s3u2.json` | 162 | 0: 81, 1: 81 | **verified** |
| `cert_o03d.json` | 622 | 0: 447, 3: 175 | **verified** |
| `cert_o13b.json` | 392 | 1: 176, 3: 175, 1 with the chain restriction: 41 | **verified** |

Exactly 41 points need the chain restriction d_R(P) ≥ cos(3/250). This matches the 41 chain witnesses reported
by the generator.

## Lemma (2-a) and its hypotheses (2-b)

- `lemma2.py`: (M) holds for (Φ, δ, τ) = (1/10, 3/25, 3/50), (1/20, 7/100, 3/100) and (1/10, 1/10, 2/25), in both
  cases and all orthants.
  - The coefficient is c = min(1/1000, c3).
  - c3 ≥ 0.0099, 0.0050 and 0.0299 for the three parameter sets.
- `chain2.py` checks H1 to H4 for the three stage-3 cases.
  - t at the box corners lies in [0.055, 0.257] (0,1:3), [0.048, 0.262] (0,3:1) and [0.096, 0.214] (1,3:0).
  - The rigorous enclosure stays inside [τ, 1 − τ].
  - The Step 2 claims hold on the lemma boxes (1/20, 7/100) and (1/10, 3/25).

## Stage links (2-h)

`chain2.py` checks the following.

- **L1.** The C3 symmetry of the pinwheel holds exactly, with labels (0 2 4)(1 3 5), and the corner directions are
  kπ/6.
- **L2.** The stage-1 boxes are exactly c* ± 1/100 for squares 0 and 1 and for their mirror images, with
  u ≤ 1/200 and 2 atan(1/200) ≤ 1/100.
- **L3.** The partners are {0,3,4,5} for X = 1 and {1,3} for X = 0. Every exclusion box lies inside the box of a
  partner, ± 3/250, and every partner is covered.
- **L4.**
  - Each pair (X, partner) maps by a power of C3 to one of the three cases.
  - D(1/2 + √3/2) ≤ 41/2500 holds for D = 1/100 and D = 3/250.
  - Every stage-3 exclusion box lies inside the third square's box.
  - The headers agree with the stage boxes.

## Negative controls (each must fail; `make_controls.py` regenerates and runs them)

| input | result |
|---|---|
| `cert_o13b`: L + 1/100; a point dropped; one weight 1/4; an exclusion dropped; all obstacle points removed | failed (each) |
| `cert_w_o0_p13_auto`: L + 1/100; each of the 14 points dropped in turn | failed (each) |
| `cert_w_o0_p13_auto`: partner-3 exclusion dropped; only the 81 inner obstacle points kept (wall witnesses removed) | failed (each) |
| `witness.py` on `cert_o13b` without the chain restriction | 41 unproved |
| `witness.py` on `cert_o13b` with a chain angle of 1/10 instead of 3/250 | 41 unproved |
| `witness.py` on `cert_w_o1` with D = 3/100 | 65 unproved |
| `witness.py` on `cert_w_o1` with DTH = 4/100 | 1 unproved |
| `sweepwin.py` in the stage-1 window with every weight × 9/10 | failed (minimum 981/1000) |
| `lemma2.py` at (1/10, 3/20, 3/50) | fails (S1 (+,+) and S0 (+,+) gradient coefficients > 0) |

`cert_o13b` with half, or one eighth, of its obstacle points still verifies. A float Monte Carlo probe (`mc.py`) on
the one-eighth version finds minimum capture 1, so most obstacle points are redundant there.
