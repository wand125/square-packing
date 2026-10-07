# Stage 2, implementation 1: rigorous branch and bound (Python + numba)

`bb_rig.py` proves the stage-2 claim of `../n3/SPEC_stage2.md` for one excused box E_k: no three pairwise
disjoint closed unit squares in H_v have square 1's pose in E_k. The method and its soundness are in
section 5 of `../n3/PROOF.md`. In brief:

- a node is a triple of pose boxes (centre and angle);
- it is discarded by an outside test, an overlap test, the inequalities of the local lemma or the
  lemma's neighbourhood;
- otherwise the largest box is halved;
- the run is a proof for E_k if and only if it ends with 0 leaves and an empty stack.

All arithmetic is interval arithmetic rounded outward by one ulp; cos, sin and atan are widened by
1e-15. The excused boxes are read from the exact rationals of `../n3/stage1_cert.json`.

## Running

Python 3.10+, numpy and numba (tested with numpy 1.26 and numba 0.67).

```bash
python bb_rig.py --box 86 --eps 0.004                     # one box; box 86 contains the pinwheel square
python bb_rig_batch.py --workers 16 --boxes 0-741 --out rig_results.jsonl   # all boxes; resumable
python fuzz_rig.py                                         # soundness fuzz test, about 2 minutes
```

## Result

`results/rig_results.jsonl` (one line per box) and `results/rig_batch.log`:

- all 742 boxes PROVED with ε = 0.004;
- every box ends with 0 leaves and an empty stack;
- 5.75·10^9 nodes in total; the largest box needed 1.6·10^7 nodes;
- 54.3 core-hours in total (per box: median 201 s, maximum 580 s);
- run on a 16-vCPU x86-64 Linux machine (c2d-highcpu-16).

Box 86 gives identical node counts on arm64 macOS and on x86-64 Linux.

`results/fuzz_rig.out` is a recorded run of the fuzz test. On 20,000 random nodes around the
pinwheel, its flex and its D6 images, it checks each pruning test's own claim on sample poses. It
found 0 violations.

## Controls

`controls/` holds a copy of `bb_rig.py` with two options that are not used for the proof
(`--side-scale`, `--no-lemma`) and the recorded runs. See `controls/README.md`.

## Note

The published `bb_rig.py` differs from the program used for the recorded run only in one comment
line, which pointed to an internal design note.
