import json
import math
import logging
import time
from pathlib import Path

logger = logging.getLogger("proximity")

SONDES_FILE = Path("/app/data/sondes.json")


def haversine(lat1, lon1, lat2, lon2):
    """Bereken afstand tussen twee GPS-coördinaten in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def load_sondes():
    """Laad sondes uit JSON-bestand."""
    if not SONDES_FILE.exists():
        logger.warning("Geen sondelijst gevonden op %s", SONDES_FILE)
        return []
    try:
        with open(SONDES_FILE, "r", encoding="utf-8") as f:
            sondes = json.load(f)
        logger.info("%d sondes geladen uit %s", len(sondes), SONDES_FILE)
        return sondes
    except Exception as e:
        logger.error(f"Fout bij laden sondelijst: {e}")
        return []


def get_nearby_sondes(gps_data, settings):
    """Return lijst met sondes binnen NEAR_THRESHOLD_M."""
    sondes = load_sondes()
    lat = gps_data.get("lat")
    lon = gps_data.get("lon")
    if not lat or not lon:
        return []

    threshold = settings.get("NEAR_THRESHOLD_M", 15000)
    results = []

    for s in sondes:
        try:
            distance = haversine(lat, lon, s["lat"], s["lon"])
            if distance <= threshold:
                s["distance"] = round(distance, 1)
                results.append(s)
        except Exception as e:
            logger.warning(f"Fout bij berekenen afstand voor sonde: {e}")

    results.sort(key=lambda x: x.get("distance", 999999))
    return results


def start_proximity_loop(settings):
    """Achtergrondthread die periodiek sondes update (placeholder voor toekomst)."""
    logger.info(f"Afstandsbepaling gestart (radius {settings.get('NEAR_THRESHOLD_M', 15000)/1000:.1f} km)")
    while True:
        time.sleep(10)
