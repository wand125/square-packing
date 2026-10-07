# Negative controls for stage 2 (not used for the proof)

`bb_rig_nc.py` is a copy of `../bb_rig.py` with two extra options:

- `--side-scale K` enlarges the hexagon (containment and the domain of squares 2 and 3);
- `--no-lemma` disables the two lemma tests.

It also records the first 100 leaves in `nc_leaves_box{K}_s{scale}_lem{0|1}.npy`.

| control | command | recorded result |
|---|---|---|
| NC1: side v, no lemma | `python bb_rig_nc.py --box 86 --no-lemma --max-nodes 1e7` | not proved: 293,399 leaves after 10^7 nodes (`records/nc1_side1.00_nolemma.out`) |
| NC1, where the leaves are | `python leafdist.py records/nc_leaves_box86_s1.0_lem0.npy` | the first 100 leaves lie within max-norm distance 0.033–0.041 of the pinwheel (`records/leafdist.out`) |
| NC3: side 1.01·v, scaled pinwheel | `python nc3_pinwheel.py` | the outside and overlap tests never fire on 135 nodes of half-width 10^-4 to 4·10^-3 around the genuine packing (`records/nc3_pinwheel.out`) |
| NC3: side 1.01·v, no lemma | `python bb_rig_nc.py --box 86 --no-lemma --side-scale 1.01 --max-nodes 1e7` | not proved: 65,443 leaves after 10^7 nodes (`records/nc3_side1.01_nolemma.out`) |

What the controls show:

- Without the lemma, the branch and bound cannot close the region near the pinwheel (NC1).
- The outside and overlap tests do not discard a genuine packing (NC3).
