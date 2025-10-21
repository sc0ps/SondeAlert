import math, time
from .config import load_settings
from .utils import state_lock

# Gedeelde statusvariabelen
gps_have, gps_lat, gps_lon, gps_last = False, 0.0, 0.0, 0
nearest, nearest_d_m = None, None
items = []  # lijst van sondes (uit radiosondy.py)
settings = {}  # actieve instellingen (wordt live bijgewerkt)


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
# Hoofd-thread: berekent dichtstbijzijnde sonde
# ----------------------------
def nearest_loop():
    """Continu controleren welke sonde het dichtstbij is."""
    global nearest, nearest_d_m

    while True:
        with state_lock:
            # Laad steeds actuele instellingen
            s = load_settings()
            thr = float(s.get("NEAR_THRESHOLD_M", 10000))
            have, glat, glon = gps_have, gps_lat, gps_lon
            lst = list(items)

        if have and lst:
            # Vind de dichtstbijzijnde sonde
            best = min(lst, key=lambda it: haversine(glat, glon, it["lat"], it["lon"]))
            d = haversine(glat, glon, best["lat"], best["lon"])

            with state_lock:
                if d <= thr:
                    nearest, nearest_d_m = best, d
                    print(f"[PROX] Dichtste sonde {best['id']} op {d/1000:.2f} km (binnen drempel {thr/1000:.1f} km)")
                else:
                    nearest, nearest_d_m = None, None
                    print(f"[PROX] Geen sonde binnen bereik (drempel {thr/1000:.1f} km, dichtste {d/1000:.2f} km)")
        else:
            with state_lock:
                nearest, nearest_d_m = None, None

        time.sleep(1)


# ----------------------------
# Functie om GPS-positie live bij te werken
# ----------------------------
def update_gps(lat, lon):
    """Wordt aangeroepen vanuit gps.py wanneer een nieuw NMEA-pakket binnenkomt."""
    global gps_have, gps_lat, gps_lon, gps_last
    with state_lock:
        gps_have, gps_lat, gps_lon, gps_last = True, lat, lon, int(time.time())


# ----------------------------
# Handige getter voor huidige status
# ----------------------------
def get_status():
    """Retourneert een snapshot van de huidige proximiteit-status."""
    with state_lock:
        return {
            "gps_have": gps_have,
            "gps_lat": gps_lat,
            "gps_lon": gps_lon,
            "nearest": nearest,
            "distance_m": nearest_d_m
        }
