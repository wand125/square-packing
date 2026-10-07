# Second check for n = 6 (unit squares in an equilateral triangle)

An independent re-check of the computer parts of the proof of s△(6) = 2 + 4/√3
(`../../certificates/n6/PROOF.md`).

| item | tool | what is checked |
|---|---|---|
| 2-a lemma (M) | `lemma2.py` | S derived from the LEMMA definitions with sympy; S ≤ −c(\|φ0\|+\|φ1\|+\|φ3\|) on the hypothesis box, 2 cases × 8 orthants |
| 2-b lemma hypotheses | `chain2.py` (H1–H4) | tilts, corner shifts, t ∈ [τ, 1−τ], P on the inner side of the outer edge, Step 2 separation claims |
| 2-c–2-f certificates | `cellgrid.py` (+ `sweepwin.py` for one window of stage 1) | every admissible, non-exempt pose captures ≥ 1; total < n; D3 invariance |
| 2-g obstacle points | `witness.py` | each obstacle point lies in the open obstacle square for every admissible pose of its box |
| 2-h stage links | `chain2.py` (L1–L4) | C3 symmetry of the pinwheel, stage-1 boxes, partners, exclusion boxes inside the claimed boxes, box growth under rotation |

## Methods

**cellgrid.py.** u = tan(t/2) is cut into intervals I = [ua, ub] whose grid contains every exclusion u-endpoint.
At the rational midpoint the square axes are fixed. Each capture square and each obstacle square (in the space
of centres) is shrunk by r·h with r ≥ √2/2 and h = ub − ua ≥ |t − t_mid|, so that membership holds for every
angle of I. The admissible region is enlarged by r·h on each side (the support function of the square is
(√2/2)-Lipschitz in t). At the fixed frame all these squares are axis-parallel, so their edges form a grid. On
each open grid cell the weight and the obstacle cover are constant, and on the closed cell they are larger. A
cell that meets the enlarged admissible triangle must then have weight ≥ 1, or lie in an obstacle square, or
have its part inside the triangle within an exclusion box active on all of I. Otherwise I is halved. Floats are
exact dyadic rationals. Coordinates are padded inwards by 1e-12, which is far above the rounding error. Near-1
weights are recomputed exactly.

This fails only where a contact is tight at both a wall and a capture edge at one angle. In the n = 6 files this
happens only for stage 1 at t = 0, along the bottom wall. That band is passed with `--window` and handed to
`sweepwin.py`.

**sweepwin.py.** This is the exact angular sweep of `../sweep.py` (critical angles from the pair and triple
determinants, one rational sample per gap, closure by upper semicontinuity), restricted to a window of centres
and to u ∈ [0, E]. Lines whose sign is constant on the window for all of [0, E] are dropped, using a
coefficient bound on each corner polynomial. Event polynomials with no root in (0, E] are dropped by the same
bound. Exclusion boxes act as capturers of weight 10.

**witness.py.** Interval branch and bound over the pose box (c_x, c_y, t) of each obstacle square. A sub-box is
closed when the point is surely in the open square, or the pose is surely not admissible. For the chain
witnesses (case 1,3:0) a sub-box can also be closed when d_R(P) < cos(DTH3) surely. The witness constructions
(inner grid, wall rule, chain rule) are not used.

**lemma2.py.** The φ3 part is T3 = 1 − cos φ3 − τ\|sin φ3\| ≤ −(τ sin Φ/Φ − Φ/2)\|φ3\|. The rest is affine in
(a, b), and its maximum over the (a, b) box is an explicit function G(φ0, φ1). A branch and bound proves
G + c(\|φ0\|+\|φ1\|) < 0 by direct interval evaluation away from the origin. On the origin box [0, r]² it uses a
first-order bound with interval second derivatives.

## Run

```sh
pip install numpy gmpy2 sympy mpmath
./run_all.sh 6                 # all checks, results in out/ (about 10 minutes on 6 cores)
python make_controls.py        # negative controls; each must fail
```

The certificates are read from `../../certificates/n6/` (set `N6_CERTS` to use another copy).

## Results

See `RESULTS.md`.

## Independence

- Written from the first checker's specification (`../../checker/SPEC.md`, including the section "Exclusion
  boxes and obstacle points"), the proof notes (`certificates/n6/PROOF.md`, `certificates/n6/triple/LEMMA.md`)
  and the certificate files only.
- The first checker's code (`check.py`) was not opened. Neither were the lemma scripts (`lemma_check.py`,
  `derive2.py`, `validity_box.py`).
- Of the witness generators (`stage_inputs.py`, `wall_witness2.py`, `chain_witness.py`), only the statements in
  their header docstrings were read. `witness.py` proves the resulting claim directly and uses none of their
  constructions.
- The author had read an earlier draft of the stage outline that accompanied the generators. That draft states the
  same stage structure as `PROOF.md`.
- Shared inputs: the certificates, the pinwheel packing `n6_packing.json`, and the claims in `SPEC.md`,
  `PROOF.md` and `LEMMA.md`.
- Shared code: `../q3.py` and `../sweep.py`, both part of this second checker.
- Tools: Python, numpy, gmpy2 (exact rationals), sympy (symbolic derivation of S), mpmath (interval arithmetic).
