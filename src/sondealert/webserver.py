import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from .utils import get_logger
from .gps import gps_data

logger = get_logger("web")

SETTINGS_FILE = "data/settings.json"
SONDES_FILE = "data/sondes.json"
HOST = "0.0.0.0"
PORT = 8080


class SondeHandler(BaseHTTPRequestHandler):
    """HTTP-handler voor SondeAlert."""

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()

    # === GET ===
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            # ---- Hoofdpagina met kaart ----
            if path in ["/", "/index.html"]:
                self._set_headers(200, "text/html; charset=utf-8")
                lat = gps_data.get("lat")
                lon = gps_data.get("lon")

                html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>SondeAlert Webinterface</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 body {{ font-family: Arial, sans-serif; margin:0; background:#f4f4f4; }}
 #map {{ height: 90vh; width:100%; }}
 header {{ background:#1565c0; color:white; padding:10px; text-align:center; font-size:20px; }}
</style>
</head>
<body>
<header>🚀 SondeAlert Live Kaart</header>
<div id="map"></div>
<script>
  const map = L.map('map').setView([{lat or '52.0'}, {lon or '5.0'}], 8);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/">OSM</a> contributors'
  }}).addTo(map);

  let userMarker = null;
  let sondeMarkers = [];

  function updateMap() {{
      fetch('/nearest.json')
        .then(r => r.json())
        .then(data => {{
            // verwijder oude sondes
            sondeMarkers.forEach(m => map.removeLayer(m));
            sondeMarkers = [];

            data.forEach(s => {{
                const marker = L.marker([s.lat, s.lon]).addTo(map)
                  .bindPopup(`<b>${{s.name}}</b><br>${{s.alt}} m<br>${{s.status}}`);
                sondeMarkers.push(marker);
            }});
        }})
        .catch(err => console.error('Fetch sondes:', err));

      // update userpositie
      fetch('/gps.json')
        .then(r => r.json())
        .then(pos => {{
            if (pos.lat && pos.lon) {{
                if (userMarker) userMarker.setLatLng([pos.lat, pos.lon]);
                else {{
                    userMarker = L.marker([pos.lat, pos.lon], {{
                        icon: L.icon({{
                            iconUrl: 'https://cdn-icons-png.flaticon.com/512/64/64113.png',
                            iconSize: [24,24]
                        }})
                    }}).addTo(map).bindPopup("📍 Jouw positie");
                    map.setView([pos.lat, pos.lon], 10);
                }}
            }}
        }});
  }}

  updateMap();
  setInterval(updateMap, 5000);
</script>
</body></html>"""
                self.wfile.write(html.encode("utf-8"))
                return

            # ---- sondes.json ----
            elif path == "/nearest.json":
                self._set_headers(200)
                try:
                    with open(SONDES_FILE, "r", encoding="utf-8") as f:
                        sondes = json.load(f)
                    self.wfile.write(json.dumps(sondes, ensure_ascii=False).encode("utf-8"))
                except FileNotFoundError:
                    self.wfile.write(b"[]")
                return

            # ---- gps.json ----
            elif path == "/gps.json":
                self._set_headers(200)
                self.wfile.write(json.dumps(gps_data, ensure_ascii=False).encode("utf-8"))
                return

            # ---- instellingen ----
            elif path == "/settings":
                self._set_headers(200)
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                    self.wfile.write(json.dumps(settings, indent=2, ensure_ascii=False).encode("utf-8"))
                except FileNotFoundError:
                    self.wfile.write(b"{}")
                return

            else:
                self._set_headers(404)
                self.wfile.write(b'{{"error":"Not Found"}}')
        except Exception as e:
            logger.exception("Fout bij GET: %s", e)
            self._set_headers(500)
            self.wfile.write(b'{{"error":"Internal Server Error"}}')

    # === POST ===
    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/settings":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                new_settings = json.loads(body.decode("utf-8"))
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_settings, f, indent=2, ensure_ascii=False)
                logger.info("Instellingen bijgewerkt via webinterface: %s", new_settings)
                self._set_headers(200)
                self.wfile.write(b'{"status":"OK"}')
            else:
                self._set_headers(404)
                self.wfile.write(b'{"error":"Not Found"}')
        except Exception as e:
            logger.exception("Fout bij POST: %s", e)
            self._set_headers(500)
            self.wfile.write(b'{"error":"Internal Server Error"}')


def start_server(host=HOST, port=PORT):
    """Start de webserver."""
    server = HTTPServer((host, port), SondeHandler)
    logger.info("Webserver gestart op http://%s:%d/", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.warning("Webserver gestopt (Ctrl+C).")
    finally:
        server.server_close()
        logger.info("Webserver afgesloten.")
