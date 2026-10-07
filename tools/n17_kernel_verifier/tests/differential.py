"""Mutation-based comparison against the supplied Python verifier (no generators)."""
import copy
import gzip
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

CRATE = Path(__file__).resolve().parents[1]
ROOT = CRATE.parent
sys.path.insert(0,str(Path(__file__).parent))
from make_fixtures import v, CELLS, closed, seed, cells

BIN=CRATE/'target/debug/n17-kernel-verifier'
BASE=CRATE/'target/differential'
BASE.mkdir(parents=True,exist_ok=True)
CELL=BASE/'cells.json';CELL.write_text(json.dumps(CELLS))
DIGEST=hashlib.sha256(CELL.read_bytes()).hexdigest()

def put(obj,path,value):
    for part in path[:-1]:obj=obj[part]
    if value is DELETE:del obj[path[-1]]
    else:obj[path[-1]]=copy.deepcopy(value)

DELETE=object()
cases=[]
def case(label,document,path,value):cases.append((label,[(document,path,value)]))
def n(label,path,value):case(label,'node',path,value)
def s(label,path,value):case(label,'seed',path,value)

s('seed schema',['schema'],'bad');n('node schema',['schema'],'bad')
s('cap',['U'],'4');n('physical',['B'],'2');n('mask',['mask'],[1,0]);s('duplicate mask',['mask'],[0,0])
n('not root',['parent'],{});s('world size',['world'],[]);s('world cell',['world',0],[])
s('bins',['bins'],0);s('bad bins type',['bins'],1.0);s('seed owned',['groups','0'],[['0','0']])
s('row count',['cells','0'],[]);s('seed interval',['cells','0',0,'interval'],['0','1'])
s('seed domain',['cells','0',0,'outer_domain'],[]);s('seed residual',['cells','0',0,'residual_polygons'],[])
s('seed reference',['cells','0',0,'reference','row'],9)
n('initial group',['initial','groups','0'],[['1','1']]);n('initial refs',['initial','cell_references','0'],[])
n('header index',['steps',0,'index'],9);n('header owner',['steps',0,'owner'],2);n('header complete',['steps',0,'complete'],1)
n('angle',['steps',0,'allowed_half_angle'],[0,1]);n('prior hull',['steps',0,'prior_owned_hulls','0'],[['1','1']])
n('partner index',['steps',0,'prior_partner_pose_covers'],{'9':[]})
n('partner length',['steps',0,'prior_partner_pose_covers','1'],[])
for key,val in [('reference',{}),('interval',['0','1']),('domain',[]),('core',[]),('core',[['-1','-1'],['1','-1'],['1','1'],['-1','1']])]:
    n('partner '+key,['steps',0,'prior_partner_pose_covers','1',0,key],val)
n('no rows',['steps',0,'rows'],[])
for key,val in [('interval',['1/10','1/6']),('interval',['-1/10','1/6']),('interval',['0','0']),('interval',['0','2']),('prior_reference',{}),('interval',['0','1/2']),('reference',{}),('self_hull_cuts',[1]),('core_vertices',[]),('core_vertices',[['1','0'],['0','1'],['-1','0']]),('common_core_halfplanes',[]),('outer_bounds',[]),('outer_domain',[])]:
    n('row '+key,['steps',0,'rows',0,key],val)
n('last row end',['steps',0,'rows',5,'interval'],['5/6','11/12'])
n('outer bound fails',['steps',0,'rows',0,'outer_bounds',0,'upper'],'-100')
for key,val in [('partner',9),('partner','1'),('partner',None),('vertices',[]),('vertices',[['0','0'],['2','0'],['2','2']])]:
    n('collision '+key,['steps',0,'rows',0,'collision_regions',0,key],val)
n('collision escapes',['steps',1,'rows',0,'core_vertices'],[['-1/100','-1/100'],['1/100','-1/100'],['1/100','1/100'],['-1/100','1/100']])
n('uncovered closure',['steps',1,'rows',0,'collision_regions'],[])
n('kernel range',['steps',0,'common_owned_kernel'],[['4','4']]);n('kernel plane',['steps',0,'common_owned_kernel'],[['0','0']])
n('compression source',['steps',0,'compression_source_hull'],[])
n('witness count',['steps',0,'inner_grid_compression','witnesses'],[])
for key,val in [('indices',[]),('indices',[9]),('weights',['-1']),('weights',['0']),('weights',['1','0']),('point',['0','0'])]:
    n('witness '+key,['steps',0,'inner_grid_compression','witnesses',0,key],val)
