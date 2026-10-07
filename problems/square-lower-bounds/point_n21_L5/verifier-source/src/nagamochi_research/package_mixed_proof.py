"""Package only a completed and replayed mixed proof, with relocatable sources."""
import argparse,hashlib,json,platform,shutil,sys,tarfile
from pathlib import Path
import numpy as np
from mixed_density_check import expand
CODE=Path(__file__).resolve().parent
FILES=['score.py','mixed_density_check.py','mixed_net_audit.py','mixed_axis_cells.py','endpoint_cells.py','mixed_rotated_verify.py','mixed_rotated_verify.cpp','verify_rotated_result.py','verify_axis_certificate.py','verify_mixed_full_proof.py']


def package(root,out):
    root=root.resolve();out=out.resolve()
    cert=json.loads((root/'certificate.json').read_text());assert cert['status']=='ALL_ANGLES_VERIFIED_AND_REPLAYED'
    count=cert['angle_count'];step=cert['net']['step'];last=count-1
    model=expand(json.loads((root/'candidate.json').read_text()));assert model[-1]==cert['candidate_digest']
    assert set(map(int,cert['results']))==set(range(count))
    assert all(cert['results'][str(j)]['status']=='ANGLE_RESULT_REPLAYED' for j in range(1,count))
    assert cert['results']['0']['status']=='AXIS_CERTIFICATE_REPLAYED'
    assert (root/'verify.cpp').read_bytes()==(CODE/'mixed_rotated_verify.cpp').read_bytes()
    out.mkdir(parents=True,exist_ok=False);(out/'code').mkdir();(out/'proof').mkdir()
    for name in FILES:shutil.copy2(CODE/name,out/'code'/name)
    for name in ('candidate.json','manifest.json','summary.json','certificate.json','verify.cpp'):
        shutil.copy2(root/name,out/'proof'/name)
    for name in ['axis']+[f'net{j:03}' for j in range(1,count)]:
        shutil.copytree(root/name,out/'proof'/name)
    (out/'requirements.txt').write_text('numpy\n')
    (out/'README.md').write_text(f'''# Mixed density and point proof: n={cert['n']}, L={cert['L']}

Every one of the {count} net angles has passed complete centre coverage and replay.
The exact mass is {cert['total_mass']} < {cert['n']}.
Candidate SHA256: `{cert['candidate_digest']}`.

## Reproduce

Use Python 3, NumPy, and a C++17 compiler named `c++`. From this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 code/verify_mixed_full_proof.py proof --workers 3
```

The checker regenerates inputs from the rational candidate, checks symmetry,
angle-net containment and budgets, rechecks the axis integer tables, compiles
the supplied C++ source without fast-math or FMA contraction, and re-executes
all {last} oblique centre-domain proofs. Recorded original filesystem paths are
provenance only: replay uses this bundle's candidate and checks its digest.

## Mathematical implication

D4 symmetry reduces orientations to [0, pi/4]. The half-angle net has step
{step} and {count} nodes. B={cert['B']} satisfies B*(1+{step})<1, so each original
unit square contains a closed net-angle core strictly in its interior.
All required centres at every net node have core measure >=1. Cores selected
inside distinct nonoverlapping packing squares are disjoint, including their
boundaries; hence their total measure would be >=n, contradicting total mass<n.

The axis table replay is independent of the generating table formula. Oblique
replay uses the SAME outward-rounded algorithm, not an independent second
implementation and not a proof-assistant formalization. No Nagamochi score
lemma is used.

`files-sha256.json` records the untouched bundle. Replay regenerates report
files and a binary; validate these hashes before replay if checking integrity.
The numerical search, LP solver and random probes are not trusted inputs to
the proof checker. Publication is a separate step.
''')
    meta=dict(status='REPLAYED_PROOF_BUNDLE',candidate_digest=model[-1],source_run=str(root),python=sys.version,numpy=np.__version__,platform=platform.platform(),certificate=cert['status'])
    (out/'bundle.json').write_text(json.dumps(meta,indent=2)+'\n')
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'files-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    archive=out.with_name(out.name+'.tar.gz')
    if archive.exists():raise FileExistsError(archive)
    with tarfile.open(archive,'w:gz') as tf:tf.add(out,arcname=out.name)
    print(json.dumps(dict(bundle=str(out),archive=str(archive),files=len(hashes),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args();package(a.root,a.out)
