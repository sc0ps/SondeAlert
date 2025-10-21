import socket
import time
import threading
from .utils import state_lock

# Globale variabelen (zichtbaar voor andere modules)
__all__ = ["gps_have", "gps_lat", "gps_lon", "gps_last"]

gps_have = False
gps_lat = 0.0
gps_lon = 0.0
gps_last = 0

def nmea_to_decimal(nmea, hemi):
    """Converteer NMEA-coördinaten naar decimale graden."""
    if not nmea:
        return None
    try:
        raw = float(nmea)
        deg = int(raw / 100)
        minutes = raw - deg * 100
        dec = deg + minutes / 60.0
        if hemi in ("S", "W"):
            dec = -dec
        return dec
    except Exception:
        return None

def start(settings):
    """Luister op UDP en verwerk NMEA-zinnen (RMC, GGA, GLL)."""
    global gps_have, gps_lat, gps_lon, gps_last

    port = int(settings.get("GPS_PORT", 5050))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(1.0)

    print(f"[GPS] Luistert op UDP-poort {port}")

    def loop():
        global gps_have, gps_lat, gps_lon, gps_last
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                line = data.decode(errors="ignore").strip()
                if not line.startswith("$"):
                    continue

                parts = line.split(",")
                lat = lon = None

                # Herken verschillende NMEA-typen
                if line.startswith("$GPRMC") and len(parts) > 6:
                    lat = nmea_to_decimal(parts[3], parts[4][:1])
                    lon = nmea_to_decimal(parts[5], parts[6][:1])
                elif line.startswith("$GPGGA") and len(parts) > 5:
                    lat = nmea_to_decimal(parts[2], parts[3][:1])
                    lon = nmea_to_decimal(parts[4], parts[5][:1])
                elif line.startswith("$GNGLL") and len(parts) > 5:
                    lat = nmea_to_decimal(parts[1], parts[2][:1])
                    lon = nmea_to_decimal(parts[3], parts[4][:1])

                # Wanneer coördinaten geldig zijn → opslaan
                if lat is not None and lon is not None:
                    with state_lock:
                        gps_lat = lat
                        gps_lon = lon
                        gps_have = True
                        gps_last = int(time.time())
                    print(f"[GPS] Positie ontvangen: {lat:.5f}, {lon:.5f}")
            except socket.timeout:
                pass
            except Exception as e:
                print(f"[GPS] Fout bij verwerken: {e}")

            # Als er 15 seconden geen update is → fix verloren
            if int(time.time()) - gps_last > 15 and gps_have:
                with state_lock:
                    gps_have = False
                print("[GPS] Geen signaal meer - fix verloren")

    threading.Thread(target=loop, daemon=True).start()
