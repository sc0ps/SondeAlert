import json
import logging
import os
import time

log = logging.getLogger("radiosondy")

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/sondes.json")
_sondes = []


def is_outdated():
    """Check of de lokale lijst ouder is dan 24 uur."""
    if not os.path.exists(DATA_FILE):
        return True
    age_hours = (time.time() - os.path.getmtime(DATA_FILE)) / 3600
    return age_hours > 24


def load_local_sondes():
    """Laad bestaande sondes.json."""
    global _sondes
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _sondes = data.get("items", [])
            log.info(f"{len(_sondes)} sondes geladen uit {DATA_FILE}")
    else:
        log.warning("Geen sondes.json gevonden — lijst leeg.")
        _sondes = []


def get_all_sondes():
    """Retourneer geladen sondes."""
    return _sondes


def update_sonde_list():
    """Dummy-download (plaatsvervanger voor echte download)."""
    log.info("Update van radiosonde-lijst gestart (dummy).")
    time.sleep(5)
    # voorbeeldlijst
    dummy = [
        {"id": "X001", "lat": 52.1, "lon": 4.3, "alt": 120.0, "status": "UNKNOWN", "place": "De Bilt"},
        {"id": "X002", "lat": 51.9, "lon": 4.2, "alt": 180.0, "status": "NEED ATTENTION", "place": "Rotterdam"},
    ]
    save_sondes(dummy)
    log.info("Nieuwe radiosonde-lijst opgeslagen.")


def save_sondes(lst):
    """Schrijf lijst naar JSON-bestand."""
    data = {"generated": int(time.time()), "count": len(lst), "items": lst}
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log.info(f"Sondes opgeslagen ({len(lst)}) → {DATA_FILE}")
    load_local_sondes()
