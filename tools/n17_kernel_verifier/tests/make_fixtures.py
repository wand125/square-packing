"""Independent tiny fixtures and oracle outputs; reads only the supplied verifier.
No certificate generator is imported. The shim only replaces project provenance and
Python 3.14's unparenthesized multiple-exception syntax for older test interpreters.
"""
import copy
import gzip
import hashlib
import json
import sys
import types
from fractions import Fraction as Q
from pathlib import Path

CRATE = Path(__file__).resolve().parents[1]
ROOT = CRATE.parent
OUT = CRATE / 'tests/data'
# The reference verifier: upstream's packing/devtools/verify_n17_kernel_certificate.py.
import os
REFERENCE = Path(os.environ.get('REFERENCE_VERIFIER', ROOT / 'upstream/verify_n17_kernel_certificate.py'))

def oracle():
    text = REFERENCE.read_text()
    text = text.replace('from devtools.provenance import provenance, repository_path',
                        'provenance = lambda _: {}\nrepository_path = str')
    text = text.replace('except TypeError, ValueError:', 'except (TypeError, ValueError):')
    module = types.ModuleType('reference_verifier')
    module.__file__ = str(REFERENCE)
    sys.modules[module.__name__] = module
    exec(compile(text, module.__file__, 'exec'), module.__dict__)
    return module

v = oracle()
P = [['1','1'],['11/10','1'],['11/10','11/10'],['1','11/10']]
C = [['-1/10','-1/10'],['1/10','-1/10'],['1/10','1/10'],['-1/10','1/10']]
CELLS = {'U':'3','order':['a','b'],'cells':{'a':P,'b':P},'design':'tiny-test'}
(OUT / 'cells.json').write_text(json.dumps(CELLS))
cells = v.Cells(('a','b'), (tuple(v.poly(P)),tuple(v.poly(P))), Q(3), {'kind':'test'})

def seed_row(o, i):
    return {'interval':[str(Q(i,3)),str(Q(i+1,3))], 'outer_domain':P,
            'residual_polygons':[P], 'reference':{'kind':'wall_seed','owner':o,'row':i}}
seed = {'schema':'generic_wall_seed_v1','U':'3','B':'1','mask':[0,1], 'bins':3,
        'world':[P,P], 'groups':{'0':[],'1':[]},
        'cells':{str(o):[seed_row(o,i) for i in range(3)] for o in range(2)}}
refs = {str(o):[r['reference'] for r in seed['cells'][str(o)]] for o in range(2)}
node = {'schema':'exact_generic_owned_hull_v1','U':'3','B':'1','mask':[0,1],
        'parent':None, 'constraints':[], 'guard_source':None,
        'node_id':'test-☃-😀',
        'source':{'sha256':hashlib.sha256(v.canonical(seed)).hexdigest()},
        'initial':{'groups':seed['groups'],'cell_references':refs},
        'mask_exclusion_proved':False,'global_optimality_proved':False}

