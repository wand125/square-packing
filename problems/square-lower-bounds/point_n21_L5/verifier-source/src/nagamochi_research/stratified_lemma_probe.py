"""Compare globally low starts with angle-stratified local counterexample starts.

This is a finite diagnostic, never a complete angle or centre certificate.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from repair_lemma_measure import np, poses, coefficients, expand_primitives, expand
from local_exchange_lemma_measure import separate


def angle_starts(scan, values, bins=24, per_bin=4):
    if bins < 1 or per_bin < 1:
        raise ValueError('Positive bin counts required')
    groups = [[] for _ in range(bins)]
    for i, pose in enumerate(scan):
        t = F(pose[2])
        if not -F(414, 1000) <= t <= F(414, 1000):
            raise ValueError('Outside finite probe angle domain')
        k = min(bins - 1, int((t + F(414, 1000)) * bins / F(828, 1000)))
        groups[k].append(i)
    selected = [i for g in groups for i in sorted(g, key=lambda j: values[j])[:per_bin]]
    return selected, [len(g) for g in groups]


def run(prior, out, seed=9277300, count=32768, bins=24, per_bin=4, mode='points_rectangles'):
    if out.exists():
        raise FileExistsError(out)
    candidate = prior / 'candidate.json'
    if not candidate.exists():
        candidate = prior / f'{mode}-candidate.json'
    model = expand(json.loads(candidate.read_text()))
    state = prior / 'state.npz'
    if not state.exists():
        state = prior / f'{mode}-state.npz'
    z = np.load(state)
    ex = expand_primitives(json.loads(str(z['primitives_json'])), model[0])
    scan = poses(model[0], count, seed)
    values = np.concatenate([coefficients(scan[i:i+2048], model[1], ex, model[0]) @ z['weights']
                             for i in range(0, count, 2048)])
    ids, occupancy = angle_starts(scan, values, bins, per_bin)
    selected = [scan[i] for i in ids]
    stratified = separate(model, ex, z['weights'], selected, values[ids], starts=len(ids))
    global_rows = separate(model, ex, z['weights'], scan, values, starts=len(ids))
    rows = stratified + global_rows
    def summary(rs):
        return dict(starts=len(rs), exact_minimum=str(min(F(r['score']) for r in rs)),
                    below_one=sum(F(r['score']) < 1 for r in rs))
    report = dict(status='FINITE_ANGLE_STRATIFIED_PROBE',
                  candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  seed=seed, count=count, bins=bins, per_bin=per_bin, occupancy=occupancy,
                  numerical_scan_minimum=float(min(values)),
                  stratified=summary(stratified), global_low=summary(global_rows),
                  selected_indices=ids, local_witnesses=rows,
                  scope='Finite samples in t=[-.414,.414]; both methods use the same pool and number of starts.',
                  general_packing_exclusion=False)
    out.write_text(json.dumps(report, indent=2))
    print({k:v for k,v in report.items() if k not in ('local_witnesses','selected_indices')}, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('prior', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('--seed', type=int, default=9277300)
    p.add_argument('--mode', default='points_rectangles')
    a = p.parse_args()
    run(a.prior, a.out, seed=a.seed, mode=a.mode)
