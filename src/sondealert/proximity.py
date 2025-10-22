import json
import math
import time
import logging
from . import gps

logger = logging.getLogger("proximity")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def start_proximity_loop(settings):
    """Bereken telkens de dichtstbijzijnde sonde binnen de ingestelde afstand."""
    logger.info(f"Afstandsbepaling gestart (radius {settings['NEAR_THRESHOLD_M']/1000:.1f} km)")

    SONDES_FILE = "/app/data/sondes.json"
    NEAREST_FILE = "/app/data/nearest.json"

    while True:
        try:
            # GPS ophalen
            gps_data = gps.get_last_position()
            if not gps_data or not gps_data.get("fix"):
                time.sleep(5)
                continue

            lat = gps_data["lat"]
            lon = gps_data["lon"]

            # Sondes laden
            with open(SONDES_FILE, "r") as f:
                data = json.load(f)

            sondes = data.get("items", [])
            if not sondes:
                time.sleep(5)
                continue

            # Bereken dichtstbijzijnde sonde
            nearest = None
            nearest_dist = float("inf")

            for s in sondes:
                try:
                    d = haversine(lat, lon, float(s["lat"]), float(s["lon"]))
                    if d < nearest_dist:
                        nearest, nearest_dist = s, d
                except Exception as e:
                    logger.warning(f"Fout bij berekenen afstand voor sonde: {e}")

            # Filter op ingestelde radius
            if nearest and nearest_dist <= settings["NEAR_THRESHOLD_M"]:
                nearest["distance"] = nearest_dist
                nearest_list = [nearest]
            else:
                nearest_list = []

            with open(NEAREST_FILE, "w") as f:
                json.dump(nearest_list, f, indent=2)

            time.sleep(5)

        except Exception as e:
            logger.error(f"Fout in proximity-loop: {e}")
            time.sleep(5)