def make_step(si, owner, prior_rows, partner_rows, prior_groups, live):
    rs=[]
    for ri in range(6):
        interval=[str(Q(ri,6)),str(Q(ri+1,6))]
        r={'interval':interval,'reference':{'kind':'phase3','node':node['node_id'],'step':si,'row':ri},
           'prior_reference':prior_rows[ri//2]['reference'], 'core_vertices':C,
           'residual_polygons':[P] if live else [],
           'collision_regions':[{'partner':1-owner,'vertices':P}],
           'common_core_halfplanes':[], 'outer_bounds':[], 'outer_domain':P if live else []}
        if live:
            for a,b,c in v.planes_of(v.poly(C)):
                upper=c+min(a*x+b*y for x,y in v.poly(P))
                r['common_core_halfplanes'].append({'normal':[str(a),str(b)],'upper':str(upper)})
            r['outer_bounds']=[{'normal':[str(a),str(b)],'upper':str(c)} for a,b,c in v.planes_of(v.poly(P))]*2
        rs.append(r)
    step={'index':si,'owner':owner,'complete':True,'allowed_half_angle':['0','1'],
          'prior_owned_hulls':copy.deepcopy(prior_groups),
          'prior_partner_pose_covers':{str(1-owner):[
              {'reference':r['reference'],'interval':r['interval'],'domain':P,'core':C} for r in partner_rows]},
          'rows':rs,'common_owned_kernel':[['1','1']] if live else []}
    if live:
        step.update(compression_source_hull=[['1','1']], inner_grid_compression={
            'mode':'replace','vertices':[['1','1']],
            'witnesses':[{'indices':[0],'weights':['1'],'point':['1','1']}]})
    return step

first=make_step(0,0,seed['cells']['0'],seed['cells']['1'],seed['groups'],True)
second=make_step(1,1,seed['cells']['1'],first['rows'],{'0':[['1','1']],'1':[]},False)
closed=copy.deepcopy(node)
closed.update(steps=[first,second],contradiction={'kind':'all_parent_poses_forbidden','owner':1,'step':1},
              closed=True,terminal=True,final_state={'groups':{'0':[['1','1']],'1':[]},
              'cells':{'0':first['rows'],'1':second['rows']}})
stall=copy.deepcopy(node)
stall.update(steps=[first],contradiction=None,closed=False,terminal=False,
             final_state={'groups':{'0':[['1','1']],'1':[]},'cells':{'0':first['rows'],'1':seed['cells']['1']}})

for label,n in [('closed',closed),('stall',stall)]:
    path=OUT/label
    path.mkdir(exist_ok=True)
    (path/'seed-any-name.json.gz').write_bytes(gzip.compress(json.dumps(seed,ensure_ascii=False,indent=2).encode(),mtime=0))
    (path/'node-any-name.json.gz').write_bytes(gzip.compress(json.dumps(n,sort_keys=True,ensure_ascii=False,indent=2).encode(),mtime=0))
    for sample in [None,0,2]:
        result=v.verify_objects(path,cells,sample=sample)
        (OUT/f'{label}-{sample}.json').write_text(json.dumps(result,indent=1)+'\n')

# A fully dead seed and step exercise the absence (not zero) of cover counters.
dead_cells=copy.deepcopy(CELLS)
D=[['-2','-2'],['-1','-2'],['-1','-1'],['-2','-1']]
dead_cells['cells']={'a':D,'b':D}
(OUT/'dead-cells.json').write_text(json.dumps(dead_cells))
ds=copy.deepcopy(seed);ds['world']=[D,D]
for rs in ds['cells'].values():
    for r in rs:r.update(outer_domain=[],residual_polygons=[])
dn=copy.deepcopy(node);dn['source']['sha256']=hashlib.sha256(v.canonical(ds)).hexdigest()
dr=[]
for i,r in enumerate(ds['cells']['0']):
    dr.append(dict(r,reference={'kind':'phase3','node':dn['node_id'],'step':0,'row':i},
                   prior_reference=r['reference'],collision_regions=[],common_core_halfplanes=[],outer_bounds=[]))
dn.update(steps=[{'index':0,'owner':0,'complete':True,'allowed_half_angle':['0','1'],
                 'prior_owned_hulls':ds['groups'],'prior_partner_pose_covers':{},'rows':dr,'common_owned_kernel':[]}],
          contradiction={'kind':'all_parent_poses_forbidden','owner':0,'step':0},closed=True,terminal=True,
          final_state={'groups':ds['groups'],'cells':dict(ds['cells'],**{'0':dr})})
path=OUT/'dead';path.mkdir(exist_ok=True)
for kind,data in [('seed',ds),('node',dn)]:
    (path/f'{kind}-fixture.json.gz').write_bytes(gzip.compress(v.canonical(data),mtime=0))
dc=v.Cells(('a','b'),(tuple(v.poly(D)),tuple(v.poly(D))),Q(3),{'kind':'test'})
(OUT/'dead-None.json').write_text(json.dumps(v.verify_objects(path,dc),indent=1)+'\n')
print('Generated closed, stall, sampled, and dead-row oracle fixtures.')

# Regenerate expectations for the supplied real fixture, without generating a certificate.
if __name__ == '__main__':
    real_cells = CRATE/'cells/cover.json'
    frame = v.file_cells(real_cells, hashlib.sha256(real_cells.read_bytes()).hexdigest())
    for sample in (None, 0, 2):
        result = v.verify_objects(OUT/'stall-w7-bins8', frame, sample=sample)
        (OUT/f'stall-w7-bins8-{sample}.json').write_text(json.dumps(result, indent=1)+'\n')
    print('Regenerated real stalled fixture full and sampled oracle results.')
