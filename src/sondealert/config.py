import json, os

# Basispaden
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUT_JSON = os.path.join(DATA_DIR, "sondes.json")
TMP_ZIP  = os.path.join(DATA_DIR, "radiosondy_archive.zip")
LAST_ZIP = os.path.join(DATA_DIR, "radiosondy_last.zip")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

RADIOSONDY_ZIP_URL = "https://radiosondy.info/export/export_csv.php?ListDown=1&all_csv=1"

# Standaardinstellingen
DEFAULTS = {
    "MONTHS_BACK": 24,
    "STATUS_KEEP": ["UNKNOWN", "NEED ATTENTION"],
    "LAUNCH_FILTERS": ["DE BILT (NL)", "DE BILT"],
    "ALT_MAX_M": 600.0,
    "UPDATE_HOURS": 24,
    "BUZZER_ENABLED": True,
    "NEAR_THRESHOLD_M": 15000.0,
    "GPS_PORT": 5050,
    "BIND_HOST": "0.0.0.0",
    "BIND_PORT": 8080,
}

def load_settings() -> dict:
    """Lees instellingen of gebruik defaults"""
    s = DEFAULTS.copy()
    if os.path.exists(SETTINGS_PATH):
        try:
            s.update(json.load(open(SETTINGS_PATH, "r")))
        except Exception as e:
            print("[!] Kon settings.json niet laden:", e)
    s["STATUS_KEEP"] = [x.upper() for x in s.get("STATUS_KEEP", [])]
    return s

def save_settings(s: dict):
    """Schrijf instellingen naar bestand"""
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2)