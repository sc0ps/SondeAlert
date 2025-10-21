import socket
import threading
import logging
import re

log = logging.getLogger("gps")

# Laatste bekende positie
_last_lat = None
_last_lon = None

def get_last_position():
    """Retourneer de laatst bekende GPS-positie (lat, lon)."""
    return _last_lat, _last_lon


def _parse_nmea_latlon(lat_str, lat_dir, lon_str, lon_dir):
    """Zet NMEA latitude/longitude om naar decimale graden."""
    try:
        # latitude: DDMM.MMMM, longitude: DDDMM.MMMM
        lat_deg = int(lat_str[:2])
        lat_min = float(lat_str[2:])
        lon_deg = int(lon_str[:3])
        lon_min = float(lon_str[3:])

        lat = lat_deg + (lat_min / 60)
        lon = lon_deg + (lon_min / 60)
        if lat_dir == "S":
            lat = -lat
        if lon_dir == "W":
            lon = -lon
        return round(lat, 5), round(lon, 5)
    except Exception:
        return None, None


def _listen_udp(port):
    """Luister naar inkomende GPS-data via UDP."""
    global _last_lat, _last_lon

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    log.info(f"Luistert op UDP-poort {port} voor GPS-data")

    pattern_gga = re.compile(r"\$..GGA")
    pattern_rmc = re.compile(r"\$..RMC")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            line = data.decode(errors="ignore").strip()
            log.info(f"Ontvangen ruwe GPS-data van {addr}: {line}")

            if pattern_rmc.search(line):
                # $GNRMC,<time>,A,<lat>,<N/S>,<lon>,<E/W>,...
                parts = line.split(",")
                if len(parts) >= 7 and parts[2] == "A":
                    lat, lon = _parse_nmea_latlon(parts[3], parts[4], parts[5], parts[6])
                    if lat and lon:
                        _last_lat, _last_lon = lat, lon
                        log.info(f"GPS-positie ontvangen (RMC): {lat}, {lon}")

            elif pattern_gga.search(line):
                # $GNGGA,<time>,<lat>,<N/S>,<lon>,<E/W>,<fix>,...
                parts = line.split(",")
                if len(parts) >= 6:
                    lat, lon = _parse_nmea_latlon(parts[2], parts[3], parts[4], parts[5])
                    if lat and lon:
                        _last_lat, _last_lon = lat, lon
                        log.info(f"GPS-positie ontvangen: {lat}, {lon}")

        except Exception as e:
            log.error(f"Fout bij verwerken GPS-data: {e}")


def start_gps_thread(port=5050):
    """Start een aparte thread die luistert naar GPS-data via UDP."""
    t = threading.Thread(target=_listen_udp, args=(port,), daemon=True)
    t.start()
    log.info("GPS-thread gestart.")
