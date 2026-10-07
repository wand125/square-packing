"""PL57: recover leaf margins only after exact replay of the source tree."""
from fractions import Fraction as F
from predicate_branch import replay_tree


def _minimum_replayed_leaf(node):
    kind=node['kind']
    if kind in ('BOUND','OPEN_BOUND'):return F(node['lower'])
    if kind=='EMPTY':return None
    if kind=='CUT':return _minimum_replayed_leaf(node['child'])
    if kind=='BRANCH':
        values=[_minimum_replayed_leaf(c) for c in node['children'].values()]
        values=[v for v in values if v is not None]
        return min(values) if values else None
    # An unresolved branch is retained; nonnegative capture only.
    if kind in ('OPEN','OPEN_EMPTY_UNVERIFIED'):return F(0)
    raise ValueError('Unknown replayed node kind')


def replay_tree_margin(cost,rows,baseline,target,tree,*,cut_verifier=None):
    if F(baseline)<0 or any(F(c)<0 for c in cost):raise ValueError('Need nonnegative capture model')
    checked=replay_tree(cost,rows,F(baseline),F(target),tree,cut_verifier=cut_verifier)
    q=_minimum_replayed_leaf(tree)
    old=F(target) if checked['certified_unit_capture'] else F(0)
    return dict(checked,lower=str(max(old,q)) if q is not None else str(old),vacuous=q is None)


def replay_capture_margin(points,record,*,L=None):
    if any(F(p[2])<0 for p in points):raise ValueError('Negative mass')
    kind=record.get('proof_type')
    if kind=='PHYSICAL_PREDICATE_TREE':
        if L is None:raise ValueError('Physical context required')
        from physical_predicate_branch import replay
        checked=replay(points,record,L)
    elif kind=='PHYSICAL_SIGNED_CONFLICTS':
        if L is None:raise ValueError('Physical context required')
        from physical_predicate_conflict import replay
        checked=replay(points,record,L)
    else:
        from predicate_partition import replay_capture_record
        checked=replay_capture_record(points,record)
    old=F(checked['lower']);q=_minimum_replayed_leaf(record['tree']) if 'tree' in record else old
    value=max(old,q) if q is not None else old
    return dict(checked,source_lower=str(old),lower=str(value),margin_recovered=value>old,
                certified_unit_capture=value>=1,vacuous=q is None,
                source_numerically_replayed=True,general_coverage_verified=False)
