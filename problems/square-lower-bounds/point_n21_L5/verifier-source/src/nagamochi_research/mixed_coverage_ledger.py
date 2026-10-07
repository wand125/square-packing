"""Summarize verified angles for each current candidate, never mix weights.
This is a result ledger, not a replacement for either verifier or replay.
"""
import json,argparse
from pathlib import Path
from fractions import Fraction as F
from mixed_density_check import expand
from mixed_net_audit import symmetry,net_certificate


def ledger(root):
    records={}
    for name,file in [('fixed_mixed','fixed-candidate.json'),('added_density','mixed-candidate.json')]:
        data=json.loads((root/file).read_text());m=expand(data);symmetry(m);net_certificate(m[1]);assert m[-2]<data['n']
        verified={};folder=root/'validation'/name
        a=json.loads((folder/'axis/result.json').read_text())
        if a['status']=='AXIS_VERIFIED':
            assert a['proof_spec']['candidate_digest']==m[-1] and F(a['gamma'])>=1
            axis_replay=json.loads((folder/'axis/replayed.json').read_text());assert axis_replay['status']=='AXIS_CERTIFICATE_REPLAYED' and axis_replay['digest']==m[-1]
            verified[0]=dict(gamma=a['gamma'],result=str(folder/'axis/result.json'))
        for p in sorted(folder.glob('net*/result.json')):
            r=json.loads(p.read_text());spec=r['manifest'];assert spec['candidate_digest']==m[-1]
            if r['status']!='ANGLE_VERIFIED':continue
            assert r['frontier']==[] and F(spec['gamma'])>=1
            replay=json.loads((p.parent/'replayed.json').read_text());assert replay['status']=='ANGLE_RESULT_REPLAYED' and replay['candidate_digest']==m[-1] and replay['index']==spec['net_index']
            j=spec['net_index']
            if j not in verified or F(spec['gamma'])>F(verified[j]['gamma']):verified[j]=dict(gamma=spec['gamma'],result=str(p))
        records[name]=dict(candidate_digest=m[-1],total_mass=str(m[-2]),proven_net_indices=sorted(verified),count=len(verified),total_angles=201,angle_results=verified,status='PARTIAL_COVERAGE_NOT_PACKING_PROOF')
    (root/'coverage-ledger.json').write_text(json.dumps(records,indent=2));print(json.dumps({k:dict(count=v['count'],indices=v['proven_net_indices']) for k,v in records.items()}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);ledger(p.parse_args().root)
