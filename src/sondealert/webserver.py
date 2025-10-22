import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .gps import get_last_position
from .proximity import get_nearby_sondes
from .config import load_settings, save_settings

logger = logging.getLogger("web")

WEB_DIR = Path(__file__).parent / "web"


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            return self.serve_file("index.html")
        elif self.path == "/settings.html":
            return self.serve_file("settings.html")
        elif self.path == "/settings.json":
            return self.serve_json(load_settings())
        elif self.path == "/gps.json":
            gps_data = get_last_position()
            return self.serve_json(gps_data)
        elif self.path == "/nearest.json":
            gps_data = get_last_position()
            settings = load_settings()
            sondes = get_nearby_sondes(gps_data, settings)
            return self.serve_json(sondes)
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == "/save_settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                save_settings(data)
                logger.info("Instellingen opgeslagen via webinterface.")
                self.serve_json({"status": "ok"})
            except Exception as e:
                logger.error(f"Fout bij opslaan instellingen: {e}")
                self.serve_json({"status": "error", "message": str(e)})
        else:
            self.send_error(404, "Endpoint not found")

    # ---------- Hulpmethodes ----------
    def serve_file(self, filename: str):
        filepath = WEB_DIR / filename
        if not filepath.exists():
            self.send_error(404, "File not found")
            return
        content = filepath.read_bytes()
        if filename.endswith(".html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content)
        elif filename.endswith(".json"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(content)

    def serve_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def start_server(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), RequestHandler)
    logger.info(f"Webserver gestart op http://{host}:{port}/")
    server.serve_forever()
