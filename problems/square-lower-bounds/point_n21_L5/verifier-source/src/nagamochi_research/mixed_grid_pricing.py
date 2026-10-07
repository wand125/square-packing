"""Bounded grid-first pricing of nonnegative, unit-mass D4 primitives.

Prices use every positive dual row. These floating-point prices only select
columns; the native verifier remains responsible for accepting certificates.
"""
from fractions import Fraction as F
import time
import numpy as np
from unified_measure import primitive_key

KINDS = ('point', 'segment', 'rectangle', 'disk', 'bump', 'annulus')


def refinement_pool(L, primitives, weights, per_kind=128, seed=20260927):
    """Perturb active geometry at several scales without imposing a grid."""
    L=float(L); rng=np.random.default_rng(seed)
    seen={primitive_key(p['kind'],p['geometry'],F(str(L))) for p in primitives}
    groups={kind:[] for kind in KINDS}
    for kind in KINDS:
        ids=[i for i in np.argsort(-np.asarray(weights),kind='stable') if primitives[i]['kind']==kind and weights[i]>1e-10][:32]
        for i in ids:
            g=np.array(list(map(lambda x:float(F(x)),primitives[i]['geometry'])))
            for j in range(48):
                h=g.copy(); scale=(.0005,.002,.01,.04,.15,.35)[j%6]
                shift=rng.normal(size=2)*scale
                if kind in ('point','disk','bump','annulus'):
                    h[:2]+=shift
                    if kind!='point':h[2]*=np.exp(rng.normal()*.35)
                    if kind=='annulus':h[3]=np.clip(h[3]+rng.normal()*.03,0.,.995)
                else:
                    centre=(h[:2]+h[2:])/2+shift; delta=(h[2:]-h[:2])/2
                    delta*=np.exp(rng.normal(size=2)*.35)
                    h=np.r_[centre-delta,centre+delta]
                coords=h[:2] if kind in ('point','disk','bump','annulus') else h
                if min(coords)<.0001 or max(coords)>L-.0001:continue
                if kind=='rectangle' and min(h[2:]-h[:2])<.0001:continue
                if kind in ('disk','bump','annulus') and not .0005<h[2]<L/2:continue
                geom=[format(x,'.13g') for x in h]
                key=primitive_key(kind,geom,F(str(L)))
                if key not in seen:
                    seen.add(key);groups[kind].append(dict(kind=kind,geometry=geom,family='refinement'))
    result=[]
    for group in groups.values():
        if len(group)>per_kind:group=[group[i] for i in np.sort(rng.choice(len(group),per_kind,replace=False))]
        result.extend(group)
    return result


