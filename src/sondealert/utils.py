# src/sondealert/utils.py
import math
import threading
import logging
import os

# === LOGGER ===
def get_logger(name="SondeAlert"):
    """
    Geeft een centraal geconfigureerde logger terug.
    Logniveau kan ingesteld worden via omgevingsvariabele LOG_LEVEL (default: INFO)
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    return logging.getLogger(name)


# === LOCK ===
state_lock = threading.Lock()

# === HULPFUNCTIES ===
def deg2rad(deg):
    """Converteert graden naar radialen."""
    return deg * (math.pi / 180.0)


def haversine(lat1, lon1, lat2, lon2):
    """
    Berekent de afstand in kilometers tussen twee GPS-coördinaten met de Haversine-formule.
    """
    R = 6371.0  # straal aarde in km
    dlat = deg2rad(lat2 - lat1)
    dlon = deg2rad(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# === TESTCODE ===
if __name__ == "__main__":
    logger = get_logger("test_utils")
    logger.info("Utils-module test gestart")

    # Test de haversine-functie met een bekende afstand (Den Haag ↔ Rotterdam)
    lat1, lon1 = 52.0705, 4.3007  # Den Haag
    lat2, lon2 = 51.9244, 4.4777  # Rotterdam
    afstand = haversine(lat1, lon1, lat2, lon2)
    logger.info("Afstand Den Haag ↔ Rotterdam: %.2f km", afstand)
