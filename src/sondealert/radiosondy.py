import os
import io
import csv
import json
import zipfile
import time
import urllib.request
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("radiosondy")

# === Config ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SONDES_FILE = os.path.join(DATA_DIR, "sondes.json")
TMP_ZIP = os.path.join(DATA_DIR, "radiosondy_tmp.zip")

RADIOSONDY_URL = "https://radiosondy.info/export/export_csv.php?ListDown=1&all_csv=1"


def _to_float(x):
    """Converteer een tekstwaarde naar float (ook met komma’s)."""
    try:
        return float(str(x).strip().replace(",", "."))
    except Exception:
        return None


def _fetch_zip(url, dest):
    """Download het ZIP-bestand van radiosondy.info."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SondeAlert/1.0 (RaspberryPi)"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            f.write(r.read())
        logger.info("ZIP-bestand succesvol gedownload.")
        return True
    except Exception as e:
        logger.error(f"Download mislukt: {e}")
        return False


def _parse_zip(zip_path, settings):
    """Ontzip en filter de radiosonde-data volgens instellingen."""
    status_keep = set(x.upper() for x in settings.get("STATUS_KEEP", []))
    launch_filters = [x.lower() for x in settings.get("LAUNCH_FILTERS", [])]
    months_back = int(settings.get("MONTHS_BACK", 24))
    alt_max = float(settings.get("ALT_MAX_M", 600))

    kept = []
    total = 0

    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            logger.info(f"Parsing {name}")
            with zf.open(name) as f:
                text = f.read().decode("latin-1", errors="ignore").lstrip("\ufeff")
                reader = csv.DictReader(io.StringIO(text), delimiter=";")
                for row in reader:
                    total += 1
                    try:
                        status = (row.get("Status", "") or "").upper()
                        if status not in status_keep:
                            continue

                        place = (row.get("StartPlace", "") or "").lower()
                        if launch_filters and not any(x in place for x in launch_filters):
                            continue

                        dts = row.get("DateTime", "")
                        try:
                            dt = datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            continue
                        if (datetime.utcnow() - dt) > timedelta(days=months_back * 30):
                            continue

                        lat = _to_float(row.get("Latitude"))
                        lon = _to_float(row.get("Longitude"))
                        alt = _to_float(row.get("Altitude"))
                        if None in (lat, lon, alt) or alt > alt_max:
                            continue

                        kept.append({
                            "id": row.get("SONDE", "").strip(),
                            "lat": lat,
                            "lon": lon,
                            "alt": alt,
                            "status": status,
                            "last": dts,
                            "place": row.get("StartPlace", ""),
                            "src": name
                        })
                    except Exception:
                        continue

    logger.info(f"{len(kept)} sondes behouden van {total} totaal.")
    json.dump({"generated": int(time.time()), "count": len(kept), "items": kept},
              open(SONDES_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return kept


def is_outdated(settings):
    """Controleer of sondes.json verouderd is."""
    if not os.path.exists(SONDES_FILE):
        return True
    max_age_h = float(settings.get("UPDATE_HOURS", 24))
    age_h = (time.time() - os.path.getmtime(SONDES_FILE)) / 3600
    return age_h > max_age_h


def load_sondes():
    """Laad de laatst bekende sondelijst."""
    if not os.path.exists(SONDES_FILE):
        return []
    try:
        data = json.load(open(SONDES_FILE, "r", encoding="utf-8"))
        return data.get("items", [])
    except Exception as e:
        logger.warning(f"Kon sondes.json niet laden: {e}")
        return []


def update_sondes(settings):
    """Update de lijst van sondes indien verouderd."""
    if not os.path.exists(os.path.dirname(SONDES_FILE)):
        os.makedirs(os.path.dirname(SONDES_FILE), exist_ok=True)

    if is_outdated(settings):
        logger.info("Radiosonde-lijst verouderd — nieuwe download gestart.")
        if _fetch_zip(RADIOSONDY_URL, TMP_ZIP):
            return _parse_zip(TMP_ZIP, settings)
        else:
            logger.error("Download mislukt — behoud bestaande lijst.")
            return load_sondes()
    else:
        logger.info("Bestaande sondelijst is nog actueel.")
        return load_sondes()
