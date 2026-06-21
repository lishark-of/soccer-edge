from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


STATIC_DIR = Path(__file__).resolve().parent / "static"


def run_dashboard_server(host: str = "127.0.0.1", port: int = 8766, api_base: str = "http://127.0.0.1:8765") -> None:
    class DashboardHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in {"", "/"}:
                self.path = "/index.html"
            return super().do_GET()

        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("X-API-Base", api_base)
            super().end_headers()

        def log_message(self, format: str, *args) -> None:
            return

    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"football-jc-analysis dashboard listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
