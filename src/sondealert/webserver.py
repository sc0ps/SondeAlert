import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from .gps import get_last_position
from .proximity import get_nearby_sondes
from .config import SETTINGS_FILE, load_settings, save_settings

log = logging.getLogger("web")

WEB_DIR = Path(__file__).parent / "web"

class SondeAlertHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _serve_file(self, filename: str):
        file_path = WEB_DIR / filename
        if file_path.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self.send_error(404, "File not found")

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ["/", "/index.html"]:
            self._serve_file("index.html")

        elif path == "/settings.html":
            self._serve_file("settings.html")

        elif path == "/gps.json":
            lat, lon = get_last_position()
            self._send_json({"lat": lat, "lon": lon})

        elif path == "/nearest.json":
            nearby = get_nearby_sondes()
            self._send_json(nearby)

        elif path == "/settings.json":
            settings = load_settings()
            self._send_json(settings)

        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == "/save_settings":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw)
                save_settings(data)
                self._send_json({"status": "ok", "saved": data})
                log.info("Instellingen bijgewerkt via webinterface.")
            except Exception as e:
                log.error(f"Fout bij opslaan instellingen: {e}")
                self._send_json({"error": str(e)}, code=500)
        else:
            self.send_error(404, "Onbekende POST-route")


def start_webserver(bind_host, bind_port):
    server = HTTPServer((bind_host, bind_port), SondeAlertHandler)
    log.info(f"Webserver gestart op http://{bind_host}:{bind_port}/")
    Thread(target=server.serve_forever, daemon=True).start()
