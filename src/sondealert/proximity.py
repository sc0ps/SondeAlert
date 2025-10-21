import time, threading, math, json
from pathlib import Path
from .utils import state_lock
from .gps import gps_have, gps_lat, gps_lon
from .config import load_settings

# === Globale variabelen ===
nearest_sondes = []      # lijst van sondes binnen bereik
nearest_lock = threading.Lock()


# === Hulpfunctie: Haversine afstand in meters ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# === Hoofdproces ===
def start_proximity():
    """Thread die constant de dichtstbijzijnde sondes zoekt"""
    settings = load_settings()
    threshold_m = float(settings.get("NEAR_THRESHOLD_M", 15000))

    data_file = Path("/app/data/sondes.json")
    if not data_file.exists():
        print("[PROX] sondes.json niet gevonden, kan geen berekening uitvoeren.")
        return

    # Laad dataset
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_sondes = data.get("items", [])
    print(f"[PROX] {len(all_sondes)} sondes geladen uit sondes.json")

    # === Thread loop ===
    def loop():
        global nearest_sondes
        while True:
            try:
                if not gps_have:
                    print("[PROX] Geen GPS beschikbaar, wacht op positie...")
                    time.sleep(2)
                    continue

                my_lat, my_lon = gps_lat, gps_lon
                settings = load_settings()
                threshold_m = float(settings.get("NEAR_THRESHOLD_M", 15000))

                near = []

                for s in all_sondes:
                    d = haversine(my_lat, my_lon, s["lat"], s["lon"])
                    if d <= threshold_m:
                        near.append({
                            "id": s["id"],
                            "status": s["status"],
                            "dist_m": d,
                            "alt": s["alt"],
                            "last": s["last"],
                            "place": s["place"],
                            "lat": s["lat"],
                            "lon": s["lon"]
                        })

                near.sort(key=lambda x: x["dist_m"])

                with nearest_lock:
                    nearest_sondes = near

                if near:
                    print(f"[PROX] {len(near)} sondes binnen {threshold_m/1000:.1f} km, dichtste {near[0]['dist_m']/1000:.2f} km.")
                else:
                    print("[PROX] Geen sondes binnen ingestelde afstand.")

                time.sleep(3)

            except Exception as e:
                print("[PROX] Fout in berekening:", e)
                time.sleep(3)

    threading.Thread(target=loop, daemon=True).start()
    print("[PROX] Proximity-thread gestart.")
