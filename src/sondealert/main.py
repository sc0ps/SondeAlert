#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import logging
import time

from . import gps, proximity, radiosondy, webserver, config

logger = logging.getLogger("main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

def main():
    logger.info("=== SondeAlert gestart ===")

    # === 1. Laad instellingen ===
    try:
        settings = config.load_settings()
        config.save_settings(settings)
        logger.info(f"Instellingen geladen: {settings}")
    except Exception as e:
        logger.error(f"Fout bij laden van instellingen: {e}")
        return

    # === 2. Radiosonde-lijst laden of bijwerken ===
    try:
        sondes = radiosondy.update_sondes(settings)
        logger.info(f"{len(sondes)} sondes geladen uit /app/src/data/sondes.json")
    except Exception as e:
        logger.error(f"Fout bij laden of bijwerken van radiosonde-lijst: {e}")

    # === 3. GPS-thread starten ===
    try:
        threading.Thread(
            target=gps.start_gps_thread, args=(settings,), daemon=True
        ).start()
        logger.info("GPS-thread gestart.")
    except Exception as e:
        logger.error(f"Kon GPS-thread niet starten: {e}")

    # === 4. Proximity-thread starten ===
    try:
        threading.Thread(
            target=proximity.start_proximity_loop, args=(settings,), daemon=True
        ).start()
        logger.info("Proximity-thread gestart.")
    except Exception as e:
        logger.error(f"Kon proximity-thread niet starten: {e}")

    # === 5. Webserver starten ===
    try:
        webserver.start_server(settings)
        logger.info("Webserver gestart op http://0.0.0.0:8080/")
    except Exception as e:
        logger.error(f"Webserver-fout: {e}", exc_info=True)

    # === 6. Updater-thread voor sondelijst (periodiek) ===
    def updater_loop():
        while True:
            try:
                sondes = radiosondy.update_sondes(settings)
                logger.info(f"Updater: {len(sondes)} sondes geladen / vernieuwd.")
            except Exception as e:
                logger.error(f"Updater-fout: {e}")
            time.sleep(float(settings.get("UPDATE_HOURS", 24)) * 3600)

    threading.Thread(target=updater_loop, daemon=True).start()

    # === Hoofdloop actief houden ===
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
