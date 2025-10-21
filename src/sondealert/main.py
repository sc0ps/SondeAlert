import time, threading
from .config import load_settings, save_settings
from .gps import start as start_gps
from .radiosondy import build_filtered_list, need_update
from .proximity import start_proximity
from .webserver import start as start_web

def main():
    print("=== SondeAlert gestart ===")

    settings = load_settings()
    save_settings(settings)

    if need_update():
        try:
            build_filtered_list()
        except Exception as e:
            print("[WARN] Kon dataset niet bijwerken:", e)
    else:
        print("[INIT] Bestaande lijst is nog actueel.")

    # Start threads
    threading.Thread(target=start_gps, args=(settings,), daemon=True).start()
    threading.Thread(target=start_proximity, daemon=True).start()
    threading.Thread(target=start_web, args=(settings.get("BIND_HOST", "0.0.0.0"), settings.get("BIND_PORT", 8080)), daemon=True).start()

    # Hoofdlus
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
