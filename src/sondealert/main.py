import threading
import logging
from . import gps, proximity, radiosondy, webserver, config

logger = logging.getLogger("main")

def main():
    logger.info("=== SondeAlert gestart ===")

    # Laad instellingen
    settings = config.load_settings()
    config.save_settings(settings)
    logger.info(f"Instellingen geladen: {settings}")

    # === Update of laad sondelijst ===
    try:
        sondes = radiosondy.update_sondes(settings)   # ✅ juiste functie
        logger.info(f"{len(sondes)} sondes geladen uit /app/data/sondes.json")
    except Exception as e:
        logger.error(f"Fout bij laden of bijwerken van radiosonde-lijst: {e}")

    # === Start GPS-thread ===
    try:
        gps.start_gps_thread(settings)
        logger.info("GPS-thread gestart.")
    except Exception as e:
        logger.error(f"Kon GPS-thread niet starten: {e}")

    # === Start proximity-thread ===
    try:
        threading.Thread(
            target=proximity.start_proximity_loop, args=(settings,), daemon=True
        ).start()
        logger.info("Proximity-thread gestart.")
    except Exception as e:
        logger.error(f"Kon proximity-thread niet starten: {e}")

    # === Start webserver ===
    try:
        webserver.start_server(settings)
    except Exception as e:
        logger.error(f"Webserver-fout: {e}", exc_info=True)


if __name__ == "__main__":
    main()
