import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from .utils import get_logger
from .gps import gps_data

logger = get_logger("web")

SETTINGS_FILE = "data/settings.json"
SONDES_FILE = "data/sondes.json"
HOST = "0.0.0.0"
PORT = 8080


class SondeHandler(BaseHTTPRequestHandler):
    """HTTP-handler voor SondeAlert."""

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
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
                self._set_headers(200, "text/html; charset=utf-8")
                lat = gps_data.get("lat")
                lon = gps_data.get("lon")

                html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="utf-8">
    <title>SondeAlert Webinterface</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 1.5em; background:#fafafa; color:#212121; }}
        h2 {{ color:#1565c0; }}
        a {{ text-decoration:none; color:#0d47a1; }}
        a:hover {{ text-decoration:underline; }}
        .card {{ background:white; padding:1em 1.5em; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); width:fit-content; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 SondeAlert Webinterface</h2>
        <p><b>Laatste GPS:</b> {lat}, {lon}</p>
        <p><a href="/nearest.json">📡 Toon sondelijst (JSON)</a></p>
        <p><a href="/settings">⚙️ Bekijk instellingen</a></p>
    </div>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))
                return

            # --- sondes.json ---
            elif path == "/nearest.json":
                self._set_headers(200)
                try:
                    with open(SONDES_FILE, "r", encoding="utf-8") as f:
                        sondes = json.load(f)
                    self.wfile.write(json.dumps(sondes, indent=2, ensure_ascii=False).encode("utf-8"))
                except FileNotFoundError:
                    self.wfile.write(b"[]")
                return

            # --- instellingen lezen ---
            elif path == "/settings":
                self._set_headers(200)
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                    self.wfile.write(json.dumps(settings, indent=2, ensure_ascii=False).encode("utf-8"))
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
        """Verwerk nieuwe instellingen via POST /settings"""
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/settings":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                new_settings = json.loads(body.decode("utf-8"))

                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_settings, f, indent=2, ensure_ascii=False)

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
    """Start de webserver op de opgegeven host en poort."""
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
