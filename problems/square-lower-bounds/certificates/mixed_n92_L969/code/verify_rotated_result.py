"""Rebuild and replay an ANGLE_VERIFIED result; same algorithm, no independence claim."""
from pathlib import Path
from fractions import Fraction as F
import json,subprocess,tempfile
from mixed_density_check import expand
from mixed_net_audit import candidate_net
from mixed_rotated_verify import export,compile_verifier


def replay(folder,binary=None,candidate=None):
    saved=json.loads((folder/'result.json').read_text());assert saved['status']=='ANGLE_VERIFIED' and saved['frontier']==[]
    # Relocation changes file paths, not the rational measure bound by the digest.
    data=json.loads(Path(candidate or saved['candidate']).read_text());model=expand(data);spec=saved['manifest']
    with tempfile.TemporaryDirectory(prefix='mixed-angle-replay-') as tmp:
        tmp=Path(tmp);rebuilt=export(model,spec['net_index'],tmp/'input.txt',F(spec['gamma']),candidate_net(data))
        assert rebuilt==spec,'Proof specification or candidate changed'
        assert (tmp/'input.txt').read_bytes()==(folder/'input.txt').read_bytes(),'Input tampered'
        if binary is None:binary=tmp/'verify';compile_verifier(binary)
        result=json.loads(subprocess.check_output([str(binary),str(tmp/'input.txt'),str(saved['nodes'])],text=True))
        for key in ('status','nodes','leaves','lower','frontier'):assert result[key]==saved[key],key
    report=dict(status='ANGLE_RESULT_REPLAYED',candidate_digest=model[-1],index=spec['net_index'],lower=result['lower'],nodes=result['nodes'],scope='Same outward-rounded algorithm re-executed; not an independent proof implementation.')
    (folder/'replayed.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);print(json.dumps(replay(p.parse_args().folder)))
