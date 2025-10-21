import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from html import escape
from .config import load_settings, save_settings
from .gps import gps_have, gps_lat, gps_lon
from .proximity import nearest_sondes, nearest_lock

# Webmap
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        # stilhouden in console
        pass

    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html_file(self, filename):
        path = os.path.join(WEB_DIR, filename)
        if not os.path.isfile(path):
            self.send_error(404, "Not Found")
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # --------- GET ---------
    def do_GET(self):
        # Dashboard
        if self.path == "/" or self.path.startswith("/index"):
            return self._send_html_file("index.html")

        # Instellingenpagina
        if self.path == "/settings":
            return self._send_html_file("settings.html")

        # JSON-data voor de kaart
        if self.path == "/nearest.json":
            with nearest_lock:
                items = list(nearest_sondes)
            payload = {
                "gps": {
                    "have": gps_have,
                    "lat": gps_lat,
                    "lon": gps_lon,
                },
                "items": items,
            }
            return self._send_json(payload)

        # -------- Static files (CSS, JS, icons etc.) --------
        if self.path.startswith("/static/"):
            # Belangrijkste fix: voeg 'static/' toe in het pad
            static_path = os.path.join(WEB_DIR, "static", self.path[len("/static/"):])
            if os.path.isfile(static_path):
                with open(static_path, "rb") as f:
                    data = f.read()

                # Content-type bepalen
                if static_path.endswith(".js"):
                    ctype = "application/javascript"
                elif static_path.endswith(".css"):
                    ctype = "text/css"
                elif static_path.endswith(".png"):
                    ctype = "image/png"
                elif static_path.endswith(".jpg") or static_path.endswith(".jpeg"):
                    ctype = "image/jpeg"
                elif static_path.endswith(".svg"):
                    ctype = "image/svg+xml"
                else:
                    ctype = "application/octet-stream"

                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        # Anders: 404
        self.send_error(404, "Not Found")

    # --------- POST ---------
    def do_POST(self):
        # Instellingen opslaan
        if self.path == "/settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            s = load_settings()
            try:
                s["NEAR_THRESHOLD_M"] = float(params.get("NEAR_THRESHOLD_M", [s["NEAR_THRESHOLD_M"]])[0])
                s["MONTHS_BACK"] = int(params.get("MONTHS_BACK", [s["MONTHS_BACK"]])[0])
                s["ALT_MAX_M"] = float(params.get("ALT_MAX_M", [s["ALT_MAX_M"]])[0])
                status_keep = params.get("STATUS_KEEP", ["UNKNOWN,NEED ATTENTION"])[0]
                s["STATUS_KEEP"] = [x.strip().upper() for x in status_keep.split(",") if x.strip()]
                launch_filters = params.get("LAUNCH_FILTERS", ["DE BILT (NL)\nDE BILT"])[0]
                s["LAUNCH_FILTERS"] = [ln.strip() for ln in launch_filters.splitlines() if ln.strip()]
                s["BUZZER_ENABLED"] = "BUZZER_ENABLED" in params

                if "BIND_HOST" in params:
                    s["BIND_HOST"] = params.get("BIND_HOST", [s.get("BIND_HOST", "0.0.0.0")])[0]
                if "BIND_PORT" in params:
                    s["BIND_PORT"] = int(params.get("BIND_PORT", [s.get("BIND_PORT", 8080)])[0])

                save_settings(s)
                print("[SETTINGS] Bestand opgeslagen:", json.dumps(s, ensure_ascii=False))
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, code=400)

        self.send_error(404, "Not Found")

# --------- Start Webserver ---------
def start(host="0.0.0.0", port=8080):
    httpd = ThreadingHTTPServer((host, port), WebHandler)
    print(f"[WEB] bereikbaar op http://{host}:{port}/")
    httpd.serve_forever()
