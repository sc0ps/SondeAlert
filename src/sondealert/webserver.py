import json
import os
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from . import gps, config

logger = logging.getLogger("web")

WEB_DIR = "/app/src/sondealert/web"
DATA_DIR = "/app/data"

class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return  # Geen standaard logging naar stderr

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            # === GPS-data ===
            if path == "/gps.json":
                gps_data = gps.get_last_position()
                self._send_json(gps_data or {})
                return

            # === Nearest sonde ===
            elif path == "/nearest.json":
                self._serve_data_file("nearest.json", default="[]")
                return

            # === Alle sondes (nieuw) ===
            elif path == "/sondes.json":
                self._serve_data_file("sondes.json", default='{"items":[]}')
                return

            # === Settings JSON ===
            elif path == "/settings.json":
                settings = config.load_settings()
                self._send_json(settings)
                return

            # === HTML pagina’s ===
            elif path in ("/", "/index.html"):
                return self._serve_html("index.html")
            elif path == "/settings.html":
                return self._serve_html("settings.html")

            # === Onbekend pad ===
            else:
                self.send_error(404, "File not found")

        except Exception as e:
            logger.error(f"Webserver GET-fout: {e}", exc_info=True)
            self.send_error(500, "Internal server error")

    def _serve_data_file(self, filename, default="{}"):
        """Serve JSON-bestanden vanuit /app/data."""
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
        else:
            data = default
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data.encode())

    def _serve_html(self, filename):
        """Serve webpagina’s vanuit /app/src/sondealert/web."""
        path = os.path.join(WEB_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
        with open(path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, data):
        encoded = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/save_settings":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                settings = json.loads(raw.decode())
                config.save_settings(settings)
                self._send_json({"status": "ok"})
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            logger.error(f"POST-fout: {e}", exc_info=True)
            self.send_error(500, "Internal server error")


def start_server(settings):
    host = settings.get("BIND_HOST", "0.0.0.0")
    port = int(settings.get("BIND_PORT", 8080))
    server = ThreadingHTTPServer((host, port), WebHandler)
    logger.info(f"Webserver gestart op http://{host}:{port}/")
    server.serve_forever()
