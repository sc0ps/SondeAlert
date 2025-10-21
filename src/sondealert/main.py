# src/sondealert/main.py
import threading
import time
import signal
import sys

from . import gps, proximity, radiosondy, webserver, config
from .utils import get_logger

logger = get_logger("main")

# === HOOFDSTARTUP ===
def main():
    logger.info("=== SondeAlert gestart ===")

    try:
        # 1️⃣ Laad instellingen
        settings = config.load_settings()
        logger.info("Instellingen geladen: %s", settings)

        # 2️⃣ Update radiosonde-lijst (indien verouderd)
        if radiosondy.needs_update():
            logger.info("Radiosonde-lijst verouderd — nieuwe download gestart.")
            radiosondy.update_sonde_list()
        else:
            logger.info("Bestaande lijst is nog actueel.")

        # 3️⃣ Start de GPS-thread
        gps_thread = threading.Thread(target=gps.start_gps_thread, daemon=True)
        gps_thread.start()
        logger.info("GPS-thread gestart.")

        # 4️⃣ Start de proximity-thread
        prox_thread = threading.Thread(target=proximity.run, daemon=True)
        prox_thread.start()
        logger.info("Proximity-thread gestart.")

        # 5️⃣ Start de webserver
        webserver.start_server()
        logger.info("Webserver gestart en bereikbaar.")

        # 6️⃣ Houd het hoofdproces actief
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.warning("SondeAlert handmatig gestopt (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        logger.exception("Onverwachte fout in hoofdloop: %s", e)
        sys.exit(1)


# === SIGNAALHANDLING (Docker-friendly) ===
def signal_handler(sig, frame):
    logger.info("SondeAlert stopt door signaal (%s).", sig)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
