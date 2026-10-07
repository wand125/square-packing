from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
import mixed_neighbor_search as module
from mixed_density_check import expand, evaluate
from mixed_net_audit import centre_domains


def test_neighbor_rows_are_exact_and_inside_unit_centre_domains():
    data = dict(n=21, L='4', B='9/10', rectangles=[dict(rectangle=['0','0','4','4'], mass='1')], points=[], total_mass='1')
    model = expand(data)
    seed = evaluate(model, F(3), F(5,2), F(199)*F(83,40000))
    rows, records = module.search(data, model, [seed], max_searches=3)
    assert len(records) == 3 and rows
    assert records[0]['index'] == 200  # Folded endpoint must preserve the domain.
    domains = {d['index']: d for d in centre_domains(F(4), F('0.9'))}
    for row in rows:
        assert F(row['score']) < 1
        assert evaluate(model, *(F(row[k]) for k in ('cx','cy','t')))['score'] == row['score']
        high = F(domains[int(row['origin'].split(':')[-1])]['centre_high'])
        assert all(F(2) <= F(row[k]) <= high for k in ('cx','cy'))


def test_numerical_deficit_cannot_admit_an_exact_nondeficit(monkeypatch):
    data = dict(n=100, L='4', B='9/10', rectangles=[dict(rectangle=['0','0','4','4'], mass='40')], points=[], total_mass='40')
    model = expand(data)
    seed = dict(cx='3', cy='3', t='0', score='0')
    monkeypatch.setattr(module, 'minimize', lambda fun, z, **kw: SimpleNamespace(x=np.array(z), fun=0.))
    rows, records = module.search(data, model, [seed], max_searches=2)
    assert records and all(r['numerical_min'] == 0 for r in records)
    assert rows == []
