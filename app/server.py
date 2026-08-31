from __future__ import annotations
import argparse, json, os, signal
from pathlib import Path
from .config import ServiceConfig
from .service import build_server

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',required=True,help='JSON service configuration produced by preflight')
    ap.add_argument('--fake',action='store_true')
    args=ap.parse_args()
    data=json.loads(Path(args.config).read_text())
    config=ServiceConfig(**data)
    config.ensure_safe()
    server=build_server(config,fake=args.fake)
    def stop(signum,frame): server.state.shutting_down=True; raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    try: server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0
if __name__=='__main__': raise SystemExit(main())
