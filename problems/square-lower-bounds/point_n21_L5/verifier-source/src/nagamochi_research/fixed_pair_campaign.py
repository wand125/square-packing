"""Fixed-epsilon pair campaign; only replayed exclusions enter the graph."""
import argparse,json,os,time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from direct_fixed_epsilon import run,verify
from normalized_axis_cells import geometry
from review_direct_pairs import count_sets
from joint_angle_lp import rotation


def check_capacity(base,pieces):
    cfg=base['config'];R=F(cfg['rot_inner']);c,s=rotation(F(cfg['t']))
    assert base['necessary_outside_axis_band']==base['n']-(cfg['k']-1)**2>0
    assert all(max(a*x+b*y for x,y in p)-min(a*x+b*y for x,y in p)<R
               for p in pieces for a,b in ((c,s),(-s,c)))


def verify_graph(source,out):
    base=json.loads(source.read_text());cfg=base['config'];q=json.loads((out/'summary.json').read_text())
    assert q['config']==cfg and 0<F(q['fixed_epsilon'])<=F(cfg['eps_max'])
    missing=q.get('missing',[]);assert missing==sorted(set(missing))
    cells,pieces=geometry(cfg,missing);check_capacity(base,pieces)
    assert q['regions']==len(pieces) and q['target']==base['n']-len(cells)
    edges=q['edges'];assert len({tuple(e) for e in edges})==len(edges)
    for chosen in edges:
        assert len(chosen)==2
        p=json.loads((out/('pair-%d-%d.json'%tuple(chosen))).read_text())
        assert p['config']==cfg and p['fixed_epsilon']==q['fixed_epsilon'] and p['missing']==missing and p['chosen']==chosen
        assert verify(p)
    count=count_sets(len(pieces),edges,q['target']);assert count==q['remaining_sets']
    return dict(verified_edges=len(edges),remaining_sets=count,conditional_excluded=count==0)


def campaign(source,out,nodes=100,epsilon=None,missing=None):
    base=json.loads(source.read_text());cfg=base['config'];e=str(F(epsilon or cfg['eps_max']))
    assert 0<F(e)<=F(cfg['eps_max'])
    missing=[] if missing is None else list(missing);assert missing==sorted(set(missing))
    cells,pieces=geometry(cfg,missing);n=len(pieces);target=base['n']-len(cells)
    check_capacity(base,pieces)
    out.mkdir(parents=True,exist_ok=True);edges=[];cases=[];start=time.monotonic()
    summary=dict(status='RUNNING',worker_pid=os.getpid(),config=cfg,fixed_epsilon=e,
                 regions=n,target=target,missing=missing,cases=cases,edges=edges,
                 limitation='Fixed epsilon, specified occupied axis cells and one specified rotor band only.')
    def save():
        summary.update(seconds=time.monotonic()-start,remaining_sets=count_sets(n,edges,target))
        tmp=out/'summary.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(out/'summary.json')
    save()
    for chosen in combinations(range(n),2):
        path=out/('pair-%d-%d.json'%chosen)
        if path.exists():
            q=json.loads(path.read_text())
            assert q['config']==cfg and q['fixed_epsilon']==e and q['missing']==missing and q['chosen']==list(chosen)
            assert verify(q)==q['verified']
        else:
            q=run(cfg,missing,chosen,e,nodes)
            tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2));tmp.replace(path)
        if q['verified']:edges.append(list(chosen))
        cases.append(dict(chosen=list(chosen),status=q['status'],verified=q['verified'],nodes=q['nodes']))
        if len(cases)%20==0:
            save();print(len(cases),len(edges),summary['remaining_sets'],flush=True)
            if summary['remaining_sets']==0:break
    save();summary['status']='CONDITIONAL_GRAPH_EXCLUDED' if summary['remaining_sets']==0 else 'FIXED_PAIR_PILOT_FINISHED'
    save();print(summary['status'],len(cases),len(edges),summary['remaining_sets'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--nodes',type=int,default=100);p.add_argument('--epsilon')
    p.add_argument('--missing',type=int,nargs='*',default=[])
    a=p.parse_args();assert a.nodes>0
    campaign(a.source,a.out,a.nodes,a.epsilon,a.missing)
