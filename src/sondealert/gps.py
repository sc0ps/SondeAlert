import socket, time, threading
from .utils import state_lock

gps_have, gps_lat, gps_lon, gps_last = False, 0.0, 0.0, 0

def nmea_to_decimal(nmea, hemi):
    if not nmea:
        return None
    raw = float(nmea)
    deg, minutes = int(raw / 100), raw - int(raw / 100) * 100
    dec = deg + minutes / 60.0
    return -dec if hemi in ("S", "W") else dec

def start(settings):
    port = int(settings.get("GPS_PORT", 5050))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    s.settimeout(1.0)
    print(f"[GPS] Luistert op UDP-poort {port}")

    def loop():
        global gps_have, gps_lat, gps_lon, gps_last
        while True:
            try:
                data, _ = s.recvfrom(2048)
                parts = data.decode(errors="ignore").split(",")
                if parts[0].endswith("RMC") and len(parts) >= 7:
                    lat = nmea_to_decimal(parts[3], parts[4][:1])
                    lon = nmea_to_decimal(parts[5], parts[6][:1])
                elif parts[0].endswith("GGA") and len(parts) >= 6:
                    lat = nmea_to_decimal(parts[2], parts[3][:1])
                    lon = nmea_to_decimal(parts[4], parts[5][:1])
                else:
                    lat = lon = None

                if lat and lon:
                    with state_lock:
                        gps_lat, gps_lon, gps_have, gps_last = lat, lon, True, int(time.time())
            except socket.timeout:
                pass

            if int(time.time()) - gps_last > 15:
                with state_lock:
                    gps_have = False
    threading.Thread(target=loop, daemon=True).start()
