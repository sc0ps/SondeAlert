import math, time, threading
from .config import load_settings
from .utils import state_lock

# Gedeelde statusvariabelen
gps_have, gps_lat, gps_lon, gps_last = False, 0.0, 0.0, 0
nearest, nearest_d_m = None, None
in_range = []     # lijst van sondes binnen drempelafstand
items = []        # alle sondes uit radiosondy.py
settings = {}     # actuele instellingen


# ----------------------------
# Hulpfuncties
# ----------------------------
def deg2rad(d):
    return d * math.pi / 180.0


def haversine(lat1, lon1, lat2, lon2):
    """Bereken afstand in meters tussen twee punten op aarde."""
    R = 6371000.0
    dLat = deg2rad(lat2 - lat1)
    dLon = deg2rad(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ----------------------------
# Hoofd-thread: controleert sondes in de buurt
# ----------------------------
def nearest_loop():
    """Continu controleren welke sondes binnen de ingestelde afstand vallen."""
    global nearest, nearest_d_m, in_range

    while True:
        with state_lock:
            s = load_settings()
            thr = float(s.get("NEAR_THRESHOLD_M", 10000))
            have, glat, glon = gps_have, gps_lat, gps_lon
            lst = list(items)

        if have and lst:
            gevonden = []
            dichtste, min_d = None, None

            for it in lst:
                d = haversine(glat, glon, it["lat"], it["lon"])
                if d <= thr:
                    gevonden.append({**it, "distance_m": d})
                if min_d is None or d < min_d:
                    min_d, dichtste = d, it

            with state_lock:
                in_range = sorted(gevonden, key=lambda x: x["distance_m"])
                nearest = dichtste if min_d is not None else None
                nearest_d_m = min_d

            if in_range:
                print(f"[PROX] {len(in_range)} sondes binnen {thr/1000:.1f} km, dichtste {min_d/1000:.2f} km.")
            else:
                print(f"[PROX] Geen sondes binnen {thr/1000:.1f} km (dichtste {min_d/1000:.2f} km).")

        else:
            with state_lock:
                nearest, nearest_d_m, in_range = None, None, []

        time.sleep(2)


# ----------------------------
# Functie om GPS live bij te werken
# ----------------------------
def update_gps(lat, lon):
    """Wordt aangeroepen vanuit gps.py wanneer een nieuw NMEA-pakket binnenkomt."""
    global gps_have, gps_lat, gps_lon, gps_last
    with state_lock:
        gps_have, gps_lat, gps_lon, gps_last = True, lat, lon, int(time.time())


# ----------------------------
# Getter voor huidige status
# ----------------------------
def get_status():
    """Geeft snapshot van huidige proximiteitsstatus."""
    with state_lock:
        return {
            "gps_have": gps_have,
            "gps_lat": gps_lat,
            "gps_lon": gps_lon,
            "nearest": nearest,
            "distance_m": nearest_d_m,
            "in_range": in_range,
        }


# ----------------------------
# Startfunctie
# ----------------------------
def start_proximity(settings=None, gps_module=None):
    """Start de proximity-thread als achtergrondproces."""
    t = threading.Thread(target=nearest_loop, daemon=True)
    t.start()
    print("[PROX] Proximity-thread gestart.")