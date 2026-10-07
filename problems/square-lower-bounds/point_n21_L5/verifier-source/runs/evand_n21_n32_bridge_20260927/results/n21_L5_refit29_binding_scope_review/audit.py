"""Audit a narrowly reviewed irrelevant-file change; never marks numerical replay complete."""
from pathlib import Path
import ast,hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'runs/evand_n21_n32_bridge_20260927/results'
EXCLUDED=ROOT/'src/nagamochi_research/mixed_ladder_aux.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def closure():
 dirs=[R/'n21_L5_refit29_final_replay',ROOT/'src/nagamochi_research']
 paths={p.stem:p for d in reversed(dirs) for p in d.glob('*.py')}
 todo=['run_frontier','run_prefix'];seen={};dynamic=[]
 while todo:
  name=todo.pop()
  if name in seen:continue
  p=paths[name];tree=ast.parse(p.read_text());parents={c:n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)};deps=set()
  for node in ast.walk(tree):
   if isinstance(node,ast.Import):
    deps.update(x.name.split('.')[0] for x in node.names)
    assert all(x.name!='checkpoint_external_cover' for x in node.names)
   elif isinstance(node,ast.ImportFrom) and node.module:
    assert node.level==0
    deps.add(node.module.split('.')[0])
    if node.module=='checkpoint_external_cover':assert {x.name for x in node.names}=={'atomic'}
   elif isinstance(node,ast.Call):
    fn=ast.unparse(node.func)
    if fn in ['eval','exec','__import__','importlib.import_module','importlib.util.spec_from_file_location','importlib.util.module_from_spec'] or fn.endswith('.exec_module'):
     a=node
     while a in parents and not isinstance(a,(ast.FunctionDef,ast.AsyncFunctionDef)):a=parents[a]
     assert name=='checkpoint_external_cover' and isinstance(a,ast.FunctionDef) and a.name=='run'
     assert fn in ['importlib.util.spec_from_file_location','importlib.util.module_from_spec','spec.loader.exec_module']
     dynamic.append(dict(path=str(p),line=node.lineno,call=ast.unparse(node),excluded_function='run',reason='Only atomic is imported by the replay entry points; run is not called.'))
  seen[name]=dict(path=str(p),sha256=sha(p),local_imports=sorted(deps&paths.keys()))
  todo.extend((deps&paths.keys())-seen.keys())
 assert str(EXCLUDED) not in {v['path'] for v in seen.values()}
 return seen,dynamic

def audit():
 modules,dynamic=closure();reports=[]
 folders=[R/f'n21_L5_refit29_final_{s}_replay' for s in ['root','sieve']]+[R/f'n21_L5_refit29_final_frontier_s{i}' for i in range(3)]
 expected={};inputs={}
 for folder in folders:
  p=folder/'inputs.json';d=json.loads(p.read_text());inputs[str(p)]=sha(p)
  for v in modules.values():assert d['bindings'].get(v['path'])==v['sha256'],('replay dependency changed',v['path'])
  changed=[]
  for path,h in d['bindings'].items():
   assert path not in expected or expected[path]==h
   expected[path]=h;now=sha(path)
   if now!=h:
    assert Path(path)==EXCLUDED,('unreviewed input change',path)
    changed.append(dict(path=path,original_sha256=h,current_sha256=now,reason='outside conservative import closure'))
  reports.append(dict(stage=folder.name,changed=changed,inputs_sha256=inputs[str(p)]))
 assert all(sha(p)==h for p,h in inputs.items())
 assert all(sha(v['path'])==v['sha256'] for v in modules.values())
 return dict(status='DEPENDENCY_SCOPE_VERIFIED',modules=modules,dynamic_import_review=dynamic,stages=reports,input_manifests=inputs,auditor_sha256=sha(__file__),numeric_replay_completion_verified=False,general_coverage_verified=False,scope='Only dependency/input consistency. Does not waive missing proofs, worker failures, partitions, numerical replay, or final theorem review.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=audit();a.out.write_text(json.dumps(r,indent=2)+'\n');print(r['status'],len(r['modules']),'modules;',sum(len(s['changed']) for s in r['stages']),'reviewed mismatches across5 stages')
