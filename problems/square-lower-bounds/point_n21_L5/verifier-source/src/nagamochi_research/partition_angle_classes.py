"""Adaptive closed-interval angle cover, with explicit pending domains."""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,time
from adaptive_angle_cover import run,verify


def complete_cover(intervals,lo,hi):
    cursor=F(lo)
    for a,b in sorted((F(a),F(b)) for a,b in intervals):
        assert a<=cursor and a<b,('gap',str(cursor),str(a))
        cursor=max(cursor,b)
    assert cursor>=F(hi),('uncovered end',str(cursor))
    return True


def run_partition(root,n,L,lo,hi,max_trials=160,max_depth=10):
    root.mkdir(parents=True,exist_ok=True);progress=root/'progress.json'
    if progress.exists():
        old=json.loads(progress.read_text())['records'][-1]
        assert old['n']==n and F(old['L'])==L and F(old['domain'][0])==lo and F(old['domain'][1])==hi
        queue=[(F(a),F(b),d) for a,b,d in old['pending']];done=old['covered'];unresolved=old['unresolved'];attempts=old['attempts']
    else:queue=[(lo,hi,0)];done=[];unresolved=[];attempts=[]
    start=time.monotonic()
    def save(status):
        state=dict(operation='angle_partition',status=status,n=n,L=str(L),domain=[str(lo),str(hi)],
                   pending=[[str(a),str(b),d] for a,b,d in queue],covered=done,unresolved=unresolved,
                   attempts=attempts,seconds_this_run=time.monotonic()-start)
        progress.write_text(json.dumps(dict(records=[state]),indent=2))
    save('RUNNING')
    for _ in range(max_trials):
        if not queue:break
        a,b,depth=queue[0];t=(a+b)/2;h=(b-a)/2;name=f'cell-{len(attempts):03}.json'
        result=run(L,t,h,root/name,True)
        item=dict(lo=str(a),hi=str(b),depth=depth,file=name,mass=result['mass']);attempts.append(item);queue.pop(0)
        if F(result['mass'])<n:done.append(item)
        elif depth>=max_depth:unresolved.append(item)
        else:queue.extend(((a,t,depth+1),(t,b,depth+1)))
        save('RUNNING')
    save('STOPPED_LOCAL_PROOF_REVIEW')
    print('PARTITION',n,len(done),len(queue),len(unresolved),len(attempts),flush=True)


def replay_partition(root,n,L,lo,hi):
    state=json.loads((root/'progress.json').read_text())['records'][-1]
    assert not state['pending'] and not state['unresolved']
    for item in state['covered']:
        q=json.loads((root/item['file']).read_text());r=verify(q);g=q['geometry']
        assert F(g['L'])==F(L) and r['mass']==item['mass']
        assert F(g['t'])-F(g['h'])==F(item['lo']) and F(g['t'])+F(g['h'])==F(item['hi'])
        assert F(r['mass'])<n
    complete_cover([(x['lo'],x['hi']) for x in state['covered']],lo,hi)
    return dict(status='EXACT_CLOSED_ANGLE_PARTITION_REPLAYED',n=n,lo=str(lo),hi=str(hi),cells=len(state['covered']))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--n',type=int,required=True)
    p.add_argument('--L',type=F,required=True);p.add_argument('--lo',type=F,required=True);p.add_argument('--hi',type=F,default=F(21,50))
    p.add_argument('--max-trials',type=int,default=160)
    a=p.parse_args();run_partition(a.root,a.n,a.L,a.lo,a.hi,a.max_trials)
