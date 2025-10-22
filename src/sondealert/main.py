# /app/src/sondealert/main.py
import threading, logging, time
from .config import load_settings, save_settings
from . import radiosondy, gps, proximity, buzzer, webserver
from .state import set_last_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("main")

def main():
    log.info("=== SondeAlert gestart ===")
    settings = load_settings()
    save_settings(settings)  # ensure file exists
    log.info("Instellingen geladen: %s", settings)

    # Update lijst bij start indien verouderd
    try:
        if radiosondy.is_outdated(settings["UPDATE_HOURS"]):
            log.info("[radiosondy] Radiosonde-lijst verouderd — nieuwe download gestart.")
            payload = radiosondy.update_sonde_list(settings)
            set_last_update(payload["generated"], payload["count"])
        else:
            # laad meta uit bestaande file
            import json, os
            from .config import SONDES_FILE
            if os.path.exists(SONDES_FILE):
                with open(SONDES_FILE,"r") as f:
                    p = json.load(f)
                    set_last_update(p.get("generated",0), p.get("count",0))
    except Exception as e:
        log.warning("Fout bij laden of bijwerken van radiosonde-lijst: %s", e)

    # Threads
    threading.Thread(target=gps.start_gps_listener, args=(settings["GPS_PORT"],), daemon=True).start()
    threading.Thread(target=proximity.proximity_loop, args=(settings,), daemon=True).start()
    threading.Thread(target=buzzer.buzzer_loop, args=(settings,), daemon=True).start()
    threading.Thread(target=webserver.serve, args=(settings["BIND_HOST"], settings["BIND_PORT"]), daemon=True).start()

    # Periodieke auto-update (1x per uur check)
    def updater():
        while True:
            time.sleep(3600)
            try:
                if radiosondy.is_outdated(settings["UPDATE_HOURS"]):
                    payload = radiosondy.update_sonde_list(load_settings())
                    set_last_update(payload["generated"], payload["count"])
            except Exception as e:
                log.warning("Updater-fout: %s", e)

    threading.Thread(target=updater, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
