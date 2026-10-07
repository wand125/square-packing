# Unit squares in a regular hexagon: the optimal packing of 3 squares

Let s(n) be the smallest side v of a regular hexagon that contains n non-overlapping unit squares
(any positions, any angles).

| n | s(n) | ≈ | optimal packing (upper bound) | lower bound |
|---|---|---|---|---|
| 3 | (1 + √3)/2 | 1.3660254 | the pinwheel (Morandi): three squares, each with a corner at every other vertex of the hexagon, each touching the next | two-stage computer-assisted proof (below) |

The packing is the one listed in Erich Friedman's Packing Center, "Squares in Hexagons"
(https://erich-friedman.github.io/packing/squinhex/). The proof here shows that it is optimal.

**Status.** The result is a computer-assisted proof. Each of its two computational stages has been
checked by two independent implementations. It has not been peer reviewed, and it has not been
formalised in Lean.

## Novelty

We are not aware of a previous proof that s(3) = (1 + √3)/2. If you know of one, please open an issue.

## Why this case is harder than it looks

The pinwheel is not rigid to first order. Each square can rotate about its corner at the vertex; to
first order no contact opens or closes, and the overlap is only of order t² (about −1.18 t² per
contact). A pure point-weight certificate (every square captures weight ≥ 1, total weight < 3)
cannot exclude this flex. So the proof has two stages and a local lemma.

## The proof (`n3/PROOF.md`)

0. **Reduction.** If three unit squares with disjoint interiors fit in a hexagon of side L < v, then
   scaling the centres away from the hexagon's centre by v/L gives three pairwise disjoint *closed*
   unit squares in H_v. So it suffices to show that H_v contains no such triple.
1. **Stage 1: a weighted point set with excused boxes** (`n3/stage1_cert.json`).
   - 630 points of total weight 749319/250000 < 3, and 742 excused boxes in pose space.
   - Their union under D6 is a tube around the flex curve.
   - Claim: every closed unit square in H_v whose pose is not excused captures weight ≥ 1.
   - Hence, in any triple, some square has its pose (up to D6) in some excused box E_k.
2. **Local lemma** (`n3/local_lemma/`). Near the pinwheel (tilts within 0.08 rad, corners within 0.05 of
   the vertices) there is no triple of pairwise disjoint closed unit squares in H_v.
   - The proof is analytic.
   - An exact identity is checked in sympy, and a radius condition in exact rational arithmetic.
   - `LOCAL_LEMMA_SHORT.md` is a one-page version.
3. **Stage 2: branch and bound for each excused box.** For each of the 742 boxes E_k: no triple with
   square 1's pose in E_k. Squares 2 and 3 range over all poses. The search uses interval arithmetic
   rounded outward, and the local lemma closes the region near the pinwheel.

## Two independent implementations of each stage

| stage | implementation 1 | implementation 2 |
|---|---|---|
| 1 | `stage1_checker/`: exact Q(√3) subdivision with Bernstein bounds; verified, 5,768 nodes | `stage1_checker2/`: exact angular line-arrangement sweep, written from `n3/SPEC_stage1.md` only; verified, 58,894 boxes |
| 2 | `stage2_checker/`: Python + numba interval branch and bound; 742/742 proved, 0 leaves, 5.75·10^9 nodes | `stage2_checker2/`: Rust interval branch and bound, written from `n3/SPEC_stage2.md` and the local lemma only; 742/742 proved, 0 leaves, 4.37·10^9 nodes |

The second implementation of each stage was written without reading the first one's code.

## Controls

- **Stage 1.** An admissible pose inside an excused box captures only 495031/500000 < 1
  (`stage1_checker2/witness_excused.json`). So the excused boxes are needed.
- **Stage 2.**
  - Without the local lemma, the box containing the pinwheel square is not proved. The leaves left
    lie close to the pinwheel.
  - At side 1.01·v the scaled pinwheel is a genuine packing. Neither implementation's outside or
    overlap test discards it (`stage2_checker/controls/`, `stage2_checker2/README.md`).
- **Soundness fuzz test** of implementation 1's pruning tests: 20,000 random nodes, 0 violations
  (`stage2_checker/results/fuzz_rig.out`).

## Reproducing

| what | command (from the directory named) | needs | time |
|---|---|---|---|
| checksums | `sha256sum -c SHA256SUMS` (or `shasum -a 256 -c`) from the root | | seconds |
| local lemma | `python ll_exact.py`, `python ll_radius.py` in `n3/local_lemma/` (recorded outputs: `*.out`) | sympy, numpy, scipy | seconds for the exact checks; the float search in `ll_radius.py` about 20 min |
| stage 1, impl. 1 | `python check_hex.py ../n3/stage1_cert.json --n 3 --root 8 --max-depth 32 --u-scale 16 --jobs 4` in `stage1_checker/` | Python 3.10+ only | about 7 min with 4 processes |
| stage 1, impl. 2 | `python hexcheck.py ../n3/stage1_cert.json --jobs 14 --grid 8` in `stage1_checker2/` | gmpy2 | about 2 h 50 min with 14 processes |
| stage 2, impl. 1 | `python bb_rig_batch.py --workers 16 --boxes 0-741` in `stage2_checker/` | numpy, numba | about 54 core-hours |
| stage 2, impl. 2 | `cargo build --release`, then `./target/release/hexs2 --cert ../n3/stage1_cert.json --threads 16 --max-depth 80` in `stage2_checker2/` | Rust 1.85, no crates | about 6 core-hours |

A single stage-2 box is a quick test: `python bb_rig.py --box 2` (about 1.5 minutes), or
`hexs2 --k 2 --max-depth 80` (about 30 s).

## Layout

- `n3/`: the proof (`PROOF.md`), the two specifications, the stage-1 certificate and the local lemma.
- `stage1_checker/`, `stage1_checker2/`: the two stage-1 checkers and their recorded runs.
- `stage2_checker/`, `stage2_checker2/`: the two stage-2 programs, their results and controls.
- `SHA256SUMS`: checksums of the certificate and all recorded results.

## Not done yet

- Peer review and a Lean formalisation.
- Other n.

## Author

Hiroaki Hosono (GitHub: wand125).

## Licence

MIT (see `LICENSE`). The packing in the table is from Erich Friedman's Packing Center.
