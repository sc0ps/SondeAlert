import csv
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from .config import OUT_JSON, TMP_ZIP, LAST_ZIP, RADIOSONDY_ZIP_URL

# mogelijke kolomnamen in CSV’s
C_DATE  = {"DateTime", "Last Frame [UTC]", "LastFrameUTC", "Last frame [UTC]", "Last frame"}
C_LAT   = {"Latitude", "φ", "lat", "latitude"}
C_LON   = {"Longitude", "λ", "lon", "longitude"}
C_ALT   = {"Altitude", "alt", "Altitude [m]", "Alt"}
C_STAT  = {"Status", "status"}
C_ID    = {"SONDE", "Number", "number", "ID", "id"}
C_PLACE = {"StartPlace", "Launch Site", "Nearest City", "Nearest city", "Startplace", "Start place"}

def _hdr(row, candidates):
    """zoek de juiste kolomnaam in CSV"""
    for k in row.keys():
        if not k:
            continue
        kk = k.strip()
        if kk in candidates or kk.lower() in {c.lower() for c in candidates}:
            return k
    return None

def _to_float(s):
    try:
        if s is None:
            return None
        s = str(s).strip().replace(",", ".")
        return float(s)
    except Exception:
        return None

def _fetch_zip(url: str, path: str):
    """download ZIP-bestand van radiosondy.info"""
    headers = {"User-Agent": "Mozilla/5.0 SondeAlert/1.0"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())
    print(f"[INIT] Download OK → {path} ({os.path.getsize(path)/1024:.1f} KB)", file=sys.stderr)

def _parse_zip_all_csv(path: str):
    """yield alle CSV’s in het ZIP-bestand"""
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as f:
                raw = f.read()
                # probeer meerdere encodings
                for enc in ("utf-8", "cp1250", "latin-1"):
                    try:
                        text = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                text = text.lstrip("\ufeff")
                reader = csv.DictReader(io.StringIO(text), delimiter=";")
                yield name, reader

def _in_last_months(dt: datetime, months: int) -> bool:
    now = datetime.now(timezone.utc)
    return (now - dt) <= timedelta(days=int(months * 30.44))

def _matches_launch(v: str, launch_filters) -> bool:
    if not v:
        return False
    s = v.strip().lower()
    return any(tag.lower() in s for tag in launch_filters)

def build_filtered_list(settings: dict):
    """Download radiosondy-data en filter deze naar een compact JSON-formaat."""
    months_back    = int(settings.get("MONTHS_BACK", 24))
    status_keep    = set((settings.get("STATUS_KEEP") or []))
    alt_max_m      = float(settings.get("ALT_MAX_M", 600.0))
    launch_filters = settings.get("LAUNCH_FILTERS") or []

    # 1) download ZIP
    _fetch_zip(RADIOSONDY_ZIP_URL, TMP_ZIP)

    kept = []
    total_rows = 0

    # 2) parse alle CSV’s in ZIP
    for name, reader in _parse_zip_all_csv(TMP_ZIP):
        first = None
        for r in reader:
            first = r
            break
        if not first:
            continue

        k_date  = _hdr(first, C_DATE)  or "Last Frame [UTC]"
        k_lat   = _hdr(first, C_LAT)   or "Latitude"
        k_lon   = _hdr(first, C_LON)   or "Longitude"
        k_alt   = _hdr(first, C_ALT)
        k_stat  = _hdr(first, C_STAT)  or "Status"
        k_id    = _hdr(first, C_ID)    or "ID"
        k_place = _hdr(first, C_PLACE) or "Nearest City"

        if not k_alt:
            # heuristiek (sommige exports hebben geen 'Altitude' header)
            cols = list(first.keys())
            if len(cols) >= 8:
                k_alt = cols[7]

        def all_rows(first_row, r):
            yield first_row
            for rr in r:
                yield rr

        for row in all_rows(first, reader):
            total_rows += 1
            try:
                status = (row.get(k_stat, "") or "").strip().upper()
                if status and status_keep and status not in status_keep:
                    continue

                place = (row.get(k_place, "") or "").strip()
                if launch_filters and not _matches_launch(place, launch_filters):
                    continue

                dts = (row.get(k_date, "") or "").strip()
                if not dts:
                    continue
                dt = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        dt = datetime.strptime(dts, fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                if not dt or not _in_last_months(dt, months_back):
                    continue

                lat = _to_float(row.get(k_lat))
                lon = _to_float(row.get(k_lon))
                alt = _to_float(row.get(k_alt))
                if lat is None or lon is None:
                    continue
                if alt is not None and alt > alt_max_m:
                    continue

                kept.append({
                    "id": str(row.get(k_id) or "").strip(),
                    "last": dt.isoformat().replace("+00:00", "Z"),
                    "lat": float(lat),
                    "lon": float(lon),
                    "alt": float(alt) if alt is not None else None,
                    "status": status,
                    "place": place,
                })
            except Exception:
                continue

    # 3) schrijf compact JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"items": kept}, f, indent=2, ensure_ascii=False)
    print(f"[INIT] {OUT_JSON}: {len(kept)} records uit {total_rows} rijen", file=sys.stderr)

    # 4) bewaar laatste ZIP
    try:
        os.replace(TMP_ZIP, LAST_ZIP)
    except Exception as e:
        print(f"[!] Kon ZIP niet bewaren: {e}", file=sys.stderr)

def need_update(settings: dict) -> bool:
    """Bepaal of de data opnieuw gedownload moet worden."""
    path = OUT_JSON
    if not os.path.exists(path):
        return True
    age_h = (time.time() - os.path.getmtime(path)) / 3600.0
    return age_h >= int(settings.get("UPDATE_HOURS", 24))
