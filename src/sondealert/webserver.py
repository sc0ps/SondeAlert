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
    def log_message(self, format, *args):
        # Geen standaard logging naar stderr
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            # === GPS-data ===
            if path == "/gps.json":
                gps_data = gps.get_last_position()
                data = json.dumps(gps_data or {}, indent=2).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
                return

            # === Nearest sonde JSON ===
            elif path == "/nearest.json":
                nearest_path = os.path.join(DATA_DIR, "nearest.json")
                if os.path.exists(nearest_path):
                    with open(nearest_path, "r") as f:
                        data = f.read().encode()
                else:
                    data = b"[]"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
                return

            # === Settings JSON ===
            elif path == "/settings.json":
                settings = config.load_settings()
                data = json.dumps(settings, indent=2).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
                return

            # === HTML pagina’s ===
            elif path in ("/", "/index.html"):
                return self.serve_file("index.html")
            elif path == "/settings.html":
                return self.serve_file("settings.html")

            # === Onbekend pad ===
            else:
                self.send_error(404, "File not found")

        except Exception as e:
            logger.error(f"Webserver-fout bij GET {path}: {e}", exc_info=True)
            self.send_error(500, "Internal server error")

    def serve_file(self, filename):
        path = os.path.join(WEB_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        if filename.endswith(".html"):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/save_settings":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                settings = json.loads(raw.decode())
                config.save_settings(settings)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Settings saved")
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            logger.error(f"Fout bij POST {path}: {e}", exc_info=True)
            self.send_error(500, "Internal server error")

def start_server(settings):
    host = settings.get("BIND_HOST", "0.0.0.0")
    port = int(settings.get("BIND_PORT", 8080))
    server = ThreadingHTTPServer((host, port), WebHandler)
    logger.info(f"Webserver gestart op http://{host}:{port}/")
    server.serve_forever()
