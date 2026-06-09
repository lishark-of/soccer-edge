from __future__ import annotations

import argparse

from src.api.server import run_api_server


LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local read-only football-jc-analysis API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host not in LOCAL_HOSTS:
        print("Refusing non-local host in read-only local mode. Use 127.0.0.1 or localhost.")
        return 2
    run_api_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
