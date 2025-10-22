import os
import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from sondealert import config, gps, proximity, radiosondy

log = logging.getLogger("web")

BASE_WEB = os.path.join(os.path.dirname(__file__), "web")


class WebHandler(SimpleHTTPRequestHandler):
    """Behandelt HTTP-verzoeken voor de SondeAlert webinterface."""

    def log_message(self, format, *args):
        # Schrijf logregels naar standaard logger i.p.v. stdout
        log.info("%s - %s" % (self.client_address[0], format % args))

    def do_GET(self):
        path = urlparse(self.path).path
        log.info(f"GET {path}")

        if path == "/" or path == "/index.html":
            return self.serve_static("index.html")
        elif path == "/settings.html":
            return self.serve_static("settings.html")

        elif path == "/settings.json":
            settings = config.load_settings()
            return self.respond_json(settings)

        elif path == "/gps.json":
            lat, lon, fix = gps.get_last_position()
            return self.respond_json({"lat": lat, "lon": lon, "fix": fix})

        elif path == "/nearest.json":
            nearest = proximity.get_nearby_sondes()
            return self.respond_json(nearest)

        elif path == "/update_sondes":
            log.info("[web] Handmatige update van sondelijst gestart via webinterface.")
            radiosondy.async_update_sonde_list()
            return self.respond_json({"ok": True, "message": "Sonde list update started."})

        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        path = urlparse(self.path).path
        log.info(f"POST {path}")

        if path == "/save_settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            config.save_settings(data)
            self.respond_json({"ok": True, "message": "Settings saved."})
        else:
            self.send_error(404, "Endpoint not found")

    # ===== Helpers =====

    def serve_static(self, filename):
        """Serve static HTML files from /web directory."""
        file_path = os.path.join(BASE_WEB, filename)
        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def respond_json(self, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_web_server():
    """Start de HTTP webserver."""
    server = ThreadingHTTPServer(("0.0.0.0", 8080), WebHandler)
    log.info("[web] Webserver gestart op http://0.0.0.0:8080/")
    server.serve_forever()
