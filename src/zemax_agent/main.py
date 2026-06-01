import json
import logging
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from zemax_agent.core import load_config, setup_logging, get_config

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self._json({"status": "ok", "zos": False, "qdrant": False, "python": True})
        elif self.path == "/api/health/zos":
            ok = self._check_zos()
            self._json({"connected": ok, "message": "OpticStudio COM ok" if ok else "OpticStudio not available"})
        elif self.path == "/api/health/qdrant":
            ok = self._check_qdrant()
            self._json({"connected": ok, "message": "Qdrant reachable" if ok else "Qdrant not available"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        if self.path == "/api/projects":
            self._json([])
        elif self.path == "/api/tasks":
            self._json([])
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _check_zos(self) -> bool:
        try:
            import clr
            clr.AddReference("ZOSAPI_NetHelper")
            import ZOSAPI_NetHelper
            path = ZOSAPI_NetHelper.ZOSAPI_NetHelper.GetZOSRootPath()
            return path is not None and path != ""
        except Exception:
            return False

    def _check_qdrant(self) -> bool:
        import urllib.request
        cfg = get_config()
        try:
            url = f"{cfg.storage.qdrant_url}/health"
            req = urllib.request.Request(url, method="GET")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            return False

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass


def run_health_server(port: int = 9876):
    server = HTTPServer(("127.0.0.1", port), HealthHandler)
    logger.info("Health API server started on http://127.0.0.1:%d", port)
    server.serve_forever()


def main():
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"

    config = load_config(str(config_path))
    logger = setup_logging(
        level=config.logging.level,
        log_file=config.logging.file,
        fmt=config.logging.format,
        datefmt=config.logging.date_format,
    )

    logger.info("Zemax Agent starting...")
    logger.info("LLM provider: %s, model: %s", config.llm.provider, config.llm.model)
    logger.info("ZOS connection mode: %s", config.zos.connection_mode)
    logger.info("Workspace: %s", config.project.workspace_dir)

    t = threading.Thread(target=run_health_server, args=(9876,), daemon=True)
    t.start()

    logger.info("Zemax Agent ready. Health API on http://127.0.0.1:9876")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Zemax Agent shutting down...")


if __name__ == "__main__":
    main()
