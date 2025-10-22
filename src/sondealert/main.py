import threading
import logging
from . import gps, proximity, radiosondy, webserver, config

logger = logging.getLogger("main")


def main():
    logger.info("=== SondeAlert gestart ===")

    # 🔧 Instellingen laden
    try:
        settings = config.load_settings()
        logger.info(f"Instellingen geladen: {settings}")
    except Exception as e:
        logger.error(f"Fout bij laden van instellingen: {e}")
        return

    # 📡 Radiosonde-lijst bijwerken indien verouderd
    try:
        if radiosondy.is_outdated(settings):
            radiosondy.update_sonde_list()
        else:
            logger.info("Bestaande lijst is nog actueel.")
    except Exception as e:
        logger.error(f"Fout bij laden of bijwerken van radiosonde-lijst: {e}")

    # 🛰️ Start GPS-thread
    try:
        gps.start_gps_thread(settings)
        logger.info("GPS-thread gestart.")
    except Exception as e:
        logger.error(f"Kon GPS-thread niet starten: {e}")

    # 📍 Start proximity-thread
    try:
        proximity_thread = threading.Thread(
            target=proximity.start_proximity_loop, args=(settings,), daemon=True
        )
        proximity_thread.start()
        logger.info("Proximity-thread gestart.")
    except Exception as e:
        logger.error(f"Kon proximity-thread niet starten: {e}")

    # 🌐 Start webserver
    try:
        webserver.start_server(settings)
        logger.info(
            f"Webserver gestart op http://{settings.get('BIND_HOST', '0.0.0.0')}:{settings.get('BIND_PORT', 8080)}/"
        )
    except Exception as e:
        logger.error(f"Webserver-fout: {e}")


if __name__ == "__main__":
    # Basis loggingconfiguratie
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
