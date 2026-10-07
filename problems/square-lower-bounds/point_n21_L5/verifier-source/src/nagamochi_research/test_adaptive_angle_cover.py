from fractions import Fraction as F
from copy import deepcopy
import json
import pytest
from adaptive_angle_cover import run,verify
from near_axis_cover_family import prove


def test_adaptive_cover_and_tamper(tmp_path):
    q=run(F(4),F(1,100),F(0),tmp_path/'proof.json',True)
    assert F(q['mass'])<12 and verify(q)['upper']==11
    g=q['geometry'];coords=list(map(F,g['coordinates']));breaks=list(map(F,g['breaks']));B=F(g['B'])
    for (i,j),pattern in zip(g['faces'],g['patterns']):
        x=(breaks[i]+breaks[i+1])/2;y=(breaks[j]+breaks[j+1])/2
        direct=[a*len(coords)+b for a,u in enumerate(coords) for b,v in enumerate(coords)
                if abs(u-x)<B/2 and abs(v-y)<B/2]
        assert pattern==direct
    bad=deepcopy(q);bad['geometry']['faces'].pop()
    with pytest.raises(AssertionError):verify(bad)


def test_uniform_near_axis_family(tmp_path):
    t=F(1,1000);source=tmp_path/'seed.json'
    q=run(F(4),t,t*t/1000,source,True,t*t/100)
    result=prove(source,tmp_path/'family.json',F(1,10))
    assert F(result['mass'])==F(23,2) and result['upper']==11
    assert result['max_t']=='1/10' and result['excluded_cells']
    q['numerators'][0]=-1;source.write_text(json.dumps(q))
    with pytest.raises(AssertionError):prove(source,tmp_path/'bad.json')


def test_closed_partition_rejects_gap():
    from partition_angle_classes import complete_cover
    assert complete_cover([('1/10','1/5'),('1/5','21/50')],F(1,10),F(21,50))
    with pytest.raises(AssertionError):complete_cover([('1/10','1/5'),('201/1000','21/50')],F(1,10),F(21,50))
