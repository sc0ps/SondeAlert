# /app/src/sondealert/config.py
import json, os, logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
SONDES_FILE   = os.path.join(DATA_DIR, "sondes.json")

DEFAULTS = {
    "MONTHS_BACK": 24,
    "STATUS_KEEP": ["UNKNOWN", "NEED ATTENTION"],
    "LAUNCH_FILTERS": ["DE BILT (NL)", "DE BILT"],
    "ALT_MAX_M": 600,
    "UPDATE_HOURS": 24,
    "BUZZER_ENABLED": True,
    "NEAR_THRESHOLD_M": 15000,
    "GPS_PORT": 5050,
    "BIND_HOST": "0.0.0.0",
    "BIND_PORT": 8080
}

def load_settings():
    s = DEFAULTS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                s.update(json.load(f))
        except Exception as e:
            logging.warning("Kon settings.json niet laden: %s", e)
    # normaliseer
    s["STATUS_KEEP"] = [x.upper() for x in s.get("STATUS_KEEP", [])]
    return s

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)
    logging.info("[config] Instellingen opgeslagen in %s", SETTINGS_FILE)
