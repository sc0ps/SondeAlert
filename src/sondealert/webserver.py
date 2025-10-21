import json, socket, threading, urllib.parse, os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from .utils import state_lock
from . import gps as gps_module
from . import proximity as prox
from .config import save_settings, load_settings

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):  # geen console spam
        pass

    def _serve_file(self, filename, mime="text/html"):
        path = os.path.join(WEB_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404)
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _ok_json(self, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            self._serve_file("index.html")
            return

        elif path == "/settings":
            self._serve_file("settings.html")
            return

        elif path == "/nearest.json":
            with state_lock:
                n, d = prox.nearest, prox.nearest_d_m
                have, glat, glon = gps_module.gps_have, gps_module.gps_lat, gps_module.gps_lon
            self._ok_json({
                "gps": {"have": have, "lat": glat if have else None, "lon": glon if have else None},
                "nearest": n, "distance_m": d
            })
            return

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/settings":
            length = int(self.headers.get("Content-Length", 0))
            data = urllib.parse.parse_qs(self.rfile.read(length).decode())

            with state_lock:
                s = load_settings()
                s["BUZZER_ENABLED"] = ("BUZZER_ENABLED" in data)
                for key in ("NEAR_THRESHOLD_M", "MONTHS_BACK", "ALT_MAX_M", "UPDATE_HOURS"):
                    if key in data:
                        try:
                            val = data[key][0]
                            s[key] = float(val) if "." in val else int(val)
                        except:
                            pass
                if "STATUS_KEEP" in data:
                    s["STATUS_KEEP"] = [x.strip().upper() for x in data["STATUS_KEEP"][0].split(",") if x.strip()]
                if "LAUNCH_FILTERS" in data:
                    s["LAUNCH_FILTERS"] = [x.strip() for x in data["LAUNCH_FILTERS"][0].split("\n") if x.strip()]
                save_settings(s)

            with state_lock:
                prox.settings = load_settings()

            self._ok_json({"ok": True, "msg": "Instellingen opgeslagen ✅"})
        else:
            self.send_error(404)


def start(settings: dict):
    bind_host = settings.get("BIND_HOST", "0.0.0.0")
    bind_port = int(settings.get("BIND_PORT", 8080))
    httpd = ThreadingHTTPServer((bind_host, bind_port), WebHandler)
    ip = socket.gethostbyname(socket.gethostname())
    print(f"[WEB] bereikbaar op http://{ip}:{bind_port}/")
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
