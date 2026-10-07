import unittest,tempfile,json,subprocess,sys
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from template_search import candidate_from_state,point_candidate
from unified_measure import validate

class ExactExportTest(unittest.TestCase):
    def test_coincident_orbits_exact_mass(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'state.npz'
            np.savez(p,L=4.,B=.9977,primitives_json=json.dumps([dict(kind='point',geometry=['2','2']),dict(kind='point',geometry=['1','1'])]),weights=[.7,1.3])
            c=candidate_from_state(p,3,'2.99999');d=point_candidate(c)
        self.assertEqual(validate(c)[4],F('2.99999'))
        self.assertEqual(sum(map(F,d['weights'])),F('2.99999'))
        self.assertEqual(len(d['sites']),5)
        self.assertEqual(F(d['weights'][d['sites'].index(['2','2'])]),F(7,20)*F('2.99999'))

    def test_fine_net_and_trimmed_metadata(self):
        from unified_measure import TRIMMED_SCHEMA
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'state.npz';net=dict(step='1/2500',last=1036);core=dict(kind='octagon_with_square_radial',margin='1/100000000')
            np.savez(p,L=4.,B=.9995,primitives_json=json.dumps([dict(kind='point',geometry=['2','2'])]),weights=[2.],net_json=json.dumps(net),core_json=json.dumps(core))
            c=candidate_from_state(p,3,'2.99999')
            self.assertEqual(c['schema'],TRIMMED_SCHEMA);self.assertEqual(c['net'],net);self.assertEqual(c['core'],core)
            np.savez(p,L=4.,B=.9995,primitives_json=json.dumps([dict(kind='point',geometry=['2','2'])]),weights=[2.])
            with self.assertRaises(ValueError):candidate_from_state(p,3,'2.99999')

    def test_exact_acceptance_and_counterexample_repair(self):
        root=Path(__file__).resolve().parents[2]
        for L,n,target,expected in [(1.5,2,'1.99','CERTIFIED'),(2.1,3,'2.99','SAVED_SEARCH_RESULT')]:
            with self.subTest(L=L),tempfile.TemporaryDirectory() as td:
                b=Path(td)
                np.savez(b/'seed.npz',L=L,B=.9977,primitives_json=json.dumps([dict(kind='point',geometry=[str(L/2)]*2)]),weights=[float(target)],poses=np.array([[L/2,L/2,0.]]),dual=np.zeros(1))
                cfg=dict(n=n,k=3,L=str(L),target=target,checkpoint='seed.npz',out='out',threshold_dir=str(root/'src/threshold_research'),code_dir=str(root/'runs/n82_n12_followup_20260927/n12/code'),research_dir=str(root/'src/rectangle_budget_optimization'),repair=dict(compare_grid=False,initial_pricing_rounds=0,max_screen_rows=8,repair_rounds=0))
                (b/'config.json').write_text(json.dumps(cfg))
                for repeat in range(2):
                    r=subprocess.run([sys.executable,str(root/'src/nagamochi_research/template_search.py'),'--config',str(b/'config.json')],capture_output=True,text=True,timeout=30)
                    self.assertEqual(r.returncode,0,r.stderr)
                    last=json.loads((b/'out/progress.json').read_text())['records'][-1]
                    self.assertEqual(last['status'],expected)
                if expected=='CERTIFIED':
                    self.assertEqual(json.loads((b/'out/proof.json').read_text())['directions_covered'],402)
                else:
                    self.assertEqual(last['search_status'],'BUDGET_EXHAUSTED')

if __name__=='__main__':unittest.main()
