import json
import logging
from pathlib import Path

log = logging.getLogger("config")

DATA_DIR = Path(__file__).parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Standaardinstellingen
DEFAULT_SETTINGS = {
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


def ensure_settings_file():
    """Maakt settings.json aan als het niet bestaat."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)


def load_settings():
    """Laadt de instellingen uit settings.json."""
    ensure_settings_file()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        # Vul ontbrekende velden aan met defaults
        for k, v in DEFAULT_SETTINGS.items():
            settings.setdefault(k, v)
        return settings
    except Exception as e:
        log.error(f"Fout bij laden instellingen: {e}")
        return DEFAULT_SETTINGS


def save_settings(settings: dict):
    """Slaat instellingen op in settings.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        log.info(f"Instellingen opgeslagen in {SETTINGS_FILE}")
    except Exception as e:
        log.error(f"Fout bij opslaan instellingen: {e}")
