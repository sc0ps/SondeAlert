import json, os, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from .config import load_settings, save_settings
from .utils import state_lock
from .gps import gps_have, gps_lat, gps_lon
from .proximity import nearest_sondes, nearest_lock

class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            self._send_html(self._html_dashboard())
        elif path == "/settings":
            self._send_html(self._html_settings())
        elif path == "/nearest.json":
            with nearest_lock:
                n = list(nearest_sondes)
            with state_lock:
                gps_data = {
                    "have": gps_have,
                    "lat": gps_lat if gps_have else None,
                    "lon": gps_lon if gps_have else None,
                }
            self._send_json({"gps": gps_data, "nearest": n})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/settings":
            from urllib.parse import parse_qs
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            s = load_settings()
            try:
                s["NEAR_THRESHOLD_M"] = float(params.get("NEAR_THRESHOLD_M", [s["NEAR_THRESHOLD_M"]])[0])
                s["MONTHS_BACK"] = int(params.get("MONTHS_BACK", [s["MONTHS_BACK"]])[0])
                s["ALT_MAX_M"] = float(params.get("ALT_MAX_M", [s["ALT_MAX_M"]])[0])
                s["STATUS_KEEP"] = [x.strip().upper() for x in params.get("STATUS_KEEP", ["UNKNOWN,NEED ATTENTION"])[0].split(",")]
                s["LAUNCH_FILTERS"] = [x.strip() for x in params.get("LAUNCH_FILTERS", ["DE BILT (NL)\nDE BILT"])[0].splitlines()]
                s["BUZZER_ENABLED"] = "BUZZER_ENABLED" in params
                save_settings(s)
                print("[SETTINGS] Bestand opgeslagen:", json.dumps(s, indent=2))
                self._send_json({"ok": True, "msg": "Settings saved ✓"})
            except Exception as e:
                print("[SETTINGS] Fout bij opslaan:", e)
                self._send_json({"ok": False, "msg": str(e)}, 500)
        else:
            self.send_error(404)

    def _send_html(self, html, code=200):
        data = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html_dashboard(self):
        return "<html><body><h1>SondeAlert Dashboard</h1><p>Dashboard werkt!</p></body></html>"

    def _html_settings(self):
        return "<html><body><h1>Settings</h1><form method='POST'><input name='NEAR_THRESHOLD_M' value='15000'><button type='submit'>Save</button></form></body></html>"

def start(host="0.0.0.0", port=8080):
    httpd = ThreadingHTTPServer((host, port), WebHandler)
    print(f"[WEB] bereikbaar op http://{host}:{port}/")
    httpd.serve_forever()
