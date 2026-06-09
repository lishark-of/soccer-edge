from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import webbrowser

LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the football-jc-analysis local read-only app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--api-port", type=int, default=8765)
    parser.add_argument("--dashboard-port", type=int, default=8766)
    parser.add_argument("--open-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host not in LOCAL_HOSTS:
        print("Refusing non-local host. Use 127.0.0.1 or localhost.")
        return 2
    for port in (args.api_port, args.dashboard_port):
        if not _port_available(args.host, port):
            print(f"Port {port} is already in use. Please stop the other service or choose another port.")
            return 2
    api_url = f"http://{args.host}:{args.api_port}"
    dashboard_url = f"http://{args.host}:{args.dashboard_port}"
    print("football-jc-analysis local app")
    print(f"API: {api_url}")
    print(f"Dashboard: {dashboard_url}")
    print("Mode: read-only local analysis")
    print("No betting/payment/order placement features are implemented.")
    api_proc = subprocess.Popen([sys.executable, "-m", "src.cli.serve_api", "--host", args.host, "--port", str(args.api_port)])
    dash_proc = None
    try:
        time.sleep(0.6)
        if api_proc.poll() is not None:
            print("API server exited during startup.")
            return 1
        dash_proc = subprocess.Popen(
            [sys.executable, "-m", "src.cli.serve_dashboard", "--host", args.host, "--port", str(args.dashboard_port), "--api-base", api_url]
        )
        time.sleep(0.6)
        if dash_proc.poll() is not None:
            print("Dashboard server exited during startup.")
            return 1
        if args.open_browser:
            webbrowser.open(dashboard_url)
        print("Press Ctrl-C to stop both local services.")
        while True:
            if api_proc.poll() is not None or dash_proc.poll() is not None:
                print("One local service stopped; shutting down the other.")
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping local app...")
        return 0
    finally:
        _terminate(api_proc)
        if dash_proc is not None:
            _terminate(dash_proc)


def _port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
