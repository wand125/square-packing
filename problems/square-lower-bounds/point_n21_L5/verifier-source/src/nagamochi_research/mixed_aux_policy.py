"""Conservative numerical recommendation; never promotes a bound or changes a job."""
import math

def choose_branch(normal,mixed):
    fields=('max_deficit','below_one','mean_deficit')
    a=normal['quality']['target_mass'];b=mixed['quality']['target_mass']
    if normal['quality']['target']!=mixed['quality']['target'] or normal['quality']['samples']!=mixed['quality']['samples']:
        raise ValueError('incomparable audits')
    if any(not math.isfinite(float(x[k])) or x[k]<0 for x in (a,b) for k in fields):
        raise ValueError('invalid quality metric')
    tolerance=dict(max_deficit=1e-8,below_one=0,mean_deficit=1e-10)
    safe=all(b[k]<=a[k]+tolerance[k] for k in fields)
    better=any(b[k]<a[k]-tolerance[k] for k in fields)
    budget=mixed['quality']['mass']<mixed['quality']['target']
    recommend=budget and safe and better
    return dict(recommended='auxiliary' if recommend else 'normal',
        reason='AUXILIARY_IMPROVES_WITHOUT_AUDIT_REGRESSION' if recommend else 'KEEP_NORMAL_TRADEOFF_OR_NO_CLEAR_GAIN',
        metrics=list(fields),tolerances=tolerance,auto_promote=False,certified=False)
