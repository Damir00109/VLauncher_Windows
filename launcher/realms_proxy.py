import http.server
import socketserver
import threading
from typing import Callable, Optional
from urllib.parse import urlparse

from launcher.config import PROXY_PORT

_COMPATIBLE_PATHS = frozenset({
    "/client/compatible",
    "/realms/client/compatible",
    "/mco/client/compatible",
})
_COMPATIBLE_BODY = b"OUTDATED"


class RealmsProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if _is_compatible_check(self.path):
            self._respond_compatible()
            return
        self.send_error(404)

    def do_POST(self):
        if _is_compatible_check(self.path):
            self._respond_compatible()
            return
        self.send_error(404)

    def _respond_compatible(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(_COMPATIBLE_BODY)))
        self.end_headers()
        self.wfile.write(_COMPATIBLE_BODY)

    def log_message(self, fmt, *args):
        pass


def _is_compatible_check(path: str) -> bool:
    return urlparse(path).path in _COMPATIBLE_PATHS


def start_realms_proxy(log: Optional[Callable[[str], None]] = None) -> None:
    class _RealmsServer(socketserver.TCPServer):
        allow_reuse_address = True

    def _serve():
        try:
            server = _RealmsServer(("127.0.0.1", PROXY_PORT), RealmsProxyHandler)
            if log:
                log(f"[REALMS] Локальная затычка 127.0.0.1:{PROXY_PORT}")
            server.serve_forever()
        except OSError as exc:
            if log:
                log(f"[REALMS] Не удалось запустить прокси :{PROXY_PORT}: {exc}")
        except Exception as exc:
            if log:
                log(f"[REALMS] Прокси остановлен: {exc}")

    threading.Thread(target=_serve, daemon=True, name="realms-proxy").start()
