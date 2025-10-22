# /app/src/sondealert/radiosondy.py
import os, io, csv, zipfile, time, json, logging, urllib.request
from datetime import datetime, timedelta
from .config import DATA_DIR, SONDES_FILE

RADIOSONDY_ZIP_URL = "https://radiosondy.info/export/export_csv.php?ListDown=1&all_csv=1"
TMP_ZIP  = os.path.join(DATA_DIR, "radiosondy_tmp.zip")
LAST_ZIP = os.path.join(DATA_DIR, "radiosondy_last.zip")

def _fetch_zip():
    req = urllib.request.Request(
        RADIOSONDY_ZIP_URL,
        headers={"User-Agent": "Mozilla/5.0 SondeAlert"}
    )
    with urllib.request.urlopen(req, timeout=300) as r, open(TMP_ZIP, "wb") as f:
        f.write(r.read())
    logging.info("[radiosondy] ZIP-bestand succesvol gedownload.")

def is_outdated(update_hours):
    if not os.path.exists(SONDES_FILE): return True
    age_h = (time.time() - os.path.getmtime(SONDES_FILE))/3600
    return age_h >= float(update_hours)

def _to_float(s):
    try: return float(str(s).strip().replace(",", "."))
    except: return None

def _dt_utc(s):
    try: return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except: return None

def update_sonde_list(settings):
    logging.info("[radiosondy] Download en verwerking van nieuwe radiosonde-lijst gestart...")
    _fetch_zip()

    kept = []
    months_back = int(settings["MONTHS_BACK"])
    status_keep = set(x.upper() for x in settings["STATUS_KEEP"])
    alt_max     = float(settings["ALT_MAX_M"])
    launch_filters = [x.lower() for x in settings["LAUNCH_FILTERS"]]

    cutoff = datetime.utcnow() - timedelta(days=months_back*30)

    total = 0
    with zipfile.ZipFile(TMP_ZIP) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"): continue
            logging.info("[radiosondy] Parsing %s", name)
            with zf.open(name) as f:
                text = f.read().decode("latin-1", errors="ignore").lstrip("\ufeff")
                reader = csv.DictReader(io.StringIO(text), delimiter=";")
                for row in reader:
                    total += 1
                    st = (row.get("Status","") or "").upper()
                    if st not in status_keep: continue
                    place = (row.get("StartPlace","") or "")
                    if launch_filters and not any(x in place.lower() for x in launch_filters):
                        continue
                    dt = _dt_utc(row.get("DateTime",""))
                    if not dt or dt < cutoff: continue
                    lat = _to_float(row.get("Latitude")); lon = _to_float(row.get("Longitude"))
                    alt = _to_float(row.get("Altitude"))
                    if None in (lat, lon, alt): continue
                    if alt > alt_max: continue
                    kept.append({
                        "id": (row.get("SONDE") or "").strip(),
                        "lat": lat, "lon": lon, "alt": alt,
                        "status": st, "last": row.get("DateTime",""),
                        "place": place, "src": name
                    })

    payload = {"generated": int(time.time()), "count": len(kept), "items": kept}
    with open(SONDES_FILE, "w") as f:
        json.dump(payload, f, ensure_ascii=False)
    if os.path.exists(TMP_ZIP):
        try: os.replace(TMP_ZIP, LAST_ZIP)
        except: pass

    logging.info("[radiosondy] %d sondes behouden van %d totaal.", len(kept), total)
    return payload
