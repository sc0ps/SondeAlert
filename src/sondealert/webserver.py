import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .gps import get_last_position
from .proximity import get_nearby_sondes
from .config import load_settings, save_settings

log = logging.getLogger("web")

# De map waarin index.html en settings.html staan
WEB_DIR = Path(__file__).parent / "web"


class SondeAlertHandler(SimpleHTTPRequestHandler):
    """HTTP-server voor SondeAlert: kaart, instellingen, en API-endpoints."""

    def _set_headers(self, code=200, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        # -----------------------
        # JSON API ENDPOINTS
        # -----------------------
        if path == "/gps.json":
            lat, lon = get_last_position()
            self._set_headers()
            self.wfile.write(json.dumps({"lat": lat, "lon": lon}).encode())

        elif path == "/nearest.json":
            lat, lon = get_last_position()
            settings = load_settings()
            gps_data = {"lat": lat, "lon": lon}
            sondes = get_nearby_sondes(gps_data, settings)
            self._set_headers()
            self.wfile.write(json.dumps(sondes, indent=2).encode())

        elif path == "/settings.json":
            settings = load_settings()
            self._set_headers()
            self.wfile.write(json.dumps(settings, indent=2).encode())

        # -----------------------
        # HTML PAGINA'S
        # -----------------------
        elif path in ["/", "/index.html"]:
            self._serve_file("index.html")
        elif path in ["/settings", "/settings.html"]:
            self._serve_file("settings.html")

        # -----------------------
        # ONBEKEND PAD
        # -----------------------
        else:
            log.warning(f"404 - onbekende route: {self.path}")
            self.send_error(404, "File not found")

    def do_POST(self):
        """Verwerkt POST naar /settings.json voor bijwerken instellingen."""
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
        """Serveert een HTML-bestand uit de webmap."""
        filepath = WEB_DIR / filename
        if filepath.exists():
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(filepath.read_bytes())
        else:
            log.error(f"Bestand niet gevonden: {filepath}")
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


# Backwards compatibility met oude main.py
start_server = start_web_server
