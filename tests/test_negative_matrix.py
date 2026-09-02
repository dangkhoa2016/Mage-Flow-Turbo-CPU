import copy, unittest
from app.contracts import baseline_contract_snapshot, validate_contract_snapshot

class NegativeMatrixTests(unittest.TestCase):
    def test_30_expected_failures(self):
        base=baseline_contract_snapshot()
        mutations=[]
        def m(name,fn): mutations.append((name,fn))
        m('1 q8 hash changed',lambda d:d['inputs']['dit'].__setitem__('sha256','bad'))
        m('2 qwen hash changed',lambda d:d['inputs']['qwen'].__setitem__('sha256','bad'))
        m('3 vae hash/default changed',lambda d:d['inputs']['vae'].__setitem__('variation','pytorch/default'))
        m('4 runtime commit changed',lambda d:d.__setitem__('runtime_commit','bad'))
        m('5 backend cuda',lambda d:d.__setitem__('backend','cuda'))
        m('6 bind 0.0.0.0',lambda d:d.__setitem__('host','0.0.0.0'))
        m('7 default profile',lambda d:d.__setitem__('default_profile','balanced'))
        m('8 demo non512',lambda d:d['profiles']['demo'].__setitem__('width',640))
        m('9 balanced non640',lambda d:d['profiles']['balanced'].__setitem__('width',512))
        m('10 research non1024',lambda d:d['profiles']['research'].__setitem__('width',768))
        m('11 steps',lambda d:d.__setitem__('steps',5))
        m('12 cfg',lambda d:d.__setitem__('cfg',2.0))
        m('13 threads',lambda d:d.__setitem__('threads',8))
        m('14 second real start',lambda d:d.__setitem__('real_acceptance_starts',2))
        m('15 artifact sha mismatch',lambda d:d.__setitem__('fetched_artifact_sha256','different'))
        m('16 model weight in evidence',lambda d:d['evidence_files'].append('oops.gguf'))
        m('17 absolute manifest',lambda d:d['manifest_paths'].append('/abs/file'))
        m('18 secret scan fail',lambda d:d.__setitem__('secret_scan_pass',False))
        m('19 token-named staged file',lambda d:d['evidence_files'].append('public/bearer-token'))
        m('20 stop evidence removed',lambda d:d.__setitem__('server_stop_pass',False))
        m('21 arbitrary width accepted',lambda d:d.__setitem__('explicit_resolution_accepted',True))
        m('22 notebook execution_count',lambda d:d.__setitem__('notebook_execution_count_null',False))
        m('23 notebook outputs',lambda d:d.__setitem__('notebook_outputs_empty',False))
        m('24 no English',lambda d:d.__setitem__('notebook_english',False))
        m('25 no Vietnamese',lambda d:d.__setitem__('notebook_vietnamese',False))
        m('26 pass without evidence',lambda d:(d.__setitem__('evidence_completed',False),d.__setitem__('overall_pass',True)))
        m('27 public pass no 401',lambda d:(d.__setitem__('public_state','PASS'),d.__setitem__('public_unauth_401',False)))
        m('28 tunnel to 8090',lambda d:(d.__setitem__('public_state','PASS'),d.__setitem__('public_tunnel_target','http://127.0.0.1:8090')))
        m('29 nonlocal upstream',lambda d:(d.__setitem__('public_state','PASS'),d.__setitem__('gateway_upstream','https://example.com')))
        m('30 public starts inference',lambda d:(d.__setitem__('public_state','PASS'),d.__setitem__('public_acceptance_generation_starts',1)))
        self.assertEqual(len(mutations),30)
        for name,fn in mutations:
            with self.subTest(name=name):
                d=copy.deepcopy(base); fn(d)
                self.assertTrue(validate_contract_snapshot(d),f'{name} unexpectedly passed')

if __name__=='__main__': unittest.main()
