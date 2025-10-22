import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from .gps import get_last_position
from .proximity import get_nearby_sondes
from .config import load_settings, save_settings

logger = logging.getLogger("web")


class WebHandler(BaseHTTPRequestHandler):
    """HTTP-handler voor SondeAlert-webinterface."""

    def _set_headers(self, code=200, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        """Verwerkt GET-verzoeken (pagina’s en JSON-data)."""
        try:
            if self.path == "/gps.json":
                gps_data = get_last_position()
                self._set_headers()
                self.wfile.write(json.dumps(gps_data).encode("utf-8"))

            elif self.path == "/settings.json":
                settings = load_settings()
                self._set_headers()
                self.wfile.write(json.dumps(settings).encode("utf-8"))

            elif self.path == "/nearest.json":
                settings = load_settings()
                gps_data = get_last_position()
                sondes = get_nearby_sondes(gps_data, settings)
                self._set_headers()
                self.wfile.write(json.dumps(sondes).encode("utf-8"))

            elif self.path == "/" or self.path == "/index.html":
                self._serve_html("/app/src/sondealert/web/index.html")

            elif self.path == "/settings.html":
                self._serve_html("/app/src/sondealert/web/settings.html")

            else:
                self.send_error(404, "File not found")

        except Exception as e:
            logger.error(f"Error handling GET {self.path}: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")

    def do_POST(self):
        """Verwerkt POST-verzoeken (voor instellingen)."""
        try:
            if self.path == "/save_settings":
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                data = json.loads(body.decode("utf-8"))
                save_settings(data)
                self._set_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            else:
                self.send_error(404, "Endpoint not found")

        except Exception as e:
            logger.error(f"Error handling POST {self.path}: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")

    def _serve_html(self, path):
        """Serveert HTML-bestanden vanaf de opgegeven locatie."""
        try:
            with open(path, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"HTML file not found: {path}")
        except Exception as e:
            logger.error(f"Error serving HTML file {path}: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")


def start_server(settings):
    """Start de ingebouwde HTTP-server."""
    try:
        host = settings.get("BIND_HOST", "0.0.0.0")
        port = settings.get("BIND_PORT", 8080)
        server = HTTPServer((host, port), WebHandler)
        logger.info(f"Webserver gestart op http://{host}:{port}/")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Webserver kon niet worden gestart: {e}", exc_info=True)
