import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .gps import get_last_position
from .proximity import get_nearby_sondes
from .config import load_settings, save_settings

log = logging.getLogger("web")

WEB_DIR = Path(__file__).parent / "web"  # map met index.html en settings.html


class SondeAlertHandler(SimpleHTTPRequestHandler):
    def _set_headers(self, code=200, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        if self.path == "/gps.json":
            lat, lon = get_last_position()
            self._set_headers()
            self.wfile.write(json.dumps({"lat": lat, "lon": lon}).encode())

        elif self.path == "/nearest.json":
            sondes = get_nearby_sondes()
            self._set_headers()
            self.wfile.write(json.dumps(sondes).encode())

        elif self.path == "/settings.json":
            settings = load_settings()
            self._set_headers()
            self.wfile.write(json.dumps(settings, indent=2).encode())

        elif self.path in ["/", "/index.html"]:
            self._serve_file("index.html")
        elif self.path == "/settings":
            self._serve_file("settings.html")
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        """Sla nieuwe instellingen op via POST naar /settings.json"""
        if self.path == "/settings.json":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                save_settings(data)
                self._set_headers(200)
                self.wfile.write(b'{"status":"ok"}')
                log.info("Instellingen bijgewerkt via webinterface.")
            except Exception as e:
                log.error(f"Fout bij POST /settings.json: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_error(404, "File not found")

    def _serve_file(self, filename):
        """Laad een HTML-bestand uit de webmap."""
        filepath = WEB_DIR / filename
        if filepath.exists():
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(filepath.read_bytes())
        else:
            self.send_error(404, f"{filename} niet gevonden")


def start_web_server(host="0.0.0.0", port=8080):
    """Start de webserver in een aparte thread."""
    server = ThreadingHTTPServer((host, port), SondeAlertHandler)
    log.info(f"Webserver gestart op http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        log.info("Webserver gestopt.")


# Backwards compatibility: sommige versies roepen start_server() aan
start_server = start_web_server
