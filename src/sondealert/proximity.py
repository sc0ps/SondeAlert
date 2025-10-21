# src/sondealert/proximity.py
import json
import time
from math import isfinite
from .utils import state_lock, haversine, get_logger
from .gps import gps_data

logger = get_logger("proximity")

SONDES_JSON = "data/sondes.json"


def load_sondes():
    """Laad de bestaande sondelijst uit JSON."""
    try:
        with open(SONDES_JSON, "r", encoding="utf-8") as f:
            sondes = json.load(f)
            logger.info("%d sondes geladen uit %s", len(sondes), SNDES_JSON)
            return sondes
    except FileNotFoundError:
        logger.warning("Bestand %s niet gevonden — geen sondes geladen.", SNDES_JSON)
        return []
    except Exception as e:
        logger.exception("Fout bij laden sondelijst: %s", e)
        return []



def find_nearby_sondes(sondes, lat, lon, max_distance_km):
    """Filtert sondes binnen de opgegeven afstand (km)."""
    nearby = []
    for s in sondes:
        try:
            if not isfinite(s.get("lat", 0)) or not isfinite(s.get("lon", 0)):
                continue
            dist = haversine(lat, lon, s["lat"], s["lon"])
            if dist <= max_distance_km:
                s["distance_km"] = round(dist, 2)
                nearby.append(s)
        except Exception as e:
            logger.debug("Fout bij afstandsbepaling: %s", e)
    return sorted(nearby, key=lambda x: x["distance_km"])


def run(radius_m=15000):
    """
    Periodieke thread die kijkt welke sondes binnen bereik zijn.
    Wordt gestart vanuit main.py.
    """
    radius_km = radius_m / 1000.0
    logger.info("Afstandsbepaling gestart (radius %.1f km)", radius_km)

    sondes = load_sondes()
    last_check = 0

    while True:
        try:
            with state_lock:
                lat = gps_data.get("lat")
                lon = gps_data.get("lon")

            if lat and lon:
                now = time.time()
                # om de 3 s opnieuw berekenen
                if now - last_check >= 3:
                    last_check = now
                    nearby = find_nearby_sondes(sondes, lat, lon, radius_km)

                    if nearby:
                        logger.info(
                            "%d sondes binnen %.1f km, dichtste %.2f km (%s)",
                            len(nearby),
                            radius_km,
                            nearby[0]["distance_km"],
                            nearby[0]["name"],
                        )
                    else:
                        logger.debug("Geen sondes binnen %.1f km", radius_km)
            else:
                logger.debug("Nog geen geldige GPS-positie.")

            time.sleep(1)

        except Exception as e:
            logger.exception("Fout in proximity-loop: %s", e)
            time.sleep(2)
