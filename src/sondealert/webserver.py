import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from .gps import gps_data
from .proximity import get_nearby_sondes
from .utils import get_logger

logger = get_logger("web")

SETTINGS_FILE = Path("/app/data/settings.json")

# Standaardinstellingen
DEFAULT_SETTINGS = {
    "NEAR_THRESHOLD_M": 15000,
    "ALT_MAX_M": 600,
    "UPDATE_HOURS": 24,
    "BUZZER_ENABLED": False
}


def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=2))
        return DEFAULT_SETTINGS


def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


settings = load_settings()


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            self.serve_file("/app/src/sondealert/templates/index.html", "text/html")
        elif parsed.path == "/settings":
            self.serve_file("/app/src/sondealert/templates/settings.html", "text/html")
        elif parsed.path == "/gps.json":
            self.json_response(gps_data)
        elif parsed.path == "/nearest.json":
            nearby = get_nearby_sondes(gps_data, settings)
            self.json_response(nearby)
        elif parsed.path == "/api/settings":
            self.json_response(settings)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            for key in settings:
                if key in params:
                    val = params[key][0]
                    if val.lower() in ["true", "false"]:
                        settings[key] = val.lower() == "true"
                    elif val.isdigit():
                        settings[key] = int(val)
            save_settings(settings)
            logger.info("Instellingen bijgewerkt: %s", settings)
            self.json_response({"status": "ok", "settings": settings})
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, path, mime):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", mime)
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def json_response(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def start_server(host="0.0.0.0", port=8080):
    httpd = HTTPServer((host, port), WebHandler)
    logger.info("Webserver gestart op http://%s:%d/", host, port)
    httpd.serve_forever()
