import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from html import escape
from .config import load_settings, save_settings, BASE_DIR
from .gps import gps_have, gps_lat, gps_lon
from .proximity import nearest_sondes, nearest_lock

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        # stil houden in console
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
        if self.path == "/" or self.path.startswith("/index"):
            return self._send_html_file("index.html")

        if self.path == "/settings":
            return self._send_html_file("settings.html")

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

        # alles onder /static/ uit web-map serveren
        if self.path.startswith("/static/"):
            path = os.path.join(WEB_DIR, self.path[len("/static/"):])
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                # Content-Type minimaal correct proberen
                if path.endswith(".js"):
                    self.send_header("Content-Type", "application/javascript")
                elif path.endswith(".css"):
                    self.send_header("Content-Type", "text/css")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        self.send_error(404, "Not Found")

    # --------- POST ---------
    def do_POST(self):
        if self.path == "/settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            s = load_settings()
            try:
                s["NEAR_THRESHOLD_M"] = float(params.get("NEAR_THRESHOLD_M", [s["NEAR_THRESHOLD_M"]])[0])
                s["MONTHS_BACK"] = int(params.get("MONTHS_BACK", [s["MONTHS_BACK"]])[0])
                s["ALT_MAX_M"] = float(params.get("ALT_MAX_M", [s["ALT_MAX_M"]])[0])
                # CSV in één veld
                status_keep = params.get("STATUS_KEEP", ["UNKNOWN,NEED ATTENTION"])[0]
                s["STATUS_KEEP"] = [x.strip().upper() for x in status_keep.split(",") if x.strip()]
                # Launch filters als multiline
                launch_filters = params.get("LAUNCH_FILTERS", ["DE BILT (NL)\nDE BILT"])[0]
                s["LAUNCH_FILTERS"] = [ln.strip() for ln in launch_filters.splitlines() if ln.strip()]
                s["BUZZER_ENABLED"] = "BUZZER_ENABLED" in params
                # (optioneel) bind host/port
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

def start(host="0.0.0.0", port=8080):
    httpd = ThreadingHTTPServer((host, port), WebHandler)
    print(f"[WEB] bereikbaar op http://{host}:{port}/")
    httpd.serve_forever()
