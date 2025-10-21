import time
import threading
import math
import json
from pathlib import Path
from .gps import gps_have, gps_lat, gps_lon
from .config import load_settings

nearest_sondes = []
nearest_lock = threading.Lock()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def start_proximity():
    """Zoekt voortdurend naar dichtstbijzijnde sondes binnen ingestelde afstand."""
    settings = load_settings()
    threshold_m = float(settings.get("NEAR_THRESHOLD_M", 15000))
    data_file = Path("/app/data/sondes.json")
    if not data_file.exists():
        print("[PROX] sondes.json niet gevonden.")
        return

    with data_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    all_sondes = data.get("items", [])
    print(f"[PROX] {len(all_sondes)} sondes geladen uit sondes.json")

    def loop():
        global nearest_sondes
        while True:
            near = []
            if gps_have:
                my_lat, my_lon = gps_lat, gps_lon
                for s in all_sondes:
                    try:
                        d = haversine(my_lat, my_lon, s["lat"], s["lon"])
                        if d <= threshold_m:
                            near.append({
                                "id": s["id"], "status": s.get("status", ""),
                                "dist_m": d, "alt": s.get("alt"), "last": s.get("last"),
                                "place": s.get("place"), "lat": s["lat"], "lon": s["lon"]
                            })
                    except Exception:
                        continue

            with nearest_lock:
                nearest_sondes = sorted(near, key=lambda x: x["dist_m"])

            if near:
                print(f"[PROX] {len(near)} sondes binnen {threshold_m/1000:.1f} km, dichtste {near[0]['dist_m']/1000:.2f} km.")
            time.sleep(3)

    threading.Thread(target=loop, daemon=True).start()
    print("[PROX] Proximity-thread gestart.")
