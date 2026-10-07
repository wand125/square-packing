import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from gmpy2 import mpq

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from q3 import Q3  # noqa: E402
import sweep  # noqa: E402


def test_q3_sign():
    assert Q3(0).sign() == 0
    assert Q3(2, -1).sign() == 1          # 2 - sqrt3 > 0
    assert Q3(-2, 1).sign() == -1
    assert Q3(1, -1).sign() == -1         # 1 - sqrt3 < 0
    assert Q3(mpq(173205, 100000), -1).sign() == -1
    assert Q3(mpq(173206, 100000), -1).sign() == 1
    assert (Q3(1, 1) * Q3(1, -1)) == Q3(-2)
    assert Q3.parse('3/2+1*sqrt3') == Q3(mpq(3, 2), 1)
    assert Q3.parse('0+1/2*sqrt3') == Q3(0, mpq(1, 2))
    assert Q3.parse('-1/2*sqrt3') == Q3(0, mpq(-1, 2))


def test_sample_points_cover_every_gap():
    ivs = [(Fraction(0), Fraction(0)), (Fraction(1, 10), Fraction(1, 5)), (Fraction(1, 2), Fraction(1, 2))]
    s = sweep.sample_points(ivs)
    assert len(s) == 3
    assert 0 < s[0] < Fraction(1, 10) and Fraction(1, 5) < s[1] < Fraction(1, 2) and Fraction(1, 2) < s[2] < 1


def run(tmp_path, cert):
    p = tmp_path / 'c.json'
    p.write_text(json.dumps(cert))
    out = tmp_path / 'o.json'
    code = sweep.main([str(p), '--out', str(out)])
    return code, json.loads(out.read_text())


N2 = {"L": "2+2/3*sqrt3", "points": [{"x": "1+1/3*sqrt3", "y": "1/3+1/3*sqrt3", "w": "1"}]}


def test_n2_verified(tmp_path):
    code, s = run(tmp_path, N2)
    assert code == 0 and s['status'] == 'verified' and s['min_capture_weight'] == '1'


@pytest.mark.parametrize('cert', [
    {"L": "201/100+2/3*sqrt3", "points": [{"x": "201/200+1/3*sqrt3", "y": "1/3+67/200*sqrt3", "w": "1"}]},
    {"L": "2+2/3*sqrt3", "points": [{"x": "51/50+1/3*sqrt3", "y": "1/3+1/3*sqrt3", "w": "1"}]},
    {"L": "2+2/3*sqrt3", "points": [{"x": "1+1/3*sqrt3", "y": "1/3+1/3*sqrt3", "w": "99/100"}]},
])
def test_n2_negative_controls_fail_with_explicit_pose(tmp_path, cert):
    code, s = run(tmp_path, cert)
    assert code == 1 and s['status'] == 'failed'
    c = s['counterexample']
    assert c and c['admissible'] and Fraction(c['captured_weight']) < 1
