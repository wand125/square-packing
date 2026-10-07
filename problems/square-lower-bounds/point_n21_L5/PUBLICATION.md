# A point-only computational certificate for s(21) = 5

The relocated split replay and a fresh one-command M1 run have passed all numerical stages and exact assembly. This is a computer-assisted certificate, with no claim of independent external review or proof-assistant verification.

Let s(n) be the infimum of side lengths of square containers holding n closed unit squares with arbitrary independent rotations and pairwise disjoint interiors. Boundary contact is allowed.

## Relation to prior work

Evan Daniel has already published a computer-assisted proof of s(21)=5 using a mixed measure of 7,536 weighted points and 1,872 line segments. Its certificate bundle was introduced in commit 086a129af29596892bfea89b9d81616957abcf59 (committer time 2026-09-27 19:56:22 UTC). The source examined here is https://github.com/evand/square-packing/tree/6e1223cf7ef2be4c70baaa36c0e7e7197076735a/s12/certificates/s21 . This work does not claim priority for the exact value.

Our measure uses only 4,604 weighted point entries, re-optimised on supports derived from Daniel's earlier point certificate. The covering-measure argument and centre-dilation reduction are existing methods; the contribution here is this reweighted point certificate and the accompanying rational verification route. Code developed with Codex requires human and independent review; our executions are not third-party verification.

## Certificate and theorem

The original candidate has SHA256 84a7dae793f05ff72de52ddcd3058e8518c1f84c461f94d11305adefe6137679. Its nonnegative point measure μ has support in [0,5]², mass

M = 2624862500021/125000000000,

and the certified capture threshold is q = 249987/250000. The strict gap is

21q − M = 999979/125000000000 > 0.

The computational statement is: every closed unit square Q contained in [0,5]² has μ(Q) ≥ q. It ranges over all positions and angles, including exact boundary contacts; checking a finite sample of angles would not establish this statement.

Equivalently μ/q has capture at least 1 and total 2624862500021/124993500000 < 21. The normalised point-file SHA256 is 9f631fbae420e0376ea636a232b7680e937deebe205dc035cfb9c43a3d74b456. Uniform scaling of weights is an exact algebraic corollary, not a new geometric verification.

Suppose a packing of 21 unit squares exists in [0,L]² with L<5. Scale the entire packing by λ=5/L, obtaining λ-sided squares in [0,5]² with disjoint interiors. Inside each enlarged square, take its concentric closed unit square with the same orientation. Each lies strictly inside its enlarged square, hence these 21 closed unit squares are pairwise disjoint and lie inside [0,5]². Their μ-masses sum to at least 21q, contradicting μ([0,5]²)=M<21q. Thus s(21)≥5. Twenty cells in the first four rows of a 5×5 grid and one cell in its fifth row give s(21)≤5. Therefore s(21)=5. Monotonicity and the same grid imply s(n)=5 for 22≤n≤25; these are corollaries, not separately searched certificates.

## All-pose verification and acceptance conditions

The point weights are invariant under reflection in either container midline and interchange of coordinates. These transformations preserve square containment and captured mass. Reflecting a centre into [0,5/2]² and, if needed, interchanging coordinates puts its orientation modulo π/2 in [0,π/4]. For t=tan(θ/2), this is contained in [0,5/12], since √2−1<5/12.

The checker covers [0,5/2]²×[0,1/2] with exactly 5,000 closed rational root boxes, determined by a 25×25×8 grid. The root replay leaves exactly 8,758 pending regions and uses 12 supplementary repairs. The next stage leaves exactly 38,730 regions and uses 104 supplementary repairs. Exactly 7,052 regions have lower t endpoint greater than 5/12 and can be omitted as outside the representative domain; they are not declared physically empty. All remaining 31,678 parents must be numerically replayed, with no gaps or duplicate ownership.

Every closed parent partition is checked including its faces, edges and corners. One-sided open angular exclusions retain their boundary strata. A nonempty leaf must have a replayed rational lower bound at least q. An empty leaf must have a replayed geometric or exact inequality contradiction. Weight transfer from an older candidate requires replay of the older local bound first; an old success flag is not a premise. Finite-angle runs, incomplete partitions, missing outputs, hash mismatches and nonzero worker exits are not acceptable substitutes.

