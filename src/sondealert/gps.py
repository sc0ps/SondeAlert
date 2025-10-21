import socket
import time
import threading
from .utils import state_lock

gps_have, gps_lat, gps_lon, gps_last = False, 0.0, 0.0, 0

def nmea_to_decimal(nmea, hemi):
    if not nmea:
        return None
    try:
        raw = float(nmea)
        deg, minutes = int(raw / 100), raw - int(raw / 100) * 100
        dec = deg + minutes / 60.0
        return -dec if hemi in ("S", "W") else dec
    except Exception:
        return None

def start(settings):
    """Luistert op UDP en verwerkt NMEA-data (RMC, GGA, GLL)."""
    port = int(settings.get("GPS_PORT", 5050))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.settimeout(1.0)

    def loop():
        global gps_have, gps_lat, gps_lon, gps_last
        while True:
            try:
                data, _ = s.recvfrom(4096)
                line = data.decode(errors="ignore").strip()
                if not line.startswith("$"):
                    continue

                parts = line.split(",")
                lat = lon = None

                # $GPRMC, $GPGGA -> reeds ondersteund
                if line.startswith("$GPRMC") and len(parts) > 6:
                    lat = nmea_to_decimal(parts[3], parts[4][:1] if len(parts[4]) else "")
                    lon = nmea_to_decimal(parts[5], parts[6][:1] if len(parts[6]) else "")
                elif line.startswith("$GPGGA") and len(parts) > 5:
                    lat = nmea_to_decimal(parts[2], parts[3][:1] if len(parts[3]) else "")
                    lon = nmea_to_decimal(parts[4], parts[5][:1] if len(parts[5]) else "")
                # ✅ nieuw: $GNGLL (gebruikt door veel moderne GNSS-modules)
                elif line.startswith("$GNGLL") and len(parts) > 5:
                    lat = nmea_to_decimal(parts[1], parts[2][:1] if len(parts[2]) else "")
                    lon = nmea_to_decimal(parts[3], parts[4][:1] if len(parts[4]) else "")

                if lat is not None and lon is not None:
                    with state_lock:
                        gps_lat, gps_lon, gps_have, gps_last = lat, lon, True, int(time.time())
                    print(f"[GPS] Positie ontvangen: {lat:.5f}, {lon:.5f}")
            except socket.timeout:
                pass
            except Exception as e:
                print(f"[GPS] Fout: {e}")

            # GPS verloren na 15 sec inactiviteit
            if int(time.time()) - gps_last > 15:
                with state_lock:
                    gps_have = False

    threading.Thread(target=loop, daemon=True).start()
