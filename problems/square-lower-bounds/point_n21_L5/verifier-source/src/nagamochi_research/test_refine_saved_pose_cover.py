from fractions import Fraction as F
import json
from full_pose_low_cover import run as initial,verify
from refine_saved_pose_cover import run


def test_refinement_and_resume_preserve_complete_partition(tmp_path):
    p=tmp_path/'candidate.json';p.write_text(json.dumps(dict(n=20,L='4',B='9/10',rectangles=[],points=[],total_mass='0')))
    src=tmp_path/'source.json';q=initial(p,src,F(4,5),3,'robust');q['symmetry']='D4';src.write_text(json.dumps(q))
    out=tmp_path/'refined.json';run(p,src,out,1)
    saved=json.loads(out.read_text());assert verify(p,saved)['leaves']==4
    assert verify(p,json.loads(out.with_suffix('.progress.json').read_text()))['leaves']==4
    run(p,src,out,1)
    assert json.loads(out.read_text())['leaves']==saved['leaves']
