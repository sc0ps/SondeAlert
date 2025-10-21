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
    """Start UDP listener voor NMEA (RMC/GGA) op opgegeven poort."""
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
                # $GPRMC
                # $GPGGA
                parts = line.split(",")
                if line.startswith("$GPRMC") and len(parts) > 6:
                    # lat, N/S, lon, E/W
                    lat = nmea_to_decimal(parts[3], parts[4][:1] if len(parts[4]) else "")
                    lon = nmea_to_decimal(parts[5], parts[6][:1] if len(parts[6]) else "")
                elif line.startswith("$GPGGA") and len(parts) > 5:
                    lat = nmea_to_decimal(parts[2], parts[3][:1] if len(parts[3]) else "")
                    lon = nmea_to_decimal(parts[4], parts[5][:1] if len(parts[5]) else "")
                else:
                    lat = lon = None

                if lat is not None and lon is not None:
                    with state_lock:
                        gps_lat, gps_lon, gps_have, gps_last = lat, lon, True, int(time.time())
            except socket.timeout:
                pass
            except Exception:
                # bescherm tegen rare/gebroken NMEA regels
                pass

            if int(time.time()) - gps_last > 15:
                with state_lock:
                    gps_have = False

    threading.Thread(target=loop, daemon=True).start()