n('unexpected compression',['steps',1,'inner_grid_compression'],{})
n('closure step',['contradiction','step'],8);n('closure kind',['contradiction','kind'],'bad');n('closure owner',['contradiction','owner'],0)
n('steps after closure',['steps'],closed['steps']+[closed['steps'][-1]])
n('no closure',['steps'],[])
n('final group',['final_state','groups','0'],[]);n('final row count',['final_state','cells','0'],[])
n('final reference',['final_state','cells','0',0,'reference'],{})
n('final outer',['final_state','cells','0',0,'outer_domain'],[])
n('final residual',['final_state','cells','0',0,'residual_polygons'],[])
n('closed flags',['closed'],1);n('overclaim',['global_optimality_proved'],True)
# Python numeric equality in references must accept bool and integral floats.
n('equal row reference',['steps',0,'rows',0,'reference','row'],False)
n('equal collision key',['steps',0,'rows',0,'collision_regions',0,'partner'],1.0)
# Earliest full failure must win over a later structural row failure in threaded runs.
cases.append(('row failure ordering',[('node',['steps',1,'rows',0,'collision_regions'],[{'partner':0,'vertices':[['0','0'],['2','0'],['2','2']]}]),('node',['steps',1,'rows',1,'reference'],{})]))
# Delete every member at multiple depths to cover malformed-input paths.
for document,source,prefix in [('node',closed,[]),('seed',seed,[]),('node',closed['steps'][0],['steps',0]),('node',closed['steps'][0]['rows'][0],['steps',0,'rows',0])]:
    for key in source:case('missing '+'.'.join(map(str,prefix+[key])),document,prefix+[key],DELETE)
# Type corruptions cover malformed arithmetic and containers without relying on panics.
rng=random.Random(31)
paths=[['steps',0,'rows',0,'core_vertices'],['steps',0,'rows',0,'interval'],['steps',0,'rows',0,'common_core_halfplanes'],['steps',0,'prior_partner_pose_covers'],['steps',0,'inner_grid_compression','witnesses',0,'weights']]
for i in range(50):n('wrong type '+str(i),rng.choice(paths),rng.choice([None,False,42,1.5,'x',{},[None],['1/0'],[['1/0','0']]]))

# Metadata exercises Python's whole JSON domain without affecting the proof.
for label,value in [('surrogate', '\ud800'),('nonfinite', [float('nan'),float('inf'),-float('inf')]),('large int',10**100),('decimal float',[0.1,1e-5,1e16,-0.0]),('Unicode',{'😀':'☃','\ud800':'\udfff'})]:
    n('metadata '+label,['metadata'],value)
n('surrogate collision partner',['steps',0,'rows',0,'collision_regions',0,'partner'],'\ud800')
n('bad rows container',['steps',0,'rows'],{})
s('bad seed row container',['cells','0'],{})
s('bad world container',['world'],{})
s('unhashable mask',['mask'],[[],1])
small=[['-1/100','-1/100'],['1/100','-1/100'],['1/100','1/100'],['-1/100','1/100']]
cases.append(('collision facet failure',[('node',['steps',1,'rows',0,'core_vertices'],small),('node',['steps',1,'prior_partner_pose_covers','0',0,'core'],small)]))
failures=[]
for number,(label,mutations) in enumerate(cases):
    ss=copy.deepcopy(seed);nn=copy.deepcopy(closed)
    for document,path,value in mutations:put(ss if document=='seed' else nn,path,value)
    if 'source' in nn and isinstance(nn['source'],dict):nn['source']['sha256']=hashlib.sha256(v.canonical(ss)).hexdigest()
    path=BASE/'certificate';path.mkdir(exist_ok=True)
    for kind,obj in [('seed',ss),('node',nn)]:
        (path/f'{kind}-test.json.gz').write_bytes(gzip.compress(v.canonical(obj),mtime=0))
    expected=v.verify(path,cells)
    for threads in [1,4]:
        output=BASE/'receipt.json'
        proc=subprocess.run([str(BIN),str(path),'--cells',str(CELL),'--cells-sha256',DIGEST,'--output',str(output),'--threads',str(threads)],capture_output=True,text=True)
        if not output.exists():failures.append((label,threads,'no receipt',proc.stderr));continue
        got=json.loads(output.read_text());output.unlink()
        if got['status']!=expected['status'] or proc.returncode!=(0 if got['status']=='PASS' else 1):
            failures.append((label,threads,expected,got,proc.stderr));continue
        if expected['failure'] and expected['failure'].startswith('malformed certificate:'):
            if not got['failure'].startswith('malformed certificate:'):failures.append((label,threads,expected['failure'],got['failure']))
        elif expected['failure']!=got['failure']:failures.append((label,threads,expected['failure'],got['failure']))
        if expected['status']=='PASS':
            for key in ('counts','certificate','closure'):
                if expected[key]!=got[key]:failures.append((label,threads,key,expected[key],got[key]))
# The real stalled certificate must match every receipt field, including FAIL counts.
real = CRATE/'tests/data/stall-w7-bins8'
real_cells = CRATE/'cells/cover.json'
real_digest = hashlib.sha256(real_cells.read_bytes()).hexdigest()
frame = v.file_cells(real_cells, real_digest)
for sample in (None, 0, 2):
    expected = v.verify(real, frame, sample=sample)
    for threads in (1, 4):
        output = BASE/'real-receipt.json'
        args = [str(BIN), str(real), '--cells', str(real_cells), '--cells-sha256', real_digest,
                '--output', str(output), '--threads', str(threads)]
        if sample is not None:
            args += ['--sample', str(sample)]
        proc = subprocess.run(args, capture_output=True, text=True)
        got = json.loads(output.read_text())
        assert proc.returncode == 1, proc.stderr
        for key in expected:
            if key not in ('seconds', 'provenance') and got[key] != expected[key]:
                failures.append(('real stall', sample, threads, key, expected[key], got[key]))
print('Real stall: full and sampled receipts compared at 1 and 4 threads.')
print(f'{len(cases)} mutations × 2 thread counts; {len(failures)} mismatches')
for f in failures:print(f)
sys.exit(bool(failures))