The final assembly checks the exact root grid, stage-to-stage pending-region identities, all parent partitions, all required parent indices, candidate identity, nonnegativity, D4 invariance, total mass and the strict gap. A separate written review explains the local containment, LP-dual residual, transfer and near-axis lemmas. This remains a computer-assisted proof: neither the checker nor the full coverage computation is formalised in a proof assistant. The reduction from the capture bound to `minSide 21 = 5` (data, mass, D4 invariance, normalisation, angle sufficiency, scaling and the grid packing) is checked in Lean 4; see [lean/README.md](lean/README.md).

## Reproduction status

Fresh root and sieve replays in a relocated frozen tree have completed and match the original proof objects. All six Intel frontier workers exited zero, replaying all 31,678 required parents. Exact assembly completed with `PORTABLE_COMPLETE_REPLAY_LINKAGE`, including the full stage linkage and strict mass gap. The one-command runner then completed from scratch on M1 with two workers in 8,577.313 seconds. Root, sieve and both frontier processes exited zero, followed by `FRESH_ALL_DOMAIN_REPLAY_VERIFIED`. Its result, complete linkage and collection checks are recorded under `acceptance/`.

The distribution contains 75,130 input files. Its gzip archive is 455,327,325 bytes in 14 parts. A complete extraction verified every file against manifest SHA256 `b0d1dcb1bdd0d93a3723df5c8a034828cd686c647599604fad5b16bc676eb098`. This archive was rebuilt on 2026-10-04 from the byte-preserving distribution (manifest `bb2883c5d05e3073011267f95cccd3301c2f97dd4c1e1d64fc4c6e46c8ec9c6c`): 53 JSON records had absolute paths of the original machine made relative to the bundle root (with the hashes that other records embed for them updated), and one unused source had its non-English strings translated. No mathematical content changed; `path-relativization-map.json` lists every edited file with its hash before and after. Packaging does not itself perform a mathematical replay. The M1 numerical run used the original frozen bundle; all 75,130 actual source reads were checked against the trimmed distribution manifest and bytes. A separate extraction checked the compressed distribution. A second full numerical run starting from the compressed parts was not timed; the reader can perform it with the provided commands.

## Mathematical appendix and checker source

[PROOF-LEMMAS.md](PROOF-LEMMAS.md) gives the local containment, physical-wall, exact-dual-residual, conflict, branch, weight-transfer, fixed-angle, near-axis and closed-partition arguments. `lemma-code-map.json` pins the 27 source files in the frozen tree that the checker executes (the appendix-named modules plus their helper modules). The appendix is a written mathematical review, not a proof-assistant certificate.

First run `python unpack_bundle.py` to reconstruct and hash-check the bundle. Readable copies of all bundled Python sources are in `verifier-source/`. Then the full command is `python verify_portable.py --workers 2 --out /tmp/n21-proof-replay`. It must use a new output directory and must finish with all numerical stages exiting zero and `FRESH_ALL_DOMAIN_REPLAY_VERIFIED` after complete assembly. The completed M1 run and measured time are recorded above. Python 3.12.2 with NumPy 2.5.3 and SciPy 1.18.1 is the tested local environment; `requirements-tested.txt` records these package versions. These are tested versions, not claims about minimum versions.

The worker count is configurable; reducing it changes scheduling, not the required set of 31,678 parents. Running only representative parents is a diagnostic and cannot return the full runner's accepted status.

## Exact support provenance

The ordered 4,604 coordinate entries are exactly those of Daniel's earlier `s21_lower_4.9950.txt`, scaled by `1001/1000` from side `5000/1001` to side `5`. Their order also matches; the weights have been re-optimised. `support-provenance.json` records both file hashes and this exact rational comparison. Scaling those coordinates alone does **not** transfer the old coverage guarantee to side 5: the new all-pose proof must be replayed. Daniel's MIT licence is retained in `UPSTREAM-LICENSE.txt`.

The 4,604 coordinates are distinct; 4,520 have positive weight and 84 retained entries have zero weight. Zero entries remain to preserve the point indices used by the proof trees.

The three point files are included under `certificates/`; see [FORMAT.md](FORMAT.md).
`python inspect_certificate.py` checks their exact data identities, normalization,
D4 invariance and mass gap without running the geometric proof. Its success is
not a replacement for the complete numerical replay.
