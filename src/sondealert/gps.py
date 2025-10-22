import logging
import socket
import time

log = logging.getLogger("gps")

_last_position = {"lat": None, "lon": None, "fix": False}


def start():
    """Start een thread die UDP GPS-data ontvangt."""
    log.info("GPS thread started.")
    port = 5050  # default UDP port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(1.0)
    log.info(f"Listening on UDP port {port} for GPS data")

    while True:
        try:
            data, _ = sock.recvfrom(2048)
            text = data.decode(errors="ignore").strip()
            parts = text.split(",")

            if parts[0].endswith("GGA") and len(parts) > 5:
                lat = _to_decimal(parts[2], parts[3])
                lon = _to_decimal(parts[4], parts[5])
                if lat and lon:
                    _last_position.update({"lat": lat, "lon": lon, "fix": True})
                    log.info(f"Received GPS position: {lat:.5f}, {lon:.5f} (fix=True)")
            time.sleep(0.1)
        except socket.timeout:
            continue
        except Exception as e:
            log.warning(f"GPS error: {e}")
            time.sleep(1)


def _to_decimal(coord, hemi):
    """Converteer NMEA naar decimale graden."""
    if not coord:
        return None
    try:
        raw = float(coord)
        deg = int(raw / 100)
        minutes = raw - deg * 100
        dec = deg + minutes / 60.0
        if hemi in ("S", "W"):
            dec = -dec
        return dec
    except:
        return None


def get_last_position():
    """Geeft laatste GPS-positie terug als tuple."""
    return _last_position["lat"], _last_position["lon"], _last_position["fix"]
