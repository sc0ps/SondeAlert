import json
import os
import logging
from pathlib import Path

log = logging.getLogger("config")

# 📁 Locatie van de instellingen in de container
SETTINGS_FILE = Path("/app/data/settings.json")

# 🔧 Standaardinstellingen (worden gebruikt als settings.json nog niet bestaat)
DEFAULT_SETTINGS = {
    "MONTHS_BACK": 24,
    "STATUS_KEEP": ["UNKNOWN", "NEED ATTENTION"],
    "LAUNCH_FILTERS": ["DE BILT (NL)", "DE BILT"],
    "ALT_MAX_M": 600,
    "UPDATE_HOURS": 24,
    "BUZZER_ENABLED": False,
    "NEAR_THRESHOLD_M": 15000,
    "GPS_PORT": 5050,
    "BIND_HOST": "0.0.0.0",
    "BIND_PORT": 8080,
}

# 🔄 Hulp: converteer booleans en ints van omgevingsvariabelen
def _convert_value(value):
    if isinstance(value, str):
        lower = value.lower()
        if lower in ("true", "yes", "1"):
            return True
        elif lower in ("false", "no", "0"):
            return False
        elif value.isdigit():
            return int(value)
    return value


def load_settings():
    """Laad instellingen uit bestand en combineer met environment variables."""
    settings = DEFAULT_SETTINGS.copy()

    # 📘 Laad lokale instellingen uit settings.json
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                user_settings = json.load(f)
                settings.update(user_settings)
                log.info(f"Instellingen geladen uit {SETTINGS_FILE}")
        except Exception as e:
            log.error(f"Fout bij laden instellingen: {e}")

    # 🌍 Overschrijf met environment-variabelen (bijv. uit docker-compose.yml)
    for key in settings.keys():
        if key in os.environ:
            settings[key] = _convert_value(os.environ[key])

    return settings


def save_settings(data):
    """Sla instellingen op naar bestand."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        log.info(f"Instellingen opgeslagen naar {SETTINGS_FILE}")
    except Exception as e:
        log.error(f"Fout bij opslaan instellingen: {e}")


def ensure_settings_file():
    """Maak settings.json aan met standaardwaarden als het nog niet bestaat."""
    if not SETTINGS_FILE.exists():
        log.info("settings.json niet gevonden, nieuw bestand aangemaakt met defaults.")
        save_settings(DEFAULT_SETTINGS)
