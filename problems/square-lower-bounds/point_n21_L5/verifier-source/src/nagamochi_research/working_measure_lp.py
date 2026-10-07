"""Finite measure LP with row generation and a full primal/dual check."""
import time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix


def solve(A, hint, seed_count=256, batch=256):
    start=time.perf_counter()
    ids=set(map(int,np.argsort(A@hint)[:seed_count]));history=[]
    for iteration in range(20):
        selected=np.array(sorted(ids),dtype=int)
        fit=linprog(np.ones(A.shape[1]),A_ub=-csr_matrix(A[selected]),b_ub=-np.ones(len(selected)),
                    bounds=(0,None),method='highs-ipm',options={'time_limit':45})
        if not fit.success:raise RuntimeError(fit.message)
        w=np.maximum(fit.x,0);scores=A@w
        bad=np.flatnonzero(scores<1-1e-7)
        history.append(dict(iteration=iteration,rows=len(selected),mass=float(sum(w)),violations=len(bad)))
        if not len(bad):
            dual=-fit.ineqlin.marginals
            loads=A[selected].T@dual
            if not np.all(np.isfinite(w)) or not np.all(np.isfinite(dual)):raise ValueError('Nonfinite LP')
            if min(dual)<-1e-7 or max(loads)>1+1e-7:raise ValueError('Dual residual failed')
            if abs(sum(w)-sum(dual))>1e-5:raise ValueError('Gap failed')
            return w,dict(status='FULL_FINITE_PRIMAL_DUAL_CHECKED',seconds=time.perf_counter()-start,
                          mass=float(sum(w)),full_rows=len(A),working_rows=len(selected),
                          minimum=float(min(scores)),dual_maximum=float(max(loads)),
                          gap=float(sum(w)-sum(dual)),history=history,
                          dual_rows=[int(selected[i]) for i in np.flatnonzero(dual>1e-9)],
                          dual_weights=[float(dual[i]) for i in np.flatnonzero(dual>1e-9)],
                          general_packing_exclusion=False)
        additions=[int(i) for i in bad[np.argsort(scores[bad])] if int(i) not in ids][:batch]
        if not additions:raise ValueError('Working constraints violate primal tolerance')
        ids.update(additions)
    raise RuntimeError('Row-generation limit; no accepted result')
