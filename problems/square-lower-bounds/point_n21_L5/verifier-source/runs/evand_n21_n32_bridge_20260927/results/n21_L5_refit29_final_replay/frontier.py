"""Numerically replay one complete original frontier parent for the new measure.
Saved success/lower fields are not proof premises. No search or optimization.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,gzip,hashlib
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src/nagamochi_research'))
from compile_box_capture_rows import geometry,validate_partition
from physical_pose_enclosure import enclose,replay_partition
from near_axis_partition_bridge import replay_band,split_at_band
from replay_capture_margin import replay_capture_margin
from transfer_point_capture import bound_alpha_one,bound
from reoptimize_physical_tree_weights import replay as tree_replay
from reoptimize_capture_weights import replay as linear_replay
from extend_reweighted_physical_tree import replay as extended_replay
R=ROOT/'runs/evand_n21_n32_bridge_20260927/results'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,expected=None):
 p=Path(p);raw=p.read_bytes()
 if expected is not None:assert hashlib.sha256(raw).hexdigest()==expected,'artifact SHA mismatch'
 return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def boxkey(b):return tuple(map(F,b))
class Checker:
 def __init__(self):
  self.old=R/'n21_L5_refit27_predicate_trial/refit/candidate.txt';self.new=R/'n21_L5_refit29_counterexample_trial/refit/candidate.txt';self.oldsha=sha(self.old);self.newsha=sha(self.new)
  self.L,self.c,self.w,_=geometry(self.old);L,c,self.v,_=geometry(self.new);assert L==self.L==5 and c==self.c
  self.op=[(*p,w) for p,w in zip(self.c,self.w)];self.np=[(*p,w) for p,w in zip(self.c,self.v)];self.q=F(249987,250000);assert all(w>=0 for w in self.v) and sum(self.v,F())<21*self.q
  self.front=R/'n21_L5_refit27_global_sieve_r_trial/frontier-output.json';self.fsha=sha(self.front);self.f=load(self.front);self.m=load(R/'n21_L5_refit27_full_assembly_trial/manifest-with-third.json');assert self.m['candidate_sha256']==self.f['candidate_sha256']==self.oldsha and self.m['frontier_sha256']==self.fsha
  self.inventory=load(R/'n21_L5_refit29_frontier_inventory10/inventory.json');assert self.inventory['candidate_sha256']==self.newsha;self.required={i for i,p in enumerate(self.f['pending']) if F(p['box'][4])<=F(5,12)};assert self.required==set(self.inventory['covered_indices']) and self.inventory['pending_failed']==self.inventory['unseen']==0 and len(self.required)==31678
  self.evidence={e['index']:e for e in self.inventory['evidence']};self.bands={};self.new_band=None
 def checked_band(self,candidate,record):
  key=(sha(candidate),json.dumps(record,sort_keys=True))
  if key not in self.bands:self.bands[key]=replay_band(candidate,record)
  return self.bands[key]
 def extras(self,index):
  e=self.evidence[index];out={};visited=set()
  def add(b,kind,path,h):
   path=Path(path);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h;out.setdefault(boxkey(b),[]).append(dict(kind=kind,path=path,sha256=h))
  def walk(path,h):
   path=Path(path);path=path if path.is_absolute() else ROOT/path
   if (str(path),h) in visited:return
   visited.add((str(path),h));d=load(path,h)
   if 'parents' in d:
    rows=[z for z in d['parents'] if z['index']==index];assert len(rows)==1;d=rows[0]
   assert d['index']==index
   for pkey,hkey in [('base_path','base_sha256'),('source_path','source_sha256')]:
    if pkey in d and hkey in d:walk(d[pkey],d[hkey])
   for z in d.get('leaves',d.get('records',[])):
    b=z['box']
    for a in [z,z.get('direct',{})]:
     if 'proof_path' in a:add(b,'DIRECT',a['proof_path'],a['proof_sha256'])
    if 'reoptimized_path' in z:add(b,'MODEL',z['reoptimized_path'],z['reoptimized_sha256'])
    for a in z.get('repair_evidence',[]):
     if a['method'] in ['CACHED_DIRECT','FRESH_DIRECT']:add(b,'DIRECT',a['path'],a['sha256'])
     elif a['method']=='EXTENDED_TREE':add(b,'EXTENDED',a['path'],a['sha256'])
     elif a['method']=='NEW_LINEAR_DUAL':add(b,'MODEL',a['path'],a['sha256'])
     elif a['method']=='NEW_CLOSED_BAND':add(b,'BAND',a['path'],a['sha256'])
     else:raise ValueError('unknown repair evidence')
  walk(e['path'],e['sha256'])
  if index==38:
   d=load(R/'n21_L5_refit29_parent38_replay_trial/result.json');z=next(z for z in d['records'] if z['label']=='3/0');p=R/'n21_L5_refit29_parent38_replay_trial/reoptimized-3-0.json';add(z['box'],'MODEL',p,sha(p))
   folder=R/'n21_L5_refit29_joined38_repair_trial';inp=load(folder/'inputs.json')
   for i,z in enumerate(inp['pending']):
    if z['label']=='8/0':
     p=folder/f'proof-{i}.json';add(z['box'],'DIRECT',p,sha(p))
  return out
 def new_axis(self,b):
  if self.new_band is None:self.new_band=self.checked_band(self.new,load(R/'n21_L5_refit29_axis_band_trial/band.json'))
  band=self.new_band
  assert F(0)<=F(b[4])<=F(b[5])<=F(band['upper']);return F(band['lower'])
 def leaf(self,b,proof,extras,band=None):
  enclosure=enclose(self.L,b);outer=enclosure['enclosing_box']
  if outer is None:return None,'GEOMETRIC_EMPTY'
  alternatives=sorted(extras.get(boxkey(b),[]),key=lambda a:['DIRECT','EXTENDED','MODEL','BAND'].index(a['kind']))
  for a in alternatives:
   artifact=load(a['path'],a['sha256']);kind=a['kind']
   if kind=='DIRECT':
    assert artifact['candidate_sha256']==self.newsha and boxkey(artifact['box'])==boxkey(b);checked=replay_partition(self.new,b,artifact['records'],self.newsha);lower=checked['lower'];vacuous=checked['vacuous']
   elif kind=='BAND':
    checked=self.checked_band(self.new,artifact);assert F(0)<=F(b[4])<=F(b[5])<=F(checked['upper']);lower=checked['lower'];vacuous=False
   else:
    assert proof is not None and boxkey(proof['box'])==boxkey(outer)
    verify=extended_replay if kind=='EXTENDED' else (tree_replay if 'tree' in proof else linear_replay);checked=verify(self.op,self.np,proof,self.L,artifact);lower=checked['lower'];vacuous=checked['vacuous']
   if vacuous:return None,kind+'_EMPTY'
   if F(lower)>=self.q:return F(lower),kind
  if band is not None:
   # Prefer the new candidate's independently replayed all-centre closed band.
   value=self.new_axis(b)
   if value>=self.q:return value,'NEW_CLOSED_BAND'
   old=self.checked_band(self.old,band);source_lower=F(old['lower'])
  else:
   assert proof is not None and boxkey(proof['box'])==boxkey(outer);old=replay_capture_margin(self.op,proof,L=self.L)
   if old.get('vacuous'):return None,'SOURCE_GEOMETRIC_EMPTY'
   source_lower=F(old['lower'])
  t=bound_alpha_one(self.c,self.w,self.v,outer,source_lower)
  if F(t['lower'])<self.q:t=bound(self.c,self.w,self.v,outer,source_lower)
  assert F(t['lower'])>=self.q,('unproved leaf',b,t['lower']);return F(t['lower']),'REPLAYED_SOURCE_TRANSFER'
 def parent(self,index):
  assert index in self.required;e=self.m['entries'][index];assert e['index']==index;source=load(e['path'],e['sha256']);parent=self.f['pending'][index]['box'];extras=self.extras(index);pieces=[]
  if e['kind']=='CAMPAIGN':
   ctx=source['context'];assert ctx['candidate_sha256']==self.oldsha and ctx['frontier_sha256']==self.fsha and ctx['global_leaf_index']==index and ctx['input']==self.f['pending'][index];rows=source['proof']['records'];validate_partition(parent,[z['enclosure']['original_box'] for z in rows]);pieces=[(z['enclosure']['original_box'],z['proof'],None,z['enclosure']) for z in rows]
  else:
   assert e['kind']=='JOINED_PARENT' and source['candidate_sha256']==self.oldsha and boxkey(source['parent'])==boxkey(parent);validate_partition(parent,[p['box'] for p in source['pieces']])
   for part in source['pieces']:
    b=part['box']
    if part['kind']=='PHYSICAL_PARTITION':rows=part['records']
    else:
     assert part['kind']=='NEAR_AXIS_CONNECTION';connection=part['proof'];assert boxkey(connection['parent'])==boxkey(b);band=connection['band'];upper=band['interval']['upper'];low,b=split_at_band(b,upper);pieces.append((low,None,band,None));rows=connection['high_records']
    validate_partition(b,[z['enclosure']['original_box'] for z in rows]);pieces.extend((z['enclosure']['original_box'],z['proof'],None,z['enclosure']) for z in rows)
  validate_partition(parent,[b for b,_,_,_ in pieces]);records=[]
  for b,proof,band,enclosure in pieces:
   if enclosure is not None:assert enclosure==enclose(self.L,b)
   value,method=self.leaf(b,proof,extras,band);records.append(dict(box=b,lower=None if value is None else str(value),method=method))
  low=min((F(z['lower']) for z in records if z['lower'] is not None),default=None);return dict(index=index,parent=parent,candidate_sha256=self.newsha,source_sha256=e['sha256'],leaves=records,lower=None if low is None else str(low),partition_recomputed=True,numerically_replayed=True,general_coverage_verified=False)
