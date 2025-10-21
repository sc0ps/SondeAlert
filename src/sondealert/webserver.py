import json, os, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from .config import load_settings, save_settings
from .utils import state_lock
from .gps import gps_have, gps_lat, gps_lon
from .proximity import nearest_sondes, nearest_lock


class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # Disable console log spam
        pass

    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html, code=200):
        data = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # === GET ===
    def do_GET(self):
        path = self.path.split("?")[0]

        # === Dashboard ===
        if path == "/" or path == "/index.html":
            self._send_html(self._html_dashboard())
            return

        # === Settings page ===
        elif path == "/settings":
            self._send_html(self._html_settings())
            return

        # === JSON API: nearest sondes ===
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
            return

        # === JSON API: current settings ===
        elif path == "/api/settings":
            try:
                s = load_settings()
                self._send_json(s)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        else:
            self.send_error(404)

    # === POST ===
    def do_POST(self):
        if self.path == "/settings":
            from urllib.parse import parse_qs

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)

            try:
                s = load_settings()
                s["NEAR_THRESHOLD_M"] = float(params.get("NEAR_THRESHOLD_M", [s["NEAR_THRESHOLD_M"]])[0])
                s["MONTHS_BACK"] = int(params.get("MONTHS_BACK", [s["MONTHS_BACK"]])[0])
                s["ALT_MAX_M"] = float(params.get("ALT_MAX_M", [s["ALT_MAX_M"]])[0])
                s["STATUS_KEEP"] = [x.strip().upper() for x in params.get("STATUS_KEEP", ["UNKNOWN,NEED ATTENTION"])[0].split(",")]
                s["LAUNCH_FILTERS"] = [x.strip() for x in params.get("LAUNCH_FILTERS", ["DE BILT (NL)\nDE BILT"])[0].splitlines()]
                s["BUZZER_ENABLED"] = "BUZZER_ENABLED" in params

                save_settings(s)
                print("[SETTINGS] File updated:", json.dumps(s, indent=2))
                self._send_json({"ok": True, "msg": "Settings saved ✓"})
            except Exception as e:
                print("[SETTINGS] Error saving:", e)
                self._send_json({"ok": False, "msg": str(e)}, 500)
        else:
            self.send_error(404)

    # === HTML templates ===
    def _html_dashboard(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>SondeAlert — Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root {
  --bg1:#0a2540;--bg2:#001220;--accent:#2ea8ff;--text:#fff;
  --card:rgba(255,255,255,0.08);--muted:#aab;
}
body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;
background:linear-gradient(180deg,var(--bg1),var(--bg2));color:var(--text);}
header{text-align:center;padding:30px 0 10px;}
h1{margin:0;color:var(--accent);}
.tabs{display:flex;justify-content:center;gap:10px;margin-top:10px;}
.tab-btn{border:1px solid var(--accent);background:transparent;color:var(--accent);
padding:8px 16px;border-radius:999px;font-weight:600;cursor:pointer;transition:.2s;}
.tab-btn.active{background:var(--accent);color:#001220;}
.card{background:var(--card);border-radius:14px;box-shadow:0 0 15px rgba(0,0,0,0.3);
padding:20px;width:90%;max-width:800px;margin:20px auto;}
.status-box{display:flex;gap:10px;align-items:center;}
.gps-ok{color:#00e676;font-weight:700;}
.gps-off{color:#ff5252;font-weight:700;}
table{width:100%;border-collapse:collapse;margin-top:10px;}
th,td{padding:6px 4px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);}
footer{text-align:center;color:var(--muted);padding:20px 0;font-size:.9em;}
#map{height:400px;border-radius:10px;margin-top:12px;}
</style>
</head>
<body>
<header>
  <h1>SondeAlert</h1>
  <div class="tabs">
    <button class="tab-btn active" onclick="window.location.href='/'">Dashboard</button>
    <button class="tab-btn" onclick="window.location.href='/settings'">Settings</button>
  </div>
</header>

<div class="card">
  <div class="status-box">
    <div>GPS: <span id="gpsStatus" class="gps-off">OFF</span></div>
    <div id="gpsPos"></div>
  </div>
</div>

<div class="card">
  <h3>Sondes within range</h3>
  <div id="sondeList">Loading...</div>
  <div id="map"></div>
</div>

<footer>© 2025 SondeAlert — Developed by Scops Owl Designs</footer>

<script>
let map=L.map('map').setView([52.1,5.2],7);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18}).addTo(map);
let myMarker=null;
let sondeMarkers=[];
let line=null;

async function refresh(){
  const res=await fetch('/nearest.json');
  const j=await res.json();

  const gps=j.gps;
  const list=j.nearest;
  const gpsEl=document.getElementById('gpsStatus');
  gpsEl.textContent=gps.have?'OK':'OFF';
  gpsEl.className=gps.have?'gps-ok':'gps-off';
  document.getElementById('gpsPos').textContent=gps.have?`Position: ${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)}`:'';

  if(gps.have){
    if(!myMarker){
      const icon=L.icon({iconUrl:'https://cdn-icons-png.flaticon.com/512/61/61183.png',iconSize:[28,28]});
      myMarker=L.marker([gps.lat,gps.lon],{icon}).addTo(map);
    } else myMarker.setLatLng([gps.lat,gps.lon]);
  }

  sondeMarkers.forEach(m=>map.removeLayer(m));
  sondeMarkers=[];
  if(line){line.remove();line=null;}

  if(list && list.length){
    const table=['<table><tr><th>ID</th><th>Status</th><th>Distance</th><th>Altitude</th><th>Last frame</th><th>Launch site</th></tr>'];
    list.forEach(s=>{
      const color=s.status==='NEED ATTENTION'?'#2196f3':'#ffb300';
      const icon=L.icon({
        iconUrl:'https://cdn-icons-png.flaticon.com/512/103/103413.png',
        iconSize:[24,24],
        iconAnchor:[12,12]
      });
      const m=L.marker([s.lat,s.lon],{icon}).addTo(map);
      m.bindPopup(`<b>${s.id}</b><br>${s.status}<br>${(s.dist_m/1000).toFixed(2)} km`);
      sondeMarkers.push(m);
      table.push(`<tr><td>${s.id}</td><td style="color:${color}">${s.status}</td><td>${(s.dist_m/1000).toFixed(2)} km</td><td>${parseInt(s.alt)} m</td><td>${s.last}</td><td>${s.place}</td></tr>`);
      if(!line && gps.have) line=L.polyline([[gps.lat,gps.lon],[s.lat,s.lon]],{color:'red'}).addTo(map);
    });
    table.push('</table>');
    document.getElementById('sondeList').innerHTML=table.join('');
  } else {
    document.getElementById('sondeList').innerHTML='No sondes in range.';
  }
}
refresh();
setInterval(refresh,5000);
</script>
</body>
</html>"""

    def _html_settings(self):
        # returns empty shell; frontend fetches actual settings
        return open(os.path.join(os.path.dirname(__file__), "settings.html")).read()


def start(host="0.0.0.0", port=8080):
    httpd = ThreadingHTTPServer((host, port), WebHandler)
    print(f"[WEB] reachable on http://{host}:{port}/")
    httpd.serve_forever()
