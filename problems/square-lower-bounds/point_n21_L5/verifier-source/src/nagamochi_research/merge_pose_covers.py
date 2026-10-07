"""Merge lower bounds on identical complete pose partitions.

Source outputs may still be candidates: the merged object must be fully
replayed with full_pose_low_cover.verify before being used as a proof.
"""
from fractions import Fraction as F
from copy import deepcopy
from pathlib import Path
import argparse,hashlib,json


def merge(covers,threshold):
    assert covers and threshold>0
    base=covers[0];q=deepcopy(base)
    assert base['model']=='FULL_SIGNED_POSE_LOW_COVER_V1'
    for other in covers:
        assert other['model']==base['model'] and other['digest']==base['digest']
        assert other.get('symmetry')==base.get('symmetry')
        assert set(other['leaves'])==set(base['leaves'])
    for path,r in q['leaves'].items():
        alternatives=[]
        for source in covers:
            s=source['leaves'][path];assert s['box']==r['box']
            assert (s['kind']=='OUTSIDE')==(r['kind']=='OUTSIDE')
            if s['kind']!='OUTSIDE':alternatives.append((F(s['lower']),s,source.get('bound_method','square')))
        if alternatives:
            value,chosen,default=max(alternatives,key=lambda t:t[0])
            q['leaves'][path]=dict(chosen,bound_method=chosen.get('bound_method',default),
                                   kind='HIGH' if value>=threshold else 'POSSIBLE_LOW')
    q['threshold']=str(threshold)
    return q


def run(sources,out,threshold):
    q=merge([json.loads(p.read_text()) for p in sources],threshold)
    q['merged_sources']=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources]
    q['merge_status']='CANDIDATE_REQUIRES_FULL_REPLAY'
    out.write_text(json.dumps(q));return q


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('sources',type=Path,nargs='+')
    p.add_argument('--threshold',type=F,default=F(4,5));a=p.parse_args();run(a.sources,a.out,a.threshold)
