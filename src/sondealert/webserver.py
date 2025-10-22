# /app/src/sondealert/webserver.py
import os, json, logging, threading, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from .config import load_settings, save_settings, SETTINGS_FILE, SONDES_FILE
from .state import get_gps, get_nearest, get_meta
from . import radiosondy

BASE_WEB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

def _read_body(handler):
    ln = int(handler.headers.get("Content-Length", "0"))
    return handler.rfile.read(ln) if ln>0 else b""

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # serve files from /web
        if path == "/": path = "/index.html"
        return os.path.join(BASE_WEB, path.lstrip("/"))

    def log_message(self, *a): pass

    def _ok_json(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _ok_text(self, text="OK"):
        data = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/gps.json":
            self._ok_json(get_gps()); return
        if self.path == "/nearest.json":
            self._ok_json(get_nearest()); return
        if self.path == "/settings.json":
            self._ok_json(load_settings() | get_meta()); return
        if self.path == "/sondes.json":
            if os.path.exists(SONDES_FILE):
                with open(SONDES_FILE,"r") as f:
                    data = json.load(f)
            else:
                data = {"generated":0,"count":0,"items":[]}
            # voeg meta toe
            data["last_update"] = get_meta()["last_update"]
            self._ok_json(data); return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/save_settings":
            body = _read_body(self).decode()
            try:
                s = load_settings()
                j = json.loads(body)
                for k in ("NEAR_THRESHOLD_M","ALT_MAX_M","UPDATE_HOURS"):
                    if k in j:
                        s[k] = int(j[k])
                if "BUZZER_ENABLED" in j:
                    s["BUZZER_ENABLED"] = bool(j["BUZZER_ENABLED"])
                if "MONTHS_BACK" in j:
                    s["MONTHS_BACK"] = int(j["MONTHS_BACK"])
                if "STATUS_KEEP" in j:
                    s["STATUS_KEEP"] = [x.strip().upper() for x in j["STATUS_KEEP"]]
                if "LAUNCH_FILTERS" in j:
                    s["LAUNCH_FILTERS"] = [x.strip() for x in j["LAUNCH_FILTERS"]]
                save_settings(s)
                self._ok_text("saved")
            except Exception as e:
                logging.warning("save_settings error: %s", e)
                self.send_error(400, "bad request")
            return

        if self.path == "/update_now":
            # run download in background thread; maar antwoord meteen
            def _run():
                try:
                    payload = radiosondy.update_sonde_list(load_settings())
                    from .state import set_last_update
                    set_last_update(payload["generated"], payload["count"])
                except Exception as e:
                    logging.error("[update_now] fout: %s", e)
            threading.Thread(target=_run, daemon=True).start()
            self._ok_text("updating")
            return

        self.send_error(404, "not found")

def serve(bind_host, bind_port):
    httpd = ThreadingHTTPServer((bind_host, int(bind_port)), Handler)
    logging.info("[web] Webserver gestart op http://%s:%s/", bind_host, bind_port)
    httpd.serve_forever()
