import csv, io, json, os, sys, time, zipfile
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
    except:
        return None

def _fetch_zip(url: str, path: str):
    """download ZIP-bestand van radiosondy.info"""
    headers = {"User-Agent": "Mozilla/5.0 SondeAlert/1.0"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())
    print(f"[✓] Download OK → {path} ({os.path.getsize(path)/1024:.1f} KB)", file=sys.stderr)

def _parse_zip_all_csv(path: str):
    """yield alle CSV’s in het ZIP-bestand"""
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as f:
                raw = f.read()
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
    """controleer of de datum binnen X maanden ligt"""
    now = datetime.now(timezone.utc)
    return (now - dt) <= timedelta(days=int(months * 30.44))

def _matches_launch(v: str, launch_filters) -> bool:
    if not v:
        return False
    s = v.strip().lower()
    return any(tag.lower() in s for tag in launch_filters)

def build_filtered_list(settings: dict):
    """download radiosondy-data en filter deze"""
    months = int(settings["MONTHS_BACK"])
    status_keep = set(x.upper() for x in settings["STATUS_KEEP"])
    launch_filters = settings["LAUNCH_FILTERS"]
    alt_max = float(settings["ALT_MAX_M"])

    if os.path.exists(TMP_ZIP):
        try:
            os.remove(TMP_ZIP)
        except:
            pass

    try:
        _fetch_zip(RADIOSONDY_ZIP_URL, TMP_ZIP)
    except Exception as e:
        print(f"[!] Download mislukt: {e}", file=sys.stderr)
        if os.path.exists(LAST_ZIP):
            print("[i] Gebruik vorige lokale ZIP", file=sys.stderr)
            os.replace(LAST_ZIP, TMP_ZIP)
        else:
            raise

    kept, total_rows = [], 0
    for name, reader in _parse_zip_all_csv(TMP_ZIP):
        print(f"↳ parsing {name}", file=sys.stderr)
        first = next(reader, None)
        if not first:
            continue

        k_date = _hdr(first, C_DATE)
        k_lat  = _hdr(first, C_LAT)
        k_lon  = _hdr(first, C_LON)
        k_alt  = _hdr(first, C_ALT)
        k_stat = _hdr(first, C_STAT)
        k_id   = _hdr(first, C_ID)
        k_place= _hdr(first, C_PLACE)

        # fallback als hoogte niet gevonden wordt
        if not k_alt:
            cols = list(first.keys())
            if len(cols) >= 8:
                k_alt = cols[7]

        def all_rows(first, r):
            yield first
            for rr in r:
                yield rr

        for row in all_rows(first, reader):
            total_rows += 1
            try:
                status = (row.get(k_stat, "") or "").strip().upper()
                if status not in status_keep:
                    continue

                place = (row.get(k_place, "") or "").strip()
                if not _matches_launch(place, launch_filters):
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
                        pass
                if dt is None or not _in_last_months(dt, months):
                    continue

                lat = _to_float(row.get(k_lat))
                lon = _to_float(row.get(k_lon))
                if lat is None or lon is None:
                    continue

                alt = _to_float(row.get(k_alt))
                if alt is None or alt >= alt_max:
                    continue

                kept.append({
                    "id": (row.get(k_id, "") or "").strip(),
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "status": status,
                    "last": dts,
                    "place": place,
                    "src": name
                })
            except Exception:
                continue

    kept.sort(key=lambda x: x["last"], reverse=True)
    out = {"generated": int(time.time()), "count": len(kept), "items": kept}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[✓] {OUT_JSON}: {len(kept)} records uit {total_rows} rijen", file=sys.stderr)

    try:
        os.replace(TMP_ZIP, LAST_ZIP)
    except Exception as e:
        print(f"[!] Kon ZIP niet bewaren: {e}", file=sys.stderr)

def need_update(settings: dict) -> bool:
    """bepaal of de data opnieuw gedownload moet worden"""
    path = OUT_JSON
    if not os.path.exists(path):
        return True
    age_h = (time.time() - os.path.getmtime(path)) / 3600
    return age_h >= int(settings["UPDATE_HOURS"])