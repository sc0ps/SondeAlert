import threading, time
from .config import load_settings, save_settings
from .radiosondy import build_filtered_list, need_update
from . import gps as gps_module
from .proximity import start_proximity
from .webserver import start as start_web

def updater(settings: dict):
    """Controleer regelmatig of radiosondy-data vernieuwd moet worden"""
    while True:
        try:
            if need_update(settings):
                print("[UPDATER] Nieuwe download nodig — bouw lijst...")
                build_filtered_list(settings)
        except Exception as e:
            print("[UPDATER] Fout:", e)
        time.sleep(int(settings["UPDATE_HOURS"]) * 3600)

def main():
    print("=== SondeAlert gestart ===")
    settings = load_settings()
    save_settings(settings)  # zorg dat settings.json bestaat

    # eerste dataset laden of aanmaken
    try:
        if need_update(settings):
            print("[INIT] Download start...")
            build_filtered_list(settings)
        else:
            print("[INIT] Bestaande lijst is nog actueel.")
    except Exception as e:
        print("[INIT] Fout bij eerste build:", e)

    # Start alle componenten in threads
    gps_module.start(settings)
    start_proximity(settings, gps_module)
    start_web(settings)

    threading.Thread(target=updater, args=(settings,), daemon=True).start()

    # Hoofdlus blijft actief
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stop SondeAlert.")

if __name__ == "__main__":
    main()
