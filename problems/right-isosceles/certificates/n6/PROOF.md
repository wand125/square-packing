# Six unit squares in a right isosceles triangle

**Theorem (computer-assisted).** The smallest right isosceles triangle containing six
non-overlapping unit squares has legs of length 4. (Five squares need the same size, s(5) = s(6) = 4;
this certificate proves only s(6) ≥ 4.)

Upper bound: the axis-parallel staircase with rows 3, 2, 1 in T_4 = conv{(0,0), (4,0), (0,4)}.

## Certificate

`n6_cert.json`: seven points, total weight 5 < 6, invariant under (x, y) ↦ (y, x):

| point | weight |
|---|---|
| (1/2, 3/2), (3/2, 1/2) | 1/2 each |
| (3/4, 1), (1, 3/4) | 1/2 each |
| (3/4, 2), (2, 3/4) | 1 each |
| (3/2, 3/2) | 1 |

Chord pairs (all pairs at distance exactly 1, `../../tools/add_pairs.py`): (1/2,3/2)–(3/2,3/2),
(3/2,1/2)–(3/2,3/2), (3/4,1)–(3/4,2), (1,3/4)–(2,3/4). Without them the run leaves 5,677
uncertified boxes at depth 22, all near centre (1, 1.3) at small angles, where the square switches
between (1/2,3/2) and (3/2,3/2) across a tilted surface.

**Lemma.** Every closed unit square Q ⊆ T_4 contains points of total weight ≥ 1.

*Proof.* Two independent exact checkers (Q(√2) arithmetic):
- checker 1 (`python3 checker/check.py certificates/n6/n6_cert.json --n 6 --max-depth 22`): symmetry D1, 1,122 nodes, 0 uncertified, maximum depth 13, 2.8 s (`check_record.json`).
- checker 2 (`../../checker2/sweep_q2.py`, all angles, no symmetry, no Lemma P): verified, minimum capture 1, 26 s (`../../checker2/runs/n6.json`).

The theorem follows by centre scaling (`../../README.md`, "The method"): total 5 < 6.

## Sanity checks (not part of the proof)

- Negative control: L = 4 + 1/100 gives 53 uncertified boxes at depth 22; L = 4 + 1/10 gives 7,611.
- Exact random probe: 20,000 rational poses, minimum capture 1.
