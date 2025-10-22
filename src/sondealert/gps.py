# /app/src/sondealert/gps.py
import socket, time, logging
from .state import set_gps

def _nmea_to_decimal(nmea, hemi):
    if not nmea: return None
    try:
        raw = float(nmea)
        deg = int(raw/100)
        minutes = raw - deg*100
        dec = deg + minutes/60.0
        return -dec if hemi in ("S","W") else dec
    except:
        return None

def start_gps_listener(gps_port):
    logging.info("[gps] GPS thread started.")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", int(gps_port)))
    s.settimeout(1.0)
    logging.info("[gps] Listening on UDP port %s for GPS data", gps_port)

    last = 0
    while True:
        try:
            data, _ = s.recvfrom(4096)
            parts = data.decode(errors="ignore").split(",")
            lat = lon = None
            if parts[0].endswith("RMC") and len(parts) >= 7:
                lat = _nmea_to_decimal(parts[3], parts[4][:1])
                lon = _nmea_to_decimal(parts[5], parts[6][:1])
            elif parts[0].endswith("GGA") and len(parts) >= 6:
                lat = _nmea_to_decimal(parts[2], parts[3][:1])
                lon = _nmea_to_decimal(parts[4], parts[5][:1])

            if lat and lon:
                set_gps(lat, lon, True)
                logging.info("[gps] Received GPS position: %.5f, %.5f (fix=True)", lat, lon)
                last = int(time.time())
        except socket.timeout:
            pass
        except Exception as e:
            logging.warning("[gps] Parse error: %s", e)

        if int(time.time()) - last > 15:
            # markeer als geen fix
            set_gps(None, None, False)
            time.sleep(0.2)
