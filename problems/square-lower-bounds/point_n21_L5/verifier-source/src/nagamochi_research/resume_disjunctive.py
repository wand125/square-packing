"""Resume a saved partial disjunction tree, replaying every reused proof."""
from saturated_joint_search import search_model,replay_model

EXACT={'EXACT_INFEASIBLE','EXACT_NO_SEPARATION_OPTION','EXACT_BRANCH_EXCLUDED','EXACT_NONPOSITIVE_COORDINATE'}


def resume_model(data,tree,node_limit,positive_index=None,certificate_solver=None):
    A,b,pairs,polys,angles=data;nodes=0;reused=0
    def visit(A,b,old):
        nonlocal nodes,reused
        current=(A,b,pairs,polys,angles)
        if old and old['status'] in EXACT:
            assert replay_model(current,old,positive_index=positive_index)
            reused+=1;return old
        if nodes>=node_limit:return old or dict(status='PENDING_NODE_LIMIT')
        if old and old['status']=='UNRESOLVED_BRANCH':
            p=old['pair'];assert type(p) is int and 0<=p<len(pairs)
            children=old['children'];assert len(children)<=len(pairs[p]['options'])
            result=[]
            for z,(row,rhs) in enumerate(pairs[p]['options']):
                child=visit(A+[row],b+[rhs],children[z] if z<len(children) else None);result.append(child)
                if child['status'] not in EXACT:return dict(status='UNRESOLVED_BRANCH',pair=p,children=result)
            return dict(status='EXACT_BRANCH_EXCLUDED',pair=p,children=result)
        r=search_model(current,node_limit-nodes,positive_index=positive_index,branch_rule='fewest',certificate_solver=certificate_solver)
        nodes+=r['nodes'];return r['tree']
    new=visit(A,b,tree)
    return dict(status=new['status'],tree=new,nodes=nodes,reused_subtrees=reused,
                verified=replay_model(data,new,positive_index=positive_index))
