import logging
import math
import time
from sondealert import config, radiosondy, gps

log = logging.getLogger("proximity")

_nearby_sondes = []


def start():
    """Thread die om de 5 sec sondes binnen de ingestelde straal zoekt."""
    log.info("Afstandsbepaling gestart.")
    while True:
        try:
            update_nearby()
        except Exception as e:
            log.warning(f"Fout in proximity-loop: {e}")
        time.sleep(5)


def update_nearby():
    """Update de lijst van sondes binnen de ingestelde afstand."""
    lat, lon, fix = gps.get_last_position()
    if not fix or lat is None or lon is None:
        return

    sondes = radiosondy.get_all_sondes()
    settings = config.load_settings()
    radius = float(settings.get("NEAR_THRESHOLD_M", 15000))

    nearby = []
    for s in sondes:
        try:
            dist = haversine(lat, lon, s["lat"], s["lon"])
            if dist <= radius:
                nearby.append({**s, "distance": dist})
        except Exception:
            continue

    global _nearby_sondes
    _nearby_sondes = sorted(nearby, key=lambda x: x["distance"])
    log.info(f"Gevonden {len(_nearby_sondes)} sondes binnen {radius/1000:.1f} km.")


def get_nearby_sondes():
    """Retourneert huidige lijst sondes binnen afstand."""
    return _nearby_sondes


def haversine(lat1, lon1, lat2, lon2):
    """Bereken afstand in meters tussen twee coördinaten."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
