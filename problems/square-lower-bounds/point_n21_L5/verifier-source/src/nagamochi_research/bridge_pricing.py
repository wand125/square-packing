"""Price additional geometric rules against a saved exact finite dual."""
import json
from time import perf_counter
from fractions import Fraction as F
from bridge_lp import ROOT,transform,canonical_rule,hits_exact
from bridge_probe import charge_atom


def main():
    start=perf_counter();r=json.loads((ROOT/'contact-results.json').read_text())
    dual=[(tuple(map(F,w['pose'])),F(w['weight'])) for w in r['results']['points_thresholds']['dual']]
    records=[]
    for seed in range(62671,62709):
        a=charge_atom(seed);pts=[tuple(map(F,p)) for p in a['sites']]
        orbit={canonical_rule([transform(p,g) for p in pts],a['winning_subsets']) for g in range(8)}
        load=F(0)
        for rule in orbit:
            sites=sorted({p for bag in rule for p in bag});index={p:i for i,p in enumerate(sites)}
            bags=[[index[p] for p in bag] for bag in rule]
            for pose,w in dual:
                h=hits_exact(pose,sites)
                if any(all(h[i] for i in bag) for bag in bags):load+=w
        records.append(dict(seed=seed,cost=len(orbit),load=str(load),reduced_cost=str(len(orbit)-load),atom=a))
    out=dict(candidates=len(records),improving=sum(F(r['reduced_cost'])<0 for r in records),seconds=perf_counter()-start,records=records,
             scope='Negative reduced cost is a candidate signal, not a guaranteed LP gain; no continuous cover.')
    (ROOT/'candidate-pricing.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(dict(candidates=out['candidates'],improving=out['improving'],seconds=out['seconds'],best=[{k:r[k] for k in ('seed','cost','load','reduced_cost')} for r in sorted(records,key=lambda r:F(r['reduced_cost']))[:5]])))

if __name__=='__main__':main()
