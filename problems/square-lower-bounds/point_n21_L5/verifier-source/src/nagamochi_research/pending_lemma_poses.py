"""Carry valid untrained poses across a support-pricing stage."""
from fractions import Fraction as F
from repair_lemma_measure import poses


def collect(saved,report,L):
    pending={tuple(map(F,p)) for p in saved.get('pending',[])+saved.get('held',[])}
    rows=list(report.get('local_witnesses',[]))
    if report.get('records'):
        last=report['records'][-1];rows+=last.get('local_witnesses',[])
        # Retaining the complete final scan avoids score-dependent omissions.
        pending.update(poses(L,last.get('scan_count',2048),last['scan_seed']))
    pending.update(tuple(F(row[k]) for k in ('cx','cy','t')) for row in rows)
    train={tuple(map(F,p)) for p in saved['train']}
    return sorted(pending-train)


def validate(points,L):
    for x,y,t in points:
        u=abs(t);h=(1-u*u+2*u)/(2*(1+u*u))
        if u>1 or not(h<=x<=L-h and h<=y<=L-h):raise ValueError('Nonphysical pending pose')
    return points
