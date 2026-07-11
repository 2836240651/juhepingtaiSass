"""本机 Agent 健康检查 HTTP 服务（供浏览器 no-cors 探测）。"""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return


def start_health_server(port: int) -> Callable[[], None]:
    server = HTTPServer(("127.0.0.1", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        server.shutdown()
        server.server_close()

    return stop
