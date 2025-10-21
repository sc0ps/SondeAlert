import json, socket, threading, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from .utils import state_lock
from . import gps as gps_module
from . import proximity as prox
from .config import save_settings, load_settings


class WebHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # -----------------------------------------------------------
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

    # -----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?")[0]

        # ---------- dashboard ----------
        if path in ("/", "/index.html"):
            with state_lock:
                have, glat, glon = gps_module.gps_have, gps_module.gps_lat, gps_module.gps_lon

            html = f"""<!DOCTYPE html>
<html lang='nl'><head><meta charset='utf-8'><title>SondeAlert</title>
<style>
:root{{--bg1:#0a2540;--bg2:#001220;--accent:#4fc3f7;--card:rgba(255,255,255,0.08);
--text:#fff;--muted:#aab;}}
body{{margin:0;min-height:100vh;background:linear-gradient(180deg,var(--bg1),var(--bg2));
background-attachment:fixed;background-size:cover;font-family:system-ui,Segoe UI,Arial,sans-serif;
color:var(--text);}}
.wrap{{max-width:900px;margin:20px auto;padding:0 12px;}}
.card{{background:var(--card);padding:20px;border-radius:12px;
box-shadow:0 0 15px rgba(0,0,0,0.3);margin-bottom:12px;}}
h1{{color:var(--accent);margin:8px 0 16px;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border-bottom:1px solid rgba(255,255,255,.1);padding:6px 4px;text-align:left;}}
.badge{{display:inline-block;padding:2px 8px;border:1px solid var(--accent);
border-radius:999px;color:var(--accent);}}
#map{{height:420px;border-radius:10px;margin-top:12px;}}
button.tab{{background:transparent;color:var(--accent);border:1px solid var(--accent);
padding:6px 12px;border-radius:8px;margin-right:6px;cursor:pointer;font-weight:600;}}
button.tab.active{{background:var(--accent);color:#001220;}}
</style>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>
<script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script>
</head>
<body><div class='wrap'>
<h1>SondeAlert</h1>
<div style="margin-bottom:12px;">
  <button class='tab active' onclick="window.location.href='/'">Dashboard</button>
  <button class='tab' onclick="window.location.href='/settings'">Instellingen</button>
</div>

<div class='card'>
  <div>GPS: <span class='badge'>{'OK' if have else 'OFF'}</span> &nbsp;
  Positie: <b>{f'{glat:.5f},{glon:.5f}' if have else '—'}</b></div>
</div>

<div class='card'>
  <h3>Dichtstbijzijnde sonde</h3>
  <div id='nearest'>Laden...</div>
  <div id='map'></div>
</div>

<script>
let map=L.map('map').setView([52.1,5.2],7);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:18}}).addTo(map);
let my=null,sn=null,line=null;

async function update(){{
  try{{
    const r=await fetch('/nearest.json?'+Date.now());
    const s=await r.json();
    document.getElementById('nearest').innerHTML = s.nearest ?
      `<table><tr><th>ID</th><th>Status</th><th>Afstand</th><th>Hoogte</th>
       <th>Laatste</th><th>Locatie</th></tr>
       <tr><td>${{s.nearest.id}}</td><td>${{s.nearest.status}}</td>
           <td>${{(s.distance_m/1000).toFixed(2)}} km</td>
           <td>${{parseInt(s.nearest.alt)}} m</td>
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
  }}catch(e){{console.error(e);}}
}}
window.addEventListener('load',()=>{{update();setInterval(update,5000);}});
</script>
</div></body></html>"""
            self._ok_html(html)
            return

        # ---------- JSON endpoint ----------
        elif path == "/nearest.json":
            with state_lock:
                n, d = prox.nearest, prox.nearest_d_m
                have, glat, glon = gps_module.gps_have, gps_module.gps_lat, gps_module.gps_lon
            self._ok_json({
                "gps": {"have": have, "lat": glat if have else None, "lon": glon if have else None},
                "nearest": n, "distance_m": d
            })
            return

        # ---------- instellingen ----------
        elif path == "/settings":
            with state_lock:
                s = load_settings()
            launch_filters_text = "\n".join(s.get("LAUNCH_FILTERS", ["DE BILT (NL)", "DE BILT"]))
            status_keep_text = ",".join(s.get("STATUS_KEEP", ["UNKNOWN", "NEED ATTENTION"]))

            html = f"""<!DOCTYPE html><html lang='nl'><head><meta charset='utf-8'>
<title>Instellingen – SondeAlert</title>
<style>
body{{margin:0;min-height:100vh;background:linear-gradient(180deg,#0a2540,#001220);
font-family:system-ui,Segoe UI,Arial,sans-serif;color:#fff;}}
.wrap{{max-width:600px;margin:20px auto;padding:0 12px;}}
.card{{background:rgba(255,255,255,0.08);padding:20px;border-radius:12px;
box-shadow:0 0 15px rgba(0,0,0,0.3);}}
label{{display:block;margin-top:10px;font-weight:600;color:#4fc3f7;}}
input,textarea{{width:100%;padding:8px;border:none;border-radius:8px;
background:rgba(255,255,255,0.1);color:#fff;}}
button{{margin-top:16px;padding:10px 16px;border:none;border-radius:8px;
font-weight:600;cursor:pointer;}}
.save{{background:#4fc3f7;color:#001220;}}
.back{{background:transparent;border:1px solid #4fc3f7;color:#4fc3f7;margin-left:8px;}}
</style></head>
<body><div class='wrap'>
<h1>Instellingen</h1>
<form id='settingsForm' method='POST' action='/settings'>
<label><input type='checkbox' name='BUZZER_ENABLED' {'checked' if s.get('BUZZER_ENABLED') else ''}> Buzzer actief</label>
<label>NEAR_THRESHOLD_M (m):</label>
<input name='NEAR_THRESHOLD_M' value='{s.get('NEAR_THRESHOLD_M',15000)}'>
<label>MONTHS_BACK:</label>
<input name='MONTHS_BACK' value='{s.get('MONTHS_BACK',24)}'>
<label>ALT_MAX_M:</label>
<input name='ALT_MAX_M' value='{s.get('ALT_MAX_M',600)}'>
<label>STATUS_KEEP (komma gescheiden):</label>
<input name='STATUS_KEEP' value="{status_keep_text}">
<label>LAUNCH_FILTERS (één per regel):</label>
<textarea name='LAUNCH_FILTERS' rows='4'>{launch_filters_text}</textarea>
<div><button type='submit' class='save'>Opslaan</button>
<button type='button' class='back' onclick="window.location.href='/'">Terug</button></div>
</form>

<script>
document.getElementById('settingsForm').addEventListener('submit', async function(e) {{
  e.preventDefault();
  const formData = new FormData(this);
  const res = await fetch('/settings', {{method:'POST', body: formData}});
  if(res.ok) alert('Instellingen opgeslagen ✅');
}});
</script>

</div></body></html>"""
            self._ok_html(html)
            return

        else:
            self.send_error(404)

    # -----------------------------------------------------------
    def do_POST(self):
    if self.path == "/settings":
        length = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(length).decode())
        with state_lock:
            s = load_settings()
            s["BUZZER_ENABLED"] = ("BUZZER_ENABLED" in data)
            for key in ("NEAR_THRESHOLD_M","MONTHS_BACK","ALT_MAX_M","UPDATE_HOURS"):
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

        # laad instellingen opnieuw in geheugen
        from .config import settings
        with state_lock:
            settings.clear()
            settings.update(load_settings())

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
