import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from core.db.database import get_db

# Logger for this module
logger = logging.getLogger(__name__)


# HTTP handler for healthcheck endpoint 
class _HealthHandler(BaseHTTPRequestHandler):
    server_version = "UberPolygonHealth/1.0"
    sys_version = ""

    # Override log_message to use standard logger
    def log_message(self, format: str, *args) -> None:
        # route logs through standard logger
        logger.info(format % args)

    # Write JSON response
    def _write_json(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Handle GET requests
    def do_GET(self):
        if self.path.startswith("/health"):
            # Minimal readiness/liveness: report env and DB connectivity
            status = {
                "status": "ok",
                "env": os.getenv("APP_ENV", "production"),
            }
            # Optional DB connectivity check
            try:
                conn = get_db()
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    _ = cur.fetchone()
                status["db"] = "ok"
            except Exception as e:
                logger.error(f"Health DB check failed: {e}")
                status["db"] = "error"
            self._write_json(200, status)
        else:
            self._write_json(404, {"status": "not_found"})


# Healthcheck server class
class HealthcheckServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    # Start the healthcheck server
    def start(self):
        if self._httpd:
            return
        self._httpd = HTTPServer((self.host, self.port), _HealthHandler)
        logger.info(f"Healthcheck server listening on {self.host}:{self.port}")
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    # Stop the healthcheck server
    def stop(self):
        if self._httpd:    
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None
            logger.info("Healthcheck server stopped")


# Start healthcheck server from environment variable
def start_healthcheck_from_env():
    """Start the healthcheck server if HEALTHCHECK_PORT is set."""
    port_str = os.getenv("HEALTHCHECK_PORT")
    if not port_str:
        return None
    try:
        port = int(port_str)
    except Exception:
        port = 8080
    server = HealthcheckServer(port=port)
    server.start()
    return server
