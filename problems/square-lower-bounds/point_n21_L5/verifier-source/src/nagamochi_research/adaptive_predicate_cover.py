"""Exact local coverage: physical enclosure, PL45, subdivision, PL46/47.

Subdivision budgets may leave unproved leaves. The caller must replay the full
original-box partition before treating a parent as certified.
"""
from fractions import Fraction as F
from time import monotonic
from physical_pose_enclosure import enclose
from predicate_lp_capture import certify
from predicate_conflict import strengthen
from predicate_branch import replay_model, solve_tree, cut_callbacks
from predicate_partition import replay_capture_record


def cover(points, L, box, *, max_depth=4, max_cuts=12, branch_depth=6,
          branch_nodes=127, physical_cuts=0):
    if max_depth < 0 or max_cuts < 0 or branch_depth < 0 or branch_nodes < 0 or physical_cuts < 0:
        raise ValueError('Negative search budget')
    queue = [(list(map(str, box)), 0, 'r')]
    leaves, events = [], []
    while queue:
        original, depth, label = queue.pop()
        start = monotonic()
        enclosure = enclose(L, original)
        outer = enclosure['enclosing_box']
        proof, method, passed = None, 'EMPTY', True
        if outer is not None:
            proof = certify(points, outer)
            proof['box'] = outer
            method, passed = 'PL45', F(proof['lower']) >= 1
        if not passed and depth < max_depth:
            axes = [4, 0, 2]
            axes = axes[depth % 3:] + axes[:depth % 3]
            # Split the ORIGINAL domain. Enclosures may overlap or leave gaps
            # outside the physical set and must not replace partition leaves.
            choice = next(((k, (F(outer[k])+F(outer[k+1]))/2) for k in axes
                           if F(original[k]) < (F(outer[k])+F(outer[k+1]))/2 < F(original[k+1])), None)
            if choice is not None:
                k, mid = choice
                for side in (1, 0):
                    child = original.copy()
                    child[k+1 if side == 0 else k] = str(mid)
                    queue.append((child, depth+1, label+str(side)))
                events.append(dict(label=label, depth=depth, method='SPLIT',
                                   lower=proof['lower'], seconds=monotonic()-start))
                continue
        has_model = bool(proof and proof.get('cost'))
        if not passed and has_model and max_cuts:
            proof = strengthen(points, proof, outer, max_cuts)
            proof['box'] = outer
            method, passed = 'PL46', F(proof['lower']) >= 1
        physical_candidate = None
        if not passed and has_model and physical_cuts:
            from physical_predicate_conflict import strengthen as physical_strengthen, replay as physical_replay
            physical_candidate = physical_strengthen(points, proof, outer, L, physical_cuts)
            if physical_replay(points, physical_candidate, L)['certified_unit_capture']:
                proof, method, passed = physical_candidate, 'PL48', True
        if not passed and has_model and branch_nodes:
            cost, rows, baseline = replay_model(points, proof)
            propose, verify = cut_callbacks(points, proof)
            tree = solve_tree(cost, rows, baseline, max_depth=branch_depth,
                              max_nodes=branch_nodes, cut_proposer=propose,
                              cut_verifier=verify)
            proof = dict(tree, base=proof, box=outer)
            method = 'PL47'
            passed = tree['replay']['certified_unit_capture']
        if not passed and physical_candidate is not None:
            proof, method = physical_candidate, 'PL48'
        if proof is not None and proof.get('proof_type') == 'PHYSICAL_SIGNED_CONFLICTS':
            from physical_predicate_conflict import replay as physical_replay
            replay = physical_replay(points, proof, L)
        else:
            replay = replay_capture_record(points, proof) if proof is not None else None
        leaves.append(dict(label=label, depth=depth, enclosure=enclosure,
                           proof=proof, method=method))
        events.append(dict(label=label, depth=depth, method=method,
                           lower=replay['lower'] if replay else None,
                           certified=replay['certified_unit_capture'] if replay else True,
                           seconds=monotonic()-start))
    return dict(records=leaves, events=events, general_coverage_verified=False)
