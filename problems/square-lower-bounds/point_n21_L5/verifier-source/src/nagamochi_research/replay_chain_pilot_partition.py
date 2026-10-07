"""Recompute exact bounds and check complete, nonoverlapping box partitions."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from math import prod
from mixed_density_check import expand,pose_lower_bound

def replay(candidate,certificate):
    data=json.loads(certificate.read_text())
    assert hashlib.sha256(candidate.read_bytes()).hexdigest()==data['candidate_sha256']
    model=expand(json.loads(candidate.read_text()));results=[]
    for record in data['records']:
        parent=list(map(F,record['parent']));boxes=[];bounds=[]
        for leaf in record['leaves']:
            box=list(map(F,leaf['box']))
            assert all(parent[i]<=box[i]<box[i+1]<=parent[i+1] for i in (0,2,4))
            bound=pose_lower_bound(model,*box);assert bound==F(leaf['lower']);bounds.append(bound);boxes.append(box)
        assert boxes
        for a,b in combinations(boxes,2):
            assert any(min(a[i+1],b[i+1])<=max(a[i],b[i]) for i in (0,2,4))
        assert sum(prod(b[i+1]-b[i] for i in (0,2,4)) for b in boxes)==prod(parent[i+1]-parent[i] for i in (0,2,4))
        assert min(bounds)==F(record['lower']) and record['certified']==(min(bounds)>=1)
        results.append(dict(pilot_index=record['pilot_index'],leaves=len(boxes),lower=str(min(bounds)),certified=min(bounds)>=1))
    return dict(status='EXACT_BOUNDS_AND_PARTITIONS_REPLAYED',records=results,independent_bound_implementation=False,general_packing_exclusion=False)
if __name__=='__main__':
    print(json.dumps(replay(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
