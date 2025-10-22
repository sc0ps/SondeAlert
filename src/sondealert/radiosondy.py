import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("radiosondy")

DATA_DIR = Path("/app/data")
SONDES_FILE = DATA_DIR / "sondes.json"
RADIOSONDY_URL = "https://radiosondy.info/export/json/active.json"


def is_outdated(settings):
    """Controleer of de lokale sondelijst ouder is dan de ingestelde tijd."""
    if not SONDES_FILE.exists():
        return True
    age_hours = settings.get("UPDATE_HOURS", 24)
    modified_time = datetime.fromtimestamp(SONDES_FILE.stat().st_mtime)
    outdated = datetime.now() - modified_time > timedelta(hours=age_hours)
    if outdated:
        logger.info(
            f"Sondelijst is ouder dan {age_hours} uur (laatste wijziging: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    else:
        logger.info(
            f"Bestaande sondelijst is nog actueel (laatste wijziging: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    return outdated


def update_sonde_list():
    """Download nieuwe sondelijst van radiosondy.info"""
    logger.info("Download en verwerking van nieuwe radiosonde-lijst gestart...")
    try:
        r = requests.get(RADIOSONDY_URL, timeout=15)
        if r.status_code != 200:
            logger.error(f"Download mislukt met status {r.status_code}")
            return False

        data = r.json()
        if not isinstance(data, list):
            logger.error("Onverwachte data-indeling bij radiosondy-download")
            return False

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SONDES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(data)} sondes opgeslagen in {SONDES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Fout bij downloaden of opslaan sondelijst: {e}")
        return False
