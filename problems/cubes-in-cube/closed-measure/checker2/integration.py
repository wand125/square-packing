#!/usr/bin/env python3
"""Exact data, rejection, checkpoint, and serial determinism checks.
Two-worker comparison is opt-in (--two-threads), never used on this laptop.
"""
import fractions, hashlib, json, pathlib, struct, subprocess, tempfile, sys
ROOT=pathlib.Path(__file__).resolve().parent
BIN=ROOT/'target/release/m4b-cert2'
def call(args, **kw):
    return subprocess.run([str(BIN),'--threads','1',*args],text=True,capture_output=True,timeout=60,**kw)
raw=(ROOT.parent/'measure.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='565dbf5dd0059aa90929e4151d85fafdeef002a1b9e9aaf83f2e6243b2d393e0'
doc=json.loads(raw);positive=[p for p in doc['pieces'] if p['density']>0]
meta=json.loads(call(['--check-data'],check=True).stdout)
assert meta['density_bits']==[struct.unpack('Q',struct.pack('d',p['density']))[0] for p in positive]
total=fractions.Fraction()
for p in positive:
    v=fractions.Fraction(p['density'])
    for lo,hi in p['bounds']:
        if hi>lo: v*=fractions.Fraction(round(10*hi)-round(10*lo),10)
    total+=v
assert fractions.Fraction(meta['T'][0])<=total<=fractions.Fraction(meta['T'][1])
assert total*fractions.Fraction(27,20)<meta['n_claim']==25
print('SHA-256, exact total, bit-for-bit densities, n_claim=25: passed')
with tempfile.TemporaryDirectory(dir=ROOT,prefix='integration-') as tmp:
    base=pathlib.Path(tmp)
    for mutation in ['density','bound','remove']:
        d=json.loads(raw);i=next(i for i,p in enumerate(d['pieces']) if p['density']>0)
        if mutation=='density': d['pieces'][i]['density']*=1.01
        elif mutation=='bound':
            d['pieces'][i]['bounds'][0]=[x+.1 for x in d['pieces'][i]['bounds'][0]]
        else: d['pieces'].pop(i)
        path=base/(mutation+'.json');path.write_text(json.dumps(d))
        p=call(['--measure',str(path),'--check-data'])
        assert p.returncode and 'check 1 symmetry failed' in p.stderr,(mutation,p.stderr)
    print('Three altered measures rejected by check 1')
    def run(name,rounds,resume=False,threads=1):
        args=['--threads',str(threads),'--seconds','20','--max-depth','4','--rounds',str(rounds),'--output',str(base/name),'--keep-leaves']
        if resume: args+=['--resume']
        p=call(args,check=True)
        return json.loads(p.stdout),json.loads((base/name/'checkpoint.json').read_text()),(base/name/'leaves.txt').read_bytes()
    one=run('one',100)
    assert one[0]['enclosure']=='mean-value-1'
    assert one[0]['fundamental_domain']=='Delta x gamma in [0, pi/2] (u sorted, 48 container symmetries; quarter turn about the third cube axis)'
    run('resume',3)
    with (base/'resume/leaves.txt').open('ab') as f:f.write(b'crash tail')
    other=run('resume',100,True)
    def compare(other):
        for key in ['boxes','leaves_by_rule','closed_volume_fraction','pending','unresolved','max_depth','leaf_chain','rounds','leaf_bytes','lemma_counts']:
            assert one[0][key]==other[0][key],key
        assert one[1]['pending']==other[1]['pending'];assert one[1]['unresolved']==other[1]['unresolved'];assert one[2]==other[2]
    compare(other)
    print('Resume + crash-tail recovery: identical leaf bytes, chain, counters and frontier')
    if '--two-threads' in sys.argv:
        compare(run('two',100,threads=2));print('1 vs 2 workers: identical')
    else:print('2-worker execution not run (single-thread resource constraint)')
    p=call(['--max-depth','0','--seconds','2','--output',str(base/'depth0'),'--unresolved-list',str(base/'unresolved.jsonl')],check=True)
    assert json.loads(p.stdout)['unresolved']==1
    assert json.loads((base/'unresolved.jsonl').read_text())['bound']['L']==0
    # Strict outside boundaries and both adjacent inequalities, using dyadic endpoints.
    boxes=[]
    for u in [ [[.375,.5],[0,.25],[0,.5]], [[0,.5],[.375,.5],[0,.25]],
               [[.25,.5],[0,.25],[.25,.5]], [[0,.25],[.25,.5],[0,.25]],
               [[0,.5],[0,.5],[0,.5]], [[.25,.25],[.25,.25],[.25,.25]] ]:
        boxes.append([[0,0],[0,0],[0,0],*u])
    result=call(['--batch'],input=''.join(json.dumps({'box':b})+'\n' for b in boxes),check=True)
    rows=[json.loads(line) for line in result.stdout.splitlines()]
    assert [r['outside'] for r in rows]==[True,True,False,False,False,False]
    assert all(isinstance(r['L'],(int,float)) for r in rows)
    # Seed an isolated checkpoint fixture to exercise outside accounting and resume.
    run('outside',0)
    path=base/'outside/checkpoint.json'; fixture=json.loads(path.read_text())
    fixture['pending']=[{'box':b,'depth':4} for b in boxes[:2]]
    path.write_text(json.dumps(fixture))
    receipt, checkpoint, leaves=run('outside',100,True)
    assert receipt['leaves_by_rule']=={'bound':0,'outside':2,'unresolved':0}
    assert receipt['closed_volume_fraction']==.125
    assert leaves.count(b':outside::')==2 and receipt['lemma_counts']==[0]*6
    resumed=run('outside',100,True)
    assert resumed[0]['leaves_by_rule']==receipt['leaves_by_rule']
    assert resumed[0]['leaf_chain']==receipt['leaf_chain'] and resumed[2]==leaves
    print('Strict outside, ties, batch schema, outside receipt/volume/digest/resume: passed')
    if sys.platform=='darwin':
        for args in [['--threads','3'],['--seconds','1201'],['--server']]: assert call(args).returncode
        print('Mac guard: all three refusals passed')
    assert call(['--output','../escape','--seconds','1']).returncode
print('integration passed')