def candidate_pool(L, k, primitives, weights, *, per_kind=64, seed=20260927,
                   grid_fraction=0.375):
    L = F(str(L))
    if not 3 <= k <= 100 or not 4 <= per_kind <= 1024:
        raise ValueError('invalid grid order or candidate budget')
    if len(primitives) != len(weights) or np.any(np.asarray(weights) < 0):
        raise ValueError('invalid weights')
    if not 0 <= grid_fraction <= 1:
        raise ValueError('invalid grid fraction')
    seen = {primitive_key(p['kind'], p['geometry'], L) for p in primitives}
    groups = {(family, kind): [] for family in ('grid', 'general', 'offgrid') for kind in KINDS}
    margin = F(1, 1000)

    def add(kind, g, family):
        # Keep radial supports inside the board in this bounded seed generator.
        if kind in ('disk', 'bump', 'annulus'):
            x, y, r = g[:3]
            if not margin < min(x-r, y-r) or max(x+r, y+r) >= L-margin:
                return
        elif not all(margin < z < L-margin for z in g):
            return
        key = primitive_key(kind, g, L)
        if key not in seen:
            seen.add(key)
            groups[family, kind].append(dict(kind=kind, geometry=list(map(str, g)), family=family))

    def site(x, y, family):
        add('point', (x, y), family)
        for h in (L/k/8, L/k/3):
            for dx, dy in ((h, F(0)), (h/2, h/2)):
                add('segment', (x-dx, y-dy, x+dx, y+dy), family)
            for w in (F(1, 500), F(1, 50)):
                add('rectangle', (x-w, y-h, x+w, y+h), family)
        for r in (F(3, 100), L/k/8, L/k/3):
            add('disk', (x, y, r), family)
            add('bump', (x, y, r), family)
            add('annulus', (x, y, r, F(9, 10)), family)

    for lines in ([L*j/k for j in range(1, k)],
                  [1+j*(L-2)/(k-2) for j in range(k-1)]):
        for x in lines:
            if x > L/2: continue
            for y in lines:
                if y <= L/2: site(x, y, 'grid')
    for i in np.argsort(-np.asarray(weights), kind='stable')[:32]:
        if weights[i] <= 0: continue
        p = primitives[i]; g = list(map(F, p['geometry']))
        x, y = ((g[0]+g[2])/2, (g[1]+g[3])/2) if p['kind'] in ('segment', 'rectangle') else g[:2]
        site(x, y, 'offgrid')
    # Deterministic low-discrepancy centres cover the board without a lattice.
    from scipy.stats import qmc
    for u, v in qmc.Halton(2, scramble=True, seed=seed).random(max(64, per_kind)):
        site(F(str(float(u)))*L/2, F(str(float(v)))*L/2, 'general')
    rng = np.random.default_rng(seed); pool = []
    for kind in KINDS:
        # Reserve a quarter of each type's budget for inherited off-grid sites.
        off = groups['offgrid', kind]; grid = groups['grid', kind]; general = groups['general', kind]
        noff = min(len(off), per_kind//4)
        ngrid = min(len(grid), round((per_kind-noff)*grid_fraction))
        ngeneral = min(len(general), per_kind-noff-ngrid)
        for group, count in ((grid, ngrid), (general, ngeneral), (off, noff)):
            ids = np.sort(rng.choice(len(group), count, replace=False)) if len(group) > count else range(len(group))
            pool.extend(group[int(i)] for i in ids)
    return pool


def propose_mixed_grid(poses, dual, L, B, primitives, weights, *, k,
                       max_columns=32, per_kind=64, seed=20260927, batch_size=16,
                       grid_fraction=0.375, refinement_per_kind=0):
    from unified_geometry import expand_primitives, matrix
    started = time.perf_counter()
    poses = np.asarray(poses, float); dual = np.asarray(dual, float)
    if poses.shape != (len(dual), 3) or not np.all(np.isfinite(dual)) or np.any(dual < 0):
        raise ValueError('invalid poses/dual')
    if max_columns < len(KINDS) or batch_size < 1:
        raise ValueError('invalid pricing budget')
    pool = candidate_pool(L, k, primitives, weights, per_kind=per_kind, seed=seed,
                          grid_fraction=grid_fraction)
    if refinement_per_kind:
        if not 1<=refinement_per_kind<=2048:raise ValueError('invalid refinement budget')
        seen={primitive_key(p['kind'],p['geometry'],L) for p in pool}
        for p in refinement_pool(L,primitives,weights,refinement_per_kind,seed):
            key=primitive_key(p['kind'],p['geometry'],L)
            if key not in seen:seen.add(key);pool.append(p)
    positive = np.flatnonzero(dual > 0); prices = np.zeros(len(pool))
    for j in range(0, len(pool), batch_size):
        expanded = expand_primitives(pool[j:j+batch_size], L)
        for start in range(0, len(positive), 256):
            ids = positive[start:start+256]
            prices[j:j+batch_size] += matrix(poses[ids], float(B), expanded).T @ dual[ids]
    ranking = [int(i) for i in np.argsort(-prices, kind='stable') if prices[i] > 1+1e-6]
    selected = []
    # One improving column per type, then compete on price with a common budget.
    for kind in KINDS:
        first = next((i for i in ranking if pool[i]['kind'] == kind), None)
        if first is not None: selected.append(first)
    selected += [i for i in ranking if i not in selected][:max_columns-len(selected)]
    columns = [pool[i] for i in selected]
    return columns, dict(status='HEURISTIC_PRICING', method='mixed_initial_pricing',
        pool_count=len(pool), positive_rows=len(positive), columns=len(columns),
        grid_fraction=grid_fraction,
        selected_families={family: sum(p['family']==family for p in columns) for family in ('grid','general','offgrid','refinement')},
        candidate_counts={kind: sum(p['kind']==kind for p in pool) for kind in KINDS},
        selected_counts={kind: sum(p['kind']==kind for p in columns) for kind in KINDS},
        selected_scores=[float(prices[i]) for i in selected],
        seconds=time.perf_counter()-started, certified=False)


def initial_state(L, B=0.9977, rhs=1.001):
    """Feasible numerical bootstrap with a uniform board and 1,701 poses.

    This is a starting dictionary, not a sub-N certificate. Its sole weight is
    the exact uniform coverage cost in real arithmetic (float here for search).
    """
    L = float(L); B = float(B)
    if not 0 < B < 1 < L: raise ValueError('invalid geometry')
    poses = []
    for t in np.linspace(0, 0.415, 21):
        c = (1-t*t)/(1+t*t); s = 2*t/(1+t*t)
        extent = (L-B*(c+s))/2
        for u in np.linspace(-1, 1, 9):
            for v in np.linspace(-1, 1, 9):
                poses.append([L/2+u*extent, L/2+v*extent, t])
    primitives = [dict(kind='rectangle', geometry=['0','0',str(L),str(L)], family='uniform_bootstrap')]
    return primitives, np.asarray(poses), np.array([rhs*(L/B)**2]), np.zeros(len(poses))


def screening_poses(L, B=0.9977, count=4096, seed=20260928, boundary_fraction=0.):
    from scipy.stats import qmc
    if not 0 <= boundary_fraction <= 1:raise ValueError('invalid boundary fraction')
    q = qmc.Halton(3, scramble=True, seed=seed).random(count)
    boundary_count=int(count*boundary_fraction)
    for i in range(boundary_count):
        # Include walls and endpoint angles, not only generic interior poses.
        if i%3==2:q[i,2]=float((i//3)%2)
        else:q[i,i%3]=float((i//3)%2)
    t = q[:, 2]*(2**.5-1); c = (1-t*t)/(1+t*t); s = 2*t/(1+t*t)
    extent = (float(L)-float(B)*(c+s))/2
    return np.column_stack((float(L)/2+(2*q[:, 0]-1)*extent,
                            float(L)/2+(2*q[:, 1]-1)*extent, t))


def quality_metrics(values, mass, target):
    """Report holes at the requested budget as well as at the saved mass."""
    values=np.asarray(values,float)
    if not len(values) or not np.all(np.isfinite(values)) or mass<=0 or target<=0:
        raise ValueError('invalid quality inputs')
    normalized=values*float(target)/float(mass)
    def metrics(v):
        deficit=np.maximum(1-v,0.)
        return dict(minimum=float(v.min()),below_one=int(np.count_nonzero(v<1)),
                    hole_fraction=float(np.mean(v<1)),mean_deficit=float(deficit.mean()),
                    max_deficit=float(deficit.max()))
    return dict(samples=len(values),mass=float(mass),target=float(target),
                saved_mass=metrics(values),target_mass=metrics(normalized),globally_verified=False)


def refine_witnesses(poses, values, L, B, score, starts=32):
    """Numerically descend in centre/angle from weak training poses only."""
    if starts<1:raise ValueError('positive witness starts required')
    ids=np.argsort(values,kind='stable')[:starts];p=np.asarray(poses)[ids].copy()
    tmax=2**.5-1;t=p[:,2];extent=(float(L)-float(B)*((1-t*t+2*t)/(1+t*t)))/2
    q=np.column_stack(((p[:,:2]-float(L)/2)/extent[:,None],2*t/tmax-1))
    def physical(z):
        t=tmax*(z[:,2]+1)/2;e=(float(L)-float(B)*((1-t*t+2*t)/(1+t*t)))/2
        return np.column_stack((float(L)/2+z[:,:2]*e[:,None],t))
    directions=np.vstack((np.zeros((1,3)),np.eye(3),-np.eye(3)))
    for delta in (.03,.01,.003,.001,.0003,.0001):
        trial=np.clip(q[:,None,:]+delta*directions[None,:,:],-1,1)
        scores=np.asarray(score(physical(trial.reshape(-1,3)))).reshape(len(q),7)
        q=trial[np.arange(len(q)),np.argmin(scores,axis=1)]
    result=physical(q)
    return result,np.asarray(score(result))
