"""Chunked job list for the leaf replay on the VM (pair x level x part), longest chunks first."""
import json, math, os
d = {}; [d.update(json.load(open(f'scan{k}.json'))) for k in (0, 1)]
RATE = {'B3D': 1.0, 'CORE1:Ty': 0.3, 'CORE1:y': 0.025, 'B3U:y': 0.12, 'B3T:y': 0.25, 'CORE': 0.004, 'CORE1:P': 0.2,
        'EDGE': 0.001, 'EMPTY': 0.0001}
base = 'inputs/indep_seam_inputs/seams'
jobs = []; tot = 0
for p in sorted(d):
    for rec, v in d[p].items():
        if rec == '_files':
            continue
        if rec.startswith('L'):
            lev = rec.split('/')[0]; fam = lev + '/fam_fix.json'
        else:
            lev = 'L0' if rec == 'merged.rec' else rec[:-4]
            fam = 'fam.json' if os.path.exists(f'{base}/{p}/fam.json') else 'fam_r1.json'
        assert os.path.exists(f'{base}/{p}/{fam}'), (p, fam)
        est = sum(RATE[k] * n for k, n in v['kinds'].items()); tot += est
        M = max(1, math.ceil(est / 3600))
        for K in range(M):
            jobs.append('\t'.join([p, lev, f'seams/{p}/{fam}', f'seams/{p}/{rec}', f'{K}/{M}', f'{p}__{lev}__{K}of{M}',
                                   str(round(est / M))]))
jobs.sort(key=lambda j: -int(j.split('\t')[-1]))
open('jobs.tsv', 'w').write('\n'.join(jobs) + '\n')
print(len(jobs), 'jobs, estimated', round(tot / 3600), 'CPU hours, largest chunk', jobs[0].split('\t')[-1], 's')
