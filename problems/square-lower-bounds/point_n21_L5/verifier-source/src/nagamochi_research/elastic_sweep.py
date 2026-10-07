"""All single exceptional long rows vs all distinct long focus rows.
Exact endpoint edge bounds certify those edges for the entire affine phase.
This does not certify wall cells or all-time unavoidability.
"""
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
from collections import Counter
import json
from elastic_motion import snapshot
from elastic_audit import triangle_edges,near_pair_hole
from motion_pilot import rows,probe
from support_pilot import holdout


def main():
    start=perf_counter();records=[];poses=holdout(6,872953)+holdout(6,719931)
    for colour in (0,1):
        longrows=[r for r in range(6) if (r+colour)%2==1];edges=triangle_edges(colour)
        base=rows(6,colour=colour)
        for focus in longrows:
            for frozen in longrows:
                if focus==frozen:continue
                r=dict(colour=colour,focus=focus,frozen_row=frozen,compression=F(1,1000),checks=[],
                       edge_certificates=[],status='FINITE_PASS_NOT_PROOF')
                fi=base.index((F(11,2),F(457,500)+F(1043,1250)*frozen))
                r['frozen_index']=fi
                for phase in ('vertical','row-left','leftmost-right'):
                    endpoint=[]
                    for time in (F(0),F(1)):
                        ps=snapshot(colour,focus,F(1,1000),time,phase,frozen)
                        assert ps[fi]==base[fi]
                        endpoint.append([sum((ps[i][a]-ps[j][a])**2 for a in (0,1)) for i,j in edges])
                    r['edge_certificates'].append(dict(phase=phase,endpoint_max_sq=[max(v) for v in endpoint],
                                                       all_time_unit_edges=all(v<=1 for row in endpoint for v in row)))
                    for time in (F(1,7),F(1,3),F(2,3),F(6,7),F(1)):
                        ps=snapshot(colour,focus,F(1,1000),time,phase,frozen)
                        pose=near_pair_hole(ps)
                        if pose is None:
                            check=probe(ps,poses)
                            if check['status']=='EXACT_EMPTY_OPEN_SQUARE':pose=check['pose']
                        e=dict(phase=phase,time=time)
                        if pose is not None:
                            e['empty_pose']=pose;r['checks'].append(e);r['status']='EXACT_REJECTED';break
                        e['samples']=len(poses);r['checks'].append(e)
                    if r['status']=='EXACT_REJECTED':break
                records.append(r)
    result=dict(records=records,seconds=perf_counter()-start,counts=dict(Counter(r['status'] for r in records)))
    Path('runs/bentz_local_motion_20260926/elastic-sweep.json').write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
