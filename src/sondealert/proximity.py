import json
import math
import time
from pathlib import Path
from .utils import get_logger

logger = get_logger("proximity")

# Pad naar de sondelijst
SONDES_FILE = Path("/app/data/sondes.json")

# Globale opslag
sondes = []


# === Haversine formule voor afstandsberekening (in meter) ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # straal van de aarde in meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# === Sondes laden uit JSON-bestand ===
def load_sondes():
    global sondes
    try:
        if not SONDES_FILE.exists():
            logger.warning("Bestand %s niet gevonden, maak lege lijst aan.", SONDES_FILE)
            sondes = []
            return

        with open(SONDES_FILE, "r") as f:
            data = json.load(f)
            sondes = data.get("items", [])
            logger.info("%d sondes geladen uit %s", len(sondes), SONDES_FILE)
    except Exception as e:
        logger.error("Fout bij laden sondelijst: %s", e)
        sondes = []


# === Bereken welke sondes binnen de ingestelde afstand vallen ===
def get_nearby_sondes(gps_data, settings):
    """Retourneert een lijst met sondes binnen de ingestelde NEAR_THRESHOLD_M"""
    if not gps_data or gps_data.get("lat") is None or gps_data.get("lon") is None:
        return []

    lat0 = gps_data["lat"]
    lon0 = gps_data["lon"]
    max_dist = settings.get("NEAR_THRESHOLD_M", 15000)
    alt_max = settings.get("ALT_MAX_M", 600)

    nearby = []

    for s in sondes:
        try:
            dist = haversine(lat0, lon0, s["lat"], s["lon"])
            if dist <= max_dist and s.get("alt", 9999) <= alt_max:
                nearby.append({
                    "id": s.get("id"),
                    "lat": s.get("lat"),
                    "lon": s.get("lon"),
                    "alt": s.get("alt"),
                    "status": s.get("status", "UNKNOWN"),
                    "distance": round(dist, 1),
                    "place": s.get("place", ""),
                    "last": s.get("last", "")
                })
        except Exception as e:
            logger.warning("Kon sonde niet verwerken: %s", e)

    return nearby


# === Thread-loop (achtergrondproces) ===
def run():
    """Wordt door main.py gestart in een aparte thread."""
    logger.info("Afstandsbepaling gestart (radius %.1f km)", 15000 / 1000)
    load_sondes()

    while True:
        # Toekomstige uitbreidingen zoals buzzer alerts of live updates
        time.sleep(3)
