"""Replay saved finite incidence and conditional-motion certificates.
No LP, matching search or conflict search is used by this checker.
Geometry and row-path premise calculations are shared with the producer.
"""
from pathlib import Path
from itertools import combinations
from collections import Counter
import json
from assignment_pilot import points,groups,cases,case_data,compatible,motion_links
from assignment_conflicts import model,domains_for,replay


def hall_check(witness,adj):
    left=witness['left'];assert len(set(left))==len(left) and all(a in adj for a in left)
    neighbors=set().union(*(set(adj[a]) for a in left))
    assert neighbors==set(witness['neighbors']) and len(neighbors)<len(left)


def matching_check(pairs,domains):
    assert len(pairs)==len(domains) and {a for a,b in pairs}==set(domains)
    assert len({b for a,b in pairs})==len(pairs)
    assert all(b in domains[a] for a,b in pairs)


def main():
    root=Path('runs/bentz_assignment_20260926');data=json.loads((root/'results.json').read_text())
    rp,bp=points(0),points(1);rg,bg=groups(rp),groups(bp)
    comp={(a,b) for a in range(len(rg)) for b in range(len(bg)) if compatible(rg[a],bg[b],rp,bp)}
    assert comp=={tuple(p) for p in data['compatible_pairs']}
    stats=Counter()
    for result in data['results']:
        rc,bc=cases(rg,result['n']),cases(bg,result['n'])
        rd=[case_data(c,rg,rp) for c in rc];bd=[case_data(c,bg,bp) for c in bc]
        assert len(result['records'])==len(rc)*len(bc)
        assert {(e['red_case'],e['blue_case']) for e in result['records']}=={(a,b) for a in range(len(rc)) for b in range(len(bc))}
        for e in result['records']:
            ri,bi=e['red_case'],e['blue_case'];r,b=rc[ri],bc[bi]
            adj={a:[bb for bb in b['groups'] if (a,bb) in comp] for a in r['groups']}
            status=e['status'];stats[status]+=1
            if status=='EXACT_INCIDENCE_HALL_REJECTION':hall_check(e['hall'],adj);continue
            links,segs,missing,blocked=motion_links(rd[ri],bd[bi],rg,bg,rp,bp)
            if status=='CONDITIONAL_MOTION_EMPTY_ANCHOR':assert missing;continue
            assert not missing
            forced=set(links);restricted={a:[bb for bb in adj[a] if all((a!=x and bb!=y) or (a==x and bb==y) for x,y in forced)] for a in adj}
            if status=='CONDITIONAL_MOTION_HALL_REJECTION':hall_check(e['hall'],restricted)
            elif status=='CONDITIONAL_SIX_BOX_CHORD_REJECTION':assert max(len(set(s)) for s in segs)>=6
            elif status=='UNRESOLVED':
                matching_check(e['matching'],restricted)
                assert e['blocked_rows']==blocked and e['segments']==[sorted(set(s)) for s in segs]
                assert {tuple(v) for v in e['links']}==forced
            else:raise AssertionError(status)
    rc,bc,_,conflict=model(data)
    entrymap={(e['red_case'],e['blue_case']):e for e in data['results'][1]['records'] if e['status']=='UNRESOLVED'}
    follow=json.loads((root/'conflicts.json').read_text());assert len(follow['records'])==len(entrymap)
    assert {(e['red_case'],e['blue_case']) for e in follow['records']}==set(entrymap)
    fs=Counter()
    for e in follow['records']:
        original=entrymap[e['red_case'],e['blue_case']];domains=domains_for(original,rc,bc,comp)
        fs[e['status']]+=1
        if e['status']=='SAT':
            pairs=[tuple(v) for v in e['assignment']];matching_check(pairs,domains)
            assert not any(conflict(a,b) for a,b in combinations(pairs,2))
        elif e['status']=='UNSAT':replay(e['proof_tree'],domains,conflict)
        else:assert e['status']=='UNKNOWN' and e['proof_tree'] is None and e['assignment'] is None
    print(json.dumps(dict(status='VERIFIED_FINITE_INCIDENCE_AND_CONDITIONAL_MOTION',counts=dict(stats),conflict_counts=dict(fs))),flush=True)


if __name__=='__main__':main()
