#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
import time

from sondealert import config, gps, proximity, radiosondy, webserver, buzzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

log = logging.getLogger("main")


def async_update_list():
    """Start de radiosonde-download in een aparte thread zodat de webserver blijft draaien."""
    try:
        log.info("[radiosondy] Asynchrone update gestart...")
        radiosondy.update_sonde_list()
        log.info("[radiosondy] Update voltooid.")
    except Exception as e:
        log.error(f"[radiosondy] Fout tijdens update: {e}")


def start_threads():
    """Start alle achtergrondthreads."""
    # GPS
    try:
        threading.Thread(target=gps.start_gps_thread, daemon=True).start()
        log.info("GPS-thread gestart.")
    except Exception as e:
        log.error(f"Kon GPS-thread niet starten: {e}")

    # Proximity
    try:
        threading.Thread(target=proximity.start_proximity_loop, daemon=True).start()
        log.info("Proximity-thread gestart.")
    except Exception as e:
        log.error(f"Kon proximity-thread niet starten: {e}")

    # Buzzer
    try:
        threading.Thread(target=buzzer.start_buzzer_loop, daemon=True).start()
        log.info("Buzzer-thread gestart.")
    except Exception as e:
        log.error(f"Kon buzzer-thread niet starten: {e}")

    # Webserver
    try:
        threading.Thread(target=webserver.start_web_server, daemon=True).start()
        log.info("Webserver gestart op http://0.0.0.0:8080/")
    except Exception as e:
        log.error(f"Kon webserver niet starten: {e}")


def main():
    log.info("=== SondeAlert gestart ===")

    # Laad of maak config
    cfg = config.load_settings()
    config.save_settings(cfg)
    log.info(f"Instellingen geladen: {cfg}")

    # Update radiosonde-lijst als deze verouderd is
    try:
        if radiosondy.is_outdated():
            log.info("[radiosondy] Radiosonde-lijst verouderd — nieuwe download gestart.")
            threading.Thread(target=async_update_list, daemon=True).start()
        else:
            log.info("[radiosondy] Radiosonde-lijst is nog actueel.")
            radiosondy.load_local_sondes()
    except Exception as e:
        log.error(f"Fout bij laden of bijwerken van radiosonde-lijst: {e}")

    # Start alle componenten
    start_threads()

    # Hoofdloop
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
