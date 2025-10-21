import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from .utils import state_lock, get_logger
from .gps import gps_data

logger = get_logger("web")

SETTINGS_FILE = "data/settings.json"
SONDES_FILE = "data/sondes.json"
HOST = "0.0.0.0"
PORT = 8080


class SondeHandler(BaseHTTPRequestHandler):
    """Eenvoudige HTTP-handler voor SondeAlert."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()

    # === GET-requests ===
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            # --- hoofdpagina ---
            if path in ["/", "/index.html"]:
                self._set_headers(200, "text/html")
                lat = gps_data.get("lat")
                lon = gps_data.get("lon")
                html = f"""
                <html>
                <head><title>SondeAlert Dashboard</title></head>
                <body>
                    <h2>🚀 SondeAlert Webinterface</h2>
                    <p><b>Laatste GPS:</b> {lat}, {lon}</p>
                    <p><a href='/nearest.json'>📡 Toon sondelijst (JSON)</a></p>
                    <p><a href='/settings'>⚙️ Bekijk instellingen</a></p>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            # --- sondes.json ---
            elif path == "/nearest.json":
                self._set_headers(200)
                try:
                    with open(SONDES_FILE, "r", encoding="utf-8") as f:
                        sondes = json.load(f)
                    self.wfile.write(json.dumps(sondes, indent=2).encode("utf-8"))
                except FileNotFoundError:
                    self.wfile.write(b"[]")
                return

            # --- instellingen lezen ---
            elif path == "/settings":
                self._set_headers(200)
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                    self.wfile.write(json.dumps(settings, indent=2).encode("utf-8"))
                except FileNotFoundError:
                    self.wfile.write(b"{}")
                return

            # --- onbekende route ---
            else:
                self._set_headers(404)
                self.wfile.write(b'{"error":"Not Found"}')

        except Exception as e:
            logger.exception("Fout bij GET: %s", e)
            self._set_headers(500)
            self.wfile.write(b'{"error":"Internal Server Error"}')

    # === POST-requests ===
    def do_POST(self):
        """Ontvang nieuwe instellingen via POST /settings"""
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/settings":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                new_settings = json.loads(body.decode("utf-8"))

                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_settings, f, indent=2)

                logger.info("Instellingen bijgewerkt via webinterface: %s", new_settings)
                self._set_headers(200)
                self.wfile.write(b'{"status":"OK"}')
            else:
                self._set_headers(404)
                self.wfile.write(b'{"error":"Not Found"}')

        except Exception as e:
            logger.exception("Fout bij POST: %s", e)
            self._set_headers(500)
            self.wfile.write(b'{"error":"Internal Server Error"}')


def start_server(host=HOST, port=PORT):
    """Start de webserver en blijf luisteren tot afsluiting."""
    server = HTTPServer((host, port), SondeHandler)
    logger.info("Webserver gestart op http://%s:%d/", host, port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.warning("Webserver gestopt (Ctrl+C).")
    except Exception as e:
        logger.exception("Fout in webserver: %s", e)
    finally:
        server.server_close()
        logger.info("Webserver afgesloten.")
