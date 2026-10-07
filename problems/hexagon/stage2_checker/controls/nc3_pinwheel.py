"""Negative control NC3 (not used for the proof).

At side 1.01 v, the pinwheel scaled by 1.01 from the centre is a genuine packing of three pairwise disjoint
closed unit squares.  So no sound "outside" or "overlap" test may fire on a node that contains it.  This
script builds nodes of several half-widths around that packing (each square's box centred at its pose,
all three box widths equal) and checks that the rigorous outside and overlap tests of bb_rig_nc.py never
fire on them.
"""
import itertools, math
import numpy as np
from bb_rig_nc import setup, outside_rig, overlap_rig, dn_f, up_f

K = 1.01


def main():
    C = setup()
    H0, H1 = dn_f(C["H0"] * K), up_f(C["H1"] * K)
    poses = [(K * C["Pw"][i, 0], K * C["Pw"][i, 1], C["Pw"][i, 2] % (math.pi / 2)) for i in range(3)]
    tmp = np.empty((4, 4)); T1 = np.empty((4, 4)); T2 = np.empty((4, 4))
    fired = 0; nodes = 0
    for w in (1e-4, 3e-4, 1e-3, 2e-3, 4e-3):
        for shift in itertools.product((-0.5, 0.0, 0.5), repeat=3):   # the packing is off-centre in the box
            boxes = [np.array([x - w + shift[0] * w, x + w + shift[0] * w, y - w + shift[1] * w, y + w + shift[1] * w,
                               t - w + shift[2] * w, t + w + shift[2] * w]) for x, y, t in poses]
            nodes += 1
            for b in boxes:
                if outside_rig(b, H0, H1, C["NSiv"], C["PI0"], C["PI1"], tmp):
                    fired += 1
            for a, b in itertools.combinations(boxes, 2):
                if overlap_rig(a, b, C["PI0"], C["PI1"], T1, T2):
                    fired += 1
    print(f"side scale {K}: {nodes} nodes around the scaled pinwheel, half-widths 1e-4..4e-3; "
          f"outside/overlap fired {fired} times -> {'OK (never fired)' if fired == 0 else 'UNSOUND'}")


if __name__ == "__main__":
    main()
