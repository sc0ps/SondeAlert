import os
import time
import zipfile
import csv
import io
import json
import requests
from datetime import datetime, timedelta
from .utils import get_logger

logger = get_logger("radiosondy")

# === CONSTANTEN ===
RADIOSONDY_URL = "https://radiosondy.info/export/latest.zip"
DATA_DIR = "data"
SONDES_JSON = os.path.join(DATA_DIR, "sondes.json")
UPDATE_INTERVAL_HOURS = 24  # standaard, tenzij overschreven door settings


# === 1️⃣ CONTROLEREN OF UPDATE NODIG IS ===
def needs_update(hours: int = UPDATE_INTERVAL_HOURS) -> bool:
    """
    Controleert of de lokale sondelijst ouder is dan 'hours' uur.
    True = nieuwe download vereist.
    """
    try:
        if not os.path.exists(SONDES_JSON):
            logger.info("Geen lokale sondelijst gevonden — update vereist.")
            return True

        modified_time = datetime.fromtimestamp(os.path.getmtime(SONDES_JSON))
        age = datetime.now() - modified_time
        if age > timedelta(hours=hours):
            logger.info(
                "Sondelijst is ouder dan %d uur (laatste wijziging: %s)",
                hours, modified_time.strftime("%Y-%m-%d %H:%M:%S")
            )
            return True

        logger.info("Bestaande sondelijst is nog actueel (laatste wijziging: %s)",
                    modified_time.strftime("%Y-%m-%d %H:%M:%S"))
        return False

    except Exception as e:
        logger.exception("Fout bij controleren update-status: %s", e)
        return True


# === 2️⃣ DOWNLOAD EN PARSE SONDELIJST ===
def update_sonde_list():
    """
    Downloadt het radiosonde-archief (ZIP) en filtert de recente sondes.
    Resultaat wordt opgeslagen als data/sondes.json.
    """
    try:
        logger.info("Download en verwerking van nieuwe radiosonde-lijst gestart...")
        os.makedirs(DATA_DIR, exist_ok=True)

        response = requests.get(RADIOSONDY_URL, timeout=30)
        if response.status_code != 200:
            logger.error("Download mislukt met status %d", response.status_code)
            return

        # ZIP-bestand inlezen vanuit geheugen
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_name = [f for f in z.namelist() if f.endswith(".csv")][0]
            with z.open(csv_name) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, "utf-8"))
                sondes = []

                for row in reader:
                    try:
                        # Filter op hoogte, status en leeftijd
                        alt = float(row.get("alt", 0))
                        status = row.get("status", "").strip()
                        time_str = row.get("time", "")
                        lat = float(row.get("lat", 0))
                        lon = float(row.get("lon", 0))
                        name = row.get("name", "").strip()

                        # Alleen recente, lage sondes
                        if alt < 600 and status in ["UNKNOWN", "NEED ATTENTION"]:
                            sondes.append({
                                "name": name,
                                "lat": lat,
                                "lon": lon,
                                "alt": alt,
                                "status": status,
                                "time": time_str
                            })
                    except Exception as e:
                        logger.debug("Fout bij verwerken rij: %s", e)

        # Schrijf naar JSON
        with open(SONDES_JSON, "w", encoding="utf-8") as out:
            json.dump(sondes, out, indent=2, ensure_ascii=False)

        logger.info("Nieuwe sondelijst succesvol opgeslagen (%d records)", len(sondes))

    except Exception as e:
        logger.exception("Fout tijdens update van sondelijst: %s", e)


# === 3️⃣ HULPFUNCTIE OM MANUEEL TE TESTEN ===
if __name__ == "__main__":
    logger.info("Test-run van radiosondy-module gestart.")
    if needs_update():
        update_sonde_list()
    else:
        logger.info("Geen update nodig.")
