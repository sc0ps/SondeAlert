import threading
import logging
import time

from . import gps, proximity, radiosondy, webserver, config

logger = logging.getLogger("main")

def main():
    logger.info("=== SondeAlert gestart ===")

    # ⬇️ Configuratie laden
    settings = config.load_settings()
    logger.info(f"Instellingen geladen: {settings}")

    # ⬇️ Radiosonde-lijst ophalen
    try:
        if radiosondy.is_outdated(settings):
            logger.info("Radiosonde-lijst verouderd — nieuwe download gestart.")
            radiosondy.update_sonde_list()
        else:
            logger.info("Bestaande lijst is nog actueel.")
    except Exception as e:
        logger.error(f"Fout bij laden van radiosonde-lijst: {e}")

    # ⬇️ GPS-thread starten
    try:
        gps_thread = threading.Thread(
            target=gps.start_gps_listener,
            args=(settings.get("GPS_PORT", 5050),),
            daemon=True
        )
        gps_thread.start()
        logger.info("GPS-thread gestart.")
    except Exception as e:
        logger.error(f"Kon GPS-thread niet starten: {e}")

    # ⬇️ Proximity-thread starten
    try:
        prox_thread = threading.Thread(
            target=proximity.start_proximity_loop,
            args=(settings,),
            daemon=True
        )
        prox_thread.start()
        logger.info("Proximity-thread gestart.")
    except Exception as e:
        logger.error(f"Kon proximity-thread niet starten: {e}")

    # ⬇️ Webserver starten
    try:
        webserver.start_server(
            host=settings.get("BIND_HOST", "0.0.0.0"),
            port=settings.get("BIND_PORT", 8080)
        )
    except Exception as e:
        logger.error(f"Kon webserver niet starten: {e}")

    # ⬇️ Hoofdloop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("SondeAlert afgesloten door gebruiker.")
    except Exception as e:
        logger.error(f"Onverwachte fout in hoofdloop: {e}", exc_info=True)


if __name__ == "__main__":
    main()
