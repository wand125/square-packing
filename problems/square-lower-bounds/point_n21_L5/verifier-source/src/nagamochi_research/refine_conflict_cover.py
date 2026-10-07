"""Heuristic clique generation, followed by an exact finite-pose cover audit."""
import argparse,json,time
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def run(source,out,rounds):
    out.mkdir(parents=True,exist_ok=False)
    graph=[int(x,16) for x in json.loads((source/'conflicts.json').read_text())]
    cliques=set(tuple(c) for c in json.loads((source/'cliques.json').read_text()))
    n=len(graph);history=[]
    for step in range(rounds+1):
        cuts=sorted(cliques);rows=[];cols=[]
        for j,c in enumerate(cuts):
            for i in c:rows.append(i);cols.append(j)
        a=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,len(cuts))).tocsc()
        fit=linprog(np.ones(len(cuts)),A_ub=-a,b_ub=-np.ones(n),bounds=(0,None),method='highs',options={'time_limit':45})
        assert fit.success,fit.message
        nums=[max(0,int(np.ceil(x*10**9))) for x in fit.x];coverage=[0]*n
        for c,w in zip(cuts,nums):
            for i in c:coverage[i]+=w
            # Independent audit of every used graph-clique certificate.
            if w:
                mask=sum(1<<i for i in c)
                assert all((mask ^ (1<<i)) & ~graph[i] == 0 for i in c)
        den=min(coverage);assert den>0
        bound=F(sum(nums),den)
        record=dict(operation='clique_cover',status='RUNNING',iteration=step,cliques=len(cuts),finite_upper=str(bound),upper_float=float(bound),updated_epoch=time.time())
        history.append(record);print(json.dumps(record),flush=True)
        (out/'progress.json').write_text(json.dumps(dict(records=history),indent=2))
        (out/'cover.json').write_text(json.dumps(dict(cliques=cuts,numerators=nums,denominator=den,finite_upper=str(bound))))
        if step==rounds:break
        dual=np.maximum(0,-fit.ineqlin.marginals);order=np.argsort(-dual,kind='stable').tolist();added=0
        for seed in range(n):
            c=[seed];remaining=graph[seed]
            for v in order:
                if remaining & (1<<v):c.append(v);remaining &= graph[v]
                if not remaining:break
            key=tuple(sorted(c))
            if key not in cliques and sum(dual[i] for i in c)>1+1e-8:
                cliques.add(key);added+=1
        if not added:break
    history.append(dict(operation='clique_cover',status='STOPPED_FINITE_POSE_REVIEW',finite_upper=str(bound),integer_upper=bound.numerator//bound.denominator,limitation='Finite saved poses only; heuristic pricing has no global optimality guarantee.'))
    (out/'progress.json').write_text(json.dumps(dict(records=history),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--rounds',type=int,default=5);a=p.parse_args();run(a.source,a.out,a.rounds)
