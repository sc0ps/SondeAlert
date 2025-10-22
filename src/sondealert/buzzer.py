import logging
import time
from sondealert import proximity, config

log = logging.getLogger("buzzer")


def start():
    """Simuleer buzzer-activiteit op basis van afstand."""
    log.info("Buzzer gestart.")
    while True:
        try:
            sondes = proximity.get_nearby_sondes()
            if not sondes:
                time.sleep(1)
                continue

            nearest = sondes[0]
            distance = nearest.get("distance", 99999)
            settings = config.load_settings()
            enabled = settings.get("BUZZER_ENABLED", True)

            if not enabled:
                time.sleep(2)
                continue

            pattern(distance)
        except Exception as e:
            log.warning(f"Buzzer fout: {e}")
            time.sleep(1)


def pattern(distance):
    """Simuleer piep-patronen op basis van afstand."""
    if distance > 10000:
        log.info("📢 Buzzer: verre sonde (>10km)")
        time.sleep(3)
    elif distance > 5000:
        log.info("📢 Buzzer: middel afstand (~5-10km)")
        time.sleep(2)
    elif distance > 2000:
        log.info("📢 Buzzer: dichtbij (~2-5km)")
        time.sleep(1)
    else:
        log.info("📢 Buzzer: zeer dichtbij (<2km)")
        time.sleep(0.5)
