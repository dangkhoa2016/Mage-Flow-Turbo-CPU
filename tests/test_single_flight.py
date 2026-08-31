import tempfile, threading, unittest
from pathlib import Path
from app.config import ServiceConfig
from app.service import ServiceState, BusyError
from app.backend import GenerationResult

class SingleFlightTests(unittest.TestCase):
    def test_second_generation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            c=ServiceConfig('/x','/d','/q','/v',str(Path(td)/'o'),str(Path(td)/'r'))
            started=threading.Event(); release=threading.Event(); background_errors=[]
            def slow(**kwargs):
                started.set(); release.wait(2)
                return GenerationResult(
                    request_id='x', profile=kwargs['profile'].name, seed=kwargs['seed'],
                    exit_code=0, elapsed_ms=1, peak_sd_cli_rss_kb=None,
                    minimum_mem_available_kb=None, artifact={'filename':'x.png'},
                    stdout_path='', stderr_path='')
            s=ServiceState(c, generator=slow, fake=True)
            def run_first():
                try: s.generate({'prompt':'x','seed':1})
                except Exception as exc: background_errors.append(exc)
            t=threading.Thread(target=run_first)
            t.start(); self.assertTrue(started.wait(1))
            with self.assertRaises(BusyError): s.generate({'prompt':'y','seed':2})
            release.set(); t.join(2)
            self.assertFalse(t.is_alive())
            self.assertEqual(background_errors,[])

if __name__=='__main__': unittest.main()
