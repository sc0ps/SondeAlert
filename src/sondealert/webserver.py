import json, socket, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from .utils import state_lock
from . import gps as gps_module
from . import proximity as prox

class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):  # geen logging in console
        pass

    def _ok_html(self, html: str):
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _ok_json(self, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]

        # --- Dashboardpagina ---
        if path in ("/", "/index.html"):
            with state_lock:
                have, glat, glon = gps_module.gps_have, gps_module.gps_lat, gps_module.gps_lon
            html = f"""<!DOCTYPE html>
<html lang='nl'>
<head>
<meta charset='utf-8'>
<title>SondeAlert</title>
<style>
:root{{--bg1:#0a2540;--bg2:#001220;--accent:#4fc3f7;--card:rgba(255,255,255,0.08);--text:#fff;--muted:#aab;}}
body{{margin:0;background:linear-gradient(180deg,var(--bg1),var(--bg2));
font-family:system-ui,Segoe UI,Arial,sans-serif;color:var(--text);}}
.wrap{{max-width:900px;margin:20px auto;padding:0 12px;}}
.card{{background:var(--card);padding:20px;border-radius:12px;
box-shadow:0 0 15px rgba(0,0,0,0.3);margin-bottom:12px;}}
h1{{color:var(--accent);margin:8px 0 16px;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border-bottom:1px solid rgba(255,255,255,.1);padding:6px 4px;text-align:left;}}
.badge{{display:inline-block;padding:2px 8px;border:1px solid var(--accent);
border-radius:999px;color:var(--accent);}}
#map{{height:420px;border-radius:10px;margin-top:12px;}}
</style>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>
<script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script>
</head>
<body>
<div class='wrap'>
<h1>SondeAlert</h1>
<div class='card'>
  <div>GPS: <span class='badge'>{'OK' if have else 'OFF'}</span> &nbsp;
  Positie: <b>{f'{glat:.5f},{glon:.5f}' if have else '—'}</b></div>
</div>
<div class='card'>
  <h3>Dichtstbijzijnde sonde</h3>
  <div id='nearest'></div>
  <div id='map'></div>
</div>
<script>
let map=L.map('map').setView([52.1,5.2],7);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:18}}).addTo(map);
let my=null,sn=null,line=null;

async function update(){{
  try{{
    const r=await fetch('/nearest.json'); const s=await r.json();
    document.getElementById('nearest').innerHTML = s.nearest ?
      `<table><tr><th>ID</th><th>Status</th><th>Afstand</th><th>Hoogte</th><th>Laatste</th><th>Locatie</th></tr>
       <tr><td>${{s.nearest.id}}</td><td>${{s.nearest.status}}</td>
           <td>${{(s.distance_m/1000).toFixed(2)}} km</td><td>${{parseInt(s.nearest.alt)}} m</td>
           <td>${{s.nearest.last}}</td><td>${{s.nearest.place}}</td></tr></table>`
      : "Geen sonde binnen bereik.";
    if(!s.gps.have) return;
    let lat=s.gps.lat,lon=s.gps.lon;
    if(!my) my=L.marker([lat,lon]).addTo(map).bindPopup('Jij'); else my.setLatLng([lat,lon]);
    const n=s.nearest,d=s.distance_m;
    if(n&&d){{
      let sl=n.lat,so=n.lon;
      if(!sn) sn=L.marker([sl,so]).addTo(map).bindPopup(`Sonde ${{n.id}}`); else sn.setLatLng([sl,so]);
      if(line) line.remove();
      line=L.polyline([[lat,lon],[sl,so]],{{color:'red'}}).addTo(map);
      map.fitBounds([[lat,lon],[sl,so]],{{padding:[40,40]}});
    }}
  }}catch(e){{}}
}}
update(); setInterval(update,5000);
</script>
</div>
</body>
</html>"""
            self._ok_html(html)
            return

        # --- JSON endpoint ---
        elif path == "/nearest.json":
            with state_lock:
                n, d = prox.nearest, prox.nearest_d_m
                have, glat, glon = gps_module.gps_have, gps_module.gps_lat, gps_module.gps_lon
            self._ok_json({
                "gps": {"have": have, "lat": glat if have else None, "lon": glon if have else None},
                "nearest": n,
                "distance_m": d
            })
            return

        # --- alles anders = 404 ---
        else:
            self.send_error(404)

def start(settings: dict):
    """Start de webserver-thread"""
    bind_host = settings.get("BIND_HOST", "0.0.0.0")
    bind_port = int(settings.get("BIND_PORT", 8080))
    httpd = ThreadingHTTPServer((bind_host, bind_port), WebHandler)
    ip = socket.gethostbyname(socket.gethostname())
    print(f"[WEB] bereikbaar op http://{ip}:{bind_port}/")
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
