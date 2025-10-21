import time
import threading
from .config import load_settings, save_settings
from .gps import start as start_gps
from .radiosondy import build_filtered_list, need_update
from .proximity import start_proximity
from .webserver import start as start_web

def main():
    print("=== SondeAlert gestart ===")

    # Instellingen laden & normaliseren
    settings = load_settings()
    save_settings(settings)

    # Radiosondy dataset bijwerken indien nodig
    try:
        if need_update(settings):
            print("[INIT] Nieuwe radiosonde-data wordt opgehaald en gefilterd...")
            build_filtered_list(settings)
        else:
            print("[INIT] Bestaande lijst is nog actueel.")
    except Exception as e:
        print(f"[INIT] Fout bij updaten van radiosonde-data: {e}")

    # Threads starten
    threading.Thread(target=start_gps, args=(settings,), daemon=True).start()
    print(f"[GPS] Luistert op UDP-poort {settings.get('GPS_PORT', 5050)}")

    threading.Thread(target=start_proximity, daemon=True).start()
    print("[PROX] Afstandsbepaling gestart")

    # Webserver starten (eigen thread)
    host = settings.get("BIND_HOST", "0.0.0.0")
    port = int(settings.get("BIND_PORT", 8080))
    threading.Thread(target=start_web, args=(host, port), daemon=True).start()
    print(f"[WEB] bereikbaar op http://{host}:{port}/")

    # Hoofdlus — draai de daemon-threads
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Afsluiten op verzoek...")

if __name__ == "__main__":
    main()
