"""CLI, receipt formatting, provenance, gzip errors, and embedded-cover smoke tests."""
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

CRATE=Path(__file__).resolve().parents[1]
ROOT=CRATE.parent
BIN=CRATE/'target/debug/n17-kernel-verifier'
BASE=CRATE/'target/cli-check';BASE.mkdir(parents=True,exist_ok=True)
CELLS=CRATE/'tests/data/cells.json'
SHA=hashlib.sha256(CELLS.read_bytes()).hexdigest()
OUTPUT=BASE/'receipt.json'

def run(directory,extra=(),embedded=False):
    args=[str(BIN),str(directory),'--output='+str(OUTPUT)]
    if not embedded:args+=['--cells',str(CELLS),'--cells-sha256',SHA]
    args+=list(extra)
    return subprocess.run(args,cwd=ROOT,capture_output=True,text=True)

proc=run(CRATE/'tests/data/closed',['--sample=2','--sample-seed=-12345678901234567890','--threads=4','--progress'])
assert proc.returncode==0,proc.stderr
text=OUTPUT.read_text();receipt=json.loads(text)
assert text==json.dumps(receipt,indent=1)+'\n'
assert receipt['directory']==str(CRATE/'tests/data/closed')
assert receipt['cells_source']=={'kind':'file','path':str(CELLS),'sha256':SHA}
lines=proc.stdout.splitlines();assert len(lines)==3,lines
assert json.loads(lines[-1])=={k:receipt[k] for k in ('status','failure','mode','seconds')}
files=sorted([CRATE/'Cargo.toml',CRATE/'Cargo.lock',CRATE/'build.rs',*list((CRATE/'src').glob('*.rs'))])
assert receipt['provenance']['source_sha256']==hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()
# Directory spelling is retained verbatim.
relative='rust/tests/data/../data/closed'
assert run(relative).returncode==0
assert json.loads(OUTPUT.read_text())['directory']==relative
bad=BASE/'bad';bad.mkdir(exist_ok=True)
shutil.copyfile(CRATE/'tests/data/closed/node-any-name.json.gz',bad/'node-bad.json.gz')
(bad/'seed-bad.json.gz').write_bytes(b'not gzip')
assert run(bad).returncode==1
assert json.loads(OUTPUT.read_text())['failure'].startswith('malformed certificate:')
shutil.copyfile(CRATE/'tests/data/closed/seed-any-name.json.gz',bad/'seed-bad.json.gz')
raw=gzip.decompress((bad/'node-bad.json.gz').read_bytes())
(bad/'node-bad.json.gz').write_bytes(gzip.compress(raw+b' extra'))
assert run(bad).returncode==1
assert json.loads(OUTPUT.read_text())['failure']=='data follows the node'
print('CLI, progress, receipt bytes, source hash, gzip and trailing-data checks passed.',flush=True)
# Temporarily supply only our clearly labeled tiny test cover, then remove it.
cover=CRATE/'cells/cover.json'
other=ROOT/'cells/cover.json'
if cover.exists() or other.exists():
    sys.path.insert(0,str(Path(__file__).parent))
    from make_fixtures import v
    source=json.loads((cover if cover.exists() else other).read_text())
    names=source['order'];world=[source['cells'][name] for name in names]
    frame=v.Cells(tuple(names),tuple(tuple(v.poly(p)) for p in world),v.Q(source['U']),{'kind':'cover','design':source['design']})
    groups={'0':[],'1':[]}
    records={}
    for o in (0,1):
        domain=v.intersect_convex(v.poly(world[o]),v.wall_box(v.Q(0),v.Q(1),frame.cap))
        encoded=[[str(x),str(y)] for x,y in domain]
        records[str(o)]=[{'interval':['0','1'],'reference':{'kind':'wall_seed','owner':o,'row':0},'outer_domain':encoded,'residual_polygons':[encoded] if encoded else []}]
    seed={'schema':'generic_wall_seed_v1','U':source['U'],'B':'1','mask':[0,1],'bins':1,'world':world,'groups':groups,'cells':records}
    node={'schema':'exact_generic_owned_hull_v1','U':source['U'],'B':'1','mask':[0,1],'parent':None,'constraints':[],'guard_source':None,'node_id':'embedded-cover-smoke','source':{'sha256':hashlib.sha256(v.canonical(seed)).hexdigest()},'initial':{'groups':groups,'cell_references':{k:[r['reference'] for r in rs] for k,rs in records.items()}},'contradiction':None,'steps':[],'final_state':{'groups':groups,'cells':records},'closed':False,'terminal':False,'mask_exclusion_proved':False,'global_optimality_proved':False}
    directory=BASE/'embedded-stall';directory.mkdir(exist_ok=True)
    for kind,obj in [('seed',seed),('node',node)]:
        (directory/f'{kind}-smoke.json.gz').write_bytes(gzip.compress(v.canonical(obj)))
    proc=run(directory,embedded=True)
    assert proc.returncode==1,proc.stderr
    got=json.loads(OUTPUT.read_text())
    assert got['failure']=='the node is a stall, not a closure',got
    assert got['cells_source']=={'kind':'cover','design':source['design']}
    expected=v.verify_objects(directory,frame)
    for key in expected:assert got[key]==expected[key],key
    print(f"Supplied {len(names)}-cell cover embedded and checked against Python; file left untouched.",flush=True)
else:
    cover.parent.mkdir(exist_ok=True)
    try:
        cover.write_bytes(CELLS.read_bytes())
        subprocess.run(['cargo','build','--offline','--manifest-path',str(CRATE/'Cargo.toml')],cwd=ROOT,check=True)
        proc=run(CRATE/'tests/data/closed',embedded=True)
        assert proc.returncode==0,proc.stderr
        assert json.loads(OUTPUT.read_text())['cells_source']=={'kind':'cover','design':'tiny-test'}
        print('Embedded-cover build and CLI check passed.',flush=True)
    finally:
        cover.unlink(missing_ok=True)
        subprocess.run(['cargo','build','--offline','--manifest-path',str(CRATE/'Cargo.toml')],cwd=ROOT,check=True)
    assert run(CRATE/'tests/data/closed',embedded=True).returncode==1
    print('Missing-cover diagnostic checked; temporary cover removed.',flush=True)

# Real stalled fixture: preserve exact layout, failure, counters and thread semantics.
real_cells = CRATE/'cells/cover.json'
real_sha = hashlib.sha256(real_cells.read_bytes()).hexdigest()
reference = None
for threads in (1, 4):
    proc = run(CRATE/'tests/data/stall-w7-bins8',
               ['--cells', str(real_cells), '--cells-sha256', real_sha, '--threads', str(threads)],
               embedded=True)
    assert proc.returncode == 1, proc.stderr
    raw = OUTPUT.read_text()
    got = json.loads(raw)
    assert raw == json.dumps(got, indent=1) + '\n'
    assert got['failure'] == 'the node is a stall, not a closure'
    assert got['counts'] == dict(collision_facet_checks=84300, collision_regions=257,
        cover_checks=112, partner_rows=672, rows_full=112, seed_points=4, seed_rows=56, steps=14)
    del got['seconds']
    assert reference is None or reference == got
    reference = got
print('Real stalled certificate receipt bytes, counters and thread equivalence checked.')
